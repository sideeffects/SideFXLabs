from __future__ import annotations

from pathlib import Path
import json
import math
import traceback

import hou
from pxr import UsdGeom

from automated_texture_builder.conversion import (
    COLOR_CHANNELS, classify, convert, delete_original_sources,
    delete_sources_for_existing_tx, display_space_name, load_ocio, manifest_existing_tx,
    manifest_source_images, resolve_existing_tx_root, resolve_ocio,
    scene_linear_space,
)
from automated_texture_builder.discovery import scan
from .materials import assignment_candidates, auto_assign, build_materials


def _parm(node: hou.Node, name: str, default=""):
    parm = node.parm(name)
    return parm.eval() if parm is not None else default


def _menu(node: hou.Node, name: str) -> str:
    parm = node.parm(name)
    if parm is None:
        raise RuntimeError(f"Missing menu parameter: {name}")
    return parm.evalAsString()


def refresh_scene_linear(node: hou.Node, show_errors: bool = False) -> str:
    """Refresh the read-only OCIO role display without building materials."""
    try:
        explicit = None if node.evalParm("use_houdini_ocio") else node.evalParm("ocio_config")
        ocio_path = resolve_ocio(explicit)
        value = scene_linear_space(load_ocio(ocio_path))
        node.parm("scene_linear_space").set(value)
        node.parm("active_ocio_config").set(str(ocio_path))
        refresh_color_rules(node)
        return value
    except Exception as exc:
        node.parm("scene_linear_space").set("Unavailable")
        node.parm("active_ocio_config").set(str(exc))
        if show_errors:
            _message(str(exc), True)
        return ""


def _set_if_present(node: hou.Node, name: str, value: str) -> None:
    parm = node.parm(name)
    if parm is not None:
        parm.set(value)


def _tx_rule_status(config) -> str:
    tx_space = classify(config, Path("/tmp/AutomatedTextureBuilder_ColorTexture.tx"))
    if tx_space.casefold() == "raw":
        return "Correct: OCIO config maps .tx files to Raw — no second conversion."
    return (
        f"WARNING: OCIO maps .tx files to {tx_space}. Set the .tx file rule to Raw "
        "to avoid double conversion."
    )


def refresh_color_rules(node: hou.Node) -> None:
    """Summarize real OCIO classifications for source textures by file type."""
    fields = ("rule_exr", "rule_tiff", "rule_web", "rule_data", "rule_target", "rule_tx")
    workflow = _menu(node, "texture_workflow")
    skip_web_linearization = bool(_parm(node, "skip_web_linearization", 0))
    try:
        explicit = None if node.evalParm("use_houdini_ocio") else node.evalParm("ocio_config")
        config = load_ocio(resolve_ocio(explicit))
        tx_rule_status = _tx_rule_status(config)
    except Exception as exc:
        for name in fields:
            _set_if_present(node, name, f"Unavailable: {exc}")
        return
    if workflow == "existing_tx":
        for name in fields[:3]:
            _set_if_present(node, name, "Not applicable — using existing TX files")
        _set_if_present(node, "rule_data", "Existing TX data maps remain Raw — no transform")
        _set_if_present(node, "rule_target", "No conversion — using existing TX files")
        _set_if_present(node, "rule_tx", tx_rule_status)
        return
    source_text = node.evalParm("texture_folder").strip()
    source = Path(source_text).expanduser() if source_text else None
    if source is None or not source.is_dir():
        for name in fields[:3]:
            _set_if_present(node, name, "Select a Source Texture Folder")
        _set_if_present(node, "rule_data", "Raw → Raw — no OCIO transform")
        target = "No TX conversion" if workflow == "source_direct" else "OCIO scene-linear"
        if workflow == "generate_tx" and skip_web_linearization:
            target += "; PNG/JPEG color pixels preserved → detected sRGB source space"
        _set_if_present(node, "rule_target", target)
        _set_if_present(
            node, "rule_tx",
            tx_rule_status,
        )
        return
    try:
        destination = scene_linear_space(config)
        texture_sets = scan(source, (source / "tx").resolve())
        groups = {
            "rule_exr": {".exr"},
            "rule_tiff": {".tif", ".tiff"},
            "rule_web": {".png", ".jpg", ".jpeg"},
        }
        textures = [
            texture
            for texture_set in texture_sets.values()
            for channel_textures in texture_set.maps.values()
            for texture in channel_textures
        ]
        for field, extensions in groups.items():
            spaces = sorted({
                display_space_name(config, classify(config, texture.source))
                for texture in textures
                if texture.channel in COLOR_CHANNELS and texture.source.suffix.lower() in extensions
            })
            if spaces:
                text = f"Read as {', '.join(spaces)} (detected source maps)"
            else:
                fallback_spaces = sorted({
                    display_space_name(
                        config,
                        classify(config, Path("/tmp") / f"AutomatedTextureBuilder_BaseColor{extension}"),
                    )
                    for extension in extensions
                })
                text = (
                    f"Read as {', '.join(fallback_spaces)} "
                    "(OCIO extension rule; no matching maps found)"
                )
            if (
                field == "rule_web"
                and workflow == "generate_tx"
                and skip_web_linearization
            ):
                text += (
                    " — shader lookup uses this detected source space; "
                    "TX pixels remain unconverted"
                )
            _set_if_present(node, field, text)
        data_count = sum(texture.channel not in COLOR_CHANNELS for texture in textures)
        _set_if_present(
            node,
            "rule_data",
            f"Raw → Raw — no OCIO transform ({data_count} file(s) found)",
        )
        if workflow == "source_direct":
            _set_if_present(node, "rule_target", "No TX conversion — source images used directly")
            _set_if_present(node, "rule_tx", tx_rule_status)
        else:
            target = f"Color TX pixels → {destination}"
            if skip_web_linearization:
                target += (
                    "; PNG/JPEG color pixels preserved → detected sRGB source space "
                    "at shader lookup"
                )
            _set_if_present(node, "rule_target", target)
            _set_if_present(node, "rule_tx", tx_rule_status)
    except Exception as exc:
        for name in fields:
            _set_if_present(node, name, f"Unavailable: {exc}")


