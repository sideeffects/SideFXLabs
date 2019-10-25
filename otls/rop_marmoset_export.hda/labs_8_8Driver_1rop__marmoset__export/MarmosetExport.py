## Questions: paula@sidefx.com
## Last Update: 20-June-2018

import mset, json, tempfile, os
from shutil import copyfile

# Check if directory exists, if not.. Create
def ValidateDir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# Work Dir
WorkDir = "\\".join(tempfile.gettempdir().split("\\")[:-1]) + "\\MHoudini\\"

# Create New Scene
mset.newScene()

# Load JSON File with Material Data
### JSON STRUCTURE -- Only contains existing maps, so size of "Index_X" may vary:
# {
#     "PROCESS": 1, 
#     "TEXDATA": {
#         "Index_0": {
#             "Albedo": "<path>\TexName_Albedo.jpg", 
#             "Mesh": "Mushroom10", 
#             "Material": "MaterialName", 
#             "Gloss": "<path>\TexName_Gloss.jpg", 
#             "Normal": "<path>\TexName_Normal_LOD0.jpg"
#         }
#     }
# }



Data = ''
with open(WorkDir + "MaterialStylesheet.json","r") as f:
        Data = f.read()
Items = json.loads(Data)

# Import FBX
mesh = mset.importModel(WorkDir + "MarmosetMesh.fbx")

# Set Timeline
mset.getTimeline().selectionStart = Items["FRAMERANGE"][0]
mset.getTimeline().selectionEnd = Items["FRAMERANGE"][1]
mset.getTimeline().currentFrame = Items['CURRENTFRAME']

# Set Sky
if Items['SKYLIGHT']["UseCustom"] == 1:
        mset.findObject("Sky").importImage(Items['SKYLIGHT']["CustomSkyLight"])
else:
        mset.findObject("Sky").loadSky("data/sky/%s" % Items['SKYLIGHT']["Preset"])

# Set Camera
if Items["CAMERA"] != "":
        mset.setCamera(mset.findObject(Items["CAMERA"]))

# Load and Assign Material to matching Mesh
for item in Items['TEXDATA']:
        MeshName = Items['TEXDATA'][item]['Mesh']
        MaterialName = Items['TEXDATA'][item]['Material']
        SceneMesh = mset.findObject(MeshName)
        Material = mset.findMaterial(MaterialName)

        MaterialTextures = list(Items['TEXDATA'][item].keys())

        if 'Albedo' in MaterialTextures:
                Material.albedo.setField('Albedo Map', mset.Texture(Items['TEXDATA'][item]['Albedo']))
        if 'MaterialTint' in MaterialTextures:
                Material.albedo.setField('Color', Items['TEXDATA'][item]['MaterialTint'])
        if 'Normal' in MaterialTextures:
                Material.surface.setField('Normal Map', mset.Texture(Items['TEXDATA'][item]['Normal']))
        if 'FlipNormalY' in MaterialTextures:
                Material.surface.setField('Flip Y', True if Items['TEXDATA'][item]['FlipNormalY'] == 1 else False)
        if 'Roughness' in MaterialTextures:
                Material.microsurface.setField('Gloss Map', mset.Texture(Items['TEXDATA'][item]['Roughness']))
                Material.microsurface.setField('Invert', True)
        elif 'Gloss' in MaterialTextures:
                Material.microsurface.setField('Gloss Map', mset.Texture(Items['TEXDATA'][item]['Gloss']))
        if 'Specular' in MaterialTextures:
                Material.reflectivity.setField('Specular Map', mset.Texture(Items['TEXDATA'][item]['Specular']))
        if 'Displacement' in MaterialTextures:
                Material.displacement.setField('Displacement Map', mset.Texture(Items['TEXDATA'][item]['Displacement']))
        if 'Opacity' in MaterialTextures:
                Material.setSubroutine("transparency", "Cutout")
                Material.transparency.setField('Alpha Map', mset.Texture(Items['TEXDATA'][item]['Opacity']))
                Material.transparency.setField('Channel', 0)

UseTransparency = True if Items["TRANSPARENT"] == 1 else False

# Export Image
if Items['RENDERTYPE'] == 0:
        ValidateDir(("/").join(Items['RENDERLOCATION'].split("/")[:-1]))
        mset.exportScreenshot(path=Items['RENDERLOCATION'], width=Items['RESOLUTION'][0], height=Items['RESOLUTION'][1], sampling=Items['PIXELSAMPLES'], transparency=UseTransparency)

# Export Video
elif Items['RENDERTYPE'] == 1:
        ValidateDir(("/").join(Items['RENDERLOCATION'].split("/")[:-1]))
        mset.exportVideo(path=Items['RENDERLOCATION'], width=Items['RESOLUTION'][0], height=Items['RESOLUTION'][1], sampling=Items['PIXELSAMPLES'], transparency=UseTransparency)

# Export .mview
elif Items['RENDERTYPE'] == 3:
        ValidateDir(("/").join(Items['MVIEWLOCATION'].split("/")[:-1]))
        mset.frameScene()
        mset.exportViewer(Items['MVIEWLOCATION'], html=False)
        copyfile(Items['MVIEWLOCATION'], WorkDir + "MarmosetViewer.mview")

# PROCESS=0: Refresh Houdini | PROCESS=1: Send to Marmoset
# if Items['PROCESS'] == 0:
#         # Close session
mset.quit()