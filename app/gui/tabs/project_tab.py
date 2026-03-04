from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models.project_models import TrackVersion


class ProjectTab(QWidget):
    def __init__(self, main_window: "MainWindow") -> None:  # type: ignore[name-defined]
        super().__init__(main_window)
        self.main_window = main_window
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.track_list = QListWidget()
        layout.addWidget(self.track_list)

        btn_row = QHBoxLayout()
        self.btn_play = QPushButton("Предпрослушать")
        self.btn_export_wav = QPushButton("Экспорт WAV")
        self.btn_export_mp3 = QPushButton("Экспорт MP3")
        self.btn_export_flac = QPushButton("Экспорт FLAC")

        btn_row.addWidget(self.btn_play)
        btn_row.addWidget(self.btn_export_wav)
        btn_row.addWidget(self.btn_export_mp3)
        btn_row.addWidget(self.btn_export_flac)

        layout.addLayout(btn_row)

        self.info_label = QLabel()
        layout.addWidget(self.info_label)

        self.btn_play.clicked.connect(self._on_play_clicked)
        self.btn_export_wav.clicked.connect(lambda: self._on_export_clicked("wav"))
        self.btn_export_mp3.clicked.connect(lambda: self._on_export_clicked("mp3"))
        self.btn_export_flac.clicked.connect(lambda: self._on_export_clicked("flac"))

    def refresh(self) -> None:
        self.track_list.clear()
        mw = self.main_window
        project = mw.current_project
        if project is None:
            self.info_label.setText("Проект не выбран.")
            return

        for tv in project.track_versions:
            self.track_list.addItem(f"{tv.track_type.value}: {tv.id}")

        self.info_label.setText(f"Проект: {project.name} ({project.id})")

    def _selected_track(self) -> TrackVersion | None:
        mw = self.main_window
        project = mw.current_project
        if project is None:
            return None
        idx = self.track_list.currentRow()
        if idx < 0 or idx >= len(project.track_versions):
            return None
        return project.track_versions[idx]

    def _on_play_clicked(self) -> None:
        track = self._selected_track()
        if not track:
            return
        self.main_window.playback_controller.play_track(track)

    def _on_export_clicked(self, fmt: str) -> None:
        track = self._selected_track()
        if not track:
            return
        self.main_window.generation_controller.export_track(track, fmt)

