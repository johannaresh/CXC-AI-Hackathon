"""
Train VAE Strategy Encoder on synthetic training data.

Usage:
    python -m scripts.train_encoder
"""

import json
import pickle
import sys
from pathlib import Path

import numpy as np
import torch
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.services.feature_engineering import build_feature_vector, FEATURE_NAMES
from backend.app.models.strategy_encoder import StrategyVAE, vae_loss

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
MODEL_DIR = DATA_DIR / "models"


def load_training_features() -> np.ndarray:
    """Load training data and compute feature vectors."""
    data_path = DATA_DIR / "synthetic" / "training_strategies.json"
    with open(data_path) as f:
        strategies = json.load(f)

    print(f"Loaded {len(strategies)} strategies from {data_path}")

    features_list = []
    for strat in strategies:
        feat = build_feature_vector(strat)
        # Use only the first 19 features (exclude reconstruction_error)
        row = [feat[name] for name in FEATURE_NAMES[:19]] + [0.0]
        features_list.append(row)

    return np.array(features_list, dtype=np.float64)


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Load and scale features
    X = load_training_features()
    print(f"Feature matrix shape: {X.shape}")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Save scaler
    scaler_path = MODEL_DIR / "feature_scaler.pkl"
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)
    print(f"Saved scaler -> {scaler_path}")

    # Create dataloader
    tensor_x = torch.tensor(X_scaled, dtype=torch.float32)
    dataset = TensorDataset(tensor_x)
    loader = DataLoader(dataset, batch_size=64, shuffle=True)

    # Build and train VAE
    model = StrategyVAE(input_dim=20, latent_dim=16)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    num_epochs = 100
    model.train()

    for epoch in range(num_epochs):
        total_loss = 0.0
        for (batch,) in loader:
            optimizer.zero_grad()
            recon, mu, logvar = model(batch)
            loss = vae_loss(recon, batch, mu, logvar)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(dataset)
        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"  Epoch {epoch + 1:3d}/{num_epochs}  loss={avg_loss:.4f}")

    # Save model
    model_path = MODEL_DIR / "strategy_encoder.pt"
    torch.save(model.state_dict(), model_path)
    print(f"Saved VAE model -> {model_path}")

    # Evaluate: compute reconstruction errors
    model.eval()
    with torch.no_grad():
        recon, _, _ = model(tensor_x)
        per_sample_mse = torch.mean((recon - tensor_x) ** 2, dim=1).numpy()

    print(f"\nReconstruction error stats:")
    print(f"  Mean: {np.mean(per_sample_mse):.6f}")
    print(f"  Std:  {np.std(per_sample_mse):.6f}")
    print(f"  Min:  {np.min(per_sample_mse):.6f}")
    print(f"  Max:  {np.max(per_sample_mse):.6f}")


if __name__ == "__main__":
    main()
