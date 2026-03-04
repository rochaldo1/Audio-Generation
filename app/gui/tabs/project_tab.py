from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
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
        self.btn_open_folder = QPushButton("Открыть папку проекта")

        btn_row.addWidget(self.btn_play)
        btn_row.addWidget(self.btn_export_wav)
        btn_row.addWidget(self.btn_export_mp3)
        btn_row.addWidget(self.btn_export_flac)
        btn_row.addWidget(self.btn_open_folder)

        layout.addLayout(btn_row)

        self.info_label = QLabel()
        layout.addWidget(self.info_label)

        self.btn_play.clicked.connect(self._on_play_clicked)
        self.btn_export_wav.clicked.connect(lambda: self._on_export_clicked("wav"))
        self.btn_export_mp3.clicked.connect(lambda: self._on_export_clicked("mp3"))
        self.btn_export_flac.clicked.connect(lambda: self._on_export_clicked("flac"))
        self.btn_open_folder.clicked.connect(self._on_open_folder_clicked)

    def refresh(self) -> None:
        self.track_list.clear()
        mw = self.main_window
        project = mw.current_project
        if project is None:
            self.info_label.setText("Проект не выбран. Создайте проект слева.")
            return

        for tv in project.track_versions:
            self.track_list.addItem(f"{tv.track_type.value}: {tv.id}")

        base = project.base_path.resolve()
        self.info_label.setText(
            f"Проект: {project.name} ({project.id})\n"
            f"Папка: {base}\n"
            f"Треков: {len(project.track_versions)}. Выберите трек и нажмите «Предпрослушать» или «Экспорт»."
        )
        if project.track_versions:
            self.track_list.setCurrentRow(0)

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
            QMessageBox.warning(
                self, "Нет выбора",
                "Выберите трек в списке (кликните по нему), затем нажмите «Предпрослушать»."
            )
            return
        path = track.audio_path_wav.resolve()
        if not path.exists():
            QMessageBox.warning(
                self, "Файл не найден",
                f"Файл не найден: {path}\nВозможно, проект был перемещён."
            )
            return
        self.main_window.playback_controller.play_track(track)

    def _on_export_clicked(self, fmt: str) -> None:
        track = self._selected_track()
        if not track:
            QMessageBox.warning(
                self, "Нет выбора",
                "Выберите трек в списке, затем нажмите «Экспорт»."
            )
            return
        try:
            out_path = self.main_window.generation_controller.export_track(track, fmt)
            abs_path = out_path.resolve()
            QMessageBox.information(
                self, "Экспорт выполнен",
                f"Файл сохранён:\n{abs_path}\n\n"
                f"Папка проекта: {track.audio_path_wav.parent.resolve()}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка экспорта",
                str(e) + "\n\nДля MP3/FLAC требуется FFmpeg в PATH."
            )

    def _on_open_folder_clicked(self) -> None:
        project = self.main_window.current_project
        if project is None:
            QMessageBox.warning(self, "Ошибка", "Проект не выбран.")
            return
        folder = project.base_path.resolve()
        if not folder.exists():
            QMessageBox.warning(self, "Ошибка", f"Папка не существует: {folder}")
            return
        if sys.platform == "win32":
            os.startfile(folder)
        elif sys.platform == "darwin":
            subprocess.run(["open", folder], check=False)
        else:
            subprocess.run(["xdg-open", folder], check=False)

