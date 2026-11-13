# One package for Unreal Engine 5.6–5.9

The same main plugin files work across all four tested Windows engine versions. Legacy is a separate importer-free alternative using the same shared content and mount; install only one variant.

Validation recorded on November 11, 2026:

| Engine | Main assets / Blueprints | Legacy assets / Blueprints | Maps per package | Import cases | Standalone build / launch |
|---|---|---|---|---|---|
| 5.6.1 | 85 / 15 | 79 / 14 | 7 | 24 passed | Passed |
| 5.7.4 | 85 / 15 | 79 / 14 | 7 | 24 passed | Passed |
| 5.8.2 | 85 / 15 | 79 / 14 | 7 | 24 passed | Passed |
| 5.9.0 | 85 / 15 | 79 / 14 | 7 | 24 passed | Passed |

Asset counts exclude maps. Hash comparisons confirmed identical distributed files in all eight main/Legacy test installations. No new compatibility edits to plugin code or binary assets were required in this four-engine pass.

## What was checked

- Both variants initialized the Labs menu and all four scripted utilities at clean startup. Callable-function metadata was present, and utility assets remained loaded after garbage collection.
- All plugin assets loaded, all Blueprints compiled, materials were recompiled, and all seven template maps opened independently in each engine.
- All five template actors completed PlayVAT, PauseVAT, ResetVAT, and RestartVAT calls in PIE without increasing their material-slot counts.
- Each engine passed 24 imports: all five modes plus a separate Fluid velocity case, each with shared dependencies on/off and master reuse on/off. Skeletal imported two meshes sharing its VAT textures.
- Parent references, unique material instances, mesh assignments, one-slot preservation, and absence of generated simple collision were verified.
- A customized shared master retained its saved defaults and file hash through repeated imports. Reuse imports used the same master and distinct instances. Shared dependency chains contained no Labs references.
- Soft, 24 FPS, and reuse-on defaults passed. Mode, destination, shared folder, and reuse state survived level changes and tab close/reopen.
- Separate Windows Development demos were built with Labs physically absent. All pak listings contained zero SideFX_Labs entries. Each executable loaded VATShowcase, ran 240 game frames, and exited normally with status 0.

## Maintaining compatibility

The distributed assets retain their existing 5.6-compatible serialization. Newer-engine test copies were never promoted into this package. Author shared asset changes in UE 5.6 and validate separate copies in newer engines; a newer-engine save may prevent an older engine from loading that customized asset.

The package has no custom C++ modules, no engine-version lock, and is enabled by default. The retained Skeletal importer adjustment accepts its existing master without the optional Use Playback Controls scalar and writes that scalar only when present. Other modes continue requiring it.

## Validation limits and known issues

- Runtime builds and game frames were checked automatically. This pass did not visually inspect each mode's animation or certify motion blur, TSR quality, or reset/seek history correctness.
- The earlier UE 5.9 interactive check restored a usable docked importer and exercised Unreal's native Content Browser folder picker. F10 / Sidebar All Tabs reproduced a Slate bOverlapsRight ensure; restoring the panels kept the importer usable. That docking warning remains unresolved and was not retested interactively in every engine.
- Material-function previews may warn about missing preview inputs, including Tex Pos on MF_Data_From_Tex. The enclosing VAT materials and standalone cooks succeeded; preview warnings were not hidden by modifying the distributed assets.
- Engine profiler/toolset notices can appear in runtime logs. No missing Labs packages, VAT shader errors, Blueprint compile errors, or runtime crashes were found in the completed checks.
- Windows builds were tested at the patch versions listed above. macOS hardware and other patch versions have not received this same validation.