def refresh_maketx_behavior(node: hou.Node) -> str:
    workflow = _menu(node, "texture_workflow")
    force_enabled = bool(node.evalParm("force_rebuild"))
    if workflow == "source_direct":
        text = "Source images direct: no TX files are generated."
    elif workflow == "existing_tx":
        text = "Existing TX: maketx will not run or regenerate files."
    elif force_enabled:
        text = "Regenerate all TX: every source texture replaces its TX output."
    else:
        text = "Incremental TX: missing, outdated, or incorrectly stored TX files are generated."
    parm = node.parm("maketx_behavior")
    if parm is not None:
        parm.set(text)
    refresh_color_rules(node)
    return text


def _update_conversion_summary(node: hou.Node, manifest: Path, workflow: str) -> str:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    textures = data.get("textures", [])
    color_count = sum(item.get("channel") in COLOR_CHANNELS for item in textures)
    skipped_color_count = sum(
        item.get("channel") in COLOR_CHANNELS
        and bool(item.get("skip_linearization", False))
        for item in textures
    )
    converted_color_count = color_count - skipped_color_count
    data_count = len(textures) - color_count
    scene_linear = data.get("color_output_space", "the OCIO scene-linear space")
    if workflow == "generate_tx":
        failed = [item for item in textures if item.get("status") == "failed"]
        if failed:
            summary = f"Failed: {len(failed)} of {len(textures)} texture files did not convert."
        else:
            color_summary = f"{converted_color_count} color → {scene_linear}"
            if skipped_color_count:
                color_summary += (
                    f"; {skipped_color_count} PNG/JPEG color preserved encoded "
                    "(linearized once at shader lookup)"
                )
            summary = f"Success: {len(textures)} files — {color_summary}; {data_count} data → Raw."
    elif workflow == "existing_tx":
        summary = (
            f"Success: {len(textures)} existing TX files; maketx not run — "
            f"{color_count} color, {data_count} Raw data."
        )
    else:
        summary = (
            f"Success: {len(textures)} source files used directly — "
            f"{color_count} color, {data_count} Raw data; maketx not run."
        )
    node.parm("conversion_summary").set(summary)
    return summary


