from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.audio.player import AudioPlayer
from app.core.ace_step_service import AceStepService
from app.core.controllers import (
    AppContext,
    GenerationController,
    PlaybackController,
    ProjectController,
)
from app.models.project_models import ContentType
from app.storage.project_repository import ProjectRepository
from app.storage.preset_repository import PresetRepository

from .tabs.instrument_tab import InstrumentTab
from .tabs.project_tab import ProjectTab
from .tabs.sfx_tab import SfxTab
from .tabs.vocal_tab import VocalTab


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Audio Generation Suite")
        self.resize(1200, 800)
        projects_root = (Path.cwd() / "projects").resolve()
        self.statusBar().showMessage(f"Проекты сохраняются в: {projects_root}")

        # Global generation progress bar (non-modal, in status bar)
        self.generation_progress = QProgressBar()
        self.generation_progress.setTextVisible(True)
        self.generation_progress.setRange(0, 0)  # indeterminate
        self.generation_progress.hide()
        self.statusBar().addPermanentWidget(self.generation_progress)

        # Core context and controllers
        ace_step_service = AceStepService()
        project_repo = ProjectRepository(Path.cwd() / "projects")
        audio_player = AudioPlayer()

        self.ctx = AppContext(
            ace_step_service=ace_step_service,
            project_repo=project_repo,
            audio_player=audio_player,
        )

        self.project_controller = ProjectController(self.ctx)
        self.generation_controller = GenerationController(self.ctx)
        self.playback_controller = PlaybackController(self.ctx)
        self.preset_repo = PresetRepository()

        self.current_project = None

        self._init_ui()
        self._load_projects()

    # ------------------------------------------------------------------ #
    # Global generation state (progress + button disabling)
    # ------------------------------------------------------------------ #

    def set_generation_state(self, in_progress: bool, message: str | None = None) -> None:
        """
        Enable/disable all generation controls and show/hide busy progress bar.
        """
        if in_progress:
            if message:
                self.generation_progress.setFormat(message)
            self.generation_progress.show()
            # Disable generate buttons across tabs
            for btn in [
                getattr(self.instrument_tab, "btn_generate", None),
                getattr(self.instrument_tab, "btn_variation", None),
                getattr(self.vocal_tab, "btn_generate_vocal", None),
                getattr(self.sfx_tab, "btn_generate", None),
            ]:
                if btn is not None:
                    btn.setEnabled(False)
        else:
            self.generation_progress.hide()
            for btn in [
                getattr(self.instrument_tab, "btn_generate", None),
                getattr(self.instrument_tab, "btn_variation", None),
                getattr(self.vocal_tab, "btn_generate_vocal", None),
                getattr(self.sfx_tab, "btn_generate", None),
            ]:
                if btn is not None:
                    btn.setEnabled(True)

    def _init_ui(self) -> None:
        central = QWidget()
        layout = QHBoxLayout(central)

        splitter = QSplitter()
        layout.addWidget(splitter)
        self.setCentralWidget(central)

        # Left: project list and controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        self.project_list = QListWidget()
        self.btn_new_instr_project = QPushButton("Новый проект: Музыка")
        self.btn_new_song_project = QPushButton("Новый проект: Песня")
        self.btn_new_sfx_project = QPushButton("Новый проект: SFX")
        self.btn_rename_project = QPushButton("Переименовать проект")
        self.btn_delete_project = QPushButton("Удалить проект")

        left_layout.addWidget(self.project_list)
        left_layout.addWidget(self.btn_new_instr_project)
        left_layout.addWidget(self.btn_new_song_project)
        left_layout.addWidget(self.btn_new_sfx_project)
        left_layout.addWidget(self.btn_rename_project)
        left_layout.addWidget(self.btn_delete_project)

        splitter.addWidget(left_widget)

        # Right: tabs
        self.tabs = QTabWidget()
        splitter.addWidget(self.tabs)
        splitter.setStretchFactor(1, 3)

        self.instrument_tab = InstrumentTab(self)
        self.vocal_tab = VocalTab(self)
        self.sfx_tab = SfxTab(self)
        self.project_tab = ProjectTab(self)

        self.tabs.addTab(self.instrument_tab, "Музыка (инструментал)")
        self.tabs.addTab(self.vocal_tab, "Песня (музыка + вокал)")
        self.tabs.addTab(self.sfx_tab, "SFX / атмосферы")
        self.tabs.addTab(self.project_tab, "Проект")

        self.btn_new_instr_project.clicked.connect(
            lambda: self._create_project(ContentType.INSTRUMENTAL)
        )
        self.btn_new_song_project.clicked.connect(
            lambda: self._create_project(ContentType.SONG)
        )
        self.btn_new_sfx_project.clicked.connect(
            lambda: self._create_project(ContentType.SFX)
        )
        self.project_list.currentRowChanged.connect(self._on_project_selected)
        self.btn_rename_project.clicked.connect(self._on_rename_project_clicked)
        self.btn_delete_project.clicked.connect(self._on_delete_project_clicked)

    def _load_projects(self) -> None:
        self.project_list.clear()
        self._projects = self.project_controller.list_projects()
        for proj in self._projects:
            self.project_list.addItem(f"{proj.name} ({proj.id})")
        if self._projects:
            self.project_list.setCurrentRow(0)

    def _create_project(self, content_type: ContentType) -> None:
        base_name = {
            ContentType.INSTRUMENTAL: "Новый инструментальный проект",
            ContentType.SONG: "Новый проект песни",
            ContentType.SFX: "Новый проект SFX",
        }[content_type]
        project = self.project_controller.create_project(base_name, content_type)
        self._load_projects()
        idx = next(
            (i for i, p in enumerate(self._projects) if p.id == project.id),
            len(self._projects) - 1,
        )
        self.project_list.setCurrentRow(idx)

    def _on_project_selected(self, index: int) -> None:
        if index < 0 or index >= len(self._projects):
            self.current_project = None
            return
        self.current_project = self._projects[index]
        self.project_tab.refresh()

    def _on_rename_project_clicked(self) -> None:
        project = self.current_project
        if project is None:
            QMessageBox.warning(
                self, "Нет выбора",
                "Выберите проект в списке слева для переименования.",
            )
            return
        new_name, ok = QInputDialog.getText(
            self,
            "Переименовать проект",
            "Название проекта:",
            text=project.name,
        )
        if not ok or new_name is None:
            return
        new_name = new_name.strip()
        if not new_name:
            QMessageBox.warning(self, "Ошибка", "Название не может быть пустым.")
            return
        project.name = new_name
        self.project_controller.save_project(project)
        self._load_projects()
        self.project_tab.refresh()

    def _on_delete_project_clicked(self) -> None:
        project = self.current_project
        if project is None:
            QMessageBox.warning(
                self, "Нет выбора",
                "Выберите проект в списке слева для удаления.",
            )
            return
        reply = QMessageBox.question(
            self,
            "Удалить проект",
            f"Удалить проект «{project.name}»?\nВся папка проекта и все треки будут удалены с диска. Это необратимо.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.ctx.audio_player.release_media()
        self.project_controller.delete_project(project)
        self.current_project = None
        self._load_projects()
        self.project_tab.refresh()

