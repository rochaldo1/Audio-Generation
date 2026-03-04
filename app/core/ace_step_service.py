from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.models.project_models import GenerationParams, VocalParams


@dataclass
class AceStepConfig:
    """
    Lightweight config for ACE-Step pipeline instantiation.
    """

    dtype: str = "bfloat16"
    cpu_offload: bool = True
    overlapped_decode: bool = True

    # Reasonable defaults inspired by official examples
    infer_step: int = 60
    guidance_scale: float = 15.0
    scheduler_type: str = "euler"
    cfg_type: str = "apg"
    omega_scale: float = 10.0
    guidance_interval: float = 0.5
    guidance_interval_decay: float = 0.0
    min_guidance_scale: float = 3.0
    use_erg_tag: bool = True
    use_erg_lyric: bool = True
    use_erg_diffusion: bool = True


class AceStepService:
    """
    Wrapper around ACE-Step 1.5 pipeline.

    Отвечает за:
    - генерацию инструментала (text->music),
    - генерацию полной песни (text+lyrics->song).
    """

    def __init__(self, config: Optional[AceStepConfig] = None) -> None:
        self.config = config or AceStepConfig()
        self._pipeline = None

    def _get_pipeline(self):
        if self._pipeline is None:
            try:
                from acestep.pipeline_ace_step import ACEStepPipeline  # type: ignore
            except ImportError as exc:
                raise RuntimeError(
                    "ace-step is not installed. Install it via "
                    "`pip install git+https://github.com/ace-step/ACE-Step.git`."
                ) from exc

            self._pipeline = ACEStepPipeline(
                dtype=self.config.dtype,
                cpu_offload=self.config.cpu_offload,
                overlapped_decode=self.config.overlapped_decode,
            )
        return self._pipeline

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #

    def generate_instrumental(
        self,
        params: GenerationParams,
        output_path: Path,
    ) -> Path:
        """
        Generate an instrumental track using ACE-Step.
        """
        pipe = self._get_pipeline()

        duration = max(1.0, float(params.duration_seconds))
        prompt = self._build_instrumental_prompt(params)

        # Инструментал без вокала: специальный маркер в lyrics.
        lyrics = "[inst]"

        manual_seeds = params.seed if params.seed is not None else 1

        pipe(
            audio_duration=duration,
            prompt=prompt,
            lyrics=lyrics,
            format="wav",
            save_path=str(output_path),
            manual_seeds=manual_seeds,
            infer_step=self.config.infer_step,
            guidance_scale=self.config.guidance_scale,
            scheduler_type=self.config.scheduler_type,
            cfg_type=self.config.cfg_type,
            omega_scale=self.config.omega_scale,
            guidance_interval=self.config.guidance_interval,
            guidance_interval_decay=self.config.guidance_interval_decay,
            min_guidance_scale=self.config.min_guidance_scale,
            use_erg_tag=self.config.use_erg_tag,
            use_erg_lyric=False,
            use_erg_diffusion=self.config.use_erg_diffusion,
        )

        return output_path

    def generate_song(
        self,
        gen_params: GenerationParams,
        vocal_params: VocalParams,
        output_path: Path,
    ) -> Path:
        """
        Generate a full song (music + vocals) from prompt and lyrics.
        """
        pipe = self._get_pipeline()

        duration = max(1.0, float(gen_params.duration_seconds))
        prompt = self._build_song_prompt(gen_params, vocal_params)
        lyrics = vocal_params.lyrics or "la la la"

        manual_seeds = gen_params.seed if gen_params.seed is not None else 1

        pipe(
            audio_duration=duration,
            prompt=prompt,
            lyrics=lyrics,
            format="wav",
            save_path=str(output_path),
            manual_seeds=manual_seeds,
            infer_step=self.config.infer_step,
            guidance_scale=self.config.guidance_scale,
            scheduler_type=self.config.scheduler_type,
            cfg_type=self.config.cfg_type,
            omega_scale=self.config.omega_scale,
            guidance_interval=self.config.guidance_interval,
            guidance_interval_decay=self.config.guidance_interval_decay,
            min_guidance_scale=self.config.min_guidance_scale,
            use_erg_tag=self.config.use_erg_tag,
            use_erg_lyric=self.config.use_erg_lyric,
            use_erg_diffusion=self.config.use_erg_diffusion,
        )

        return output_path

    # --------------------------------------------------------------------- #
    # Prompt helpers
    # --------------------------------------------------------------------- #

    def _build_instrumental_prompt(self, params: GenerationParams) -> str:
        parts: list[str] = []
        if params.prompt:
            parts.append(params.prompt.strip())
        else:
            parts.append("instrumental music")

        if params.genre:
            parts.append(f"genre: {params.genre}")
        if params.tempo_bpm:
            parts.append(f"tempo: {params.tempo_bpm} bpm")

        density = params.arrangement_density or "medium"
        complexity = params.structure_complexity or "medium"

        parts.append(f"arrangement density: {density}")
        parts.append(f"structure complexity: {complexity}")
        parts.append("no vocals, instrumental only")

        return ", ".join(parts)

    def _build_song_prompt(
        self,
        gen_params: GenerationParams,
        vocal_params: VocalParams,
    ) -> str:
        parts: list[str] = []
        if gen_params.prompt:
            parts.append(gen_params.prompt.strip())
        else:
            parts.append("full song with vocals")

        if gen_params.genre:
            parts.append(f"genre: {gen_params.genre}")
        if gen_params.tempo_bpm:
            parts.append(f"tempo: {gen_params.tempo_bpm} bpm")

        parts.append(f"vocal style: {vocal_params.style}")
        parts.append(f"delivery: {vocal_params.delivery}")
        parts.append(f"intensity: {vocal_params.intensity:.2f}")

        return ", ".join(parts)

