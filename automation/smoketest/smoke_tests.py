from __future__ import print_function
from __future__ import division
from houdinihelp import api

import xml.etree.ElementTree as ET
import glob
import os
import sys

import logging
import hou

HOUDINI_VERSION = ["17.5", "18.0", "18.5", "19.0"]
MAJOR_MINOR = "%s.%s" % hou.applicationVersion()[:2]

logging.basicConfig(level=logging.DEBUG)

# Remove logs we don't care about.
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def check_labs_namespace(node):
    correct_namespace = "gamedev" if MAJOR_MINOR == "17.5" else "labs"
    return node.type().nameComponents()[1] == correct_namespace


def check_labs_prefix(node):
    correct_prefix = "GameDev" if MAJOR_MINOR == "17.5" else "Labs"
    return node.type().description().split()[0] == correct_prefix


def check_icon(node):
    return "subnet" not in node.type().icon()


def check_output_node(node):
    if node.type().category().name() not in ["Sop", "Top"]:
        return True

    for child in node.children():
        if child.type().name() == "output":
            return True

    return False


def check_input_names(node):
    for _name in node.inputLabels():
        if "Sub-Network" in _name:
            return False

    return True


def check_tab_submenu(node):
    xml_data = node.type().definition().sections()['Tools.shelf'].contents()
    root = ET.fromstring(xml_data)

    submenu_name = None
    for submenu in root.iter("toolSubmenu"):
        submenu_name = submenu.text
        break

    correct_submenu_name = "GameDev" if MAJOR_MINOR == "17.5" else "Labs"
    if correct_submenu_name not in submenu_name or submenu_name is None:
        return False

    return True


def check_version(node):
    version = node.type().definition().version()
    if version != "":
        return True
    return False

def check_docs(node):
    nodetype = node.type()
    pages = api.get_pages()
    helppath = api.nodetype_to_path(nodetype)
    sourcepath = pages.source_path(helppath)
    return pages.store.exists(sourcepath)



def check_analytics(node):
    sections = node.type().definition().sections()
    if "OnCreated" in sections:
        if "analytics" in sections["OnCreated"].contents():
            return True
    return False


def check_parm_names(node):
    parmTemplates = list(node.type().parmTemplates())

    for parmtemplate in parmTemplates:
        _name = parmtemplate.name()

        if _name.startswith('newparameter') or _name.startswith('parm') or _name.startswith('folder'):
            return False
    return True


def run_tests(node):
    node_name = node.type().description() + "(" + node.type().name() + ")"
    _ok = True

    if not check_labs_namespace(node):
        print(node_name + ": __SmoketestError__ : Incorrect Namespace")
        _ok = False

    if not check_icon(node):
        print(node_name + ": __SmoketestWarning__ : Generic Icon")
        _ok = False

    if not check_output_node(node):
        print(node_name + ":  __SmoketestWarning__ : Missing Output Node")
        _ok = False

    if not check_input_names(node):
        print(node_name + ":  __SmoketestWarning__ : Generic Input Name ")
        _ok = False

    if not check_tab_submenu(node):
        print(node_name + ": __SmoketestError__ : Wrong Tab Menu Entry")
        _ok = False

    if not check_analytics(node):
        print(node_name + ": __SmoketestWarning__ : No Analytics Code")
        _ok = False

    # if not check_docs(node):
    #     print(node_name + ": __SmoketestWarning__ : No Documentation")
    #     _ok = False

    if not check_parm_names(node):
        # print(node_name + ": __SmoketestNote__ : Contains Invalid Parm Names")
        # _ok = False
        pass

    return _ok


if __name__ == '__main__':
    if MAJOR_MINOR not in HOUDINI_VERSION:
        print("Houdini %s is not supported. Please use Houdini 17.5-18.5" % MAJOR_MINOR)
        sys.exit(1)

    nodes_to_ignore = \
        ["sop_rc_register_images", "rc_texture_model", "gamedev::sop_substance_material",
         "meshes.hda", "gamedev::sop_instant_meshes", "gamedev::sop_instant_meshes::2.0"]
    if MAJOR_MINOR != "17.5":
        nodes_to_ignore = \
            ["labs::sop_rc_register_images", "labs::rc_texture_model",
             "labs::instant_meshes::2.0", "labs::instant_meshes",
             "labs::substance_material"]

    current_folder = os.path.dirname(os.path.abspath(__file__))
    repo_dir = os.getenv("WORKSPACE", "C:\\Github\\SideFXLabs")
    if MAJOR_MINOR != "17.5":
        repo_dir = os.getenv("WORKSPACE", "C:\\Github\\SideFXLabs")
    if len(sys.argv) > 1:
        repo_dir = sys.argv[1] + "/SideFXLabs"

    hda_files = glob.glob(os.path.join(repo_dir, "otls/*.hda"))

    cop_node = hou.node("/img").createNode("img")
    obj_node = hou.node("/obj")
    sop_node = hou.node("/obj").createNode("geo")
    dop_node = hou.node("/obj").createNode("dopnet") if MAJOR_MINOR != "17.5" else None
    vop_node = hou.node("/mat") if MAJOR_MINOR != "17.5" else None
    rop_node = hou.node("/out")
    shop_node = hou.node("/shop")
    top_node = hou.node("/obj").createNode("topnet")

    categories = {"Cop2": cop_node, "Object": obj_node, "Driver": rop_node,
                  "Sop": sop_node, "Shop": shop_node}
    if MAJOR_MINOR != "17.5":
        categories["Dop"] = dop_node
        categories["Vop"] = vop_node
        categories["Top"] = top_node


    num_nodes = 0
    num_skipped = 0
    num_failed = 0

    for hda_file in hda_files:

        hda_file = hda_file.replace("\\", "/")
        hou.hda.installFile(hda_file)
        definitions = hou.hda.definitionsInFile(hda_file)
        for definition in definitions:
            name = definition.nodeType().name()

            num_nodes = num_nodes + 1

            if name not in nodes_to_ignore:
                print("Attempting to Create Node : " + name)
                ok = True
                try:
                    category = definition.nodeType().category().name()
                    new_node = categories[category].createNode(name)
                    ok = run_tests(new_node)
                    new_node.destroy()
                    if not ok:
                        num_failed = num_failed + 1
                except Exception as e:
                    print(e)
                    ok = False
                    num_failed = num_failed + 1
                print("Tests", "passed" if ok else "FAILED", "on :", name)
            else:
                num_skipped = num_skipped + 1

    print("Completed", num_nodes, "tests")
    print("Skipped", num_skipped)
    print("Failed", num_failed)
    hou.exit()
