from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.core.model_manager import ModelManager
from app.models.project_models import VocalParams


class NNSVSService:
    """
    Wrapper around NNSVS for vocal synthesis.

    NOTE: This is a configurable stub that expects you to wire it to
    actual NNSVS models and configurations.
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

        For now this method raises NotImplementedError to indicate that
        NNSVS recipe-specific wiring is required.
        """
        raise NotImplementedError(
            "NNSVSService.synthesize_vocals is not yet implemented. "
            "Configure NNSVS models and implement the synthesis pipeline."
        )

