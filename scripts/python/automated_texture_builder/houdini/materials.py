from __future__ import annotations

import json
from pathlib import Path
import re

import hou
import voptoolutils

from automated_texture_builder.geometry_detail import geometry_detail_plan
from automated_texture_builder.matching import match_materials_to_paths, normalize_usd_root


OPENPBR_INPUTS = {
    "base_weight": ("base_weight", "float"),
    "base_color": ("base_color", "color3"),
    "base_diffuse_roughness": ("base_diffuse_roughness", "float"),
    "base_metalness": ("base_metalness", "float"),
    "specular_weight": ("specular_weight", "float"),
    "specular_color": ("specular_color", "color3"),
    "specular_roughness": ("specular_roughness", "float"),
    "specular_ior": ("specular_ior", "float"),
    "specular_roughness_anisotropy": ("specular_roughness_anisotropy", "float"),
    "transmission_weight": ("transmission_weight", "float"),
    "transmission_color": ("transmission_color", "color3"),
    "transmission_depth": ("transmission_depth", "float"),
    "transmission_scatter": ("transmission_scatter", "color3"),
    "transmission_scatter_anisotropy": ("transmission_scatter_anisotropy", "float"),
    "transmission_dispersion_scale": ("transmission_dispersion_scale", "float"),
    "transmission_dispersion_abbe_number": ("transmission_dispersion_abbe_number", "float"),
    "translucency_weight": ("subsurface_weight", "float"),
    "translucency_color": ("subsurface_color", "color3"),
    "subsurface_weight": ("subsurface_weight", "float"),
    "subsurface_color": ("subsurface_color", "color3"),
    "subsurface_radius": ("subsurface_radius", "float"),
    "subsurface_radius_scale": ("subsurface_radius_scale", "color3"),
    "subsurface_scatter_anisotropy": ("subsurface_scatter_anisotropy", "float"),
    "fuzz_weight": ("fuzz_weight", "float"),
    "fuzz_color": ("fuzz_color", "color3"),
    "fuzz_roughness": ("fuzz_roughness", "float"),
    "coat_weight": ("coat_weight", "float"),
    "coat_color": ("coat_color", "color3"),
    "coat_roughness": ("coat_roughness", "float"),
    "coat_roughness_anisotropy": ("coat_roughness_anisotropy", "float"),
    "coat_ior": ("coat_ior", "float"),
    "coat_darkening": ("coat_darkening", "float"),
    "thin_film_weight": ("thin_film_weight", "float"),
    "thin_film_thickness": ("thin_film_thickness", "float"),
    "thin_film_ior": ("thin_film_ior", "float"),
    "emission_luminance": ("emission_luminance", "float"),
    "emission_color": ("emission_color", "color3"),
    "opacity": ("geometry_opacity", "float"),
}

STANDARD_INPUTS = {
    **{key: value for key, value in OPENPBR_INPUTS.items() if key not in {
        "base_weight", "base_diffuse_roughness", "base_metalness", "specular_weight",
        "specular_ior", "specular_roughness_anisotropy", "transmission_weight",
        "transmission_dispersion_scale", "transmission_dispersion_abbe_number",
        "translucency_weight", "translucency_color",
        "subsurface_weight", "subsurface_radius_scale", "subsurface_scatter_anisotropy",
        "fuzz_weight", "fuzz_color", "fuzz_roughness", "coat_weight",
        "coat_roughness_anisotropy", "coat_ior", "coat_darkening", "thin_film_weight",
        "emission_luminance", "opacity",
    }},
    "base_weight": ("base", "float"),
    "base_diffuse_roughness": ("diffuse_roughness", "float"),
    "base_metalness": ("metalness", "float"),
    "specular_weight": ("specular", "float"),
    "specular_ior": ("specular_IOR", "float"),
    "specular_roughness_anisotropy": ("specular_anisotropy", "float"),
    "specular_anisotropy_angle": ("specular_rotation", "float"),
    "transmission_weight": ("transmission", "float"),
    "transmission_dispersion_scale": ("transmission_dispersion", "float"),
    "translucency_weight": ("subsurface", "float"),
    "translucency_color": ("subsurface_color", "color3"),
    "subsurface_weight": ("subsurface", "float"),
    "subsurface_radius": ("subsurface_scale", "float"),
    "subsurface_radius_scale": ("subsurface_radius", "color3"),
    "subsurface_scatter_anisotropy": ("subsurface_anisotropy", "float"),
    "fuzz_weight": ("sheen", "float"),
    "fuzz_color": ("sheen_color", "color3"),
    "fuzz_roughness": ("sheen_roughness", "float"),
    "coat_weight": ("coat", "float"),
    "coat_roughness_anisotropy": ("coat_anisotropy", "float"),
    "coat_anisotropy_angle": ("coat_rotation", "float"),
    "coat_ior": ("coat_IOR", "float"),
    "thin_film_thickness": ("thin_film_thickness", "float"),
    "thin_film_ior": ("thin_film_IOR", "float"),
    "emission_luminance": ("emission", "float"),
    "opacity": ("opacity", "color3"),
}


def safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")
    return value or "material"


def _input_index(node: hou.Node, name: str) -> int:
    try:
        return node.inputNames().index(name)
    except ValueError as exc:
        raise RuntimeError(f"{node.type().name()} has no input named {name}") from exc


def _connect(target: hou.Node, target_name: str, source: hou.Node) -> None:
    target.setInput(_input_index(target, target_name), source, 0)


def _connect_output(target: hou.Node, target_name: str, source: hou.Node, output_name: str) -> None:
    target.setInput(
        _input_index(target, target_name), source,
        source.outputNames().index(output_name),
    )


def _make_builder(library: hou.Node, name: str) -> hou.Node:
    """Create the single portable MaterialX subnet supported by this tool."""
    builder = voptoolutils._setupMtlXBuilderSubnet(
        destination_node=library, name=name, mask=voptoolutils.MTLX_TAB_MASK,
        folder_label="USD MaterialX Builder", render_context="mtlx",
    )
    builder.setName(name, unique_name=True)
    builder.setUserData("automated_texture_builder", "1")
    builder.setMaterialFlag(True)
    return builder


def _uv_node(builder: hou.Node, uv_primvar: str) -> hou.Node:
    if uv_primvar == "st":
        uv = builder.createNode("mtlxtexcoord", "uv_st")
    else:
        uv = builder.createNode("mtlxgeompropvalue", "uv_" + safe_name(uv_primvar))
        uv.parm("signature").set("vector2")
        uv.parm("geomprop").set(uv_primvar)
    uv.setPosition(hou.Vector2(-7.0, 1.0))
    return uv


def _append_float_control(
    templates: list[hou.ParmTemplate], name: str, label: str, default: float,
    minimum: float, maximum: float,
) -> None:
    templates.append(hou.FloatParmTemplate(
        name, label, 1, default_value=(default,), min=minimum, max=maximum,
    ))


def _append_int_control(
    templates: list[hou.ParmTemplate], name: str, label: str, default: int,
    minimum: int, maximum: int,
) -> None:
    templates.append(hou.IntParmTemplate(
        name, label, 1, default_value=(default,), min=minimum, max=maximum,
    ))


def _append_toggle_control(
    templates: list[hou.ParmTemplate], name: str, label: str, default: bool,
) -> None:
    templates.append(hou.ToggleParmTemplate(name, label, default_value=default))


