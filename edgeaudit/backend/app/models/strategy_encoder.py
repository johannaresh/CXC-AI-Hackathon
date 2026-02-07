"""
Strategy Encoder — PyTorch model that encodes strategy feature vectors
into a latent representation for downstream overfit detection and regime analysis.
"""

import torch
import torch.nn as nn


class StrategyEncoder(nn.Module):
    def __init__(self, input_dim: int = 64, latent_dim: int = 16):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, latent_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.encoder(x)


def encode_strategy(features: list[float]) -> list[float]:
    """Encode raw strategy features into a latent vector.

    TODO: Load trained weights from artifact store.
    TODO: Normalize input features before encoding.
    """
    model = StrategyEncoder(input_dim=len(features))
    model.eval()
    with torch.no_grad():
        tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0)
        latent = model(tensor)
    return latent.squeeze(0).tolist()