def _assigned_udim_status(stage, matches: dict[str, str], manifest: Path) -> str:
    """Validate that assigned UDIM materials can read suitable USD UV primvars."""
    data = json.loads(manifest.read_text(encoding="utf-8"))
    sets = {item["name"]: item for item in data.get("texture_sets", [])}
    checked = 0
    issues: list[str] = []
    for set_name, prim_path in matches.items():
        item = sets.get(set_name, {})
        texture_tiles = {
            int(tile)
            for texture in item.get("maps", {}).values()
            if texture.get("udim")
            for tile in texture.get("tiles", [])
        }
        if not texture_tiles:
            continue
        prim = stage.GetPrimAtPath(prim_path)
        mesh = prim
        while mesh and mesh.IsValid() and mesh.GetTypeName() != "Mesh":
            mesh = mesh.GetParent()
        if not mesh or not mesh.IsValid():
            issues.append(f"{set_name}: assigned prim has no parent Mesh")
            continue
        api = UsdGeom.PrimvarsAPI(mesh)
        primvar = api.FindPrimvarWithInheritance("st")
        if not primvar or not primvar.HasValue():
            primvar = api.FindPrimvarWithInheritance("uv")
        if not primvar or not primvar.HasValue():
            issues.append(f"{set_name}: {mesh.GetPath()} has no st/uv primvar")
            continue
        checked += 1
        try:
            values = primvar.ComputeFlattened() or []
            uv_tiles = set()
            for value in values:
                u, v = float(value[0]), float(value[1])
                # Ignore exact tile-border vertices; interior values identify
                # the patch without assigning a shared edge to the wrong tile.
                if math.isclose(u, round(u), abs_tol=1e-7) or math.isclose(v, round(v), abs_tol=1e-7):
                    continue
                if u >= 0.0 and v >= 0.0:
                    uv_tiles.add(1001 + math.floor(u) + 10 * math.floor(v))
            # A texture set may legitimately contain tiles used by sibling
            # meshes.  Only warn when this assigned mesh references a tile
            # for which the material has no texture file.
            missing = sorted(uv_tiles - texture_tiles) if uv_tiles else []
            if missing:
                issues.append(
                    f"{set_name}: {primvar.GetPrimvarName()} requires missing "
                    f"texture tile(s) {', '.join(map(str, missing))}"
                )
        except Exception:
            # The primvar exists and is correctly named; some procedural prims
            # cannot expose flattened values until render time.
            pass
    if issues:
        return "WARNING: " + "; ".join(issues)
    if checked:
        return f"Assigned {len(matches)} material(s); UDIM st/uv verified on {checked} mesh(es)."
    return f"Assigned {len(matches)} material(s); no assigned UDIM sets required UV validation."


def _message(text: str, error: bool = False) -> None:
    print(text)
    if hou.isUIAvailable():
        hou.ui.displayMessage(
            text,
            title="Automated Texture Builder",
            severity=hou.severityType.Error if error else hou.severityType.Message,
        )


def _solaris_nodes(controller: hou.Node):
    parent = controller.parent()
    displayed_before = next(
        (
            child for child in parent.children()
            if child.isGenericFlagSet(hou.nodeFlag.Display)
        ),
        None,
    )
    requested = controller.evalParm("library_name").strip() or controller.name()
    owner = controller.path()
    library = next(
        (
            child for child in parent.children()
            if child.type().name() == "materiallibrary"
            and child.userData("automated_texture_builder") == "1"
            and child.userData("automated_texture_builder_controller") == owner
        ),
        None,
    )
    if library is None:
        candidate = parent.node(requested)
        if (
            candidate is not None
            and candidate.type().name() == "materiallibrary"
            and candidate.userData("automated_texture_builder") == "1"
        ):
            library = candidate
    if library is None:
        library = parent.createNode("materiallibrary", requested)
        library.setUserData("automated_texture_builder", "1")
    elif library.name() != requested:
        library.setName(requested, unique_name=True)
    library.setUserData("automated_texture_builder_controller", owner)
    library.setInput(0, controller)
    library.parm("matpathprefix").set("/materials/")
    library.parm("genpreviewshaders").set(1)
    library.setPosition(controller.position() + hou.Vector2(0.0, -2.0))
    # The HDA itself is a pass-through controller while the visible Material
    # Library is created as its sibling. Move existing downstream consumers
    # behind the library so they receive the authored materials and bindings.
    # Without this, a node wired to the controller before Build silently
    # bypasses the generated Material Library.
    for connection in list(controller.outputConnections()):
        downstream = connection.outputNode()
        if downstream == library:
            continue
        downstream.setInput(
            connection.inputIndex(), library, connection.outputIndex(),
        )
    # Remove the separate Assign Material LOP produced by older tool versions.
    # Preserve any downstream wiring by reconnecting its consumers to the
    # Material Library, which now authors the bindings itself.
    for child in list(parent.children()):
        if (
            child.type().name() == "assignmaterial"
            and child.userData("automated_texture_builder") == "1"
            and child.inputs() and child.inputs()[0] == library
        ):
            for connection in child.outputConnections():
                connection.outputNode().setInput(
                    connection.inputIndex(), library, connection.outputIndex(),
                )
            child.destroy()
    # Creating a LOP can take the display flag, and older versions explicitly
    # forced it onto the generated Material Library. Preserve the artist's
    # currently displayed node instead. If the library was already displayed
    # before this rebuild, leave that deliberate/current state unchanged.
    if displayed_before is not None and displayed_before != library:
        displayed_before.setGenericFlag(hou.nodeFlag.Display, True)
    elif displayed_before is None:
        library.setGenericFlag(hou.nodeFlag.Display, False)
    return library


