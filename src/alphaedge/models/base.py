"""
Abstract base class for all prediction models.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import numpy as np
import pandas as pd


class BaseModel(ABC):
    """Every model must implement train, predict, save, load."""

    name: str = "base"

    @abstractmethod
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """Train the model. Return a dict of metrics."""
        ...

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Return predictions (1-D array)."""
        ...

    @abstractmethod
    def save(self, path: str) -> None:
        """Persist model artefacts to *path*."""
        ...

    @abstractmethod
    def load(self, path: str) -> None:
        """Restore model artefacts from *path*."""
        ...
