## Questions: paula@sidefx.com

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

Data = ''
with open(WorkDir + "MaterialStylesheet.json","r") as f:
    Data = f.read()
Items = json.loads(Data)

# Import FBX
mesh = mset.importModel(WorkDir + "MarmosetMesh.fbx")

# Set Timeline
mset.getTimeline().totalFrames = max(Items["FRAMERANGE"][1] - Items["FRAMERANGE"][0], 1)
mset.getTimeline().selectionEnd = Items["FRAMERANGE"][1]
mset.getTimeline().selectionStart = Items["FRAMERANGE"][0]
mset.getTimeline().currentFrame = Items['CURRENTFRAME']

# Set Sky
if Items['SKYLIGHT']["UseCustom"] == 1:
    mset.findObject("Sky").importImage(Items['SKYLIGHT']["CustomSkyLight"])
else:
    mset.findObject("Sky").loadSky(Items['SKYLIGHT']["Preset"])

# Set Camera
if Items["CAMERA"] != "":
    mset.setCamera(mset.findObject(Items["CAMERA"]))

# Load and Assign Material to matching Mesh
for item in Items['TEXDATA'].keys():
    Material = mset.findMaterial(item)

    HoudiniMaterial = Items["TEXDATA"][item]
    HoudiniMaterialKeys = HoudiniMaterial.keys()

    if 'diffuse' in HoudiniMaterialKeys:
        Material.albedo.setField('Albedo Map', mset.Texture(HoudiniMaterial['diffuse']))
    if 'diffuse_tint' in HoudiniMaterialKeys:
        Material.albedo.setField('Color', HoudiniMaterial['diffuse_tint'])
    if 'tangentnormal' in HoudiniMaterialKeys:
        Material.surface.setField('Normal Map', mset.Texture(HoudiniMaterial['tangentnormal']))
#     if 'FlipNormalY' in MaterialTextures:
#         Material.surface.setField('Flip Y', True if Items['TEXDATA'][item]['FlipNormalY'] == 1 else False)
    if 'roughness' in HoudiniMaterialKeys:
        Material.microsurface.setField('Roughness Map', mset.Texture(HoudiniMaterial['roughness']))
    if "roughness_scalar" in HoudiniMaterialKeys:
        Material.microsurface.setField('Roughness', HoudiniMaterial['roughness_scalar'])
    if "metallic" in HoudiniMaterialKeys:
        Material.reflectivity.setField("Metalness Map", mset.Texture(HoudiniMaterial["metallic"]))
    if "metallic_scalar" in HoudiniMaterialKeys:
        Material.reflectivity.setField("Metalness", HoudiniMaterial["metallic_scalar"])
    if 'displacement' in HoudiniMaterialKeys:
        Material.setSubroutine("displacement","Height")
        Material.displacement.setField('Displacement Map', mset.Texture(HoudiniMaterial["displacement"]))
    if 'opacity' in HoudiniMaterialKeys:
        Material.setSubroutine("transparency", "Dither")
        Material.transparency.setField('Alpha Map', mset.Texture(HoudiniMaterial["opacity"]))
        Material.transparency.setField('Channel', 0)
        Material.transparency.setField('Use Albedo Alpha', False)
    if "occlusion" in HoudiniMaterialKeys:
        Material.setSubroutine("occlusion", "Occlusion")
        Material.occlusion.setField('Occlusion Map', mset.Texture(HoudiniMaterial["occlusion"]))


UseTransparency = True if Items["TRANSPARENT"] == 1 else False

# Export Image
if Items['RENDERTYPE'] == 0:
    ValidateDir(("/").join(Items['RENDERLOCATION'].split("/")[:-1]))
    mset.renderCamera(path=Items['RENDERLOCATION'], width=Items['RESOLUTION'][0], height=Items['RESOLUTION'][1], sampling=Items['PIXELSAMPLES'], transparency=UseTransparency)
    mset.quit()

# Export Video
elif Items['RENDERTYPE'] == 1:
    ValidateDir(("/").join(Items['RENDERLOCATION'].split("/")[:-1]))
    mset.exportVideo(path=Items['RENDERLOCATION'], width=Items['RESOLUTION'][0], height=Items['RESOLUTION'][1], sampling=Items['PIXELSAMPLES'], transparency=UseTransparency)
    mset.quit()

# Export .mview
elif Items['RENDERTYPE'] == 2:
    ValidateDir(("/").join(Items['MVIEWLOCATION'].split("/")[:-1]))
    mset.frameScene()
    mset.exportViewer(Items['MVIEWLOCATION'], html=False)
    copyfile(Items['MVIEWLOCATION'], WorkDir + "MarmosetViewer.mview")
    mset.quit()