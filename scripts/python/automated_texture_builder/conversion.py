from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Iterable

from .discovery import scan, udim_pattern
from .model import TextureFile, TextureSet


COLOR_CHANNELS = {
    "base_color", "specular_color", "transmission_color", "transmission_scatter",
    "translucency_color", "subsurface_color", "fuzz_color", "coat_color",
    "emission_color",
}


def houdini_oiio_tool(name: str) -> str | None:
    """Prefer the OIIO executable shipped with the running Houdini install."""
    hfs = os.environ.get("HFS", "").strip()
    if hfs:
        candidate = Path(hfs) / "bin" / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return shutil.which(name)


def resolve_ocio(explicit: str | Path | None = None) -> Path:
    value = str(explicit) if explicit else os.environ.get("OCIO", "")
    if not value:
        raise RuntimeError("No OCIO config selected and $OCIO is not set")
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise RuntimeError(f"OCIO config does not exist: {path}")
    return path


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_ocio(path: Path):
    try:
        import PyOpenColorIO as ocio
    except ImportError as exc:
        raise RuntimeError("PyOpenColorIO is required; run through Houdini 22 or install OCIO Python") from exc
    config = ocio.Config.CreateFromFile(str(path))
    config.validate()
    return config


def scene_linear_space(config) -> str:
    """Return the colorspace assigned to OCIO's required scene_linear role."""
    try:
        import PyOpenColorIO as ocio
        role = ocio.ROLE_SCENE_LINEAR
    except (ImportError, AttributeError):
        role = "scene_linear"
    if hasattr(config, "getRoleColorSpace"):
        value = config.getRoleColorSpace(role)
    else:
        value = config.getColorSpaceNameByRole(role)
    if not value:
        raise RuntimeError("The selected OCIO config has no scene_linear role")
    return str(value)


def classify(config, path: Path) -> str:
    value = config.getColorSpaceFromFilepath(str(path))
    if isinstance(value, tuple):
        value = value[0]
    if not value:
        raise RuntimeError(f"No OCIO file rule matched {path}")
    return str(value)


def display_space_name(config, value: str) -> str:
    """Use the active config family's preferred spelling for a colorspace."""
    color_space = config.getColorSpace(value)
    if color_space is None:
        return value
    if scene_linear_space(config).casefold() == "acescg":
        preferred = next(
            (
                str(alias) for alias in color_space.getAliases()
                if str(alias).startswith("sRGB Encoded")
            ),
            None,
        )
        if preferred:
            return preferred
    return str(color_space.getName())


