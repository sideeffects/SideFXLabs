# VAT Importer

The main SideFX Labs package includes the editor-only Python VAT importer. Legacy does not include it. Install one package using the [installation instructions](README.md), then open **SideFX Labs → Plugins → VAT Importer**.

## Importing

1. Choose Soft, Rigid, Fluid, Sprite, or Skeletal before selecting files. Soft is the initial default.
2. Select an FBX mesh and the matching VAT textures. Skeletal accepts multiple FBX files sharing one Position/Rotation texture pair; other modes accept one mesh.
3. Use the export suffixes `_pos`, `_rot`, `_col`, `_lookup`, `_pos2`, and `_col2` to identify texture roles. Fluid requires its lookup texture. Sprite requires Position and Color; the remaining modes require Position and Rotation.
4. Choose a destination under `/Game`, a material name, and the Houdini FPS matching the export. The default is 24 FPS. Interpolation is enabled where supported; Fluid uses its existing decoding without that switch.
5. Click **Import VAT**. The importer creates textures, meshes, and a new material instance, and assigns that instance to each existing mesh material slot. It does not generate collision.

Hover over controls for additional help. Settings are remembered during the current editor session, including tab reopen and level changes. They are not saved across editor restarts.

## Optional Fluid velocity

Select a single `_vel.exr` alongside the other Fluid textures to use supplied velocity. The importer reads embedded `sidefx_labs_velocity` metadata when present. Without embedded metadata it uses the entered FPS and the established Houdini-local velocity convention. Velocity JSON sidecars are not read.

Export velocity from a finite float3 point attribute `v` in Houdini units per second. Accuracy depends on the supplied velocity field; adding an attribute alone does not guarantee correct motion blur or TSR. Reset and seek history discontinuities are a separate limitation.

## Shared project-owned materials

Set **Shared Dependencies** to a new folder such as `/Game/VATShared` to copy all five importer masters and their required nested Labs material functions and textures into your project. Browse uses Unreal's Content Browser folder picker. Keep imports outside the shared folder.

Later imports reuse the library without overwriting it. You can edit its masters and functions; those changes affect existing instances using them. Preserve asset paths, required importer parameter names and types, and the library metadata on `Materials/M_Import_Soft`. Save customizations before importing. Incomplete or incompatible libraries produce an inline error rather than falling back to Labs assets.

**Reuse Master Material** defaults on. With a shared folder it uses the project's mode-specific master; without one it uses the plugin master. Turn it off to duplicate the selected master into each import destination. The duplicate retains the selected source's function references. Every import creates a distinct material instance, and import-specific settings are applied to that instance without changing master defaults.

Leaving Shared Dependencies empty retains references to Labs content, regardless of the reuse option. Existing imports are not migrated. To adopt new plugin master definitions, create a new library rather than overwriting a customized one.

Playback Blueprints are excluded from this copying workflow. Duplicate them and their parents separately if needed. Verify the complete dependency chain in Reference Viewer, then disable Labs, restart, and package your game to confirm independence.

## Platform notes

The same importer files are validated on Windows in UE 5.6.1, 5.7.4, 5.8.2, and 5.9.0. The importer includes a native macOS file-selection backend, but macOS import and rendering have not been verified on hardware. Manual file paths remain available if browsing fails.
