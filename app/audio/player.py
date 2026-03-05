from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer


class AudioPlayer(QObject):
    """
    Wrapper around QMediaPlayer for in-app playback with position/duration support.
    """
    positionChanged = Signal(int)
    durationChanged = Signal(int)
    playbackStateChanged = Signal(object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._audio_output = QAudioOutput()
        self._player = QMediaPlayer()
        self._player.setAudioOutput(self._audio_output)
        self._player.positionChanged.connect(self.positionChanged.emit)
        self._player.durationChanged.connect(self.durationChanged.emit)
        self._player.playbackStateChanged.connect(self.playbackStateChanged.emit)

    def set_volume(self, volume: int) -> None:
        self._audio_output.setVolume(max(0, min(volume, 100)) / 100.0)

    def play_file(self, path: Path) -> None:
        abs_path = path.resolve() if path.exists() else path
        url = QUrl.fromLocalFile(str(abs_path))
        self._player.setSource(url)
        self._player.play()

    def play(self) -> None:
        self._player.play()

    def pause(self) -> None:
        self._player.pause()

    def stop(self) -> None:
        self._player.stop()

    def position(self) -> int:
        return self._player.position()

    def duration(self) -> int:
        return self._player.duration()

    def set_position(self, ms: int) -> None:
        self._player.setPosition(ms)

    def playback_state(self):
        return self._player.playbackState()

