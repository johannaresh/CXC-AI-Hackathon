"""
Strategy Encoder — Variational Autoencoder (VAE) that learns latent
representations of strategy feature vectors. The reconstruction error
doubles as an anomaly signal for downstream overfit detection.
"""

import os
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

_MODEL_DIR = Path(__file__).resolve().parents[3] / "data" / "models"
_encoder_model = None
_feature_scaler = None


class StrategyVAE(nn.Module):
    def __init__(self, input_dim: int = 20, latent_dim: int = 16):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
        )
        self.fc_mu = nn.Linear(64, latent_dim)
        self.fc_logvar = nn.Linear(64, latent_dim)
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.Linear(128, input_dim),
        )

    def encode(self, x: torch.Tensor):
        h = self.encoder(x)
        return self.fc_mu(h), self.fc_logvar(h)

    def reparameterize(self, mu: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        return self.decoder(z)

    def forward(self, x: torch.Tensor):
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        recon = self.decode(z)
        return recon, mu, logvar


def vae_loss(recon_x: torch.Tensor, x: torch.Tensor,
             mu: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
    """VAE loss = MSE reconstruction + KL divergence."""
    mse = nn.functional.mse_loss(recon_x, x, reduction="sum")
    kl = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
    return mse + kl


def _load_model():
    """Lazily load trained VAE and scaler from disk."""
    global _encoder_model, _feature_scaler

    model_path = _MODEL_DIR / "strategy_encoder.pt"
    scaler_path = _MODEL_DIR / "feature_scaler.pkl"

    if model_path.exists() and scaler_path.exists():
        import pickle
        _encoder_model = StrategyVAE(input_dim=20, latent_dim=16)
        _encoder_model.load_state_dict(torch.load(model_path, weights_only=True))
        _encoder_model.eval()

        with open(scaler_path, "rb") as f:
            _feature_scaler = pickle.load(f)
    else:
        _encoder_model = None
        _feature_scaler = None


def encode_strategy(features: list[float]) -> list[float]:
    """Encode strategy features into a 16-dim latent vector.

    Args:
        features: List of 20 feature values (ordered per FEATURE_NAMES).

    Returns:
        16-dimensional latent vector.
    """
    global _encoder_model, _feature_scaler
    if _encoder_model is None or _feature_scaler is None:
        _load_model()

    if _encoder_model is None or _feature_scaler is None:
        # No trained model or scaler available — return zeros
        return [0.0] * 16

    arr = np.array(features, dtype=np.float64).reshape(1, -1)
    arr = _feature_scaler.transform(arr)
    tensor = torch.tensor(arr, dtype=torch.float32)

    with torch.no_grad():
        mu, _ = _encoder_model.encode(tensor)
    return mu.squeeze(0).tolist()


def get_reconstruction_error(features: list[float]) -> float:
    """Compute VAE reconstruction error (MSE) for anomaly detection.

    High error = strategy is unlike anything in training distribution.

    Args:
        features: List of 20 feature values.

    Returns:
        Reconstruction MSE (float). Returns 0.0 if no model is loaded.
    """
    global _encoder_model, _feature_scaler
    if _encoder_model is None or _feature_scaler is None:
        _load_model()

    if _encoder_model is None or _feature_scaler is None:
        return 0.0

    arr = np.array(features, dtype=np.float64).reshape(1, -1)
    scaled = _feature_scaler.transform(arr)
    tensor = torch.tensor(scaled, dtype=torch.float32)

    with torch.no_grad():
        recon, _, _ = _encoder_model(tensor)
        mse = nn.functional.mse_loss(recon, tensor).item()
    return float(mse)
