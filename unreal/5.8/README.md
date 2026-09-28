# SideFX Labs for Unreal Engine

Materials, templates, Blueprint utilities, and editor tools for Unreal Engine 5.6, 5.7, and 5.8. The same package can be used in all three versions.

## Choose a package

| Package | Included |
|---|---|
| `SideFX_Labs` | Shared content, scripted utilities, Labs menu, and Python VAT importer |
| `Legacy/SideFX_Labs` | The same shared content, utilities, and menu, without the VAT importer |

Both use the plugin name and content mount `/SideFX_Labs`. **Do not install them together.**

Neither package contains a custom C++ module or requires compiling Labs binaries.

## Installation

1. Close Unreal Editor and back up your project and any customized Labs assets.
2. Copy the chosen `SideFX_Labs` folder into your project's `Plugins` directory. Create it if necessary.
3. Open the project. Labs is enabled by default unless your project explicitly disables it. Allow its built-in **PCG**, **Python Editor Script Plugin**, and **Editor Scripting Utilities** dependencies to load; restart if prompted.
4. Enable **Show Plugin Content** in the Content Browser.

The Labs menu and scripted utilities initialize on editor startup. Utilities appear in the applicable asset or actor context menus.

## Content and tools

- **Materials:** reusable materials and material functions.
- **Blueprints:** editor utilities and example playback Blueprints.
- **Templates:** example assets and demonstration maps under `/SideFX_Labs/Templates`.
- **Labs menu:** tool access and links to Labs resources.
- **VAT importer (main package only):** imports Houdini Vertex Animation Textures. See the [VAT Importer Guide](VAT_IMPORTER.md) for shared materials, customization, and project-owned dependencies.

## Game packaging

Labs enables Unreal's built-in **PCG plugin**. Depending on your engine and target platform, packaging may require platform build tools even for a Blueprint-only project.

If packaging reports a missing **PCGCompute** module, check that your build includes the required PCG modules. If your game does not need Labs or PCG, follow the workflow below to remove those dependencies before packaging. Do not disable PCG if another part of your game needs it.

The Python importer, startup menu, and editor utilities are authoring tools, not runtime gameplay features.

## Recommended workflow

Use Labs to create and prototype assets, then keep the content your game needs in your project's own Content folder.

1. Duplicate the required assets **and their dependencies** through Unreal's Content Browser.
2. Update references to use your project-owned copies. Include parent Blueprints, materials, functions, textures, and structs where required.
3. Use **Reference Viewer** to confirm the resulting assets no longer reference `/SideFX_Labs/...`.
4. Disable Labs, restart Unreal, and package and test your game. Disable PCG only if nothing else requires it.

Copying an asset into `/Game` does not automatically remove its plugin dependencies. For VAT imports, the optional shared-material workflow can create project-owned material dependencies directly; see the [VAT Importer Guide](VAT_IMPORTER.md).

Keep original plugin assets unchanged where possible so Labs updates do not overwrite your customizations. Use Unreal's asset tools to move or duplicate assets, not File Explorer.
