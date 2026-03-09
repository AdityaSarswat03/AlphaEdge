"""
LSTM model for time-series stock prediction.
"""
import numpy as np
from typing import Any, Dict, Optional
from pathlib import Path
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler
import joblib
from alphaedge.models.base import BaseModel
from alphaedge.logger import log


class _LSTMNet(nn.Module):
    """PyTorch LSTM network."""

    def __init__(self, input_size: int, hidden_size: int = 64, num_layers: int = 2, dropout: float = 0.2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size, hidden_size, num_layers,
            batch_first=True, dropout=dropout if num_layers > 1 else 0.0,
        )
        self.fc1 = nn.Linear(hidden_size, 32)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(32, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        out = self.relu(self.fc1(out[:, -1, :]))
        return self.fc2(out)


class LSTMModel(BaseModel):
    """LSTM deep-learning model."""

    name = "lstm"

    def __init__(self, sequence_length: int = 60, hidden_size: int = 64, num_layers: int = 2):
        self.sequence_length = sequence_length
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.scaler = MinMaxScaler()
        self.model: Optional[_LSTMNet] = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ── helpers ──────────────────────────────────────────────────
    def _build(self, input_size: int) -> _LSTMNet:
        return _LSTMNet(input_size, self.hidden_size, self.num_layers).to(self.device)

    def _make_sequences(self, X: np.ndarray, y: Optional[np.ndarray] = None):
        """Create sliding-window sequences."""
        seqs, targets = [], []
        for i in range(len(X) - self.sequence_length):
            seqs.append(X[i: i + self.sequence_length])
            if y is not None:
                targets.append(y[i + self.sequence_length])
        seqs_arr = np.array(seqs)
        if y is not None:
            return seqs_arr, np.array(targets)
        return seqs_arr

    # ── Train ────────────────────────────────────────────────────
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        epochs: int = 50,
        batch_size: int = 64,
        lr: float = 0.001,
    ) -> Dict[str, Any]:
        X_scaled = self.scaler.fit_transform(X_train)
        X_seq, y_seq = self._make_sequences(X_scaled, y_train)

        if self.model is None:
            self.model = self._build(X_seq.shape[2])

        dataset = TensorDataset(
            torch.FloatTensor(X_seq),
            torch.FloatTensor(y_seq).unsqueeze(1),
        )
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        criterion = nn.MSELoss()

        self.model.train()
        best_loss = float("inf")
        for epoch in range(epochs):
            total_loss = 0.0
            for xb, yb in loader:
                xb, yb = xb.to(self.device), yb.to(self.device)
                optimizer.zero_grad()
                loss = criterion(self.model(xb), yb)
                loss.backward()
                optimizer.step()
                total_loss += loss.item() * xb.size(0)
            avg = total_loss / len(dataset)
            if avg < best_loss:
                best_loss = avg
            if (epoch + 1) % 10 == 0:
                log.info(f"LSTM epoch {epoch+1}/{epochs}  loss={avg:.6f}")

        log.info(f"LSTM training done – best loss {best_loss:.6f}")
        return {"best_loss": best_loss}

    # ── Predict ──────────────────────────────────────────────────
    def predict(self, X: np.ndarray) -> np.ndarray:
        # Apply pending state from load() if needed
        if self.model is None and hasattr(self, "_pending_state") and self._pending_state is not None:
            X_scaled = self.scaler.transform(X)
            X_seq = self._make_sequences(X_scaled)
            self.model = self._build(X_seq.shape[2])
            self.model.load_state_dict(self._pending_state)
            self._pending_state = None
            log.info("LSTM: applied pending state dict from loaded checkpoint")
        elif self.model is None:
            raise RuntimeError("Model not trained. Call train() first.")
        else:
            X_scaled = self.scaler.transform(X)
            X_seq = self._make_sequences(X_scaled)

        self.model.eval()
        with torch.no_grad():
            t = torch.FloatTensor(X_seq).to(self.device)
            preds = self.model(t).cpu().numpy().flatten()
        return preds

    # ── Persistence ──────────────────────────────────────────────
    def save(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "state_dict": self.model.state_dict() if self.model else None,
                "scaler": self.scaler,
                "seq_len": self.sequence_length,
                "hidden": self.hidden_size,
                "layers": self.num_layers,
            },
            path,
        )
        log.info(f"LSTM saved → {path}")

    def load(self, path: str) -> None:
        ckpt = torch.load(path, map_location=self.device, weights_only=True)
        self.scaler = ckpt["scaler"]
        self.sequence_length = ckpt["seq_len"]
        self.hidden_size = ckpt["hidden"]
        self.num_layers = ckpt["layers"]
        # Rebuild architecture – need a forward pass to infer input_size
        # so we defer building until predict() if state_dict is stored
        self._pending_state = ckpt.get("state_dict")
        log.info(f"LSTM loaded ← {path}")
