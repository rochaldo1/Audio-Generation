from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import torch


@dataclass
class ModelConfig:
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    musicgen_model_size: str = "small"  # tiny / small / medium


class ModelManager:
    """
    Central place to lazily load and manage heavy models (MusicGen, NNSVS).
    Takes GPU VRAM limitations into account by preferring smaller models.
    """

    def __init__(self, config: Optional[ModelConfig] = None) -> None:
        self.config = config or ModelConfig()
        self._musicgen_model = None
        self._nnsvs_engines: dict[str, object] = {}

    @property
    def device(self) -> torch.device:
        return torch.device(self.config.device)

    def get_musicgen(self):
        """
        Lazily loads the MusicGen model with the configured size.
        """
        if self._musicgen_model is None:
            try:
                from audiocraft.models import musicgen
            except ImportError as exc:
                raise RuntimeError(
                    "audiocraft is not installed. Install it via `pip install audiocraft`."
                ) from exc

            model_name = self.config.musicgen_model_size
            # 'small' is a good compromise for 4 GB VRAM
            self._musicgen_model = musicgen.MusicGen.get_pretrained(
                model_name, device=str(self.device)
            )
        return self._musicgen_model

    def get_nnsvs_engine(self, voice_id: str = "default"):
        """
        Lazily loads an NNSVS engine for a given voice.

        The actual loading logic (paths to pre-trained models, configs, etc.)
        should be configured separately. Here we provide a placeholder that can
        be wired to your NNSVS recipe.
        """
        if voice_id in self._nnsvs_engines:
            return self._nnsvs_engines[voice_id]

        try:
            from nnsvs import inference as nnsvs_inference  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "nnsvs is not installed. Install it via `pip install nnsvs`."
            ) from exc

        # TODO: wire this to your actual NNSVS recipe and model paths.
        # For now we raise an informative error to indicate that configuration is needed.
        raise NotImplementedError(
            "NNSVS engine loading is not configured. "
            "Configure paths to pre-trained NNSVS models and replace this stub."
        )

