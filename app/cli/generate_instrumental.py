from __future__ import annotations

import argparse
from pathlib import Path

from app.core.ace_step_service import AceStepService
from app.core.controllers import AppContext, GenerationController, ProjectController
from app.core.model_manager import ModelManager
from app.models.project_models import ContentType, GenerationParams, Project
from app.storage.project_repository import ProjectRepository
from app.audio.player import AudioPlayer


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an instrumental track using MusicGen.")
    parser.add_argument("--prompt", required=True, help="Text description of the music.")
    parser.add_argument("--duration", type=int, default=15, help="Duration in seconds.")
    args = parser.parse_args()

    model_manager = ModelManager()
    ace_step_service = AceStepService()
    project_repo = ProjectRepository(Path.cwd() / "projects_cli")
    audio_player = AudioPlayer()

    ctx = AppContext(
        model_manager=model_manager,
        ace_step_service=ace_step_service,
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