def _owned_library(controller: hou.Node):
    """Find the generated Material Library belonging to this controller."""
    owner = controller.path()
    return next(
        (
            child for child in controller.parent().children()
            if child.type().name() == "materiallibrary"
            and child.userData("automated_texture_builder") == "1"
            and child.userData("automated_texture_builder_controller") == owner
        ),
        None,
    )


def _published_material_paths(library: hou.Node) -> dict[str, str]:
    """Reconstruct matching names from an already-published Material Library."""
    stored = library.userData("automated_texture_builder_material_paths")
    if stored:
        try:
            material_paths = json.loads(stored)
            if isinstance(material_paths, dict):
                return {str(name): str(path) for name, path in material_paths.items()}
        except (TypeError, ValueError):
            pass
    count = library.parm("materials")
    result = {}
    for index in range(1, int(count.eval()) + 1 if count is not None else 1):
        node_parm = library.parm(f"matnode{index}")
        if node_parm is None:
            continue
        name = node_parm.eval().strip()
        if name:
            result[name] = "/materials/" + name
    return result


def _clear_library_assignments(library: hou.Node) -> None:
    count = library.parm("materials")
    for index in range(1, int(count.eval()) + 1 if count is not None else 1):
        _set_if_present(library, f"assign{index}", 0)
        _set_if_present(library, f"geopath{index}", "")


def _assignment_status(node: hou.Node, library: hou.Node, material_paths, manifest=None):
    """Apply current assignment settings and return matches plus an artist-facing status."""
    if not bool(node.evalParm("auto_assign")):
        _clear_library_assignments(library)
        return {}, "Automatic assignment is off."

    input_node = node.inputs()[0] if node.inputs() else None
    if input_node is None:
        _clear_library_assignments(library)
        return {}, "WARNING: Connect the builder after the Solaris geometry before assigning materials."

    stage = input_node.stage()
    root = node.evalParm("geometry_root").strip() or "/"
    candidates = assignment_candidates(stage, root)
    matches = auto_assign(library, stage, material_paths, root)
    if not matches:
        return {}, (
            f"WARNING: Found {len(candidates)} Mesh/GeomSubset prim(s) below {root}, "
            f"but none uniquely matched the {len(material_paths)} texture-set name(s)."
        )
    if manifest is None:
        unmatched = sorted(set(material_paths) - set(matches))
        suffix = f" Unmatched: {', '.join(unmatched)}." if unmatched else ""
        return matches, f"Assigned {len(matches)} of {len(material_paths)} material(s).{suffix}"
    return matches, _assigned_udim_status(stage, matches, manifest)


def update_assignments(node: hou.Node) -> None:
    """Refresh bindings immediately when assignment controls change."""
    library = _owned_library(node)
    if library is None:
        status = "Build the materials once; assignment will then update automatically."
        _set_if_present(node, "assignment_note", status)
        return
    material_paths = _published_material_paths(library)
    matches, status = _assignment_status(node, library, material_paths)
    _set_if_present(node, "assignment_note", status)
    library.cook(force=True)


