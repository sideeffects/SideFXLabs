from __future__ import annotations

from pathlib import Path
import re

from .model import TextureFile, TextureSet


SUPPORTED = {".bmp", ".exr", ".hdr", ".jpeg", ".jpg", ".png", ".tga", ".tif", ".tiff"}
UDIM_RE = re.compile(r"(?<!\d)(1\d{3})(?!\d)")
CHANNEL_RE = re.compile(
    r"(?:^|[_\-.])(?P<channel>"
    r"base[_ ]?color|albedo|diffuse|diff|color|"
    r"base[_ ]?metalness|metallic|metalness|metal|met|"
    r"base[_ ]?weight|base[_ ]?diffuse[_ ]?roughness|diffuse[_ ]?roughness|"
    r"specular[_ ]?weight|specular[_ ]?level|specularlevel|"
    r"specular[_ ]?roughness[_ ]?anisotropy|specular[_ ]?anisotropy[_ ]?angle|"
    r"specular[_ ]?anisotropy|"
    r"anisotropy[_ ]?angle|anisotropy|anisotropy[_ ]?level|"
    r"specular[_ ]?roughness|roughness|rough|rgh|specular[_ ]?color|specular[_ ]?ior|"
    r"transmission[_ ]?dispersion[_ ]?abbe[_ ]?number|transmission[_ ]?dispersion[_ ]?scale|"
    r"transmission[_ ]?scatter[_ ]?anisotropy|transmission[_ ]?scatter|"
    r"transmission[_ ]?color|transmission[_ ]?depth|transmission[_ ]?weight|"
    r"translucency[_ ]?color|translucency[_ ]?weight|translucency|transmission|"
    r"subsurface[_ ]?scatter[_ ]?anisotropy|subsurface[_ ]?radius[_ ]?scale|"
    r"subsurface[_ ]?color|subsurface[_ ]?radius|subsurface[_ ]?weight|subsurface|sss|scattering|"
    r"fuzz[_ ]?color|sheen[_ ]?color|fuzz[_ ]?roughness|sheen[_ ]?roughness|"
    r"fuzz[_ ]?weight|fuzz|sheen|"
    r"coat[_ ]?roughness[_ ]?anisotropy|coat[_ ]?anisotropy[_ ]?angle|coat[_ ]?anisotropy|"
    r"coat[_ ]?normal|coat[_ ]?tangent|"
    r"coat[_ ]?color|coat[_ ]?roughness|"
    r"coat[_ ]?ior|coat[_ ]?darkening|coat[_ ]?weight|clearcoat|coat|"
    r"thin[_ ]?film[_ ]?weight|thin[_ ]?film[_ ]?thickness|thin[_ ]?film[_ ]?ior|"
    r"emission[_ ]?luminance|emission[_ ]?weight|emission[_ ]?color|emissive|emission|"
    r"geometry[_ ]?opacity|geometry[_ ]?thin[_ ]?walled|thin[_ ]?walled|opacity|"
    r"vector[_ ]?displacement|vdisp|"
    r"normal(?:[_ ]?(?:opengl|gl))?|nor(?:[_ ]?(?:opengl|gl))?|"
    r"nrm(?:[_ ]?(?:opengl|gl))?|geometry[_ ]?tangent|tangent|"
    r"height|hgt|displacement|disp|displ"
    r")(?=$|[_\-.])",
    re.IGNORECASE,
)

