# SideFX Labs for Unreal Engine 5.8

Choose **one** of these alternative installations:

| `SideFX_Labs` | Materials, templates, playback Blueprints, scripted utilities, Labs menu, and Python VAT importer |
| `Legacy/SideFX_Labs` | The same shared content, utilities, and menu, without the VAT importer |

Both use the plugin name and content mount `/SideFX_Labs`. Do not install them together.

## Install

1. Close Unreal Editor and back up your project and any customized Labs assets.
2. Copy the chosen `SideFX_Labs` folder into your project's `Plugins` directory (create it if necessary).
3. Open the project and enable SideFX Labs if needed. Allow its built-in PCG, Python Editor Script Plugin, and Editor Scripting Utilities dependencies to load; restart if prompted.
4. Enable **Show Plugin Content** in the Content Browser to see the assets. The Labs menu and scripted utilities initialize on editor startup.

Neither package ships a custom C++ module or requires compiling Labs binaries. Python is editor-only; the importer is not a packaged-game runtime feature. The main importer's native file picker currently supports Windows and mac.

## VAT importer (main package only)

Open **SideFX Labs → Plugins → VAT Importer**. Choose the VAT type first, then select the FBX mesh and exported textures. Only Skeletal accepts multiple mesh files sharing the VAT textures. Filename suffixes identify texture roles. Choose a destination such as `/Game/VAT`, adjust settings, and import. Settings are remembered for the current editor session.

Legacy has no importer scripts, importer widget, importer material templates, or VAT Importer menu entry.

## Examples
Templates are under `/SideFX_Labs/Templates`, including the `VAT_...` folders and `VAT_Gameplay/Gameplay_VAT_Demo`. The gameplay demo demonstrates the shared playback functions using keyboard controls; focus the PIE viewport to send input.