def inspect(path: Path, oiiotool: str | None) -> dict[str, str]:
    if not oiiotool:
        return {"available": "false"}
    result = subprocess.run(
        [oiiotool, "--info", "-v", "--stats", str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return {"available": "true", "returncode": str(result.returncode), "report": result.stdout.strip()}


def _output_path(texture: TextureFile, source_root: Path, output_root: Path) -> Path:
    relative = texture.source.relative_to(source_root)
    return (output_root / relative).with_suffix(".tx")


def image_pixel_type(path: Path, oiiotool: str | None = None) -> str:
    """Read the actual source pixel type through OIIO, independent of extension."""
    executable = oiiotool or houdini_oiio_tool("oiiotool")
    if not executable:
        return ""
    result = subprocess.run(
        [executable, "--info", str(path)], text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )
    if result.returncode:
        return ""
    match = re.search(
        r"\b\d+\s+channel(?:s)?,\s+"
        r"(uint8|sint8|int8|uint16|sint16|int16|uint32|sint32|int32|half|float|double)\b",
        result.stdout, re.IGNORECASE,
    )
    if not match:
        return ""
    value = match.group(1).lower()
    return {"int8": "sint8", "int16": "sint16", "int32": "sint32"}.get(value, value)


GEOMETRY_DETAIL_CHANNELS = {"height", "displacement", "vector_displacement"}
WEB_COLOR_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def tx_pixel_space(
    channel: str, source_space: str, scene_linear: str, skip_linearization: bool,
) -> str:
    """Describe the pixels written to TX, independently of its .tx file rule."""
    if channel not in COLOR_CHANNELS:
        return "Raw"
    return source_space if skip_linearization else scene_linear


def shader_lookup_space(texture: TextureFile) -> str:
    """Return the one color-space transform still required at shader lookup."""
    if texture.channel in COLOR_CHANNELS and (
        texture.status == "source_direct" or texture.skip_linearization
    ):
        return texture.source_space
    return "Raw"


def should_skip_web_color_linearization(
    channel: str, path: Path, enabled: bool,
    config=None, source_space: str = "",
) -> bool:
    """Bypass only display-referred PNG/JPEG color maps.

    An explicit OCIO filename/path rule that identifies a linear or log source
    remains authoritative, so its required gamut/transfer conversion is kept.
    """
    if not (
        enabled
        and channel in COLOR_CHANNELS
        and path.suffix.lower() in WEB_COLOR_EXTENSIONS
    ):
        return False
    if config is None or not source_space:
        return True
    color_space = config.getColorSpace(source_space)
    encoding = str(color_space.getEncoding()).strip().casefold() if color_space else ""
    if encoding:
        return encoding in {"sdr-video", "hdr-video", "display-referred"}
    # Encoding metadata is optional in OCIO. This conservative fallback covers
    # common sRGB naming without overriding spaces explicitly named as linear.
    normalized = source_space.casefold().replace("_", " ").replace("-", " ")
    return "srgb" in normalized and "linear" not in normalized


def maketx_output_type(
    channel: str, source_type: str, color_transform: bool = True,
) -> str:
    """Choose storage from map semantics and the source's real pixel type."""
    source_type = source_type.lower()
    if channel in GEOMETRY_DETAIL_CHANNELS:
        # Displacement is evaluated geometrically and must never be quantized
        # down just because an incoming file happened to use integer storage.
        return "float"
    if channel in COLOR_CHANNELS and color_transform:
        # OCIO color conversion creates linear floating-point values. Half is
        # sufficient for 8-bit/half inputs; 16-bit and float sources use float
        # so their extra precision is not discarded during the transform.
        if source_type in {"uint16", "sint16", "uint32", "sint32", "float", "double"}:
            return "float"
        return "half"
    # Raw numeric/vector maps are not transformed, so preserve their storage
    # class instead of automatically expanding every downloaded texture.
    if source_type in {"uint8", "sint8", "uint16", "sint16", "half", "float"}:
        return source_type
    if source_type in {"uint32", "sint32", "double"}:
        return "float"
    return ""


def maketx_storage_args(
    channel: str, source: Path, source_type: str = "",
    color_transform: bool = True,
) -> list[str]:
    """Choose a TX container and type without losing meaningful precision."""
    output_type = maketx_output_type(channel, source_type, color_transform)
    if output_type in {"half", "float"}:
        return ["--format", "exr", "-d", output_type]
    if output_type in {"uint8", "sint8", "uint16", "sint16"}:
        return ["--format", "tiff", "-d", output_type]
    # Fallback for unusual/unknown inputs: maketx preserves the input type.
    if channel in GEOMETRY_DETAIL_CHANNELS:
        return ["--format", "exr", "-d", "float"]
    if (channel in COLOR_CHANNELS and color_transform) or source.suffix.lower() == ".exr" or channel == "normal":
        return ["--format", "exr", "-d", "half"]
    return []


def convert(
    source_root: Path,
    output_root: Path | None = None,
    ocio_path: str | Path | None = None,
    output_space: str | None = None,
    force: bool = False,
    inspect_images: bool = True,
    skip_png_jpeg_linearization: bool = False,
) -> Path:
    source_root = source_root.expanduser().resolve()
    output_root = (output_root or source_root / "tx").expanduser().resolve()
    ocio_path = resolve_ocio(ocio_path)
    config = load_ocio(ocio_path)
    output_space = output_space or scene_linear_space(config)
    maketx = houdini_oiio_tool("maketx")
    oiiotool = houdini_oiio_tool("oiiotool")
    if not maketx:
        raise RuntimeError("Houdini's maketx was not found in $HFS/bin or PATH")
    sets = scan(source_root, output_root)
    previous: dict[str, dict] = {}
    previous_manifest = output_root / "automated_texture_manifest.json"
    if previous_manifest.is_file():
        try:
            previous = {
                item.get("output", ""): item
                for item in json.loads(previous_manifest.read_text(encoding="utf-8")).get("textures", [])
            }
        except (OSError, ValueError, TypeError):
            previous = {}
    failures: list[str] = []
    for texture_set in sets.values():
        for channel, textures in texture_set.maps.items():
            for texture in textures:
                texture.source_space = display_space_name(
                    config, classify(config, texture.source),
                )
                texture.skip_linearization = should_skip_web_color_linearization(
                    channel, texture.source, skip_png_jpeg_linearization,
                    config, texture.source_space,
                )
                transform_color = channel in COLOR_CHANNELS and not texture.skip_linearization
                texture.output_space = tx_pixel_space(
                    channel, texture.source_space, output_space,
                    texture.skip_linearization,
                )
                texture.source_pixel_type = image_pixel_type(texture.source, oiiotool)
                texture.output_pixel_type = maketx_output_type(
                    channel, texture.source_pixel_type, transform_color,
                )
                texture.output = _output_path(texture, source_root, output_root)
                if inspect_images:
                    texture.before_info = inspect(texture.source, oiiotool)
                stored_output_type = (
                    image_pixel_type(texture.output, oiiotool)
                    if texture.output.exists() else ""
                )
                storage_matches = (
                    not texture.output_pixel_type
                    or stored_output_type == texture.output_pixel_type
                )
                prior = previous.get(str(texture.output), {})
                settings_match = (
                    bool(prior.get("skip_linearization", False))
                    == texture.skip_linearization
                    and prior.get("output_space", texture.output_space) == texture.output_space
                )
                current = (
                    texture.output.exists()
                    and texture.output.stat().st_mtime >= max(texture.source.stat().st_mtime, ocio_path.stat().st_mtime)
                    and storage_matches
                    and settings_match
                )
                if current and not force:
                    texture.status = "current"
                else:
                    texture.output.parent.mkdir(parents=True, exist_ok=True)
                    handle = tempfile.NamedTemporaryFile(
                        prefix=f".{texture.output.stem}.", suffix=".tx", dir=texture.output.parent, delete=False
                    )
                    temp = Path(handle.name)
                    handle.close()
                    temp.unlink(missing_ok=True)
                    command = [
                        maketx, "--oiio", "--checknan", "--filter", "box",
                        "--wrap", "black", "--sattrib", "oiio:ColorSpace", texture.output_space,
                        "--sattrib", "automated_texture_builder:channel", channel,
                        "--sattrib", "automated_texture_builder:source_color_space",
                        texture.source_space,
                        "--sattrib", "automated_texture_builder:baked_color_space",
                        texture.output_space,
                        "--sattrib", "automated_texture_builder:lookup_color_space",
                        texture.source_space if texture.skip_linearization else "Raw",
                        "--sattrib", "automated_texture_builder:source_pixel_type",
                        texture.source_pixel_type or "unknown",
                        "--sattrib", "automated_texture_builder:output_pixel_type",
                        texture.output_pixel_type or "preserve-input",
                        "--sattrib", "automated_texture_builder:skip_linearization",
                        "true" if texture.skip_linearization else "false",
                    ]
                    command += maketx_storage_args(
                        channel, texture.source, texture.source_pixel_type,
                        transform_color,
                    )
                    if transform_color and texture.source_space != texture.output_space:
                        command += [
                            "--colorconfig", str(ocio_path), "--colorconvert",
                            texture.source_space, texture.output_space,
                        ]
                    command += ["-o", str(temp), str(texture.source)]
                    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    if result.returncode:
                        temp.unlink(missing_ok=True)
                        texture.status = "failed"
                        failures.append(f"{texture.source}: {result.stdout.strip()}")
                    else:
                        os.replace(temp, texture.output)
                        texture.status = "converted"
                if texture.output.exists() and inspect_images:
                    texture.after_info = inspect(texture.output, oiiotool)
    manifest = write_manifest(source_root, output_root, ocio_path, output_space, sets)
    if failures:
        raise RuntimeError("Texture conversion failed:\n" + "\n".join(failures))
    return manifest


def manifest_existing_tx(
    tx_root: Path,
    ocio_path: str | Path | None = None,
    inspect_images: bool = True,
) -> Path:
    """Create a material manifest from an already-converted TX folder."""
    tx_root = tx_root.expanduser().resolve()
    ocio_path = resolve_ocio(ocio_path)
    config = load_ocio(ocio_path)
    output_space = scene_linear_space(config)
    oiiotool = houdini_oiio_tool("oiiotool")
    sets = scan(tx_root, extensions={".tx"})
    for texture in _iter_textures(sets):
        texture.output = texture.source
        texture.source_space = output_space if texture.channel in COLOR_CHANNELS else "Raw"
        texture.output_space = texture.source_space
        texture.status = "existing_tx"
        if inspect_images:
            texture.after_info = inspect(texture.source, oiiotool)
    return write_manifest(tx_root, tx_root, ocio_path, output_space, sets)


def resolve_existing_tx_root(selected: Path) -> Path:
    """Accept either a TX folder itself or its source-folder parent."""
    selected = selected.expanduser().resolve()
    conventional = selected / "tx"
    if conventional.is_dir() and next(conventional.rglob("*.tx"), None) is not None:
        return conventional
    return selected


def deletable_sources(manifest_path: Path) -> list[Path]:
    """Validate that every manifest source has a corresponding generated TX."""
    manifest_path = manifest_path.expanduser().resolve()
    if not manifest_path.is_file():
        raise RuntimeError("No completed TX manifest was found. Generate the TX files first.")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_root = Path(data["source_root"]).resolve()
    output_root = Path(data["output_root"]).resolve()
    if output_root != (source_root / "tx").resolve():
        raise RuntimeError("The manifest is not a generated source-to-TX build; source deletion is blocked.")
    targets: set[Path] = set()
    missing: list[Path] = []
    for item in data.get("textures", []):
        source = Path(item["source"]).resolve()
        output_text = item.get("output")
        output = Path(output_text).resolve() if output_text else None
        if not source.is_relative_to(source_root) or source.is_relative_to(output_root):
            raise RuntimeError(f"Unsafe source path in manifest; deletion blocked: {source}")
        if output is None or not output.is_relative_to(output_root) or not output.is_file():
            missing.append(output or source)
        elif source.is_file():
            targets.add(source)
    if missing:
        raise RuntimeError(
            f"Source deletion is blocked because {len(missing)} generated TX file(s) are missing."
        )
    if not targets:
        raise RuntimeError("No original source textures remain to delete.")
    return sorted(targets, key=lambda path: path.as_posix().casefold())


def delete_original_sources(manifest_path: Path) -> list[Path]:
    """Delete only manifest-listed sources whose generated TX files exist."""
    targets = deletable_sources(manifest_path)
    for target in targets:
        target.unlink()
    return targets


def deletable_sources_for_existing_tx(selected: Path) -> list[Path]:
    """Find source images that have a verified TX counterpart in an existing-TX workflow."""
    selected = selected.expanduser().resolve()
    tx_root = resolve_existing_tx_root(selected)
    source_root = selected.parent if selected.name.casefold() == "tx" else selected
    sets = scan(source_root, None if tx_root == source_root else tx_root)
    tx_by_name: dict[str, list[Path]] = {}
    for tx in tx_root.rglob("*.tx"):
        if tx.is_file():
            tx_by_name.setdefault(tx.name.casefold(), []).append(tx.resolve())
    targets: set[Path] = set()
    missing: list[Path] = []
    for texture in _iter_textures(sets):
        source = texture.source.resolve()
        relative = source.relative_to(source_root)
        expected = (tx_root / relative).with_suffix(".tx").resolve()
        sibling = (source.parent / "tx" / source.name).with_suffix(".tx").resolve()
        matches = {path for path in (expected, sibling) if path.is_file()}
        if not matches:
            matches = set(tx_by_name.get(source.with_suffix(".tx").name.casefold(), []))
        if len(matches) != 1:
            missing.append(source)
        else:
            targets.add(source)
    if missing:
        raise RuntimeError(
            f"Source deletion is blocked because {len(missing)} source file(s) do not have one unique TX counterpart."
        )
    if not targets:
        raise RuntimeError("No original source textures remain to delete.")
    return sorted(targets, key=lambda path: path.as_posix().casefold())


def delete_sources_for_existing_tx(selected: Path) -> list[Path]:
    targets = deletable_sources_for_existing_tx(selected)
    for target in targets:
        target.unlink()
    return targets


def manifest_source_images(
    source_root: Path,
    ocio_path: str | Path | None = None,
    inspect_images: bool = False,
) -> Path:
    """Create a material manifest that references native source images directly."""
    source_root = source_root.expanduser().resolve()
    ocio_path = resolve_ocio(ocio_path)
    config = load_ocio(ocio_path)
    output_space = scene_linear_space(config)
    oiiotool = houdini_oiio_tool("oiiotool")
    manifest_root = source_root / ".automated_texture_builder"
    sets = scan(source_root, manifest_root)
    for texture in _iter_textures(sets):
        texture.output = texture.source
        texture.source_space = display_space_name(
            config, classify(config, texture.source),
        )
        texture.output_space = texture.source_space if texture.channel in COLOR_CHANNELS else "Raw"
        texture.status = "source_direct"
        if inspect_images:
            texture.before_info = inspect(texture.source, oiiotool)
    return write_manifest(source_root, manifest_root, ocio_path, output_space, sets)


def _iter_textures(sets: dict[str, TextureSet]) -> Iterable[TextureFile]:
    for texture_set in sets.values():
        for textures in texture_set.maps.values():
            yield from textures


def write_manifest(
    source_root: Path,
    output_root: Path,
    ocio_path: Path,
    output_space: str,
    sets: dict[str, TextureSet],
) -> Path:
    payload = {
        "schema_version": 4,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_root": str(source_root),
        "output_root": str(output_root),
        "ocio": {"path": str(ocio_path), "sha256": file_hash(ocio_path)},
        "color_output_space": output_space,
        "texture_sets": [],
        "textures": [texture.json() for texture in _iter_textures(sets)],
    }
    for name in sorted(sets):
        item = sets[name]
        maps = {}
        for channel, textures in sorted(item.maps.items()):
            maps[channel] = {
                "path": udim_pattern(textures),
                "udim": any(texture.udim is not None for texture in textures),
                "tiles": sorted({texture.udim for texture in textures if texture.udim is not None}),
                "color_space": textures[0].output_space,
                "lookup_space": shader_lookup_space(textures[0]),
            }
        payload["texture_sets"].append({"name": name, "maps": maps})
    path = output_root / "automated_texture_manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)
    return path
