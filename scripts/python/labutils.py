import os
import hou
import uuid
import shutil
import json

try:
    import requests
    requests_enabled = True
except:
    # requests library missing
    requests_enabled = False

try:
    from PySide2.QtCore import QSettings
    settings = QSettings("SideFX", "SideFXLabs")
except:
    settings = None


home = os.environ["HOUDINI_USER_PREF_DIR"]
config = os.path.join(home, "hcommon.pref")

GA_TRACKING_ID = "UA-2947225-9"


def can_send_anonymous_stats():
    can_share = False

    f = open(config, "r")
    for line in f.readlines():
        if line.startswith("sendAnonymousStats"):
            if line.strip().strip(";").split(":=")[1].strip() == "1":
                can_share = True
            break
    f.close()

    override = os.getenv("HOUDINI_ANONYMOUS_STATISTICS", "1")
    if int(override) == 0:
        can_share = False

    return can_share


def track_event(category, action, label=None, value=0):

    # Generate a random user ID and store it as a setting per Google's guidelines
    hou_uuid = uuid.uuid4()
    if settings:
        if settings.value("uuid"):
            hou_uuid = settings.value("uuid")
        else:
            settings.setValue("uuid", hou_uuid)

    data = {
        'v': '1',  # API Version.
        'tid': GA_TRACKING_ID,  # Tracking ID / Property ID.
        # Anonymous Client Identifier. Ideally, this should be a UUID that
        # is associated with particular user, device, or browser instance.
        'cid': hou_uuid,
        't': 'event',  # Event hit type.
        'ec': category,  # Event category.
        'ea': action,  # Event action.
        'el': label,  # Event label.
        'ev': value,  # Event value, must be an integer
    }

    if requests_enabled:
        try:
            response = requests.post(
                'http://www.google-analytics.com/collect', data=data, timeout=0.1)

        except:
            pass


def like_node(node):
    if can_send_anonymous_stats():
        track_event("Like Events", "liked node", str(node.type().name()))
    hou.ui.displayMessage("Thanks!\n We're glad you like using this tool.\n"
                          " Letting us know will help us prioritize which tools get focused on. ")

def dislike_node(node):
    if can_send_anonymous_stats():
        track_event("Like Events", "dislike node", str(node.type().name()))
    hou.ui.displayMessage("Thanks!\n We're sorry you're not enjoying using this tool.\n"
                          " If you'd like to share your thoughts, please email us at support@sidefx.com. ")

# Temporary check to see if node in labs namespace
def is_labs_node(node):
    name = node.type().name()
    if name.startswith("labs::"):
        return True
    else:
        return False

def send_on_create_analytics(node):
    if can_send_anonymous_stats() and is_labs_node(node):
        track_event("Node Created", str(node.type().name()), str(node.type().definition().version()))

def create_directory_if_not_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def empty_directory_recursive(directory):
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except:
            pass

def extract_section_file(section, savelocation, writemode="wb"):
    with open(savelocation, writemode) as SectionFile:
        try:
            SectionFile.write(section.contents())
        except:
            SectionFile.write(section.binaryContents())

def saveBackgroundImages(node, images):
    result = []
    for image in images:
        image_dict = {
            'path' : image.path(),
            'rect' : [
                image.rect().min().x(),
                image.rect().min().y(),
                image.rect().max().x(),
                image.rect().max().y()
            ]
        }
        if image.relativeToPath():
            image_dict['relativetopath'] = image.relativeToPath()
        if image.brightness() != 1.0:
            image_dict['brightness'] = image.brightness()
        result.append(image_dict)

    with hou.undos.group('Edit Background Images'):
        if result:
            node.setUserData(theBackgroundImagesKey, json.dumps(result))
        else:
            node.destroyUserData(theBackgroundImagesKey)


def add_network_image(network_editor, image_path, scale=0.4, embedded=False):

        image = hou.NetworkImage()

        if embedded:
            data = None
            with open(image_path, "rb") as file:
                data = file.read()

            hou.node("/obj/").setDataBlock(os.path.basename(image_path), data, '')
            image.setPath("opdatablock:/obj/{}".format(os.path.basename(image_path)))
        else:
            image.setPath(image_path)
        
        bounds = network_editor.visibleBounds()
        bounds.expand((-bounds.size()[0]*scale, -bounds.size()[1]*scale))
        image.setRect(bounds)

        background_images = network_editor.backgroundImages() + (image,)
        network_editor.setBackgroundImages(background_images)
        saveBackgroundImages(hou.node("/obj/"), background_images)

def remap_material_override(material_type, material_override, mapping_file):
        CleanDict = {}

        with open(mapping_file) as f:
            data = json.load(f)
            
            Lookup = data["materials"][material_type]

            for x in data["supported"]:
                if x in Lookup.keys():
                    enabled = Lookup[x][0]
                    
                    # if not isinstance(enabled, int):
                    #     enabled = MaterialNode.parm(enabled).evalAsInt() 
                        
                    if enabled == 1:
                        CleanDict[x] = material_override[Lookup[x][1]] 
                            
        return CleanDict 

def extract_embedded_image(path, destination):
    # Likely a COP
    if path.startswith("op:"):
        node = hou.node(path)

        if node != None:
            if node.type().category().name() == "Cop2":
                node.saveImage(destination)

    # Deal with HDA Stored "Textures"
    elif path.startswith("opdef:"):
        with open(destination, "w") as f:
            f.write(hou.readFile(path))