"""
Mapping Strategy - Strategie di identificazione settore basate su AI/Attention.
"""

from abc import ABC, abstractmethod

import torch
import torch.nn.functional as F

from src.domain.constants import SETTORE_KEYS, AssetCategory


class MappingStrategy(ABC):
    @abstractmethod
    def identify_sector(self, columns: list[str]) -> AssetCategory:
        pass


class AttentionMappingStrategy(MappingStrategy):
    """
    Usa un meccanismo di attenzione (Softmax) per determinare il settore dell'asset.
    Implementazione basata sulla logica originale RGD-Alpha.
    """

    def identify_sector(self, columns: list[str]) -> AssetCategory:
        scores = {"FINANCE": 0.0, "LOGISTICS": 0.0, "RELATIONS": 0.0}
        cols_lower = [str(c).lower() for c in columns]

        for col in cols_lower:
            for settore, keys in SETTORE_KEYS.items():
                for key in keys:
                    if key == col:
                        scores[settore] += 2.0  # Match esatto
                    elif key in col:
                        scores[settore] += 1.0

        # Conversione in Tensor per calcolo Softmax
        scores_list = list(scores.values())
        scores_tensor = torch.tensor([scores_list], dtype=torch.float32)

        if scores_tensor.sum() == 0:
            return AssetCategory.GENERAL

        # Calcolo Attenzione
        attention_weights = F.softmax(scores_tensor, dim=-1).flatten()
        sector_names = list(scores.keys())

        # Selezione del settore con peso maggiore
        max_idx = torch.argmax(attention_weights).item()
        if attention_weights[max_idx] < 0.45:
            return AssetCategory.GENERAL

        return AssetCategory(sector_names[max_idx])
