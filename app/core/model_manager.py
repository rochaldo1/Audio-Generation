from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

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
        self._musicgen_model: Optional[Tuple[object, object]] = None
        self._nnsvs_engines: dict[str, object] = {}

    @property
    def device(self) -> torch.device:
        return torch.device(self.config.device)

    def get_musicgen(self) -> Tuple[object, object]:
        """
        Lazily loads a MusicGen model from Hugging Face transformers.
        """
        if self._musicgen_model is None:
            try:
                from transformers import AutoProcessor, MusicgenForConditionalGeneration
            except ImportError as exc:
                raise RuntimeError(
                    "transformers is not installed. Install it via `pip install transformers`."
                ) from exc

            size_to_repo = {
                "tiny": "facebook/musicgen-small",
                "small": "facebook/musicgen-small",
                "medium": "facebook/musicgen-medium",
            }
            repo_id = size_to_repo.get(self.config.musicgen_model_size, "facebook/musicgen-small")

            processor = AutoProcessor.from_pretrained(repo_id)
            model = MusicgenForConditionalGeneration.from_pretrained(repo_id)
            model.to(self.device)

            self._musicgen_model = (processor, model)
        return self._musicgen_model

    def get_nnsvs_engine(self, voice_id: str = "default"):
        """
        Lazily loads an NNSVS engine for a given voice using pre-trained
        models hosted on Hugging Face.
        """
        if voice_id in self._nnsvs_engines:
            return self._nnsvs_engines[voice_id]

        try:
            from nnsvs.pretrained import create_svs_engine  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "nnsvs is not installed. Install it via `pip install nnsvs`."
            ) from exc

        voice_repo_map = {
            "default": "r9y9/yoko_latest",
        }
        repo_id = voice_repo_map.get(voice_id, "r9y9/yoko_latest")

        engine = create_svs_engine(repo_id)
        self._nnsvs_engines[voice_id] = engine
        return engine