ALIASES = {
    "basecolor": "base_color",
    "base_color": "base_color",
    "albedo": "base_color",
    "diffuse": "base_color",
    "diff": "base_color",
    "color": "base_color",
    "baseweight": "base_weight",
    "base_weight": "base_weight",
    "diffuseroughness": "base_diffuse_roughness",
    "diffuse_roughness": "base_diffuse_roughness",
    "basediffuseroughness": "base_diffuse_roughness",
    "base_diffuse_roughness": "base_diffuse_roughness",
    "basemetalness": "base_metalness",
    "base_metalness": "base_metalness",
    "metallic": "base_metalness",
    "metalness": "base_metalness",
    "metal": "base_metalness",
    "met": "base_metalness",
    "specularweight": "specular_weight",
    "specular_weight": "specular_weight",
    "specularlevel": "legacy_specular_level",
    "specular_level": "legacy_specular_level",
    "specularroughness": "specular_roughness",
    "specular_roughness": "specular_roughness",
    "roughness": "specular_roughness",
    "rough": "specular_roughness",
    "rgh": "specular_roughness",
    "specularcolor": "specular_color",
    "specular_color": "specular_color",
    "specularior": "specular_ior",
    "specular_ior": "specular_ior",
    "specularroughnessanisotropy": "specular_roughness_anisotropy",
    "specular_roughness_anisotropy": "specular_roughness_anisotropy",
    "specularanisotropy": "specular_roughness_anisotropy",
    "specular_anisotropy": "specular_roughness_anisotropy",
    "anisotropy": "specular_roughness_anisotropy",
    "anisotropylevel": "specular_roughness_anisotropy",
    "anisotropy_level": "specular_roughness_anisotropy",
    "specularanisotropyangle": "specular_anisotropy_angle",
    "specular_anisotropy_angle": "specular_anisotropy_angle",
    "anisotropyangle": "specular_anisotropy_angle",
    "anisotropy_angle": "specular_anisotropy_angle",
    "transmission": "transmission_weight",
    "transmissionweight": "transmission_weight",
    "transmission_weight": "transmission_weight",
    "translucency": "translucency_weight",
    "translucencyweight": "translucency_weight",
    "translucency_weight": "translucency_weight",
    "translucencycolor": "translucency_color",
    "translucency_color": "translucency_color",
    "transmissioncolor": "transmission_color",
    "transmission_color": "transmission_color",
    "transmissiondepth": "transmission_depth",
    "transmission_depth": "transmission_depth",
    "transmissionscatter": "transmission_scatter",
    "transmission_scatter": "transmission_scatter",
    "transmissionscatteranisotropy": "transmission_scatter_anisotropy",
    "transmission_scatter_anisotropy": "transmission_scatter_anisotropy",
    "transmissiondispersionscale": "transmission_dispersion_scale",
    "transmission_dispersion_scale": "transmission_dispersion_scale",
    "transmissiondispersionabbenumber": "transmission_dispersion_abbe_number",
    "transmission_dispersion_abbe_number": "transmission_dispersion_abbe_number",
    "subsurface": "subsurface_weight",
    "subsurfaceweight": "subsurface_weight",
    "subsurface_weight": "subsurface_weight",
    "sss": "subsurface_weight",
    "scattering": "subsurface_weight",
    "subsurfacecolor": "subsurface_color",
    "subsurface_color": "subsurface_color",
    "subsurfaceradius": "subsurface_radius",
    "subsurface_radius": "subsurface_radius",
    "subsurfaceradiusscale": "subsurface_radius_scale",
    "subsurface_radius_scale": "subsurface_radius_scale",
    "subsurfacescatteranisotropy": "subsurface_scatter_anisotropy",
    "subsurface_scatter_anisotropy": "subsurface_scatter_anisotropy",
    "fuzz": "fuzz_weight", "fuzzweight": "fuzz_weight", "fuzz_weight": "fuzz_weight",
    "sheen": "fuzz_weight",
    "fuzzcolor": "fuzz_color", "fuzz_color": "fuzz_color",
    "sheencolor": "fuzz_color", "sheen_color": "fuzz_color",
    "fuzzroughness": "fuzz_roughness", "fuzz_roughness": "fuzz_roughness",
    "sheenroughness": "fuzz_roughness", "sheen_roughness": "fuzz_roughness",
    "coat": "coat_weight", "coatweight": "coat_weight", "coat_weight": "coat_weight",
    "clearcoat": "coat_weight",
    "coatcolor": "coat_color", "coat_color": "coat_color",
    "coatroughness": "coat_roughness", "coat_roughness": "coat_roughness",
    "coatroughnessanisotropy": "coat_roughness_anisotropy",
    "coat_roughness_anisotropy": "coat_roughness_anisotropy",
    "coatanisotropy": "coat_roughness_anisotropy",
    "coat_anisotropy": "coat_roughness_anisotropy",
    "coatanisotropyangle": "coat_anisotropy_angle",
    "coat_anisotropy_angle": "coat_anisotropy_angle",
    "coatnormal": "coat_normal", "coat_normal": "coat_normal",
    "coattangent": "coat_tangent", "coat_tangent": "coat_tangent",
    "coatior": "coat_ior", "coat_ior": "coat_ior",
    "coatdarkening": "coat_darkening", "coat_darkening": "coat_darkening",
    "thinfilmweight": "thin_film_weight", "thin_film_weight": "thin_film_weight",
    "thinfilmthickness": "thin_film_thickness", "thin_film_thickness": "thin_film_thickness",
    "thinfilmior": "thin_film_ior", "thin_film_ior": "thin_film_ior",
    "emissionluminance": "emission_luminance", "emission_luminance": "emission_luminance",
    "emissionweight": "emission_luminance", "emission_weight": "emission_luminance",
    "emissioncolor": "emission_color", "emission_color": "emission_color",
    "emission": "emission_color", "emissive": "emission_color",
    "opacity": "opacity", "geometryopacity": "opacity", "geometry_opacity": "opacity",
    "thinwalled": "thin_walled", "thin_walled": "thin_walled",
    "geometrythinwalled": "thin_walled", "geometry_thin_walled": "thin_walled",
    "normal": "normal",
    "normalopengl": "normal",
    "normal_opengl": "normal",
    "normalgl": "normal",
    "normal_gl": "normal",
    "nor": "normal",
    "noropengl": "normal",
    "nor_opengl": "normal",
    "norgl": "normal",
    "nor_gl": "normal",
    "nrm": "normal",
    "nrmopengl": "normal",
    "nrm_opengl": "normal",
    "nrmgl": "normal",
    "nrm_gl": "normal",
    "tangent": "tangent", "geometrytangent": "tangent", "geometry_tangent": "tangent",
    "height": "height",
    "hgt": "height",
    "displacement": "displacement",
    "disp": "displacement",
    "displ": "displacement",
    "vectordisplacement": "vector_displacement",
    "vector_displacement": "vector_displacement",
    "vdisp": "vector_displacement",
}