def _add_texture_controls(
    builder: hou.Node, texture_mode: str,
    offset_per_instance: bool = False, instance_offset_scale: float = 1.0,
) -> None:
    """Create one visible control node that drives every generated texture lookup."""
    controls: list[hou.ParmTemplate] = []
    if texture_mode in {"triplanar", "triplanar_breakup"}:
        _append_float_control(controls, "atb_projection_scale", "Projection Scale", 1.0, 0.001, 100.0)
        _append_float_control(controls, "atb_projection_blend", "Projection Blend", 1.0, 0.0, 1.0)
        if texture_mode == "triplanar_breakup":
            _append_float_control(controls, "atb_breakup_frequency", "Breakup Frequency", 1.0, 0.001, 100.0)
            _append_float_control(controls, "atb_breakup_amount", "Breakup Amount", 0.15, 0.0, 10.0)
    elif texture_mode == "hex":
        _append_float_control(controls, "atb_pattern_tiling", "Pattern Tiling", 1.0, 0.001, 100.0)
        _append_float_control(controls, "atb_random_rotation", "Random Rotation", 1.0, 0.0, 1.0)
        _append_float_control(controls, "atb_rotation_min", "Rotation Minimum", 0.0, -360.0, 360.0)
        _append_float_control(controls, "atb_rotation_max", "Rotation Maximum", 360.0, -360.0, 360.0)
        _append_float_control(controls, "atb_random_scale", "Random Scale", 1.0, 0.0, 1.0)
        _append_float_control(controls, "atb_scale_min", "Scale Minimum", 0.5, 0.001, 10.0)
        _append_float_control(controls, "atb_scale_max", "Scale Maximum", 2.0, 0.001, 10.0)
        _append_float_control(controls, "atb_random_offset", "Random Offset", 1.0, 0.0, 1.0)
        _append_float_control(controls, "atb_offset_min", "Offset Minimum", 0.0, -10.0, 10.0)
        _append_float_control(controls, "atb_offset_max", "Offset Maximum", 1.0, -10.0, 10.0)
        _append_float_control(controls, "atb_pattern_falloff", "Pattern Falloff", 0.5, 0.0, 1.0)
        _append_float_control(controls, "atb_pattern_contrast", "Pattern Contrast", 0.5, 0.0, 1.0)
    if offset_per_instance and texture_mode in {
        "repeat", "hex", "triplanar", "triplanar_breakup",
    }:
        _append_float_control(
            controls, "atb_instance_offset_scale", "Per-Instance Offset Scale",
            instance_offset_scale, 0.0, 100.0,
        )
    if not controls:
        return
    control = builder.createNode("null", "texture_controls")
    control.setComment(
        "UNIVERSAL TEXTURE CONTROLS\n"
        "Shared artist controls. Every compatible texture lookup in this material "
        "references these values. This UI-only node is not part of the MaterialX graph."
    )
    control.setGenericFlag(hou.nodeFlag.DisplayComment, True)
    control.setColor(hou.Color((0.25, 0.55, 0.75)))
    control.setPosition(hou.Vector2(-7.0, 4.0))
    group = control.parmTemplateGroup()
    group.append(hou.FolderParmTemplate(
        "atb_texture_controls", "Texture Controls", tuple(controls),
    ))
    control.setParmTemplateGroup(group)


def _reference(parm: hou.Parm | None, parent_parm: str) -> None:
    if parm is not None:
        parm.setExpression(f'ch("../texture_controls/{parent_parm}")')


def _apply_hex_controls(node: hou.Node) -> None:
    """Drive every standard MaterialX hex lookup from the material controls."""
    for parm_name, control_name in (
        ("tilingx", "atb_pattern_tiling"),
        ("tilingy", "atb_pattern_tiling"),
        ("rotation", "atb_random_rotation"),
        ("rotationrangex", "atb_rotation_min"),
        ("rotationrangey", "atb_rotation_max"),
        ("scale", "atb_random_scale"),
        ("scalerangex", "atb_scale_min"),
        ("scalerangey", "atb_scale_max"),
        ("offset", "atb_random_offset"),
        ("offsetrangex", "atb_offset_min"),
        ("offsetrangey", "atb_offset_max"),
        ("falloff", "atb_pattern_falloff"),
        ("falloffcontrast", "atb_pattern_contrast"),
    ):
        _reference(node.parm(parm_name), control_name)


def _instance_offset_vector3(parent: hou.Node, primvar: str) -> hou.Node:
    """Read and scale one renderer-neutral vector3 USD primvar."""
    result = parent.node("instance_offset_scaled")
    if result is not None:
        return result
    value = parent.createNode("mtlxgeompropvalue", "instance_offset")
    value.parm("signature").set("vector3")
    value.parm("geomprop").set(primvar)
    # Missing primvars use MaterialX's zero default and preserve the old look.
    result = parent.createNode("mtlxmultiply", "instance_offset_scaled")
    result.parm("signature").set("vector3FA")
    _connect(result, "in1", value)
    _reference(result.parm("in2"), "atb_instance_offset_scale")
    return result


def _add_instance_offset_2d(
    parent: hou.Node, coordinates: hou.Node, primvar: str,
) -> hou.Node:
    """Add the XY components of the shared vector3 offset to UV coordinates."""
    xy = parent.createNode("mtlxconvert", "instance_offset_xy")
    xy.parm("signature").set("vector3vector2")
    _connect(xy, "in", _instance_offset_vector3(parent, primvar))
    result = parent.createNode("mtlxadd", "uv_instance_offset")
    result.parm("signature").set("vector2")
    _connect(result, "in1", coordinates)
    _connect(result, "in2", xy)
    return result


