from __future__ import annotations

import argparse
from pathlib import Path

from app.core.controllers import AppContext, GenerationController, ProjectController
from app.core.mix_service import MixService
from app.core.model_manager import ModelManager
from app.core.music_gen_service import MusicGenService
from app.core.nnsvs_service import NNSVSService
from app.models.project_models import ContentType, GenerationParams, Project
from app.storage.project_repository import ProjectRepository
from app.audio.player import AudioPlayer


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an instrumental track using MusicGen.")
    parser.add_argument("--prompt", required=True, help="Text description of the music.")
    parser.add_argument("--duration", type=int, default=15, help="Duration in seconds.")
    args = parser.parse_args()

    model_manager = ModelManager()
    music_service = MusicGenService(model_manager)
    nnsvs_service = NNSVSService(model_manager)
    mix_service = MixService()
    project_repo = ProjectRepository(Path.cwd() / "projects_cli")
    audio_player = AudioPlayer()

    ctx = AppContext(
        model_manager=model_manager,
        music_service=music_service,
        nnsvs_service=nnsvs_service,
        mix_service=mix_service,
        project_repo=project_repo,
        audio_player=audio_player,
    )

    project_controller = ProjectController(ctx)
    generation_controller = GenerationController(ctx)

    project = project_controller.create_project("CLI Instrumental", ContentType.INSTRUMENTAL)
    params = GenerationParams(prompt=args.prompt, duration_seconds=args.duration)
    track = generation_controller.generate_instrumental(project, params)
    print(f"Generated instrumental saved to: {track.audio_path_wav}")


if __name__ == "__main__":
    main()

