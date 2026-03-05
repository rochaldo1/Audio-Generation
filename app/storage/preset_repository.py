from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional

from app.models.project_models import GenerationParams, SfxParams, VocalParams


class PresetRepository:
    """
    JSON-based storage for reusable generation presets/templates.
    """

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        if root_dir is None:
            root_dir = Path.cwd() / "presets"
        self.root_dir = root_dir
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _preset_path(self, name: str) -> Path:
        safe_name = name.replace("/", "_")
        return self.root_dir / f"{safe_name}.json"

    def save_instrumental_preset(self, name: str, params: GenerationParams) -> None:
        self._save_preset(
            name,
            {
                "type": "instrumental",
                "params": asdict(params),
            },
        )

    def save_vocal_preset(self, name: str, params: VocalParams) -> None:
        self._save_preset(
            name,
            {
                "type": "vocal",
                "params": asdict(params),
            },
        )

    def save_sfx_preset(self, name: str, params: SfxParams) -> None:
        self._save_preset(
            name,
            {
                "type": "sfx",
                "params": asdict(params),
            },
        )

    def _save_preset(self, name: str, data: Dict) -> None:
        path = self._preset_path(name)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_presets(self, preset_type: Optional[str] = None) -> List[str]:
        """Return preset names. If preset_type is set, filter by type (instrumental/vocal/sfx)."""
        if preset_type is None:
            return sorted(p.stem for p in self.root_dir.glob("*.json"))
        result = []
        for p in self.root_dir.glob("*.json"):
            data = self._load_preset(p.stem)
            if data and data.get("type") == preset_type:
                result.append(p.stem)
        return sorted(result)

    def load_instrumental_preset(self, name: str) -> Optional[GenerationParams]:
        data = self._load_preset(name)
        if not data or data.get("type") != "instrumental":
            return None
        return GenerationParams(**data["params"])

    def load_vocal_preset(self, name: str) -> Optional[VocalParams]:
        data = self._load_preset(name)
        if not data or data.get("type") != "vocal":
            return None
        return VocalParams(**data["params"])

    def load_sfx_preset(self, name: str) -> Optional[SfxParams]:
        data = self._load_preset(name)
        if not data or data.get("type") != "sfx":
            return None
        return SfxParams(**data["params"])

    def _load_preset(self, name: str) -> Optional[Dict]:
        path = self._preset_path(name)
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

