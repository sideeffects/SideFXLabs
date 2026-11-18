from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TextureFile:
    source: Path
    texture_set: str
    channel: str
    udim: int | None
    source_space: str = ""
    output_space: str = "Raw"
    source_pixel_type: str = ""
    output_pixel_type: str = ""
    skip_linearization: bool = False
    output: Path | None = None
    status: str = "planned"
    before_info: dict[str, Any] = field(default_factory=dict)
    after_info: dict[str, Any] = field(default_factory=dict)

    def json(self) -> dict[str, Any]:
        value = asdict(self)
        value["source"] = str(self.source)
        value["output"] = str(self.output) if self.output else None
        return value


@dataclass
class TextureSet:
    name: str
    maps: dict[str, list[TextureFile]] = field(default_factory=dict)

    def add(self, texture: TextureFile) -> None:
        self.maps.setdefault(texture.channel, []).append(texture)