def run(node: hou.Node) -> None:
    try:
        refresh_maketx_behavior(node)
        workflow = _menu(node, "texture_workflow")
        source_text = node.evalParm("texture_folder").strip()
        source = Path(source_text).expanduser() if source_text else None
        output = source / "tx" if source else None
        ocio = resolve_ocio(None if node.evalParm("use_houdini_ocio") else node.evalParm("ocio_config"))
        scene_linear = scene_linear_space(load_ocio(ocio))
        node.parm("scene_linear_space").set(scene_linear)
        node.parm("active_ocio_config").set(str(ocio))
        with hou.undos.group("Build automated textures and materials"):
            if workflow == "generate_tx":
                if source is None:
                    raise RuntimeError("Choose a Source Texture Folder for Generate / Update TX mode")
                manifest = convert(
                    source,
                    output,
                    ocio,
                    scene_linear,
                    bool(node.evalParm("force_rebuild")),
                    bool(node.evalParm("inspect_images")),
                    bool(_parm(node, "skip_web_linearization", 0)),
                )
            elif workflow == "existing_tx":
                if source is None:
                    raise RuntimeError("Choose the Texture Folder containing the existing TX files")
                manifest = manifest_existing_tx(
                    resolve_existing_tx_root(source), ocio, bool(node.evalParm("inspect_images"))
                )
            else:
                if source is None:
                    raise RuntimeError("Choose a Source Texture Folder for Source Images Direct mode")
                manifest = manifest_source_images(source, ocio, bool(node.evalParm("inspect_images")))
            _update_conversion_summary(node, manifest, workflow)
            library = _solaris_nodes(node)
            offset_per_instance = bool(_parm(node, "offset_per_instance", 0))
            instance_offset_primvar = str(
                _parm(node, "instance_offset_primvar", "atb_instance_offset")
            ).strip()
            if offset_per_instance and not instance_offset_primvar:
                raise RuntimeError(
                    "Instance Offset Primvar cannot be empty when per-instance offset is enabled"
                )
            material_paths = build_materials(
                library,
                manifest,
                _menu(node, "surface_model"),
                _menu(node, "texture_mode"),
                "st",
                float(node.evalParm("height_scale")),
                float(node.evalParm("height_zero")),
                _menu(node, "geometry_detail_mode"),
                float(node.evalParm("bump_scale")),
                offset_per_instance,
                instance_offset_primvar,
                float(_parm(node, "instance_offset_scale", 1.0)),
            )
            matches, assignment_status = _assignment_status(
                node, library, material_paths, manifest,
            )
            _set_if_present(node, "assignment_note", assignment_status)
            library.parent().layoutChildren(items=(library,))
        _message(
            f"Built {len(material_paths)} visible Solaris material subnet(s) in:\n{library.path()}\n"
            f"OCIO scene-linear: {scene_linear}\nManifest: {manifest}\n"
            f"Automatic assignments: {len(matches)}. {assignment_status}\n"
            f"Output node: {library.path()}"
        )
    except Exception as exc:
        summary = node.parm("conversion_summary")
        if summary is not None:
            summary.set(f"Failed: {exc}")
        traceback.print_exc()
        _message(str(exc), True)
        raise


def delete_sources(node: hou.Node) -> None:
    """Delete only verified source images from the last successful TX build."""
    workflow = _menu(node, "texture_workflow")
    if workflow == "source_direct":
        raise RuntimeError("Original source deletion is blocked while Use Source Images Directly is selected.")
    source_text = node.evalParm("texture_folder").strip()
    if not source_text:
        raise RuntimeError("Choose the source Texture Folder first.")
    try:
        source = Path(source_text).expanduser().resolve()
        if workflow == "generate_tx":
            deleted = delete_original_sources(source / "tx" / "automated_texture_manifest.json")
        else:
            deleted = delete_sources_for_existing_tx(source)
        node.parm("conversion_summary").set(
            f"Deleted {len(deleted)} verified original source texture file(s); generated TX files were preserved."
        )
        _message(
            f"Deleted {len(deleted)} original source texture file(s).\n"
            "Only files listed in the completed manifest were removed; generated TX files were preserved."
        )
    except Exception as exc:
        _message(str(exc), True)
        raise


def browse_folder(node: hou.Node, parm_name: str) -> None:
    if not hou.isUIAvailable():
        return
    value = hou.ui.selectFile(file_type=hou.fileType.Directory, chooser_mode=hou.fileChooserMode.Read)
    if value:
        node.parm(parm_name).set(value)