def _canonical(value: str) -> str:
    return ALIASES[value.lower().replace(" ", "_")]


def _is_explicit_opengl_normal(texture: TextureFile) -> bool:
    matches = list(CHANNEL_RE.finditer(texture.source.stem))
    if not matches:
        return False
    token = matches[-1].group("channel").lower().replace(" ", "_")
    return texture.channel == "normal" and (
        "opengl" in token or token.endswith("_gl")
    )


def parse_texture(path: Path) -> TextureFile | None:
    matches = list(CHANNEL_RE.finditer(path.stem))
    if not matches:
        return None
    match = matches[-1]
    channel = _canonical(match.group("channel"))
    texture_set = path.stem[: match.start()].rstrip("_.-") or "material"
    udims = list(UDIM_RE.finditer(path.stem))
    udim = int(udims[-1].group(1)) if udims else None
    return TextureFile(path.resolve(), texture_set, channel, udim)


def scan(
    root: Path,
    output_root: Path | None = None,
    extensions: set[str] | None = None,
) -> dict[str, TextureSet]:
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Texture folder does not exist: {root}")
    output_root = output_root.resolve() if output_root else None
    extensions = extensions or SUPPORTED
    sets: dict[str, TextureSet] = {}
    for path in sorted(root.rglob("*"), key=lambda p: p.as_posix().casefold()):
        if not path.is_file() or path.name.startswith(".") or path.suffix.lower() not in extensions:
            continue
        if output_root and (path == output_root or output_root in path.parents):
            continue
        texture = parse_texture(path)
        if texture:
            sets.setdefault(texture.texture_set, TextureSet(texture.texture_set)).add(texture)
    if not sets:
        raise ValueError(f"No recognized material textures found under {root}")
    for item in sets.values():
        for channel, textures in item.maps.items():
            textures.sort(key=lambda t: (t.udim or 0, t.source.name.casefold()))
            by_tile: dict[int | None, list[TextureFile]] = {}
            for texture in textures:
                by_tile.setdefault(texture.udim, []).append(texture)
            selected = []
            for files in by_tile.values():
                explicit_opengl = [
                    texture for texture in files
                    if _is_explicit_opengl_normal(texture)
                ]
                if channel == "normal" and len(explicit_opengl) == 1:
                    selected.append(explicit_opengl[0])
                else:
                    selected.extend(files)
            item.maps[channel] = selected
            duplicates = {
                tile: files for tile, files in by_tile.items()
                if len(files) > 1
                and not (
                    channel == "normal"
                    and len([
                        texture for texture in files
                        if _is_explicit_opengl_normal(texture)
                    ]) == 1
                )
            }
            if duplicates:
                details = []
                for tile, files in duplicates.items():
                    label = f"UDIM {tile}" if tile is not None else "untiled map"
                    details.append(
                        f"{label}: " + ", ".join(file.source.name for file in files)
                    )
                raise ValueError(
                    f"Texture set {item.name!r} has multiple files for channel "
                    f"{channel!r} ({'; '.join(details)}). Remove the duplicate or "
                    "rename it to a different recognized channel."
                )
    return sets


def udim_pattern(textures: list[TextureFile], use_output: bool = True) -> str:
    texture = textures[0]
    path = texture.output if use_output and texture.output else texture.source
    if texture.udim is None:
        return str(path)
    # Replace the tile in the filename only. A parent folder may also contain
    # a 1001-style asset/version token and must never be rewritten.
    return str(path.with_name(UDIM_RE.sub("<UDIM>", path.name, count=1)))