def _triplanar_position(
    parent: hou.Node, breakup: bool, instance_offset_primvar: str = "",
) -> hou.Node:
    """Build one renderer-neutral MaterialX position graph shared by all maps."""
    result = parent.node("triplanar_position_output")
    if result is not None:
        return result
    position = parent.createNode("mtlxposition", "triplanar_position")
    position.parm("space").set("object")
    scaled = parent.createNode("mtlxmultiply", "triplanar_position_scaled")
    scaled.parm("signature").set("vector3FA")
    _connect(scaled, "in1", position)
    _reference(scaled.parm("in2"), "atb_projection_scale")
    result = scaled
    if instance_offset_primvar:
        offset_position = parent.createNode("mtlxadd", "triplanar_position_offset")
        offset_position.parm("signature").set("vector3")
        _connect(offset_position, "in1", scaled)
        _connect(
            offset_position, "in2",
            _instance_offset_vector3(parent, instance_offset_primvar),
        )
        result = offset_position
    base_position = result
    if breakup:
        frequency = parent.createNode("mtlxmultiply", "breakup_frequency")
        frequency.parm("signature").set("vector3FA")
        _connect(frequency, "in1", result)
        _reference(frequency.parm("in2"), "atb_breakup_frequency")
        noise = parent.createNode("mtlxnoise3d", "breakup_noise")
        noise.parm("signature").set("vector3")
        _connect(noise, "position", frequency)
        amount = parent.createNode("mtlxmultiply", "breakup_amount")
        amount.parm("signature").set("vector3FA")
        _connect(amount, "in1", noise)
        _reference(amount.parm("in2"), "atb_breakup_amount")
        result = parent.createNode("mtlxadd", "triplanar_position_output")
        result.parm("signature").set("vector3")
        _connect(result, "in1", base_position)
        _connect(result, "in2", amount)
    else:
        result.setName("triplanar_position_output", unique_name=False)
    return result


def _image(
    parent: hou.Node, name: str, path: str, signature: str,
    uv: hou.Node, texture_mode: str, lookup_space: str = "Raw",
    uv_transform: hou.Node | None = None,
    instance_offset_primvar: str = "",
) -> hou.Node:
    if texture_mode in {"triplanar", "triplanar_breakup"}:
        breakup = texture_mode == "triplanar_breakup"
        projection = parent.createNode("mtlxtriplanarprojection", name + "_projection")
        projection.parm("signature").set(signature)
        for axis in "xyz":
            projection.parm("file" + axis).set(path)
            colorspace = projection.parm("file" + axis + "colorspace")
            if colorspace is not None:
                colorspace.set(lookup_space)
        _connect(
            projection, "position",
            _triplanar_position(parent, breakup, instance_offset_primvar),
        )
        _reference(projection.parm("blend"), "atb_projection_blend")
        return projection
    if texture_mode == "hex":
        source_name = name if signature == "color3" else name + "_hex_source"
        source = parent.createNode("mtlxhextiledimage", source_name)
        source.parm("file").set(path)
        if source.parm("filecolorspace"):
            source.parm("filecolorspace").set(lookup_space)
        _connect(source, "texcoord", uv_transform or uv)
        _apply_hex_controls(source)
        if signature == "float":
            channel = parent.createNode("mtlxseparate3c", name)
            _connect(channel, "in", source)
            return channel
        if signature == "vector3":
            converted = parent.createNode("mtlxconvert", name)
            converted.parm("signature").set("color3vector3")
            _connect(converted, "in", source)
            return converted
        return source
    node = parent.createNode("mtlximage", name)
    node.parm("signature").set(signature)
    node.parm("file").set(path)
    if node.parm("filecolorspace"):
        node.parm("filecolorspace").set(lookup_space)
    _connect(node, "texcoord", uv_transform if texture_mode == "repeat" and uv_transform else uv)
    if texture_mode == "repeat":
        node.parm("uaddressmode").set("periodic")
        node.parm("vaddressmode").set("periodic")
    return node


