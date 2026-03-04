from __future__ import annotations

from pathlib import Path

from pydub import AudioSegment


def export_to_mp3(wav_path: Path, mp3_path: Path) -> Path:
    audio = AudioSegment.from_wav(str(wav_path))
    audio.export(str(mp3_path), format="mp3")
    return mp3_path


def export_to_flac(wav_path: Path, flac_path: Path) -> Path:
    audio = AudioSegment.from_wav(str(wav_path))
    audio.export(str(flac_path), format="flac")
    return flac_path

