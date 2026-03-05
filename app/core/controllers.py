from __future__ import annotations

import random
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.audio.export_utils import export_to_flac, export_to_mp3
from app.audio.player import AudioPlayer
from app.core.ace_step_service import AceStepService
from app.core.model_manager import ModelManager
from app.models.project_models import (
    ContentType,
    GenerationParams,
    Project,
    SfxParams,
    TrackType,
    TrackVersion,
    VocalParams,
)
from app.storage.project_repository import ProjectRepository


@dataclass
class AppContext:
    model_manager: ModelManager
    ace_step_service: AceStepService
    project_repo: ProjectRepository
    audio_player: AudioPlayer


class ProjectController:
    def __init__(self, ctx: AppContext) -> None:
        self.ctx = ctx

    def create_project(self, name: str, content_type: ContentType) -> Project:
        project_id = uuid.uuid4().hex[:8]
        base_path = self.ctx.project_repo.root_dir / project_id
        base_path.mkdir(parents=True, exist_ok=True)
        project = Project(
            id=project_id,
            name=name,
            base_path=base_path,
            content_type=content_type,
        )
        self.ctx.project_repo.save_project(project)
        return project

    def save_project(self, project: Project) -> None:
        self.ctx.project_repo.save_project(project)

    def list_projects(self) -> list[Project]:
        return self.ctx.project_repo.list_projects()


class GenerationController:
    def __init__(self, ctx: AppContext) -> None:
        self.ctx = ctx

    def generate_instrumental(self, project: Project, params: GenerationParams) -> TrackVersion:
        out_wav = project.base_path / f"{uuid.uuid4().hex[:8]}_instr.wav"
        self.ctx.ace_step_service.generate_instrumental(params, out_wav)

        tv = TrackVersion(
            id=uuid.uuid4().hex[:8],
            track_type=TrackType.INSTRUMENTAL,
            audio_path_wav=out_wav,
            generation_params=params,
            engine="ace-step-1.5",
        )
        project.track_versions.append(tv)
        self.ctx.project_repo.save_project(project)
        return tv

    def create_variation(self, project: Project, base_track: TrackVersion) -> TrackVersion:
        """
        Create a new instrumental variation using the same parameters but a new seed.
        """
        if not base_track.generation_params:
            raise ValueError("Base track has no generation parameters for variation.")

        params = base_track.generation_params
        new_params = GenerationParams(
            prompt=params.prompt,
            duration_seconds=params.duration_seconds,
            tempo_bpm=params.tempo_bpm,
            genre=params.genre,
            arrangement_density=params.arrangement_density,
            structure_complexity=params.structure_complexity,
            # Use a new random seed so that ACE-Step produces an actual variation.
            seed=random.randint(1, 2**31 - 1),
        )
        return self.generate_instrumental(project, new_params)

    def generate_vocal(
        self,
        project: Project,
        params: VocalParams,
        gen_params: Optional[GenerationParams] = None,
    ) -> TrackVersion:
        """
        Generate full song (music + vocals) using ACE-Step.

        Если gen_params не указан, используется дефолтная заготовка.
        """
        if gen_params is None:
            gen_params = GenerationParams(
                prompt="vocal song",
                duration_seconds=30,
            )

        out_wav = project.base_path / f"{uuid.uuid4().hex[:8]}_song.wav"
        self.ctx.ace_step_service.generate_song(gen_params, params, out_wav)

        tv = TrackVersion(
            id=uuid.uuid4().hex[:8],
            track_type=TrackType.MIX,
            audio_path_wav=out_wav,
            vocal_params=params,
            generation_params=gen_params,
            engine="ace-step-1.5",
        )
        project.track_versions.append(tv)
        self.ctx.project_repo.save_project(project)
        return tv

    def generate_sfx(self, project: Project, params: SfxParams) -> TrackVersion:
        out_wav = project.base_path / f"{uuid.uuid4().hex[:8]}_sfx.wav"
        # Use dedicated SFX generation path in AceStepService so that
        # prompts explicitly describe a sound effect rather than an instrumental track.
        self.ctx.ace_step_service.generate_sfx(params, out_wav)

        tv = TrackVersion(
            id=uuid.uuid4().hex[:8],
            track_type=TrackType.SFX,
            audio_path_wav=out_wav,
            sfx_params=params,
            generation_params=None,
            engine="ace-step-1.5",
        )
        project.track_versions.append(tv)
        self.ctx.project_repo.save_project(project)
        return tv

    def export_track(self, track: TrackVersion, export_format: str) -> Path:
        if export_format == "wav":
            return track.audio_path_wav
        if export_format == "mp3":
            if track.audio_path_mp3 and track.audio_path_mp3.exists():
                return track.audio_path_mp3
            mp3_path = track.audio_path_wav.with_suffix(".mp3")
            export_to_mp3(track.audio_path_wav, mp3_path)
            track.audio_path_mp3 = mp3_path
            return mp3_path
        if export_format == "flac":
            if track.audio_path_flac and track.audio_path_flac.exists():
                return track.audio_path_flac
            flac_path = track.audio_path_wav.with_suffix(".flac")
            export_to_flac(track.audio_path_wav, flac_path)
            track.audio_path_flac = flac_path
            return flac_path
        raise ValueError(f"Unsupported export format: {export_format}")


class PlaybackController:
    def __init__(self, ctx: AppContext) -> None:
        self.ctx = ctx

    def play_track(self, track: TrackVersion) -> None:
        self.ctx.audio_player.play_file(track.audio_path_wav)

    def stop(self) -> None:
        self.ctx.audio_player.stop()

