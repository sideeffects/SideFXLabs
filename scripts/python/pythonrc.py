import hou, labutils


# Hide GSplat nodes in Houdini versions before 22.0, as they are not compatible
if hou.applicationVersion()[0] < 22:
    try:
        hou.hscript("ophide Lop labs::relight_gsplats::1.0")
        hou.hscript("ophide Sop labs::delight_gsplats::1.0")
        hou.hscript("ophide Sop labs::normals_from_gsplats::1.0")
    except hou.Error:
        pass


# Prefer VAT 3.1 before Houdini 22 and VAT 4.0 in Houdini 22.
if hou.applicationVersion()[0] < 23:
    try:
        if hou.applicationVersion()[0] < 22:
            hou.hscript("ophide Driver labs::vertex_animation_textures::4.0")
        _vat_version = "3.1" if hou.applicationVersion()[0] < 22 else "4.0"
        _vat_preference = "labs::Driver/vertex_animation_textures::" + _vat_version
        _vat_hierarchy = (hou.getenv("HOUDINI_OPNAMESPACE_HIERARCHY") or "").split()
        hou.putenv("HOUDINI_OPNAMESPACE_HIERARCHY", " ".join([_vat_preference] + [item for item in _vat_hierarchy if item != _vat_preference]))
        hou.hda.reloadNamespaceOrder()
    except hou.Error:
        pass


# Hide Labs VAT in Houdini 23+, including definitions installed after startup.
if hou.applicationVersion()[0] >= 23:
    if not hasattr(hou, "_sidefx_labs_hide_vat"):
        def _hide_labs_vat(event_type=None, **kwargs):
            prefix = "labs::vertex_animation_textures"
            for node_type in hou.ropNodeTypeCategory().nodeTypes().values():
                name = node_type.name()
                if name == prefix or name.startswith(prefix + "::"):
                    node_type.setHidden(True)

        hou._sidefx_labs_hide_vat = _hide_labs_vat
        hou.hda.addEventCallback(
            (hou.hdaEventType.LibraryInstalled, hou.hdaEventType.AssetCreated),
            hou._sidefx_labs_hide_vat,
        )
    hou._sidefx_labs_hide_vat()


# Deprecating Labs OCIO ACES Profile and Labs Alternative Grey Background for Houdini Versions 20 - 21
labutils.deprecate_settings_warnings()

