from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from app.models.project_models import (
    ContentType,
    GenerationParams,
    Project,
    SfxParams,
    TrackType,
    TrackVersion,
    VocalParams,
)


class ProjectRepository:
    """
    Simple JSON-based storage for projects and track versions.
    """

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        if root_dir is None:
            root_dir = Path.cwd() / "projects"
        self.root_dir = root_dir
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _project_dir(self, project_id: str) -> Path:
        return self.root_dir / project_id

    def _project_meta_path(self, project_id: str) -> Path:
        return self._project_dir(project_id) / "project.json"

    def save_project(self, project: Project) -> None:
        project_dir = self._project_dir(project.id)
        project_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "id": project.id,
            "name": project.name,
            "content_type": project.content_type.value,
            "track_versions": [self._track_to_dict(tv) for tv in project.track_versions],
        }

        with self._project_meta_path(project.id).open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_project(self, project_id: str) -> Optional[Project]:
        meta_path = self._project_meta_path(project_id)
        if not meta_path.exists():
            return None

        with meta_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        project_dir = self._project_dir(project_id)
        track_versions = [self._track_from_dict(tv, project_dir) for tv in data.get("track_versions", [])]

        return Project(
            id=data["id"],
            name=data["name"],
            base_path=project_dir,
            content_type=ContentType(data.get("content_type", ContentType.INSTRUMENTAL.value)),
            track_versions=track_versions,
        )

    def list_projects(self) -> List[Project]:
        projects: List[Project] = []
        for project_dir in self.root_dir.iterdir():
            if not project_dir.is_dir():
                continue
            project = self.load_project(project_dir.name)
            if project is not None:
                projects.append(project)
        return projects

    @staticmethod
    def _track_to_dict(tv: TrackVersion) -> Dict:
        return {
            "id": tv.id,
            "track_type": tv.track_type.value,
            "audio_path_wav": str(tv.audio_path_wav),
            "audio_path_mp3": str(tv.audio_path_mp3) if tv.audio_path_mp3 else None,
            "audio_path_flac": str(tv.audio_path_flac) if tv.audio_path_flac else None,
            "generation_params": vars(tv.generation_params) if tv.generation_params else None,
            "vocal_params": vars(tv.vocal_params) if tv.vocal_params else None,
            "sfx_params": vars(tv.sfx_params) if tv.sfx_params else None,
            "duration_seconds": tv.duration_seconds,
            "sample_rate": tv.sample_rate,
            "bitrate_kbps": tv.bitrate_kbps,
            "genre": tv.genre,
            "mood": tv.mood,
            "tempo_bpm": tv.tempo_bpm,
        }

    @staticmethod
    def _track_from_dict(data: Dict, project_dir: Path) -> TrackVersion:
        gen_params = data.get("generation_params")
        vocal_params = data.get("vocal_params")
        sfx_params = data.get("sfx_params")

        return TrackVersion(
            id=data["id"],
            track_type=TrackType(data["track_type"]),
            audio_path_wav=project_dir / Path(data["audio_path_wav"]).name,
            audio_path_mp3=project_dir / Path(data["audio_path_mp3"]).name if data.get("audio_path_mp3") else None,
            audio_path_flac=project_dir / Path(data["audio_path_flac"]).name if data.get("audio_path_flac") else None,
            generation_params=GenerationParams(**gen_params) if gen_params else None,
            vocal_params=VocalParams(**vocal_params) if vocal_params else None,
            sfx_params=SfxParams(**sfx_params) if sfx_params else None,
            duration_seconds=data.get("duration_seconds"),
            sample_rate=data.get("sample_rate"),
            bitrate_kbps=data.get("bitrate_kbps"),
            genre=data.get("genre"),
            mood=data.get("mood"),
            tempo_bpm=data.get("tempo_bpm"),
        )