def _normal_texture(
    parent: hou.Node, name: str, path: str, uv: hou.Node,
    texture_mode: str, uv_transform: hou.Node | None,
    instance_offset_primvar: str = "",
) -> hou.Node:
    """Create a normal lookup appropriate for ordinary or hex-broken UV tiling."""
    if texture_mode == "hex":
        normal = parent.createNode("mtlxhextilednormalmap", name)
        normal.parm("file").set(path)
        if normal.parm("filecolorspace"):
            normal.parm("filecolorspace").set("Raw")
        _connect(normal, "texcoord", uv_transform or uv)
        _apply_hex_controls(normal)
        return normal
    if texture_mode in {"triplanar", "triplanar_breakup"}:
        image = _image(
            parent, name, path, "vector3", uv, texture_mode,
            "Raw", uv_transform, instance_offset_primvar=instance_offset_primvar,
        )
        normal = parent.createNode("mtlxnormalmap", name + "_normalmap")
        _connect(normal, "in", image)
        return normal
    image = _image(
        parent, name + "_image", path, "vector3", uv,
        texture_mode, "Raw", uv_transform,
    )
    normal = parent.createNode("mtlxnormalmap", name)
    _connect(normal, "in", image)
    return normal


def _uv_transform_node(
    builder: hou.Node, uv: hou.Node, instance_offset_primvar: str = "",
) -> hou.Node:
    """One shared USD-compatible 2D transform for all UV-tiled image maps."""
    transform = builder.createNode("mtlxUsdTransform2d", "uv_transform2d")
    _connect(transform, "in", uv)
    transform.parm("scalex").set(1.0)
    transform.parm("scaley").set(1.0)
    transform.parm("rotation").set(0.0)
    transform.parm("translationx").set(0.0)
    transform.parm("translationy").set(0.0)
    transform.setPosition(hou.Vector2(-7.0, -0.5))
    if instance_offset_primvar:
        return _add_instance_offset_2d(builder, transform, instance_offset_primvar)
    return transform


def _angle_to_tangent(builder: hou.Node, angle: hou.Node, name: str) -> hou.Node:
    """Convert Painter's normalized anisotropy angle into a tangent vector."""
    radians = builder.createNode("mtlxmultiply", name + "_radians")
    radians.parm("signature").set("float")
    radians.parm("in2").set(6.283185307179586)
    _connect(radians, "in1", angle)
    cosine = builder.createNode("mtlxcos", name + "_cos")
    sine = builder.createNode("mtlxsin", name + "_sin")
    _connect(cosine, "in", radians)
    _connect(sine, "in", radians)
    tangent = builder.createNode("mtlxtangent", name + "_basis_u")
    bitangent = builder.createNode("mtlxbitangent", name + "_basis_v")
    tangent_weighted = builder.createNode("mtlxmultiply", name + "_tangent_u")
    tangent_weighted.parm("signature").set("vector3FA")
    _connect(tangent_weighted, "in1", tangent)
    _connect(tangent_weighted, "in2", cosine)
    bitangent_weighted = builder.createNode("mtlxmultiply", name + "_tangent_v")
    bitangent_weighted.parm("signature").set("vector3FA")
    _connect(bitangent_weighted, "in1", bitangent)
    _connect(bitangent_weighted, "in2", sine)
    result = builder.createNode("mtlxadd", name + "_tangent")
    result.parm("signature").set("vector3")
    _connect(result, "in1", tangent_weighted)
    _connect(result, "in2", bitangent_weighted)
    return result


def clear_generated(library: hou.Node) -> None:
    for child in list(library.children()):
        if child.userData("automated_texture_builder") == "1":
            child.destroy()


def _publish_library(library: hou.Node, material_paths: dict[str, str]) -> dict[str, str]:
    # Keep the original texture-set names for assignment-only refreshes. Node
    # names are sanitized and are not always sufficient to reconstruct them.
    library.setUserData(
        "automated_texture_builder_material_paths",
        json.dumps(material_paths, sort_keys=True),
    )
    count = library.parm("materials")
    if count is not None:
        count.set(len(material_paths))
        for index, set_name in enumerate(sorted(material_paths), 1):
            node_name = material_paths[set_name].rsplit("/", 1)[-1]
            for parm_name, value in (
                (f"enable{index}", 1), (f"matflag{index}", 0),
                (f"matnode{index}", node_name), (f"matpath{index}", node_name),
                (f"assign{index}", 0), (f"geopath{index}", ""),
            ):
                parm = library.parm(parm_name)
                if parm is not None:
                    parm.set(value)
    library.layoutChildren()
    return material_paths


