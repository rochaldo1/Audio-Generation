from __future__ import annotations

from pathlib import Path
from typing import Optional

import soundfile as sf  # type: ignore

from app.core.lyrics_to_labels import build_labels_from_lyrics
from app.core.model_manager import ModelManager
from app.models.project_models import VocalParams


class NNSVSService:
    """
    Wrapper around NNSVS for vocal synthesis using pre-trained voices.
    """

    def __init__(self, model_manager: ModelManager) -> None:
        self.model_manager = model_manager

    def synthesize_vocals(
        self,
        params: VocalParams,
        output_path: Path,
        reference_instrumental: Optional[Path] = None,
    ) -> Path:
        """
        Synthesize a vocal waveform from lyrics and vocal parameters.

        Currently uses a built-in demo score to generate HTS labels and
        the pre-trained voice engine loaded via ModelManager.
        """
        engine = self.model_manager.get_nnsvs_engine(params.voice_id)
        labels = build_labels_from_lyrics(params)

        wav, sr = engine.svs(labels)
        sf.write(str(output_path), wav, sr)
        return output_path

