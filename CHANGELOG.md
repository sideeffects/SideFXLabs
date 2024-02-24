# SideFX Labs Changelog

### Production Release [20.0.625](https://github.com/sideeffects/SideFXLabs/releases/tag/20.0.625) - Feb 22, 2024

**NEW TOOLS**
- [20.0.608](https://github.com/sideeffects/SideFXLabs/releases/tag/20.0.608) ***Labs Chaotic Shapes SOP*** - Added a new node that generates chaotic point clouds based on attractor formulas.
- [20.0.598](https://github.com/sideeffects/SideFXLabs/releases/tag/20.0.598) ***SideFX Labs Unreal Plugin 5.1/5.2/5.3*** - Upgraded plugin versions. Starting with version 5.1, the plugins have adopted a new, safer namespace practice. So please be sure to read "README BEFORE UPGRADE.txt", which you can find next to the plugin folder. Updated tools that work with these plugins to correctly display the latest compatible plugin versions.

**MAJOR UPDATES**   
- [20.0.608](https://github.com/sideeffects/SideFXLabs/releases/tag/20.0.608) ***Labs Flipbook Textures ROP*** - Included a control for the directions to add viewport paddings. Viewport paddings are necessary to avoid the "Indie Edition" watermarks showing up in the render outputs. By default, the paddings are added to the top and bottom, but depending on your camera's aspect ratio, you may need to add the paddings to the left and right instead.
- [20.0.595](https://github.com/sideeffects/SideFXLabs/releases/tag/20.0.595) ***Labs Flipbook Textures ROP*** - Fixed an issue where MDC passes were not correctly lit. This issue originated from H20, so it was also fixed on the Houdini side in H20.0.592. Also improved color space handling. Previously you could only use Labs OCIO ACES color spaces with this node. Now you can now use Labs OCIO ACES, H19.5's built-in OCIO ACES, or H20's built-in OCIO ACES. This works on both H19.5 and H20.
- [20.0.595](https://github.com/sideeffects/SideFXLabs/releases/tag/20.0.595) ***Labs OCIO ACES 1.2 (Minimal)*** - Updated the color space config file. If you have *Labs OCIO ACES* installed and you want to convert a linear image to ACES sRGB color space, you can go inside a *VOP COP2 Filter COP*, create a *OCIO Transform VOP*, set From Space to "ACEScg" and set To Space to "Output - sRGB". You can ignore this if you are not using *Labs OCIO ACES*.
- [20.0.592](https://github.com/sideeffects/SideFXLabs/releases/tag/20.0.592) ***Labs Biome ... SOPs*** - Renamed *Labs Biome Adjust Settings SOP* to *Labs Biome Profile SOP*. Updated the scripts, UI, and workflows of *Labs Biome Profile SOP*, *Labs Biome Initialize SOP*, and *Labs Biome Curve Setup SOP*.

**MINOR UPDATES**
- [20.0.615](https://github.com/sideeffects/SideFXLabs/releases/tag/20.0.615) **Demo scene files** - Removed all the demo files that are at least 2 years old. Some of these files were too big so they inflated the sizes of the release ZIPs you download from GitHub. The newer example HIP files can be found under `SideFXLabs/hip/examples/TOOL_NAME`. The removed files can still be found on GitHub if you click on Switch branches/tags and choose a tag earlier than 20.0.614.
- [20.0.615](https://github.com/sideeffects/SideFXLabs/releases/tag/20.0.615) ***Labs Desktop Preset*** - Changed the 2nd linked pane tab groups from the Outputs context to the Object context, which is used far more often.
- [20.0.608](https://github.com/sideeffects/SideFXLabs/releases/tag/20.0.608) ***Labs Biome ... SOPs*** - Updated a few default parameters to allow reading/writing JSON data in the correct places. Added OnCreate scripts to create missing JSON files.
- [20.0.608](https://github.com/sideeffects/SideFXLabs/releases/tag/20.0.608) ***Labs Align and Distribute SOP*** - Changed the default piece distribution pattern from a line to a grid, which is easier to visualize.
- [20.0.605](https://github.com/sideeffects/SideFXLabs/releases/tag/20.0.605) ***labs_binarysearch()*** - Updated the Labs VEX function in *sidefxlabs_data.h* to safeguard it against an edge-case scenario where floating-point value comparisons would yield false results due to literals having a higher precision than array elements in the default 32-bit VEX.
- [20.0.605](https://github.com/sideeffects/SideFXLabs/releases/tag/20.0.605) ***VAT_utilities.h*** - Removed because it is no longer used by anything.
- [20.0.603](https://github.com/sideeffects/SideFXLabs/releases/tag/20.0.603) ***Labs Pathfinding Global SOP*** - Added an options to rename the End Points attribute.
- [20.0.603](https://github.com/sideeffects/SideFXLabs/releases/tag/20.0.603) ***Labs Settlement Connections SOP*** - Added an options to rename the End Points attribute.
- [20.0.603](https://github.com/sideeffects/SideFXLabs/releases/tag/20.0.603) ***Labs Loop Volume SOP*** - Updated the Help Page and internal warning messages so that the node provides a clearer instruction on how to use the second input to achieve less visual repetition.
- [20.0.602](https://github.com/sideeffects/SideFXLabs/releases/tag/20.0.602) ***Labs Compilable Segments*** - Changed the SOP alias name from *Compilable Segments* to comply with the Labs convention which requires the "Labs" prefix if an alias creates any Labs nodes instead of only Houdini native nodes.

**BUG FIXES**
- [20.0.615](https://github.com/sideeffects/SideFXLabs/releases/tag/20.0.615) ***Labs Extract Image Metadata TOP 1.1*** - Added the missing Help page file.
- [20.0.608](https://github.com/sideeffects/SideFXLabs/releases/tag/20.0.608) ***Labs Biome ... SOPs*** - Fixed an error with OnCreate scripts.
- [20.0.602](https://github.com/sideeffects/SideFXLabs/releases/tag/20.0.602) **Node namespace** - Fixed an old typo related to back when the "labs" namespace was rebranded from "gamedev". This typo was throwing some annoying warning messages in some old files.