def _replace_surface(builder: hou.Node, surface_model: str) -> hou.Node:
    old = builder.node("mtlxstandard_surface")
    if surface_model == "standard_surface":
        old.setName("standard_surface", unique_name=True)
        return old
    surface = builder.createNode("mtlxopen_pbr_surface", "openpbr_surface")
    for connection in old.outputConnections():
        connection.outputNode().setInput(connection.inputIndex(), surface, connection.outputIndex())
    old.destroy()
    return surface


def build_materials(
    library: hou.Node,
    manifest_path: Path,
    surface_model: str = "openpbr",
    texture_mode: str = "auto",
    uv_primvar: str = "st",
    height_scale: float = 0.01,
    height_zero: float = 0.0,
    detail_mode: str = "auto",
    bump_scale: float = 1.0,
    offset_per_instance: bool = False,
    instance_offset_primvar: str = "atb_instance_offset",
    instance_offset_scale: float = 1.0,
) -> dict[str, str]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    clear_generated(library)
    material_paths: dict[str, str] = {}
    input_map = OPENPBR_INPUTS if surface_model == "openpbr" else STANDARD_INPUTS
    for index, texture_set in enumerate(data["texture_sets"]):
        set_name = texture_set["name"]
        node_name = safe_name(set_name)
        builder = _make_builder(library, node_name)
        _add_texture_controls(
            builder, texture_mode,
            offset_per_instance=offset_per_instance,
            instance_offset_scale=instance_offset_scale,
        )
        surface = _replace_surface(builder, surface_model)
        surface.setPosition(hou.Vector2(1.0, 1.0))
        displacement = builder.node("mtlxdisplacement")
        uv = _uv_node(builder, uv_primvar)
        instance_primvar = instance_offset_primvar if offset_per_instance else ""
        uv_transform = (
            _uv_transform_node(builder, uv, instance_primvar)
            if texture_mode in {"repeat", "hex"} else None
        )
        maps = texture_set["maps"]
        for offset, (channel, (input_name, signature)) in enumerate(input_map.items()):
            if channel not in maps or input_name not in surface.inputNames():
                continue
            path = maps[channel]["path"]
            image = _image(
                builder, channel, path, signature, uv, texture_mode,
                maps[channel].get("lookup_space", "Raw"),
                uv_transform, instance_offset_primvar=instance_primvar,
            )
            image.setPosition(hou.Vector2(-4.5, 5.0 - offset * 1.1))
            _connect(surface, input_name, image)
        if surface_model == "openpbr":
            for channel, input_name in (
                ("tangent", "geometry_tangent"),
                ("coat_tangent", "geometry_coat_tangent"),
            ):
                if channel not in maps:
                    continue
                tangent = _image(
                    builder, channel, maps[channel]["path"], "vector3", uv,
                    texture_mode, "Raw", uv_transform, instance_offset_primvar=instance_primvar,
                )
                _connect(surface, input_name, tangent)
            for channel, input_name in (
                ("specular_anisotropy_angle", "geometry_tangent"),
                ("coat_anisotropy_angle", "geometry_coat_tangent"),
            ):
                explicit_tangent = "tangent" if channel == "specular_anisotropy_angle" else "coat_tangent"
                if channel not in maps or explicit_tangent in maps:
                    continue
                angle = _image(
                    builder, channel, maps[channel]["path"], "float", uv,
                    texture_mode, "Raw", uv_transform, instance_offset_primvar=instance_primvar,
                )
                _connect(surface, input_name, _angle_to_tangent(builder, angle, channel))
        thin_walled_input = "geometry_thin_walled" if surface_model == "openpbr" else "thin_walled"
        if "thin_walled" in maps:
            mask = _image(
                builder, "thin_walled", maps["thin_walled"]["path"], "float",
                uv, texture_mode, "Raw", uv_transform, instance_offset_primvar=instance_primvar,
            )
            compare = builder.createNode("mtlxcompare", "thin_walled_threshold")
            compare.parm("test").set(3)  # greater than
            compare.parm("input2").set(0.5)
            _connect(compare, "input1", mask)
            _connect(surface, thin_walled_input, compare)
        elif "translucency_weight" in maps or "translucency_color" in maps:
            parm = surface.parm(thin_walled_input)
            if parm is not None:
                parm.set(1)
        if "legacy_specular_level" in maps and "specular_weight" not in maps:
            surface.setComment(
                "Legacy SpecularLevel was not connected. Export OpenPBR SpecularWeight instead."
            )
        normal_result = None
        if "normal" in maps:
            normal = _normal_texture(
                builder, "normal", maps["normal"]["path"], uv,
                texture_mode, uv_transform, instance_offset_primvar=instance_primvar,
            )
            normal.setPosition(hou.Vector2(-1.5, -3.0))
            _connect(surface, "geometry_normal" if surface_model == "openpbr" else "normal", normal)
            normal_result = normal
        if "coat_normal" in maps:
            normal = _normal_texture(
                builder, "coat_normal", maps["coat_normal"]["path"], uv,
                texture_mode, uv_transform, instance_offset_primvar=instance_primvar,
            )
            _connect(surface, "geometry_coat_normal" if surface_model == "openpbr" else "coat_normal", normal)
        bump_channel, displacement_channel = geometry_detail_plan(maps, detail_mode)
        if bump_channel:
            height = _image(
                builder, bump_channel, maps[bump_channel]["path"], "float",
                uv, texture_mode, "Raw", uv_transform, instance_offset_primvar=instance_primvar,
            )
            bump = builder.createNode("mtlxbump", bump_channel + "_bump")
            bump.parm("scale").set(bump_scale)
            _connect(bump, "height", height)
            if normal_result is not None:
                _connect(bump, "normal", normal_result)
            _connect(surface, "geometry_normal" if surface_model == "openpbr" else "normal", bump)
            height.setPosition(hou.Vector2(-4.5, -5.0))
            bump.setPosition(hou.Vector2(-1.5, -5.0))
        if displacement_channel:
            vector = displacement_channel == "vector_displacement"
            displacement_image = _image(
                builder, displacement_channel, maps[displacement_channel]["path"],
                "vector3" if vector else "float",
                uv, texture_mode, "Raw", uv_transform, instance_offset_primvar=instance_primvar,
            )
            centered_height = builder.createNode("mtlxsubtract", "height_zero_level")
            centered_height.parm("signature").set("vector3" if vector else "float")
            if vector:
                for component in "xyz":
                    centered_height.parm("in2_vector3" + component).set(height_zero)
                displacement.parm("signature").set("vector3")
            else:
                centered_height.parm("in2").set(height_zero)
            _connect(centered_height, "in1", displacement_image)
            displacement.parm("scale").set(height_scale)
            displacement_image.setPosition(hou.Vector2(-4.5, -6.5))
            centered_height.setPosition(hou.Vector2(-3.0, -5.0))
            displacement.setPosition(hou.Vector2(-1.5, -5.0))
            _connect(displacement, "displacement", centered_height)
        builder.layoutChildren()
        builder.setPosition(hou.Vector2(float(index % 4) * 4.0, -float(index // 4) * 3.0))
        material_paths[set_name] = "/materials/" + builder.name()
    return _publish_library(library, material_paths)


def assignment_candidates(stage, geometry_root: str) -> list[tuple[str, bool]]:
    """Return assignable USD prims below the requested root."""
    candidates = []
    root_path = normalize_usd_root(geometry_root)
    root = stage.GetPseudoRoot() if root_path == "/" else stage.GetPrimAtPath(root_path)
    if root:
        for prim in stage.Traverse():
            path = str(prim.GetPath())
            in_root = (
                root_path == "/"
                or path == root_path
                or path.startswith(root_path + "/")
            )
            if in_root and prim.GetTypeName() in {"Mesh", "GeomSubset"}:
                candidates.append((path, prim.GetTypeName() == "GeomSubset"))
    return candidates


def auto_assign(library: hou.Node, stage, material_paths: dict[str, str], geometry_root: str) -> dict[str, str]:
    candidates = assignment_candidates(stage, geometry_root)
    matches = match_materials_to_paths(
        material_paths, candidates, allow_single_fallback=True,
    )
    # Material Library uses the same sorted order authored by _publish_library.
    # Bind directly in each material entry instead of creating another LOP.
    for index, set_name in enumerate(sorted(material_paths), 1):
        assigned_path = matches.get(set_name, "")
        assign_parm = library.parm(f"assign{index}")
        path_parm = library.parm(f"geopath{index}")
        if assign_parm is not None:
            assign_parm.set(1 if assigned_path else 0)
        if path_parm is not None:
            path_parm.set(assigned_path)
    return matches
