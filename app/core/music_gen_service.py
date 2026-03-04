from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import soundfile as sf
import torch

from app.core.model_manager import ModelManager
from app.models.project_models import GenerationParams


class MusicGenService:
    """
    Wrapper around MusicGen (via Hugging Face transformers)
    to generate instrumental music and SFX from text prompts.
    """

    def __init__(self, model_manager: ModelManager) -> None:
        self.model_manager = model_manager

    def _get_model(self) -> Tuple[object, object]:
        processor, model = self.model_manager.get_musicgen()
        return processor, model

    def generate_instrumental(
        self,
        params: GenerationParams,
        output_path: Path,
        sample_rate: Optional[int] = None,
    ) -> Path:
        """
        Generate an instrumental track from text description using transformers MusicGen.
        """
        processor, model = self._get_model()
        device = self.model_manager.device

        prompt = params.prompt or ""
        duration = max(1, int(params.duration_seconds))

        inputs = processor(
            text=[prompt],
            padding=True,
            return_tensors="pt",
        ).to(device)

        # Heuristic: number of audio tokens is roughly proportional to duration.
        max_new_tokens = duration * 256

        with torch.no_grad():
            audio_values = model.generate(
                **inputs,
                do_sample=True,
                max_new_tokens=max_new_tokens,
            )

        audio = audio_values[0, 0].cpu().numpy()

        if sample_rate is None:
            model_sr = getattr(getattr(model, "config", None), "sample_rate", None)
            feat_sr = getattr(getattr(processor, "feature_extractor", None), "sampling_rate", None)
            sample_rate = model_sr or feat_sr or 32000

        sf.write(str(output_path), audio, samplerate=sample_rate)
        return output_path

