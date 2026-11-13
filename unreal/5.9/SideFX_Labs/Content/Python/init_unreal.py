import unreal
if unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem) is not None:
    import labs_vat_ui
    labs_vat_ui.register_menu()
