from __future__ import annotations

from pathlib import Path
from typing import Optional

import soundfile as sf
import torch

from app.core.model_manager import ModelManager
from app.models.project_models import GenerationParams


class MusicGenService:
    """
    Wrapper around MusicGen to generate instrumental music and SFX from text prompts.
    """

    def __init__(self, model_manager: ModelManager) -> None:
        self.model_manager = model_manager

    def generate_instrumental(
        self,
        params: GenerationParams,
        output_path: Path,
        sample_rate: int = 32000,
    ) -> Path:
        """
        Generate an instrumental track from text description.
        """
        model = self.model_manager.get_musicgen()

        duration = max(1, int(params.duration_seconds))
        device = self.model_manager.device

        # MusicGen expects a list of prompts.
        model.set_generation_params(
            duration=duration,
            top_k=250,
            top_p=0.0,
            temperature=1.0,
            cfg_coef=3.0,
        )

        with torch.no_grad():
            wav = model.generate([params.prompt], progress=True)

        # wav: Tensor [batch, channels, time]; we take the first sample
        wav_tensor = wav[0].cpu()
        sf.write(str(output_path), wav_tensor.T.numpy(), samplerate=sample_rate)
        return output_path

