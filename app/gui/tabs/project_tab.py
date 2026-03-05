from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from app.models.project_models import TrackVersion


def _ms_to_str(ms: int) -> str:
    s = max(0, ms // 1000)
    m, s = divmod(s, 60)
    return f"{m}:{s:02d}"


class ProjectTab(QWidget):
    def __init__(self, main_window: "MainWindow") -> None:  # type: ignore[name-defined]
        super().__init__(main_window)
        self.main_window = main_window
        self._seeking = False
        self._init_ui()
        self._connect_player()

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
        self.btn_rename_track = QPushButton("Переименовать трек")

        btn_row.addWidget(self.btn_play)
        btn_row.addWidget(self.btn_export_wav)
        btn_row.addWidget(self.btn_export_mp3)
        btn_row.addWidget(self.btn_export_flac)
        btn_row.addWidget(self.btn_open_folder)
        btn_row.addWidget(self.btn_rename_track)

        layout.addLayout(btn_row)

        # Playback controls: pause, stop, seek slider
        playback_row = QHBoxLayout()
        self.btn_pause = QPushButton("Пауза")
        self.btn_stop = QPushButton("Стоп")
        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 0)
        self.time_label = QLabel("0:00 / 0:00")

        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.seek_slider.setEnabled(False)

        playback_row.addWidget(self.btn_pause)
        playback_row.addWidget(self.btn_stop)
        playback_row.addWidget(self.seek_slider, 1)
        playback_row.addWidget(self.time_label)

        layout.addLayout(playback_row)

        self.info_label = QLabel()
        layout.addWidget(self.info_label)

        self.btn_play.clicked.connect(self._on_play_clicked)
        self.btn_pause.clicked.connect(self._on_pause_clicked)
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        self.seek_slider.sliderPressed.connect(self._on_slider_pressed)
        self.seek_slider.sliderReleased.connect(self._on_slider_released)
        self.seek_slider.sliderMoved.connect(self._on_slider_moved)
        self.btn_export_wav.clicked.connect(lambda: self._on_export_clicked("wav"))
        self.btn_export_mp3.clicked.connect(lambda: self._on_export_clicked("mp3"))
        self.btn_export_flac.clicked.connect(lambda: self._on_export_clicked("flac"))
        self.btn_open_folder.clicked.connect(self._on_open_folder_clicked)
        self.btn_rename_track.clicked.connect(self._on_rename_track_clicked)

    def _connect_player(self) -> None:
        player = self.main_window.ctx.audio_player
        player.positionChanged.connect(self._on_position_changed)
        player.durationChanged.connect(self._on_duration_changed)
        player.playbackStateChanged.connect(self._on_playback_state_changed)

    def _on_position_changed(self, ms: int) -> None:
        if not self._seeking:
            self.seek_slider.setValue(ms)
        dur = self.main_window.ctx.audio_player.duration()
        self.time_label.setText(f"{_ms_to_str(ms)} / {_ms_to_str(dur)}")

    def _on_duration_changed(self, ms: int) -> None:
        self.seek_slider.setRange(0, max(0, ms))
        self.seek_slider.setValue(0)
        pos = self.main_window.ctx.audio_player.position()
        self.time_label.setText(f"{_ms_to_str(pos)} / {_ms_to_str(ms)}")

    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        paused = state == QMediaPlayer.PlaybackState.PausedState
        self.btn_pause.setEnabled(playing or paused)
        self.btn_pause.setText("Пауза" if playing else "Продолжить")
        self.btn_stop.setEnabled(playing or paused)
        self.seek_slider.setEnabled(playing or paused)

    def _on_pause_clicked(self) -> None:
        player = self.main_window.ctx.audio_player
        if player.playback_state() == QMediaPlayer.PlaybackState.PlayingState:
            player.pause()
        else:
            player.play()

    def _on_stop_clicked(self) -> None:
        self.main_window.ctx.audio_player.stop()

    def _on_slider_pressed(self) -> None:
        self._seeking = True

    def _on_slider_released(self) -> None:
        self._seeking = False
        ms = self.seek_slider.value()
        self.main_window.ctx.audio_player.set_position(ms)

    def _on_slider_moved(self, value: int) -> None:
        if self._seeking:
            dur = self.main_window.ctx.audio_player.duration()
            self.time_label.setText(f"{_ms_to_str(value)} / {_ms_to_str(dur)}")

    def refresh(self) -> None:
        self.track_list.clear()
        mw = self.main_window
        project = mw.current_project
        if project is None:
            self.info_label.setText("Проект не выбран. Создайте проект слева.")
            return

        for tv in project.track_versions:
            label = tv.title.strip() if tv.title and tv.title.strip() else f"{tv.track_type.value}: {tv.id}"
            self.track_list.addItem(label)

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

    def _on_rename_track_clicked(self) -> None:
        track = self._selected_track()
        if not track:
            QMessageBox.warning(
                self, "Нет выбора",
                "Выберите трек в списке для переименования.",
            )
            return
        current = (track.title or "").strip() or f"{track.track_type.value}: {track.id}"
        new_title, ok = QInputDialog.getText(
            self,
            "Переименовать трек",
            "Название трека:",
            text=current,
        )
        if not ok or new_title is None:
            return
        new_title = new_title.strip()
        if not new_title:
            QMessageBox.warning(self, "Ошибка", "Название не может быть пустым.")
            return
        track.title = new_title
        mw = self.main_window
        mw.project_controller.save_project(mw.current_project)
        self.refresh()

