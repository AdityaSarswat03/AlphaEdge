"""
Lightweight Transformer model for stock prediction.
"""
import math
import numpy as np
from typing import Any, Dict, Optional
from pathlib import Path
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler
from alphaedge.models.base import BaseModel
from alphaedge.logger import log


class _PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 500):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        pos = torch.arange(0, max_len).unsqueeze(1).float()
        div = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(pos * div)
        pe[:, 1::2] = torch.cos(pos * div)
        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:, : x.size(1)]


class _TransformerNet(nn.Module):
    def __init__(self, input_size: int, d_model: int = 64, n_heads: int = 4, n_layers: int = 2, dropout: float = 0.1):
        super().__init__()
        self.input_proj = nn.Linear(input_size, d_model)
        self.pos_enc = _PositionalEncoding(d_model)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=n_heads, dim_feedforward=d_model * 4,
            dropout=dropout, batch_first=True,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        self.fc = nn.Linear(d_model, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.input_proj(x)
        x = self.pos_enc(x)
        x = self.encoder(x)
        return self.fc(x[:, -1, :])


class TransformerModel(BaseModel):
    """Transformer time-series model."""

    name = "transformer"

    def __init__(self, sequence_length: int = 60, d_model: int = 64, n_heads: int = 4, n_layers: int = 2):
        self.sequence_length = sequence_length
        self.d_model = d_model
        self.n_heads = n_heads
        self.n_layers = n_layers
        self.scaler = MinMaxScaler()
        self.model: Optional[_TransformerNet] = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _build(self, input_size: int) -> _TransformerNet:
        return _TransformerNet(input_size, self.d_model, self.n_heads, self.n_layers).to(self.device)

    def _make_sequences(self, X: np.ndarray, y: Optional[np.ndarray] = None):
        seqs, targets = [], []
        for i in range(len(X) - self.sequence_length):
            seqs.append(X[i: i + self.sequence_length])
            if y is not None:
                targets.append(y[i + self.sequence_length])
        if y is not None:
            return np.array(seqs), np.array(targets)
        return np.array(seqs)

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
            torch.FloatTensor(X_seq), torch.FloatTensor(y_seq).unsqueeze(1),
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
            best_loss = min(best_loss, avg)
            if (epoch + 1) % 10 == 0:
                log.info(f"Transformer epoch {epoch+1}/{epochs}  loss={avg:.6f}")

        log.info(f"Transformer training done – best loss {best_loss:.6f}")
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
            log.info("Transformer: applied pending state dict from loaded checkpoint")
        elif self.model is None:
            raise RuntimeError("Model not trained.")
        else:
            X_scaled = self.scaler.transform(X)
            X_seq = self._make_sequences(X_scaled)

        self.model.eval()
        with torch.no_grad():
            preds = self.model(torch.FloatTensor(X_seq).to(self.device)).cpu().numpy().flatten()
        return preds

    # ── Persistence ──────────────────────────────────────────────
    def save(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "state_dict": self.model.state_dict() if self.model else None,
                "scaler": self.scaler,
                "config": {
                    "seq_len": self.sequence_length,
                    "d_model": self.d_model,
                    "n_heads": self.n_heads,
                    "n_layers": self.n_layers,
                },
            },
            path,
        )
        log.info(f"Transformer saved → {path}")

    def load(self, path: str) -> None:
        ckpt = torch.load(path, map_location=self.device, weights_only=True)
        self.scaler = ckpt["scaler"]
        cfg = ckpt["config"]
        self.sequence_length = cfg["seq_len"]
        self.d_model = cfg["d_model"]
        self.n_heads = cfg["n_heads"]
        self.n_layers = cfg["n_layers"]
        self._pending_state = ckpt.get("state_dict")
        log.info(f"Transformer loaded ← {path}")
