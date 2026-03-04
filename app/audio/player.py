from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer


class AudioPlayer:
    """
    Thin wrapper around QMediaPlayer for simple in-app playback.
    """

    def __init__(self) -> None:
        self._audio_output = QAudioOutput()
        self._player = QMediaPlayer()
        self._player.setAudioOutput(self._audio_output)

    def set_volume(self, volume: int) -> None:
        self._audio_output.setVolume(max(0, min(volume, 100)) / 100.0)

    def play_file(self, path: Path) -> None:
        abs_path = path.resolve() if path.exists() else path
        url = QUrl.fromLocalFile(str(abs_path))
        self._player.setSource(url)
        self._player.play()

    def pause(self) -> None:
        self._player.pause()

    def stop(self) -> None:
        self._player.stop()

