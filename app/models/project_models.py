from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional


class ContentType(str, Enum):
    INSTRUMENTAL = "instrumental"
    SONG = "song"  # музыка + вокал
    SFX = "sfx"


class TrackType(str, Enum):
    INSTRUMENTAL = "instrumental"
    VOCAL = "vocal"
    MIX = "mix"
    SFX = "sfx"


@dataclass
class GenerationParams:
    prompt: str
    duration_seconds: int = 30
    tempo_bpm: Optional[int] = None
    genre: Optional[str] = None
    arrangement_density: str = "medium"  # low / medium / high
    structure_complexity: str = "medium"  # simple / medium / complex
    seed: Optional[int] = None


@dataclass
class VocalParams:
    lyrics: str
    voice_id: str = "default"
    style: str = "neutral"
    delivery: str = "legato"  # legato / staccato / mixed
    intensity: float = 0.5  # 0..1
    enable_background_voices: bool = False


@dataclass
class SfxParams:
    prompt: str
    sfx_type: str = "atmosphere"  # atmosphere / short_sfx / transition / background
    duration_seconds: int = 5


@dataclass
class TrackVersion:
    id: str
    track_type: TrackType
    audio_path_wav: Path
    audio_path_mp3: Optional[Path] = None
    audio_path_flac: Optional[Path] = None

    generation_params: Optional[GenerationParams] = None
    vocal_params: Optional[VocalParams] = None
    sfx_params: Optional[SfxParams] = None

    duration_seconds: Optional[float] = None
    sample_rate: Optional[int] = None
    bitrate_kbps: Optional[int] = None
    genre: Optional[str] = None
    mood: Optional[str] = None
    tempo_bpm: Optional[int] = None


@dataclass
class Project:
    id: str
    name: str
    base_path: Path
    content_type: ContentType = ContentType.INSTRUMENTAL
    track_versions: List[TrackVersion] = field(default_factory=list)

