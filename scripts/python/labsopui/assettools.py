#!/usr/bin/env python

import hou
import os
import re
import json
import defaulttools

from hutil.Qt.QtCore import QRegExp, QSize, Qt
from hutil.Qt.QtGui import QRegExpValidator, QStandardItemModel, QStandardItem, QIcon, QFont
from hutil.Qt.QtWidgets import QWidget, QLayout, QLineEdit, QLabel, QPushButton, QDialog, QListWidgetItem, QFileDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QListWidget, QListView, QCheckBox, QComboBox, QSpacerItem, QSizePolicy, QSpinBox, QTableView, QTableWidget, QAbstractItemView, QTreeView


def getConfigKeys():

    keys = ['vhdapath',
            'show_branch',
            'enable_user_default',
            'enable_branch_default',
            'branch_custom_list',
            'default_branch_idx',
            'user_custom_list',
            'default_user_idx',
            'enable_versioning',
            'menu_entry']

    return keys

def createVHDAConfigData(path=None,
                         show_branch=None,
                         enable_user=None,
                         enable_branch=None,
                         branch_labels=None,
                         branch_default_idx=None,
                         user_labels=None,
                         user_default_idx=None,
                         enable_versioning=None,
                         menu_entry=None):

    data = {}

    if path is not None:
        data[getConfigKeys()[0]] = path
    else:
        data[getConfigKeys()[0]] = "$HOUDINI_USER_PREF_DIR/otls"

    if show_branch is not None:
        data[getConfigKeys()[1]] = show_branch
    else:
        data[getConfigKeys()[1]] = True

    if enable_user is not None:
        data[getConfigKeys()[2]] = enable_user
    else:
        data[getConfigKeys()[2]] = True

    if enable_branch is not None:
        data[getConfigKeys()[3]] = enable_branch
    else:
        data[getConfigKeys()[3]] = True

    if branch_labels is not None:
        data[getConfigKeys()[4]] = branch_labels
    else:
        data[getConfigKeys()[4]] = getDefaultBranchLabels()

    if branch_default_idx is not None:
        data[getConfigKeys()[5]] = branch_default_idx
    else:
        data[getConfigKeys()[5]] = 0

    if user_labels is not None:
        data[getConfigKeys()[6]] = user_labels
    else:
        data[getConfigKeys()[6]] = getDefaultUserLabels()

    if user_default_idx is not None:
        data[getConfigKeys()[7]] = user_default_idx
    else:
        data[getConfigKeys()[7]] = 0

    if enable_versioning is not None:
        data[getConfigKeys()[8]] = enable_versioning
    else:
        data[getConfigKeys()[8]] = True

    if menu_entry is not None:
        data[getConfigKeys()[9]] = menu_entry
    else:
        data[getConfigKeys()[9]] = "Digital Assets"

    return data

def getVHDAConfigFilePath():
    """ Returns the path for the config file, which is created under $HOUDINI_USER_PREF_DIR/vhda.config

    """

    return os.path.join(hou.expandString('$HOUDINI_USER_PREF_DIR'),"vhda.config")

def getDefaultUserLabels():
    """ Returns a list of possible labels for the User dropdown menus.

    """

    return [hou.userName()]

def getDefaultBranchLabels():
    """ Returns a list of possible labels for the Branch dropdown menus.

    """

    return ["dev", "beta", "main"]

def getDefaultInstallLabels():
    """ Returns a list of possible labels for the File Path dropdown menus.

    """

    return ["Saved Preference", "User Preference", "Hip File Directory", "Site-Specific", "Embedded"]

def getDefaultInstallPaths():
    """ Returns a list of possible paths for the File Path dropdown menus.

    """

    return [getVHDAConfigValue(getConfigKeys()[0]), "$HOUDINI_USER_PREF_DIR/otls", "$HIP/hda", "$HSITE/hda", "Embedded"]

def initVHDAConfigFile():

    vhdaconfigfile = getVHDAConfigFilePath()

    if not os.path.exists(vhdaconfigfile):
        # create an empy config file
        data = {}
        with open(vhdaconfigfile,'w') as outfile:
            json.dump(data,outfile, indent=4, sort_keys=True)

    # populate with missing config keys
    data = {}
    with open(vhdaconfigfile, 'r') as json_file:
        data = json.load(json_file)

    overwrite = False
    default_data = createVHDAConfigData()
    for key in default_data :
        if key not in data:
            overwrite = True
            data[key] = default_data[key]

    if overwrite:
        with open(vhdaconfigfile, 'w') as json_file:
            json.dump(data,json_file, indent=4, sort_keys=True)


def writeVHDAConfigFile(path=None,
                        show_branch=None,
                        enable_user=None,
                        enable_branch=None,
                        branch_labels=None,
                        branch_default_idx=None,
                        user_labels=None,
                        user_default_idx=None,
                        enable_versioning=None,
                        menu_entry=None):

    """ Writes/Overwrites the vhda.config file.

        param enable_user: Enabled 'User' checkbox on creation window by default.
        param enable_branch: Enables     'Branch' checkbox on creation window by default.
        param path: the vhdapath. If no path is given, it will use the default user pref dir.
        param show_branch: whenever to sisplays the branch in in the Tab menu.  -> Cluster (dev)

    """
    vhdaconfigfile = getVHDAConfigFilePath()
    data = createVHDAConfigData(path,
                                show_branch,
                                enable_user,
                                enable_branch,
                                branch_labels,
                                branch_default_idx,
                                user_labels,
                                user_default_idx,
                                enable_versioning,
                                menu_entry)

    with open(vhdaconfigfile,'w') as outfile:
        json.dump(data,outfile, indent=4, sort_keys=True)

def getVHDAConfigValue(key):
    """ Reads the vhda.config file and returns the value at key. If the config file does not exists it creates a default.

        param key: The key to return, 'vhdapath', 'show_branch', etc...

    """
    vhdaconfigfile = getVHDAConfigFilePath()
    data = {}
    with open(vhdaconfigfile) as infile:
        data = json.load(infile)

    return data[key]

def createVHDADir(path):
    """ Creates a directory if it does not exists.

    """
    path_expanded = hou.expandString(path)
    if not os.path.exists(path_expanded):
        os.makedirs(path_expanded)

def isVersionedDefinition(definition):
    """ Returns if the definition is version in the format: major.minor

        :param defintion: the HDADefition by hou.node.type().definition()
    """

    name_components = definition.nodeType().nameComponents()
    user = name_components[1]
    global_ver = name_components[3]

    if "." in global_ver:
        return True

def isVHDA(node):
    if not node.canCreateDigitalAsset():
        definition = node.type().definition()
        if definition:
            return isVersionedDefinition(definition)
    return False

def isHDA(node):
    if not node.canCreateDigitalAsset():
        definition = node.type().definition()
        if definition:
            return True
    return False

def isSubnet(node):
    if node.canCreateDigitalAsset():
        return True

def getToolSubmenu(hda_def):
    """ Returns the tab submenu entries of this node.
        Note: A node could be placed in multipe entries at once.

        :param defintion: the HDADefition by hou.node.type().definition()
    """

    import xml.etree.ElementTree as ET
    if hda_def.hasSection('Tools.shelf'):
        sections = hda_def.sections()
        ts_section = sections['Tools.shelf'].contents()

        root = ET.fromstring(ts_section)
        tool = root[0]
        submenus = tool.findall('toolSubmenu')
        if submenus:
            tool_submenus = []
            for submenu in submenus:
                tool_submenus.append(submenu.text)
            return tool_submenus
        else:
            return None
    else:
        return None

def getAllToolSubmenus(node_type_category='Sop'):
    """ Returns a list of all tab submenu entries in the scene file.

        :param node_type_category_name: the HDADefition by hou.node.type().definition()

            hou.nodeTypeCategories().keys()
            ['Shop', 'Cop2', 'CopNet', 'ChopNet', 'Object', 'Driver', 'Chop', 'Sop', 'Manager', 'Vop', 'Director', 'Dop', 'VopNet']
    """

    tool_submenus = []
    for category in hou.nodeTypeCategories().values():
        if category.name() == node_type_category:
            for node_type in category.nodeTypes().values():
                for definition in node_type.allInstalledDefinitions():
                    submenus = getToolSubmenu(definition)
                    if submenus is not None:
                        for submenu in submenus:
                            if submenu not in tool_submenus:
                                tool_submenus.append(submenu)

    tool_submenus.sort()
    return tool_submenus


def setToolSubmenu(hda_def, new_submenu='Digital Assets', old_submenu='Digital Assets'):
    """ Sest the tab menu entry for a node.

        :param hda_def: the HDADefition by hou.node.type().definition()
        :param new_submenu: This will be the new submenu, replacing old_submenu entry.
        :param old_submenu: This entry will be replaced by new_submenu.
    """

    context_dict = {
        'Shop': 'SHOP',
        'Cop2': 'COP2',
        'Object': 'OBJ',
        'Chop': 'CHOP',
        'Sop': 'SOP',
        'Vop': 'VOP',
        'VopNet': 'VOPNET',
        'Driver': 'ROP',
        'TOP': 'TOP',
        'Lop': 'LOP',
        'Dop': 'DOP'}

    utils_dict = {
        'Shop': 'shoptoolutils',
        'Cop2': 'cop2toolutils',
        'Object': 'objecttoolutils',
        'Chop': 'choptoolutils',
        'Sop': 'soptoolutils',
        'Vop': 'voptoolutils',
        'VopNet': 'vopnettoolutils',
        'Driver': 'drivertoolutils',
        'TOP': 'toptoolutils',
        'Lop': 'loptoolutils',
        'Dop': 'doptoolutils'}

    if hda_def.hasSection('Tools.shelf'):
        old_submenu = getToolSubmenu(hda_def)[0]
    else:
        content = """<?xml version="1.0" encoding="UTF-8"?>
<shelfDocument>
<!-- This file contains definitions of shelves, toolbars, and tools.
It should not be hand-edited when it is being used by the application.
Note, that two definitions of the same element are not allowed in
a single file. -->
<tool name="$HDA_DEFAULT_TOOL" label="$HDA_LABEL" icon="$HDA_ICON">
    <toolMenuContext name="viewer">
    <contextNetType>SOP</contextNetType>
    </toolMenuContext>
    <toolMenuContext name="network">
    <contextOpType>$HDA_TABLE_AND_NAME</contextOpType>
    </toolMenuContext>
    <toolSubmenu>Digital Assets</toolSubmenu>
    <script scriptType="python"><![CDATA[import soptoolutils
soptoolutils.genericTool(kwargs, \'$HDA_NAME\')]]></script>
</tool>
</shelfDocument>
        """

        context = context_dict[hda_def.nodeType().category().name()]
        util = utils_dict[hda_def.nodeType().category().name()]
        content = content.replace('<contextNetType>SOP</contextNetType>', '<contextNetType>{}</contextNetType>'.format(context))
        content = content.replace('soptoolutils', util)
        hda_def.addSection('Tools.shelf', content)
        old_submenu = 'Digital Assets'

    tools = hda_def.sections()["Tools.shelf"]
    content = tools.contents()
    new_submenu = '<toolSubmenu>{submenu}</toolSubmenu>'.format(submenu=new_submenu)
    old_submenu = '<toolSubmenu>{submenu}</toolSubmenu>'.format(submenu=old_submenu)
    content = content.replace(old_submenu,new_submenu)

    hda_def.addSection('Tools.shelf', content)

def setVHDASection(hda_def, has_user=True,has_branch=True):

    data = {}

    if has_user and has_branch:
        data['namespace'] = 'both'
    elif has_user and not has_branch:
        data['namespace'] = 'user'
    elif has_branch and not has_user:
        data['namespace'] = 'branch'
    else:
        # do not add section, check if there is one, in which case remove it.
        data['namespace'] = 'none'

    tmp_filepath = os.path.join(hou.expandString("$HOUDINI_TEMP_DIR"),"vhda_section.json")

    with open(tmp_filepath,'w') as outfile:
        json.dump(data,outfile, indent=4, sort_keys=True)

    section_file = open(tmp_filepath, 'r')
    hda_def.addSection('VHDA', section_file.read())
    section_file.close()

    os.remove(tmp_filepath)

def allInstalledDefinitionsInScene(node_type_category_name='Sop'):
    """ Returns all the HDA definitions installed in the scene.

        :param node_type_category_name: the HDADefition by hou.node.type().definition()

            hou.nodeTypeCategories().keys()
            ['Shop', 'Cop2', 'CopNet', 'ChopNet', 'Object', 'Driver', 'Chop', 'Sop', 'Manager', 'Vop', 'Director', 'Dop', 'VopNet']
    """
    definitions = []
    for category in hou.nodeTypeCategories().values():
        if category.name() == node_type_category_name:
            for node_type in category.nodeTypes().values():
                for definition in node_type.allInstalledDefinitions():
                    definitions.append(definition)
    return definitions

def allVHDAFilesInPath():
    """ Returns the filename of all the VHDA definitions saved in the VHDA Path directory, including .hda extension

        Valid asset file namings:

        user.dev.asset_name.2.3.hda
        dev.asset_name.2.3.hda
        asset_name.2.3.hda

    """
    hda_files = []
    hda_path = hou.expandString(getVHDAConfigValue(getConfigKeys()[0]))

    regex = "(([a-zA-Z])\w+\.){1,3}\d+\.\d+\."  + getAssetfileExtenstion()
    regex_nover = "(([a-zA-Z])\w+\.){1,3}" + getAssetfileExtenstion()

    if os.path.exists(hda_path):
        for hda_file in os.listdir(hda_path):
            if re.match(regex,hda_file) or re.match(regex_nover,hda_file):
                hda_files.append(os.path.join(hda_path, hda_file))
    return hda_files

def allNonInstalledDefinitionsInVHDAPath():

    definitions = []
    vhda_path = hou.expandString(getVHDAConfigValue(getConfigKeys()[0]))
    for hda_file in allVHDAFilesInPath():
        definition = None
        try:
            definition = hou.hda.definitionsInFile(os.path.join(vhda_path,hda_file))[0]
        except hou.OperationFailed:
            pass
        else:
            if definition:
                if not definition.isInstalled():
                    definitions.append(definition)
    return definitions


def getLatestMajorVersion(definitions, hda_files, namespace_user, namespace_branch, name):
    """ Returns the highest major version number from a given list of definitions.

    """

    major = 0

    # Major version by installed definition
    for definition in definitions:
        other_label, other_namespace_user, other_namespace_type, other_name, other_major, other_minor = separateVHDATypeNameComponents(definition.nodeType())
        if namespace_user == other_namespace_user and namespace_branch == other_namespace_type and name == other_name:
            if other_major > major:
                major = other_major


    # Major version by hda files in VHDA Path directory
    for hda_file in hda_files:
        file_namespace_user, file_namespace_type, file_name, file_major, file_minor = separateVHDAFileNameComponents(hda_file)
        if namespace_user == file_namespace_user and namespace_branch == file_namespace_type and name == file_name:
            if file_major > major:
                major = file_major

    return major

def getLatestMinorVersion(definitions, hda_files, namespace_user, namespace_branch, name, major):
    """ Returns the highest minor version number from a given list of definitions.

    """

    minor = 0

    # Minor version by installed definition
    for definition in definitions:
        other_label, other_namespace_user, other_namespace_type, other_name, other_major, other_minor = separateVHDATypeNameComponents(definition.nodeType())
        if namespace_user == other_namespace_user and namespace_branch == other_namespace_type and name == other_name and major == other_major:
            if other_minor > minor:
                minor = other_minor

     # Minor version by hda files in VHDA Path directory
    for hda_file in hda_files:
        file_namespace_user, file_namespace_type, file_name, file_major, file_minor = separateVHDAFileNameComponents(hda_file)
        if namespace_user == file_namespace_user and namespace_branch == file_namespace_type and name == file_name and major == file_major:
            if file_minor > minor:
                minor = file_minor

    return minor

def getInstalledVHDADefinitions(node, use_namespace=True):
    """ Given a node, it returns the HDADefinition for all versions of the node's definition.

        :param  use_namespace: Comparison by the asset type only, or using namespace and major/minor version as well.

    """

    label, namespace_user, namespace_branch, name, major, minor = separateVHDATypeNameComponents(node.type())

    other_definitions = []

    for definition in allInstalledDefinitionsInScene(node.type().category().name()):
        other_label, other_namespace_user, other_namespace_type, other_name, other_major, other_minor = separateVHDATypeNameComponents(definition.nodeType())

        if use_namespace:
            if namespace_user == other_namespace_user and namespace_branch == other_namespace_type and name == other_name:
                other_definitions.append(definition)
        else:
            if name == other_name:
                other_definitions.append(definition)

    return other_definitions

def getHDALibraryFilesPaths(node, use_namespace=False):
    """ Given a node, it returns the HDADefinition's Library File Path for all versions of the node's definition.

        :param  use_namespace: Comparison by the asset type only, or using namespace and major/minor version as well.

    """

    paths = []
    for definition in getInstalledVHDADefinitions(node,use_namespace):
        file_path = definition.libraryFilePath()
        # Do not add duplicates
        if file_path not in paths:
            # Do not add to OPLibSop.hda or any node inside the houdini install directory, like kinefx etc...
            if hou.expandString('$HFS') not in file_path:
                paths.append(definition.libraryFilePath())

    paths.sort(reverse=True)
    return paths

def isVHDAInstalled(definitions, namespace_user, namespace_branch, name, major, minor):
    """ From a given list of definitions and asset naming returns if the version digital asset is installed in the scene file.

    """
    for definition in definitions:
        other_label, other_namespace_user, other_namespace_type, other_name, other_major, other_minor = separateVHDATypeNameComponents(definition.nodeType())
        if namespace_user == other_namespace_user and  namespace_branch == other_namespace_type and name == other_name and major == other_major and minor == other_minor:
            return True
    return False

def isVHDAFileExists(hda_files, namespace_user, namespace_branch, name, major, minor):
    hda_name = constructVHDATypeName(namespace_user, namespace_branch, name, major, minor)
    for hda_file in hda_files:
        file_namespace_user, file_namespace_type, file_name, file_major, file_minor = separateVHDAFileNameComponents(hda_file)
        hda_filename = constructVHDATypeName(file_namespace_user, file_namespace_type, file_name, file_major, file_minor)
        if hda_name == hda_filename:
            return True

def splitVersionComponents(version_string):
    """ Given a version string it returns the major and minor versions as integers.

        :param version_string: The last component of the the name of the asse type ('def::test::1.3' -> '1.3')

    """
    # Empty version string should return 0 major 0 minor
    if version_string == "":
        return 0, 0

    version_components = version_string.split(".")
    major = 1
    minor = 0

    if len(version_components) > 0:
        if version_components[0] != '':
            major = int(version_components[0])
    if len(version_components) > 1 and version_components[1] != "":
        minor = int(version_components[1])

    return major, minor

def separateVHDATypeNameComponents(node_type):
    """ Given a node_type, it will return separate name components of the node type including the label for the Tab menu.

    """

    name_components = node_type.nameComponents()

    # The returned possible components for vhda:
    # ('', 'user::dev', 'custom_asset', '1.0')
    # ('', 'dev', 'custom_asset', '1.0')
    # ('', '', 'custom_asset', '1.0')

    # Internal assets with no version number:
    # ('', '', 'agentedit', '')

    # TO DO:
    # With Scope Network Type currently ingnored
    # ('Sop/rbdmaterialfracture', '', 'rbdwoodfracture', '')

    # TO DO:
    # when only on namespace is given it is not possible to know if it is a user or type namespace.

    namespaces = name_components[1].split("::")
    namespace_user = ""
    namespace_branch = ""

    if len(namespaces) == 1:
        # default to branch
        namespace_branch = namespaces[0]
        hda_def = node_type.definition()
        if hda_def.hasSection('VHDA'):
            content = hda_def.sections()['VHDA'].contents()
            data = json.loads(content)
            if 'namespace' in data:
                if data['namespace'] == 'user':
                    namespace_user = namespaces[0]
                    namespace_branch = ""
    elif len(namespaces) == 2:
        namespace_user = namespaces[0]
        namespace_branch = namespaces[1]

    name = name_components[2]
    major, minor = splitVersionComponents(name_components[3])

    # A default description/label of the node as it would appear in the Tab Menu.
    label = node_type.description()
    label = constructVHDALabel(label)

    return label, namespace_user, namespace_branch, name, major, minor

def separateVHDAFileNameComponents(file_name):
    """ Given a VHDA filename, it will return separate name components of the node type.

    """

    base_name = os.path.basename(file_name)
    major = 0
    minor = 0

    r = re.search("(\d+\.\d+)",base_name)

    if r is None:
        name_components = os.path.splitext(base_name)[0]
    else:
        version_string = r.groups()[0]
        major, minor = splitVersionComponents(version_string)
        name_components = re.split(r'\.\d+\.\d+\.',base_name)[0]

    namespaces = name_components.split(".")
    namespace_user = ""
    namespace_branch = ""
    name = ""

    if (len(namespaces)==1):
        name = namespaces[0]
    elif (len(namespaces)==2):
        name = namespaces[1]
        # default to branch
        namespace_branch = namespaces[0]
        hda_def = hou.hda.definitionsInFile(file_name)[0]
        if hda_def.hasSection('VHDA'):
            content = hda_def.sections()['VHDA'].contents()
            data = json.loads(content)
            if 'namespace' in data:
                if data['namespace'] == 'user':
                    namespace_user = namespaces[0]
                    namespace_branch = ""
    elif (len(namespaces)==3):
        namespace_user = namespaces[0]
        namespace_branch = namespaces[1]
        name = namespaces[2]

    return namespace_user, namespace_branch, name, major, minor

def constructVHDATypeName(namespace_user, namespace_branch, name, major, minor):
    """ Given a set of name components it will return the full versioned asset name.

    """

    vhda_name = ["{}::".format(x) for x in [namespace_user, namespace_branch] if x != ""]
    vhda_name += name

    if major > 0:
        vhda_name += "::{0}.{1}".format(major, minor)
    return re.sub("[^0-9a-zA-Z\.:_]+", "", "".join(vhda_name))

def constructVHDALabel(label, namespace_branch=None):
    """ Constructs the description/label of the node as it appears in the Tab menu.

        If there is namespace_branch it will show in the description inside round brackets, such as 'Foo (dev)'
        If no namespace_branch is given, make sure to remove any previously given namespace_branch from the description, if any.

    """

    if namespace_branch:
        if getVHDAConfigValue(getConfigKeys()[1]):
            return "%s (%s)" % (label,namespace_branch.capitalize())
        else:
            return "%s" % (re.sub("[\(\[].*?[\)\]]", "", label).rstrip())
    else:
        return re.sub("[\(\[].*?[\)\]]", "", label).rstrip()

def getAssetfileExtenstion():
    """ Based on the license type it returns the corresponding hipfile exteinsion

    """
    if hou.licenseCategory() == hou.licenseCategoryType.Commercial:
        return "hda"
    elif hou.licenseCategory() == hou.licenseCategoryType.Indie:
        return "hdalc"
    else:
        return "hdanc"

def constructVHDAFileName(namespace_user, namespace_branch,name,major,minor):
    """ Constructs file name in which the asset will be saved.

    """
    vhda_name = ["{}.".format(x) for x in [namespace_user, namespace_branch] if x != ""]
    vhda_name += name

    if major > 0:
        vhda_name += ".{0}.{1}.{2}".format(major, minor, getAssetfileExtenstion())
    else:
        vhda_name += ".{0}".format(getAssetfileExtenstion())
    return re.sub("[^0-9a-zA-Z\.:_]+", "", "".join(vhda_name))

def copyToNewVHDA(node):
    """ Creates a versioned copy of an existing versioned/not versioned digital asset.

        This definition is called from the opmenu Versioned Digital Asset -> Save As...
    """

    initVHDAConfigFile()

    # Make sure the save directory exists
    createVHDADir(getVHDAConfigValue(getConfigKeys()[0]))
    label, namespace_user, namespace_branch, name, major, minor = separateVHDATypeNameComponents(node.type())

    definitions = getInstalledVHDADefinitions(node)
    hda_files = allVHDAFilesInPath()

    major = getLatestMajorVersion(definitions, hda_files, namespace_user, namespace_branch, name)

    if major != 0:
        major += 1
    minor = 0

    tabmenu = getToolSubmenu(node.type().definition())
    tabmenu = "Digital Asset" if tabmenu == None else tabmenu[0]
    category_name = node.type().category().name()

    button_idx, values = newVHDAWindow(name,
                                       label,
                                       getVHDAConfigValue(getConfigKeys()[0]),
                                       namespace_user,
                                       namespace_branch,
                                       major,
                                       minor,
                                       category_name,
                                       tabmenu,
                                       definitions,
                                       hda_files,
                                       new_asset=False)

    if button_idx == 1:
        namespace_user   = values[0]
        namespace_branch   = values[1]
        name             = values[2]
        label            = values[3]
        major            = values[4]
        minor            = values[5]
        tabmenu          = values[6]
        savedir          = values[7]

        copyToVHDA(node, namespace_user, namespace_branch, name, major, minor, label, tabmenu, savedir)

def createNewVHDAFromSubnet(node):
    """ Creates a new versioned digital asset from a subnet

        This definition is called from the opmenu Versioned Digital Asset -> Save As...
    """

    initVHDAConfigFile()

    # Make sure the save directory exists
    createVHDADir(getVHDAConfigValue(getConfigKeys()[0]))

    name = node.name()
    name = ''.join([i for i in name if not i.isdigit()])

    label = name.title()
    label= label.replace("_"," ")

    major = int(node.digitsInName())
    if major == 0:
        major = 1

    category_name = node.type().category().name()
    scene_definitions = allInstalledDefinitionsInScene(category_name)
    hda_files = allVHDAFilesInPath()

    button_idx, values = newVHDAWindow(name,
                                       label,
                                       getVHDAConfigValue(getConfigKeys()[0]),
                                       namespace_user="",
                                       namespace_branch="",
                                       major=major,
                                       minor=0,
                                       category_name=category_name,
                                       tabmenu="Digital Assets",
                                       scene_definitions=scene_definitions,
                                       hda_files=hda_files,
                                       new_asset=True)

    if button_idx == 1:
        namespace_user   = values[0]
        namespace_branch   = values[1]
        name             = values[2]
        label            = values[3]
        major            = values[4]
        minor            = values[5]
        tabmenu          = values[6]
        savedir          = values[7]

        createVHDA(node, namespace_user, namespace_branch, name, major, minor, label, tabmenu, savedir)

def increaseMajorVersion(node):
    """ Increases the major version number of the versioned digital asset.

        This definition is called from the opmenu Versioned Digital Asset -> Increase Major Version

    """

    initVHDAConfigFile()

    # Make sure the save directory exists
    createVHDADir(getVHDAConfigValue(getConfigKeys()[0]))

    label, namespace_user, namespace_branch, name, major, minor = separateVHDATypeNameComponents(node.type())

    old_name = constructVHDATypeName(namespace_user, namespace_branch, name, major, minor)
    definitions = getInstalledVHDADefinitions(node)
    hda_files = allVHDAFilesInPath()

    major = getLatestMajorVersion(definitions, hda_files, namespace_user, namespace_branch, name)
    major = 1 if major == 0 else major + 1
    minor = 0

    new_name = constructVHDATypeName(namespace_user, namespace_branch, name, major, minor)
    node_definition = node.type().definition()

    if NewVHDABumpVersionWindow('major', old_name,new_name, node_definition):
        save_dir = getVHDAConfigValue(getConfigKeys()[0]) if node_definition.libraryFilePath() != "Embedded" else "Embedded"
        copyToVHDA(node, namespace_user, namespace_branch, name, major, minor, label, None, save_dir)

def increaseMinorVersion(node):
    """ Increases the minor version number of the versioned digital asset.

        This definition is called from the opmenu Versioned Digital Asset -> Increase Minor Version

    """

    initVHDAConfigFile()

    # Make sure the save directory exists
    createVHDADir(getVHDAConfigValue(getConfigKeys()[0]))
    label, namespace_user, namespace_branch, name, major, minor = separateVHDATypeNameComponents(node.type())

    old_name = constructVHDATypeName(namespace_user, namespace_branch, name, major, minor)
    definitions = getInstalledVHDADefinitions(node)
    hda_files = allVHDAFilesInPath()

    if major == 0:
        major = 1
        minor = getLatestMinorVersion(definitions, hda_files, namespace_user, namespace_branch, name, major)
    else:
        minor = getLatestMinorVersion(definitions, hda_files, namespace_user, namespace_branch, name, major) + 1

    new_name = constructVHDATypeName(namespace_user, namespace_branch, name, major, minor)
    node_definition = node.type().definition()

    if NewVHDABumpVersionWindow('minor', old_name,new_name, node.type().definition()):
        save_dir = getVHDAConfigValue(getConfigKeys()[0]) if node_definition.libraryFilePath() != "Embedded" else "Embedded"
        copyToVHDA(node, namespace_user, namespace_branch, name, major, minor, label, None, save_dir)


def openPreferences(node):
    """ Runs the Preference Window

        This definition is called from the opmenu Versioned Digital Asset -> Preferences...

    """
    initVHDAConfigFile()

    category_name = node.type().category().name()
    newVHDAPreferenceWindow(category_name)

def copyToVHDA(node, namespace_user, namespace_branch, name, major, minor, label, tabmenu, savedir):
    """ Given a base node (that is an existing digital asset), it will create a copy with the given namescape, name, version, label and tabmenu parameters.

    """
    hda_name  = constructVHDATypeName(namespace_user, namespace_branch,name,major,minor)
    hda_label = constructVHDALabel(label,namespace_branch)
    hda_filename = constructVHDAFileName(namespace_user, namespace_branch,name,major,minor)
    hda_savedir = savedir
    hda_filepath = os.path.join(hda_savedir, hda_filename) if hda_savedir != "Embedded" else "Embedded"
    tmp_filepath = os.path.join(hou.expandString("$HOUDINI_TEMP_DIR"),"tmphda.hda")


    # # Update and save new HDA
    vhda_def = node.type().definition()
    # vhda_options = vhda_def.options()
    # vhda_options.setSaveInitialParmsAndContents(True)
    # vhda_options.setSaveSpareParms(True) ####### TO-DO

    vhda_def.save(tmp_filepath, template_node=node)#, options=vhda_options) ######

    created_definition = hou.hda.definitionsInFile(tmp_filepath)[0]
    # Sets the tabmenu location only if it differs from the original
    if tabmenu:
        setToolSubmenu(created_definition, tabmenu)

    setVHDASection(created_definition, False if namespace_user == "" else True,
                                       False if namespace_branch == "" else True)
    created_definition.copyToHDAFile(hda_filepath,hda_name,hda_label)
    os.remove(tmp_filepath)

    hou.hda.installFile(hda_filepath)

    hou.hda.reloadAllFiles(True)
    node.changeNodeType(hda_name)

def createVHDA(node, namespace_user, namespace_branch, name, major, minor, label, tabmenu, savedir):
    """ Given a base node (that is not an existing digital asset, etc.. subnet), it will genrate a new asset with the given namescape, name, version, label and tabmenu parameters.

    """
    hda_name  = constructVHDATypeName(namespace_user, namespace_branch,name,major,minor)
    hda_label = constructVHDALabel(label,namespace_branch)
    hda_filename = constructVHDAFileName(namespace_user, namespace_branch,name,major,minor)
    hda_savedir = savedir
    hda_filepath = os.path.join(hda_savedir, hda_filename) if hda_savedir != "Embedded" else "Embedded"

    max_num_inputs = 0

    # If there are inputs to the node, find the largest index of the input connections and use it as the max_num_inputs
    # This will preserve the inputs at the right indexes
    if len(node.inputs()) > 0:
        for connection in node.inputConnections():
            max_num_inputs = max(max_num_inputs,connection.inputIndex())
        max_num_inputs = max_num_inputs + 1

    vhda_node = node.createDigitalAsset(
        name = hda_name,
        hda_file_name = hda_filepath,
        description = hda_label,
        min_num_inputs = 0,
        max_num_inputs = max_num_inputs,
        save_as_embedded = hda_savedir == "Embedded"
    )

    vhda_node.setName(name, unique_name=True)
    vhda_def = vhda_node.type().definition()

    # Update and save new HDA
    vhda_options = vhda_def.options()
    vhda_options.setSaveInitialParmsAndContents(True)
    #vhda_options.setSaveSpareParms(True) ####### TO-DO

    vhda_def.setOptions(vhda_options)
    setVHDASection(vhda_def, False if namespace_user == "" else True,
                             False if namespace_branch == "" else True)
    setToolSubmenu(vhda_def, tabmenu)

    vhda_def.save(hda_filepath, vhda_node, vhda_options)
    hou.hda.installFile(hda_filepath)
    hou.hda.reloadAllFiles(True)

def deleteVersions(node):
    """ Given a node it builds a list of installed and uninstalled versioned digital assets that can be selected and destroyed/removed from the hip file and from disk.

    """

    label, namespace_user, namespace_branch, name, major, minor = separateVHDATypeNameComponents(node.type())

    definitions = getInstalledVHDADefinitions(node, use_namespace=False)

    # list of tuples to store, hda_name, hda_definition, major and minor version for sorting.
    entries = []

    # Collect installed definitions
    for definition in definitions:
        other_label, other_namespace_user, other_namespace_type, other_name, other_major, other_minor = separateVHDATypeNameComponents(definition.nodeType())
        hda_name = constructVHDATypeName(other_namespace_user, other_namespace_type, other_name, other_major, other_minor)

        entries.append((hda_name, definition, other_namespace_user, other_namespace_type, other_name, other_major, other_minor))

    # Collect not installed definitions from vhda path
    for definition in allNonInstalledDefinitionsInVHDAPath():
        hda_file = definition.libraryFilePath()
        file_namespace_user, file_namespace_type, file_name, file_major, file_minor = separateVHDAFileNameComponents(hda_file)
        if (name == file_name):
            hda_name = constructVHDATypeName(file_namespace_user, file_namespace_type, file_name, file_major, file_minor)
            entries.append((hda_name, definition, file_namespace_user, file_namespace_type, file_name, file_major, file_minor))

    if len(entries):
        import time
        from operator import itemgetter

        # sort entries
        entries_sorted = []
        for entry in sorted(entries, key=itemgetter(0,5,6), reverse=True):
            entries_sorted.append((entry[0], # hda_name
                                   entry[1], # definition
                                   entry[2], # namespace_user
                                   entry[3], # namespace_type
                                   entry[4], # file_name
                                   entry[5], # major version
                                   entry[6], # minor version
                                   str(time.ctime(os.path.getmtime(entry[1].libraryFilePath()))), # creation
                                   entry[1].libraryFilePath())) # file_path

        button_idx, selected = newVHDADeleteWindow(entries_sorted)
        if button_idx and selected:

            # Get a list of all other nodes that are affected by the removal.
            all_nodes = hou.node("/obj").allSubChildren()

            # construct list with only selected entries. [hda_name, definition, node_instances]
            entries_selected = []
            for i in selected:
                nodelist = []
                if entries_sorted[i][1].isInstalled():
                    for other_node in all_nodes:
                        if other_node.type().name() == entries_sorted[i][0]:
                            nodelist.append(other_node)

                entries_selected.append([entries_sorted[i][0],entries_sorted[i][1],nodelist])

            button_idx = newVHDADeleteConfirmWindow(entries_selected)

            if button_idx:

                all_defs = allInstalledDefinitionsInScene(node.type().definition())
                # Let's switch the node type before destroying it to avoid generating Embedded asset.
                # If there are other VHDA with the same asset let's switch to one of them.
                # For this, we need to get the set which is 'Complement of A in U' A=selected B=defs
                # Otherwise switch to a null node.



                # Change all nodes containing this definition.
                new_nodetype = 'null'

                not_selected = []

                for i in list(set(list(range(0,len(entries)))) - set(selected)):
                    if entries_sorted[i][1].isInstalled():
                        not_selected.append((entries_sorted[i][1], entries_sorted[i][5], entries_sorted[i][6]))

                # if there is any other node type not selected find a one that can be used.
                not_selected_sorted = []
                if len(not_selected) > 0:
                    not_selected_sorted = sorted(not_selected, key=itemgetter(1,2), reverse=False)

                for entry in entries_selected:
                    for node in entry[2]:
                        if len(not_selected) > 0:
                            node.changeNodeType(not_selected_sorted[0][0].nodeType().name())
                            #replaced_node = node.changeNodeType('null')
                        else:
                            prev_nodename = node.type().name()
                            replaced_node = node.changeNodeType('null')
                            replaced_node.setComment("Previous " + prev_nodename + " at location " + entry[1].libraryFilePath() + " was removed and replaced by a null node.")
                            replaced_node.setGenericFlag(hou.nodeFlag.DisplayComment,True)

                    file_path = entry[1].libraryFilePath()
                    if entry[1].isInstalled():
                        entry[1].destroy()
                       # Make sure empty *.hda files are removed
                        try:
                            hou.hda.definitionsInFile(file_path)
                        except hou.OperationFailed:
                            if os.path.exists(file_path):
                                os.remove(file_path)
                    else:
                        # not installed, safe to remove in current scene file.
                        os.remove(file_path)

    else:
        creation_selection = hou.ui.displayMessage(text='There are no assets to delete!',
                                    severity=hou.severityType.Message,
                                    title='Delete Asset Info')


# WINDOW CREATION CALLS
def newVHDAWindow(name,label,path,namespace_user,namespace_branch, major, minor, category_name, tabmenu, scene_definitions, hda_files, new_asset):

    defaults = [ namespace_user, namespace_branch, name, label, path, major, minor, category_name, tabmenu, scene_definitions, hda_files, new_asset]
    dialog = NewVHDADialog(hou.ui.mainQtWindow(), defaults)
    dialog.exec_()
    button_idx = dialog.exitval
    values = dialog.parmvals

    return button_idx, values

def NewVHDABumpVersionWindow(increase, old_name, new_name, hda_def):

    defaults = [ increase, old_name, new_name, hda_def]
    dialog = BumpVersionVHDADialog(hou.ui.mainQtWindow(), defaults)
    dialog.exec_()
    button_idx = dialog.exitval
    return button_idx

def newVHDADeleteWindow(entries=[]):

    defaults = [ entries ]
    dialog = DeleteVHDADialog(hou.ui.mainQtWindow(), defaults)
    dialog.exec_()
    button_idx = dialog.exitval
    values = dialog.parmvals

    return button_idx, values

def newVHDADeleteConfirmWindow(entries=[]):

    defaults = [ entries ]
    dialog = DeleteConfirmVHDADialog(hou.ui.mainQtWindow(), defaults)
    dialog.exec_()
    button_idx = dialog.exitval

    return button_idx

def newVHDAPreferenceWindow(category_name):

    defaults = [category_name]
    dialog = VHDAPreferencesDialog(hou.ui.mainQtWindow(), defaults)
    dialog.exec_()
    button_idx = dialog.exitval
    values = dialog.parmvals

class NamespaceWidget(QWidget):
    def __init__(self, parent = None):
        super(NamespaceWidget, self).__init__(parent)

        self.parnet = parent

        self.layout = QHBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(5,1,5,1)

        self.layout.setSizeConstraint(QLayout.SetMinimumSize)

        self.selected_btn = QLabel("")
        self.setSelectedIcon(False)
        self.layout.addWidget(self.selected_btn)

        self.spacer = QLabel("  ")
        self.layout.addWidget(self.spacer)


        self.namespace_edit  = QLineEdit("")
        regex = QRegExp("[a-zA-Z_\s]+")
        validator = QRegExpValidator(regex)
        self.namespace_edit.setValidator(validator)
        self.namespace_edit.textChanged.connect(self.on_LineEditChanged)

        self.layout.addWidget(self.namespace_edit)

        self.remove_btn = QPushButton("")
        self.remove_btn.setIcon(hou.qt.createIcon("BUTTONS_multi_remove"))
        self.remove_btn.setIconSize(QSize(15, 15))
        self.remove_btn.setMaximumSize(QSize(23, 23))
        self.remove_btn.clicked.connect(self.on_removedClick)

        self.layout.addWidget(self.remove_btn)

        self.setLayout(self.layout)

    def on_LineEditChanged(self):

        namespace = self.namespace_edit.text()

        if " " in namespace:
            namespace = namespace.replace(" ", "_")
            cursorpos = self.namespace_edit.cursorPosition()
            self.namespace_edit.setText(namespace)
            self.namespace_edit.setCursorPosition(cursorpos)

    def setSelectedIcon(self, selected):

        if selected:
            icon = hou.qt.createIcon("MISC_checkbox_light_on")
        else:
            icon = hou.qt.createIcon("MISC_checkbox_light_off")

        self.selected_btn.setPixmap(icon.pixmap(QSize(20,20)))

    def setWidgetItem(self, widget_item):
        self.widget_item = widget_item
        self.list_widget = widget_item.listWidget()

    def setLabel(self, label):
        self.namespace_edit.setText(label)

    def getLabel(self):
        return self.namespace_edit.text()

    def sizeHint(self):
       return QSize(100,25)

    def on_removedClick(self):
        my_row = self.list_widget.row(self.widget_item)
        self.list_widget.takeItem(my_row)

        disable = False
        if self.list_widget.count() == 1:
            disable = True

        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item:
                widget = self.list_widget.itemWidget(item)
                if widget:
                    widget.setDisabled(disable)

        height_limit = 26*4
        current_height = 26 * self.list_widget.count()

        self.list_widget.setFixedHeight(height_limit if current_height > height_limit else current_height)

    def setDisabled(self, disabled=False):
        self.remove_btn.setDisabled(disabled)

# PREFERENCES DIALOG
class VHDAPreferencesDialog(QDialog):
    def __init__(self, parent, defaults):
        super(VHDAPreferencesDialog, self).__init__(parent)

        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)
        self.setWindowIcon(hou.qt.createIcon("MISC_generic"))
        self.setWindowTitle("Preferences")
        self.defaults = defaults
        self.parmvals = []
        self.exitval = None
        self.custom_path_edit = None
        self.pathlabel_edit = None
        self.buildUI()

    def closeEvent(self, event):
        pass

    def on_OK(self):
        self.exitval = 1

        branch_labels = []
        for i in range(self.branch_listwidget.count()):
            item = self.branch_listwidget.item(i)
            widget = self.branch_listwidget.itemWidget(item)
            label = widget.getLabel()
            branch_labels.append(label)

        user_labels = []
        for i in range(self.user_listwidget.count()):
            item = self.user_listwidget.item(i)
            widget = self.user_listwidget.itemWidget(item)
            label = widget.getLabel()
            user_labels.append(label)

        writeVHDAConfigFile(self.pathmode.currentText(),
                            self.show_dev_enable.isChecked(),
                            self.enable_user.isChecked(),
                            self.enable_branch.isChecked(),
                            branch_labels,
                            self.branch_listwidget.currentRow(),
                            user_labels,
                            self.user_listwidget.currentRow(),
                            self.enable_versioning.isChecked(),
                            self.tabmenu_edit.currentText())

        self.close()

    def on_Reset(self):
        self.exitval = 1

        writeVHDAConfigFile()

        self.close()

    def on_Cancel(self):
        self.exitval = None
        self.close()

    def on_addNewUserItemClicked(self):

        self.addNewItem(self.user_listwidget, label="custom")

    def on_addNewBranchItemClicked(self):

        self.addNewItem(self.branch_listwidget, label="custom")

    def addNewItem(self, list_widget, label="dev"):

        item = QListWidgetItem(list_widget)
        list_widget.addItem(item)

        my_widget = NamespaceWidget()
        my_widget.setWidgetItem(item)
        my_widget.setLabel(label)
        my_widget.setDisabled(True)

        item.setSizeHint(my_widget.sizeHint())
        list_widget.setItemWidget(item, my_widget)

        if list_widget.count()>1:
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                if item:
                    widget = list_widget.itemWidget(item)
                    if widget:
                        widget.setDisabled(False)

        height_limit = 26*4
        current_height = 26 * list_widget.count()

        list_widget.setFixedHeight(height_limit if current_height > height_limit else current_height)


    def on_InputFileButtonClicked(self):
        path = hou.expandString(self.pathmode.currentText())
        if not os.path.isdir(path):
            path = hou.expandString(hou.expandString("$HOUDINI_USER_PREF_DIR/otls"))

        dirname = str(QFileDialog.getExistingDirectory(self, "Select Directory"))

        if os.path.isdir(dirname):
            self.pathmode.setEditText(dirname)

    def on_PathModeChanged(self):

        value = self.pathmode.currentText()
        default_install_labels = getDefaultInstallLabels()
        default_install_paths = getDefaultInstallPaths()

        if value == default_install_labels[0]:
            value = default_install_paths[0]
        elif value == default_install_labels[1]:
            value = default_install_paths[1]
        elif value == default_install_labels[2]:
            value = default_install_paths[2]
        elif value == default_install_labels[3]:
            value = default_install_paths[3]

        self.pathmode.setEditText(value)
        self.pathlabel_edit.setText(os.path.normpath(hou.expandString(value)))

    def on_UserItemChanged(self, current, previous):

        if current:
            current_widget = self.user_listwidget.itemWidget(current)
            current_widget.setSelectedIcon(True)
        if previous:
            previous_widget = self.user_listwidget.itemWidget(previous)
            previous_widget.setSelectedIcon(False)

    def on_BranchItemChanged(self, current, previous):

        if current:
            current_widget = self.branch_listwidget.itemWidget(current)
            current_widget.setSelectedIcon(True)
        if previous:
            previous_widget = self.branch_listwidget.itemWidget(previous)
            previous_widget.setSelectedIcon(False)

    def buildUI(self):

        # BASE LAYOUT ----------------------------

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.gbcolumn_layout = QHBoxLayout()
        layout.addLayout(self.gbcolumn_layout)

        # SIMPLE FOLDER - Name Construction ----------------------------
        self.name_gb = QGroupBox("Name Construction")
        self.gbcolumn_layout.addWidget(self.name_gb)

        name_gb_layout = QVBoxLayout()
        name_gb_layout.setSizeConstraint(QLayout.SetMaximumSize)
        self.name_gb.setLayout(name_gb_layout)

        # User Items Label
        user_items_label_layout = QHBoxLayout()
        name_gb_layout.addLayout(user_items_label_layout)

        self.banch_items_label = QLabel("Custom User Entries")

        self.add_btn = QPushButton("")
        self.add_btn.setIcon(hou.qt.createIcon("BUTTONS_list_add"))
        self.add_btn.setIconSize(QSize(15, 15))
        self.add_btn.setMaximumSize(QSize(23, 23))
        self.add_btn.clicked.connect(self.on_addNewUserItemClicked)

        user_items_label_layout.addWidget(self.banch_items_label)
        user_items_label_layout.addWidget(self.add_btn)

        # User Items
        user_items_layout = QHBoxLayout()
        name_gb_layout.addLayout(user_items_layout)

        self.user_listwidget = QListWidget()
        self.user_listwidget.setAlternatingRowColors(True)
        self.user_listwidget.currentItemChanged.connect(self.on_UserItemChanged)


        for entry in getVHDAConfigValue(getConfigKeys()[6]):
            self.addNewItem(self.user_listwidget, entry)

        self.user_listwidget.setCurrentRow(getVHDAConfigValue(getConfigKeys()[7]))
        self.user_listwidget.setResizeMode(QListView.Adjust)

        user_items_layout.addWidget(self.user_listwidget)

        # Branch Items Label
        branch_items_label_layout = QHBoxLayout()
        name_gb_layout.addLayout(branch_items_label_layout)

        self.banch_items_label = QLabel("Custom Branch Entries")

        self.add_btn = QPushButton("")
        self.add_btn.setIcon(hou.qt.createIcon("BUTTONS_list_add"))
        self.add_btn.setIconSize(QSize(15, 15))
        self.add_btn.setMaximumSize(QSize(23, 23))
        self.add_btn.clicked.connect(self.on_addNewBranchItemClicked)

        branch_items_label_layout.addWidget(self.banch_items_label)
        branch_items_label_layout.addWidget(self.add_btn)

        # Branch Items
        branch_items_layout = QHBoxLayout()
        name_gb_layout.addLayout(branch_items_layout)

        self.branch_listwidget = QListWidget()
        self.branch_listwidget.setAlternatingRowColors(True)
        self.branch_listwidget.currentItemChanged.connect(self.on_BranchItemChanged)

        for entry in getVHDAConfigValue(getConfigKeys()[4]):
            self.addNewItem(self.branch_listwidget, entry)

        self.branch_listwidget.setCurrentRow(getVHDAConfigValue(getConfigKeys()[5]))
        self.branch_listwidget.setResizeMode(QListView.Adjust)

        branch_items_layout.addWidget(self.branch_listwidget)

         # Enable User Namespace
        user_layout = QHBoxLayout()
        name_gb_layout.addLayout(user_layout)

        _label2 = QLabel("")
        _label2.setFixedSize(85, 25)
        self.enable_user = QCheckBox("Enable User Namespace")
        self.enable_user.setChecked(getVHDAConfigValue(getConfigKeys()[2]))

        user_layout.addWidget(_label2)
        user_layout.addWidget(self.enable_user)

        # Enable Branch Namespace
        branch_layout = QHBoxLayout()
        name_gb_layout.addLayout(branch_layout)

        _label2 = QLabel("")
        _label2.setFixedSize(85, 25)
        self.enable_branch = QCheckBox("Enable Branch Namespace")
        self.enable_branch.setChecked(getVHDAConfigValue(getConfigKeys()[3]))

        branch_layout.addWidget(_label2)
        branch_layout.addWidget(self.enable_branch)

        # Enable Versioning
        version_layout = QHBoxLayout()
        name_gb_layout.addLayout(version_layout)

        _label2 = QLabel("")
        _label2.setFixedSize(85, 25)
        self.enable_versioning = QCheckBox("Enable Versioning")
        self.enable_versioning.setChecked(getVHDAConfigValue(getConfigKeys()[8]))

        version_layout.addWidget(_label2)
        version_layout.addWidget(self.enable_versioning)



        # SIMPLE FOLDER - Tab Menu ----------------------------
        self.tabmenu_gb = QGroupBox("Tab Menu")
        self.gbcolumn_layout.addWidget(self.tabmenu_gb)

        tabmenu_gb_layout = QVBoxLayout()
        self.tabmenu_gb.setLayout(tabmenu_gb_layout)

        # Display Branch
        tabmenu_layout = QHBoxLayout()
        tabmenu_gb_layout.addLayout(tabmenu_layout)

        _label2 = QLabel("")
        _label2.setFixedSize(85, 25)
        self.show_dev_enable = QCheckBox("Display Branch in Label")
        self.show_dev_enable.setChecked(getVHDAConfigValue(getConfigKeys()[1]))

        tabmenu_layout.addWidget(_label2)
        tabmenu_layout.addWidget(self.show_dev_enable)

        # Tab Menu
        tabmenu_layout = QHBoxLayout()
        tabmenu_gb_layout.addLayout(tabmenu_layout)

        tabmenu_label = QLabel("Menu Entry")
        tabmenu_label.setFixedSize(85, 20)
        self.tabmenu_edit = QComboBox(self)
        self.tabmenu_edit.setEditable(True)

        # Populate with existing entries
        self.tabmenu_edit.addItems(getAllToolSubmenus(self.defaults[0]))
        idx = self.tabmenu_edit.findText(getVHDAConfigValue(getConfigKeys()[9]))

        if idx == -1:
            self.tabmenu_edit.setEditText("Digital Assets")
        else:
            self.tabmenu_edit.setCurrentIndex(self.tabmenu_edit.findText(getVHDAConfigValue(getConfigKeys()[9])))

        tabmenu_layout.addWidget(tabmenu_label)
        tabmenu_layout.addWidget(self.tabmenu_edit)

        # Spacer layout
        spacer_label = QLabel("")
        tabmenu_gb_layout.addWidget(spacer_label)
        spacer_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # SIMPLE FOLDER - Asset Location ----------------------------
        self.path_gb = QGroupBox("Asset Location")
        layout.addWidget(self.path_gb)

        path_gb_layout = QVBoxLayout()
        self.path_gb.setLayout(path_gb_layout)

        # Save Path
        savepath_layout = QHBoxLayout()
        path_gb_layout.addLayout(savepath_layout)

        _label1 = QLabel("Save Path")
        _label1.setFixedSize(85, 25)

        self.pathmode = QComboBox()
        self.pathmode.setEditable(True)
        self.pathmode.addItems(getDefaultInstallLabels())
        self.pathmode.setEditText(getVHDAConfigValue(getConfigKeys()[0]))
        self.pathmode.activated.connect(self.on_PathModeChanged)

        self.assetlocation_btn = QPushButton("")
        self.assetlocation_btn.setIcon(hou.qt.createIcon("BUTTONS_folder"))
        self.assetlocation_btn.setFixedSize(30, 28)
        self.assetlocation_btn.clicked.connect(self.on_InputFileButtonClicked)

        savepath_layout.addWidget(_label1)
        savepath_layout.addWidget(self.pathmode)
        savepath_layout.addWidget(self.assetlocation_btn)

        # Path Preview

        custompath_layout = QHBoxLayout()
        path_gb_layout.addLayout(custompath_layout)

        pathlabel = QLabel("Preview")
        pathlabel.setFixedSize(85, 25)
        custompath_layout.addWidget(pathlabel)
        self.pathlabel_edit = QLabel(os.path.normpath(hou.expandString(getVHDAConfigValue(getConfigKeys()[0]))))
        self.pathlabel_edit.setWordWrap(True)

        custompath_layout.addWidget(self.pathlabel_edit)

        self.on_PathModeChanged()

        # VERSIONING - Tab Menu ----------------------------

        self.versioning_gb = QGroupBox("Version Switching")
        layout.addWidget(self.versioning_gb)

        versioning_layout = QVBoxLayout()
        self.versioning_gb.setLayout(versioning_layout)

        self.versioning_preview = QLabel("""Use the 'Asset Name and Path' menu on the parameter interface\n to switch between versions. If it is not visible, go to:\nAssets -> Asset Manager... -> Configuration Tab
and set 'Asset Bar' menu to 'Display Menu of All Definitions'.""")
        self.versioning_preview.setAlignment(Qt.AlignCenter)
        self.versioning_preview.setToolTip("")

        versioning_layout.addWidget(self.versioning_preview)

        # BUTTON SPACER ----------------------------
        verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(verticalSpacer)

        # BUTTONS ----------------------------

        buttons_layout = QHBoxLayout()
        layout.addLayout(buttons_layout)

        # TO DO:
        # Reset Defaults

        buttons_layout.setAlignment(Qt.AlignRight)
        self.Reset_btn = QPushButton("Restore Factory Defaults")
        self.Reset_btn.setFixedWidth(180)
        horizontalSpacer = QSpacerItem(200, 0, QSizePolicy.Maximum, QSizePolicy.Expanding)
        self.OK_btn = QPushButton("Apply")
        self.OK_btn.setFixedWidth(100)
        self.OK_btn.setDefault(True)
        self.Cancel_btn = QPushButton("Cancel")
        self.Cancel_btn.setFixedWidth(100)
        self.OK_btn.clicked.connect(self.on_OK)
        self.Cancel_btn.clicked.connect(self.on_Cancel)
        self.Reset_btn.clicked.connect(self.on_Reset)

        buttons_layout.addWidget(self.Reset_btn)
        buttons_layout.addItem(horizontalSpacer)
        buttons_layout.addWidget(self.OK_btn)
        buttons_layout.addWidget(self.Cancel_btn)

# SAVE AS NEW VHDA DIALOG
class NewVHDADialog(QDialog):
    def __init__(self, parent, defaults):
        super(NewVHDADialog, self).__init__(parent)

        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("New Versioned Digital Asset")
        self.setWindowIcon(hou.qt.createIcon("MISC_digital_asset"))
        self.defaults = defaults
        self.exitval = None
        self.parmvals = defaults
        self.user_edit = ""
        self.branch_edit = ""
        self.assettype_edit = None
        self.assetlabel_edit = None
        self.majorversion_edit = None
        self.minorversion_edit = None
        self.user_enable = None
        self.branch_enable = None
        self.OK_btn = None
        self.validator = None

        self.user_enable_tooltip = """When you name digital assets, there is a risk that someday Side Effects,
or a subcontractor, or a third party vendor, will use the same name, causing a conflict.
Enabling this, can guard against this by including the name of the asset creator
in the name of the asset."""

        self.branch_enable_tooltip = """When you name digital assets, there is a risk that someday Side Effects,
or a subcontractor, or a third party vendor, will use the same name, causing a conflict.
Enabling this, can guard against this by including the purpose of the asset in the name of the asset."""

        self.assettype_label_tooltip =  """Sets the node's type name and the major and minor version number. """

        self.assettype_tooltip = """Sets the node's type name. When User and Branch are enabled,
their content will be prepanded, while the major and
minor versions will always be appened to the type name."""

        self.majorversion_tooltip = """The major version of the asset."""

        self.minorversion_tooltip = """The minor version of the asset. The value always tries to suggest the next available
minor version number when the major version is changed."""

        self.assetlabel_tooltip = """The name of the asset as it will show up in the tab menu."""
        self.tabmenu_tooltip = """The submenu inside the tab menu in which to place the asset.
Optionally to place the node in a hierarchy of submenus use '/' character."""

        self.name_preview_tooltip = """Shows the file create."""

        self.buildUI()

    def closeEvent(self, event):
        pass

    def on_OK(self):
        self.exitval = 1
        major = self.majorversion_edit.value()
        minor = self.minorversion_edit.value()

        self.parmvals = [self.user_edit.currentText(),
                         self.branch_edit.currentText(),
                         self.assettype_edit.text(),
                         self.assetlabel_edit.text(),
                         self.majorversion_edit.value(),
                         self.minorversion_edit.value(),
                         self.tabmenu_edit.currentText(),
                         self.pathmode.currentText()]

        if not self.branch_enable.isChecked():
            self.parmvals[1] = ""
        if not self.user_enable.isChecked():
            self.parmvals[0] = ""
        if not self.version_enable.isChecked():
            self.parmvals[4] = 0
            self.parmvals[5] = 0
        self.close()

    def on_Cancel(self):
        self.exitval = None
        self.close()

    def updateOKBtn(self, user, branch, assettype, major, minor):
        if isVHDAInstalled(self.defaults[9], user, branch, assettype, major, minor) or isVHDAFileExists(self.defaults[10], user, branch, assettype, major, minor):
            self.OK_btn.setEnabled(False)
        else:
            self.OK_btn.setEnabled(True)

    def setAssetNamePreview(self, user, branch, name, major, minor):

        self.assetname_preview.setText(constructVHDATypeName(user, branch,name,major,minor))

    def setAssetPathPreview(self, path, user, branch, name, major, minor):


        if not self.version_enable.isChecked():
            major = 0
            minor = 0

        self.pathlabel_edit.setText(os.path.normpath(os.path.join(hou.expandString(path),constructVHDAFileName(user,branch,name,major,minor))))

    def on_MajorVersionChanged(self):

        user = self.user_edit.currentText() if self.user_enable.isChecked() else ""
        branch = self.branch_edit.currentText() if self.branch_enable.isChecked() else ""

        major = self.majorversion_edit.value()
        minor = getLatestMinorVersion(self.defaults[9], self.defaults[10], user, branch, self.assettype_edit.text(), major)
        if minor != 0:
            minor += 1

        self.minorversion_edit.setValue(minor)

        self.setAssetNamePreview(user, branch, self.assettype_edit.text(), major, minor)
        self.setAssetPathPreview(self.pathmode.currentText(), user, branch, self.assettype_edit.text(), major, minor)

        self.updateOKBtn(user, branch, self.assettype_edit.text(), major, minor)

    def on_LineEditChanged(self):
        user = self.user_edit.currentText() if self.user_enable.isChecked() else ""
        branch = self.branch_edit.currentText() if self.branch_enable.isChecked() else ""

        self.user_edit.setDisabled(not self.user_enable.isChecked())
        self.branch_edit.setDisabled(not self.branch_enable.isChecked())
        self.majorversion_edit.setDisabled(not self.version_enable.isChecked())
        self.minorversion_edit.setDisabled(not self.version_enable.isChecked())

        major = self.majorversion_edit.value()
        minor = self.minorversion_edit.value()

        if not self.version_enable.isChecked():
            major = 0
            minor = 0

        if " " in user:
            user = user.replace(" ", "_")
            cursorpos = self.user_edit.lineEdit().cursorPosition()
            self.user_edit.setEditText(user)
            self.user_edit.lineEdit().setCursorPosition(cursorpos)

        if " " in branch:
            branch = branch.replace(" ", "_")
            cursorpos = self.branch_edit.lineEdit().cursorPosition()
            self.branch_edit.setEditText(branch)
            self.branch_edit.lineEdit().setCursorPosition(cursorpos)

        self.setAssetNamePreview(user, branch, self.assettype_edit.text(), major, minor)
        self.setAssetPathPreview(self.pathmode.currentText(), user, branch, self.assettype_edit.text(), major, minor)

        self.updateOKBtn(user, branch, self.assettype_edit.text(), major, minor)

    def on_AssetTypeChanged(self):
        user = self.user_edit.currentText() if self.user_enable.isChecked() else ""
        branch = self.branch_edit.currentText() if self.branch_enable.isChecked() else ""

        self.user_edit.setDisabled(not self.user_enable.isChecked())
        self.branch_edit.setDisabled(not self.branch_enable.isChecked())
        self.majorversion_edit.setDisabled(not self.version_enable.isChecked())
        self.minorversion_edit.setDisabled(not self.version_enable.isChecked())

        major = self.majorversion_edit.value()
        minor = self.minorversion_edit.value()

        if self.version_enable.isChecked():
            major = 0
            minor = 0

        assettype = self.assettype_edit.text()
        assettype = assettype.replace(" ", "_")

        cursorpos = self.assettype_edit.cursorPosition()
        self.assettype_edit.setText(assettype)
        self.assettype_edit.setCursorPosition(cursorpos)

        self.setAssetNamePreview(user, branch, assettype, major, minor)
        self.setAssetPathPreview(self.pathmode.currentText(), user, branch, assettype, major, minor)

        self.updateOKBtn(user, branch, assettype, major, minor)

    def on_AssetLabelChanged(self):
        user = self.user_edit.currentText() if self.user_enable.isChecked() else ""
        branch = self.branch_edit.currentText() if self.branch_enable.isChecked() else ""

        self.user_edit.setDisabled(not self.user_enable.isChecked())
        self.branch_edit.setDisabled(not self.branch_enable.isChecked())

        major = self.majorversion_edit.value()
        minor = self.minorversion_edit.value()
        self.majorversion_edit.setDisabled(not self.version_enable.isChecked())
        self.minorversion_edit.setDisabled(not self.version_enable.isChecked())

        if self.version_enable.isChecked():
            major = 0
            minor = 0
        assettype = self.assettype_edit.text()

        self.setAssetNamePreview(user, branch, assettype, major, minor)
        self.setAssetPathPreview(self.pathmode.currentText(), user, branch, assettype, major, minor)

        self.updateOKBtn(user, branch, assettype, major, minor)

    def PopulateUserEdit(self):

        user_entries = getVHDAConfigValue(getConfigKeys()[6])
        user_entry_idx = getVHDAConfigValue(getConfigKeys()[7])

        self.user_edit.addItems(user_entries)

        if self.defaults[0] != "":
            if self.defaults[0] not in user_entries:
                self.user_edit.addItem(self.defaults[0])
                self.user_edit.setCurrentIndex(self.user_edit.count()-1)
            else:
                idx = self.user_edit.findText(self.defaults[0])
                self.user_edit.setCurrentIndex(idx)
        else:
            self.user_edit.setCurrentIndex(user_entry_idx)
            self.user_edit.setEditText(user_entries[user_entry_idx])

    def PopulateBranchEdit(self):

        branch_entries = getVHDAConfigValue(getConfigKeys()[4])
        branch_entry_idx = getVHDAConfigValue(getConfigKeys()[5])

        self.branch_edit.addItems(branch_entries)

        if self.defaults[1] != "":
            if self.defaults[1] not in branch_entries:
                self.branch_edit.addItem(self.defaults[1])
                self.branch_edit.setCurrentIndex(self.branch_edit.count()-1)
            else:
                idx = self.branch_edit.findText(self.defaults[1])
                self.branch_edit.setCurrentIndex(idx)
        else:
            self.branch_edit.setCurrentIndex(branch_entry_idx)
            self.branch_edit.setEditText(branch_entries[branch_entry_idx])


    def on_InputFileButtonClicked(self):
        path = hou.expandString(self.pathmode.currentText())
        if not os.path.isdir(path):
            path = hou.expandString(hou.expandString("$HOUDINI_USER_PREF_DIR/otls"))

        dirname = str(QFileDialog.getExistingDirectory(self, "Select Directory"))

        if os.path.isdir(dirname):
            self.pathmode.setEditText(dirname)

        self.setAssetPathPreview(self.pathmode.currentText(),
                                 self.user_edit.currentText(),
                                 self.branch_edit.currentText(),
                                 self.assettype_edit.text(),
                                 self.majorversion_edit.value(),
                                 self.minorversion_edit.value())

    def on_PathModeChanged(self):

        value = self.pathmode.currentText()
        cursorpos = self.pathmode.lineEdit().cursorPosition()

        default_install_labels = getDefaultInstallLabels()
        default_install_paths = getDefaultInstallPaths()

        if value == default_install_labels[0]:
            value = default_install_paths[0]
        elif value == default_install_labels[1]:
            value = default_install_paths[1]
        elif value == default_install_labels[2]:
            value = default_install_paths[2]
        elif value == default_install_labels[3]:
            value = default_install_paths[3]

        self.pathmode.setEditText(value)
        self.setAssetPathPreview(self.pathmode.currentText(),
                                 self.user_edit.currentText(),
                                 self.branch_edit.currentText(),
                                 self.assettype_edit.text(),
                                 self.majorversion_edit.value(),
                                 self.minorversion_edit.value())
        self.pathmode.lineEdit().setCursorPosition(cursorpos)


    def buildUI(self):

        w = 600

        # BASE LAYOUT ----------------------------
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Init button before anything else
        self.OK_btn = QPushButton("Create")

        self.gbcolumn_layout = QHBoxLayout()
        layout.addLayout(self.gbcolumn_layout)

        # SIMPLE FOLDER - Name Construction ----------------------------
        self.name_gb = QGroupBox("Name Construction")
        self.gbcolumn_layout.addWidget(self.name_gb)

        name_gb_layout = QVBoxLayout()
        self.name_gb.setLayout(name_gb_layout)

        # Type
        assetbranch_layout = QHBoxLayout()
        name_gb_layout.addLayout(assetbranch_layout)

        assettype_label = QLabel("          Type")
        assettype_label.setFixedSize(110, 20)
        assettype_label.setToolTip(self.assettype_label_tooltip)

        self.assettype_edit = QLineEdit(self.defaults[2])
        self.assettype_edit.setToolTip(self.assettype_tooltip)
        self.assettype_edit.textChanged.connect(self.on_AssetTypeChanged)

        regex_type = QRegExp("[a-zA-Z_\s]+")
        validator_type = QRegExpValidator(regex_type)
        self.assettype_edit.setValidator(validator_type)

        assetbranch_layout.addWidget(assettype_label)
        assetbranch_layout.addWidget(self.assettype_edit)

        # User
        user_layout = QHBoxLayout()
        name_gb_layout.addLayout(user_layout)

        self.user_enable = QCheckBox()
        self.user_enable.clicked.connect(self.on_LineEditChanged)

        checked = False
        if self.defaults[11]: # creating from subnet
            checked = getVHDAConfigValue(getConfigKeys()[2])
        else:
            if self.defaults[0] != "":
                checked = True

        self.user_enable.setChecked(checked)
        self.user_enable.setToolTip(self.user_enable_tooltip)
        self.user_enable.setFixedSize(19, 20)

        user_label = QLabel("User")
        user_label.setToolTip(self.user_enable_tooltip)
        user_label.setFixedSize(85, 20)

        self.user_edit = QComboBox(self)
        self.user_edit.setEditable(True)
        self.user_edit.setToolTip(self.user_enable_tooltip)

        regex = QRegExp("[a-zA-Z_\s]+")
        validator = QRegExpValidator(regex)
        self.user_edit.setValidator(validator)

        self.user_edit.editTextChanged.connect(self.on_LineEditChanged)
        user_layout.addWidget(self.user_enable)
        user_layout.addWidget(user_label)
        user_layout.addWidget(self.user_edit)

        # Branch
        branch_layout = QHBoxLayout()
        name_gb_layout.addLayout(branch_layout)

        self.branch_enable = QCheckBox()
        self.branch_enable.clicked.connect(self.on_LineEditChanged)

        checked = False
        if self.defaults[11]: # creating from subnet
            checked = getVHDAConfigValue(getConfigKeys()[3])
        else:
            if self.defaults[1] != "":
                checked = True

        self.branch_enable.setChecked(checked)
        self.branch_enable.setToolTip(self.branch_enable_tooltip)
        self.branch_enable.setFixedSize(19, 20)

        branch_label = QLabel("Branch")
        branch_label.setToolTip(self.branch_enable_tooltip)
        branch_label.setFixedSize(85, 20)

        self.branch_edit = QComboBox(self)
        self.branch_edit.setEditable(True)
        self.branch_edit.setToolTip(self.branch_enable_tooltip)
        self.branch_edit.setValidator(validator)
        self.branch_edit.activated.connect(self.on_LineEditChanged)
        self.branch_edit.editTextChanged.connect(self.on_LineEditChanged)

        branch_layout.addWidget(self.branch_enable)
        branch_layout.addWidget(branch_label)
        branch_layout.addWidget(self.branch_edit)

        # Version
        version_layout = QHBoxLayout()
        name_gb_layout.addLayout(version_layout)

        self.version_enable = QCheckBox()
        self.version_enable.setFixedSize(19, 20)

        self.version_enable.clicked.connect(self.on_LineEditChanged)

        checked = False
        if self.defaults[11]: # creating from subnet
            checked = getVHDAConfigValue(getConfigKeys()[8])
        else:
            if self.defaults[5] != 0:
                checked = True

        self.version_enable.setChecked(checked)

        version_label = QLabel("Version")
        version_label.setFixedSize(85, 20)

        major_label = QLabel("Major")
        major_label.setFixedSize(100, 20)

        minor_label = QLabel("Minor")
        minor_label.setFixedSize(100, 20)

        self.majorversion_edit = QSpinBox()
        self.minorversion_edit = QSpinBox()
        self.majorversion_edit.setToolTip(self.majorversion_tooltip)
        self.minorversion_edit.setToolTip(self.minorversion_tooltip)
        self.majorversion_edit.setFixedHeight(21)
        self.minorversion_edit.setFixedHeight(21)

        self.majorversion_edit.setValue(self.defaults[5] if self.defaults[5] != None else 0)
        self.minorversion_edit.setValue(self.defaults[6] if self.defaults[6] != None else 0)

        self.majorversion_edit.setRange(1,10000)
        self.minorversion_edit.setRange(0,10000)

        self.majorversion_edit.valueChanged.connect(self.on_MajorVersionChanged)
        self.minorversion_edit.valueChanged.connect(self.on_LineEditChanged)

        version_layout.addWidget(self.version_enable)
        version_layout.addWidget(version_label)

        version_layout.addWidget(self.majorversion_edit)

        version_layout.addWidget(self.minorversion_edit)

         # Asset Name Preview
        assetname_preview_layout = QHBoxLayout()
        name_gb_layout.addLayout(assetname_preview_layout)

        previewname_label = QLabel("Preview")
        previewname_label.setFixedSize(110, 20)

        self.assetname_preview = QLabel()

        assetname_preview_layout.addWidget(previewname_label)
        assetname_preview_layout.addWidget(self.assetname_preview)

        # SIMPLE FOLDER - Tab Menu ----------------------------

        self.tabmenu_gb = QGroupBox("Tab Menu")
        self.gbcolumn_layout.addWidget(self.tabmenu_gb)

        tabmenu_gb_layout = QVBoxLayout()
        self.tabmenu_gb.setLayout(tabmenu_gb_layout)

        # Asset Label

        assetlabel_layout = QHBoxLayout()
        tabmenu_gb_layout.addLayout(assetlabel_layout)

        assetlabel_label = QLabel("Asset Label")
        assetlabel_label.setToolTip(self.assetlabel_tooltip)
        assetlabel_label.setFixedSize(85, 20)
        self.assetlabel_edit = QLineEdit(self.defaults[3])
        self.assetlabel_edit.setToolTip(self.assetlabel_tooltip)
        self.assetlabel_edit.textChanged.connect(self.on_AssetLabelChanged)

        regex_label = QRegExp("[a-zA-Z_\s0-9]+")
        validator_label = QRegExpValidator(regex_label)
        self.assetlabel_edit.setValidator(validator_label)

        assetlabel_layout.addWidget(assetlabel_label)
        assetlabel_layout.addWidget(self.assetlabel_edit)

        # Tab Menu
        tabmenu_layout = QHBoxLayout()
        tabmenu_gb_layout.addLayout(tabmenu_layout)

        tabmenu_label = QLabel("Menu Entry")
        tabmenu_label.setFixedSize(85, 20)
        tabmenu_label.setToolTip(self.tabmenu_tooltip)
        self.tabmenu_edit = QComboBox(self)
        self.tabmenu_edit.setEditable(True)
        self.tabmenu_edit.setToolTip(self.tabmenu_tooltip)

        # Populate with existing entries
        self.tabmenu_edit.addItems(getAllToolSubmenus(self.defaults[7]))

        if self.defaults[11]: # creating from subnet
            self.tabmenu_edit.setEditText(getVHDAConfigValue(getConfigKeys()[9]))
        else:
            idx = self.tabmenu_edit.findText(self.defaults[8])

            if idx == -1:
                self.tabmenu_edit.setEditText("Digital Assets")
            else:
                self.tabmenu_edit.setCurrentIndex(self.tabmenu_edit.findText(self.defaults[8]))

        tabmenu_layout.addWidget(tabmenu_label)
        tabmenu_layout.addWidget(self.tabmenu_edit)

        # Spacer layout
        spacer_label = QLabel("")
        tabmenu_gb_layout.addWidget(spacer_label)
        spacer_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


        # SIMPLE FOLDER - Asset Location ----------------------------
        self.path_gb = QGroupBox("Asset Location")
        layout.addWidget(self.path_gb)

        path_gb_layout = QVBoxLayout()
        self.path_gb.setLayout(path_gb_layout)

        # Save Path
        savepath_layout = QHBoxLayout()
        path_gb_layout.addLayout(savepath_layout)

        _label1 = QLabel("Save Path")
        _label1.setFixedSize(110, 25)
        self.pathmode = QComboBox()
        self.pathmode.setEditable(True)
        self.pathmode.addItems(getDefaultInstallLabels())
        self.pathmode.setEditText(getVHDAConfigValue(getConfigKeys()[0]))
        self.pathmode.editTextChanged.connect(self.on_PathModeChanged)


        self.assetlocation_btn = QPushButton("")
        self.assetlocation_btn.setIcon(hou.qt.createIcon("BUTTONS_folder"))
        self.assetlocation_btn.setFixedSize(30, 28)
        self.assetlocation_btn.clicked.connect(self.on_InputFileButtonClicked)

        savepath_layout.addWidget(_label1)
        savepath_layout.addWidget(self.pathmode)
        savepath_layout.addWidget(self.assetlocation_btn)

        # Path Preview
        custompath_layout = QHBoxLayout()
        path_gb_layout.addLayout(custompath_layout)

        pathlabel = QLabel("Preview")
        pathlabel.setFixedSize(110, 25)
        custompath_layout.addWidget(pathlabel)
        self.pathlabel_edit = QLabel()
        self.pathlabel_edit.setWordWrap(True)

        custompath_layout.addWidget(self.pathlabel_edit)

        # BUTTON SPACER ----------------------------
        verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(verticalSpacer)

        # BUTTONS ----------------------------
        buttons_layout = QHBoxLayout()
        layout.addLayout(buttons_layout)

        buttons_layout.setAlignment(Qt.AlignRight)
        self.Cancel_btn = QPushButton("Cancel")
        self.OK_btn.clicked.connect(self.on_OK)
        self.OK_btn.setDefault(True)
        self.OK_btn.setFixedWidth(100)
        self.Cancel_btn.clicked.connect(self.on_Cancel)
        self.Cancel_btn.setFixedWidth(100)

        buttons_layout.addWidget(self.OK_btn)
        buttons_layout.addWidget(self.Cancel_btn)

        self.PopulateUserEdit()
        self.PopulateBranchEdit()
        self.on_LineEditChanged()
        self.on_PathModeChanged()


class BumpVersionVHDADialog(QDialog):
    def __init__(self, parent, defaults):
        super(BumpVersionVHDADialog, self).__init__(parent)

        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)

        if defaults[0] == 'major':
            self.setWindowTitle("Increase Major Version")
        else:
            self.setWindowTitle("Increase Minor Version")

        try:
            self.setWindowIcon(hou.qt.createIcon(defaults[3].icon()))
        except hou.OperationFailed:
            self.setWindowIcon(hou.qt.createIcon("MISC_generic"))

        self.defaults = defaults
        self.parmvals = []
        self.exitval = None
        self.custom_path_edit = None
        self.buildUI()

    def closeEvent(self, event):
        pass

    def on_OK(self):
        self.exitval = 1
        self.close()

    def on_Cancel(self):
        self.exitval = None
        self.close()

    def buildUI(self):

        w = 300

        self.setFixedWidth(w)
        self.setFixedHeight(w)

        # BASE LAYOUT ----------------------------
        layout = QVBoxLayout()
        self.setLayout(layout)

        # SIMPLE FOLDER - Asset Preview ----------------------------
        self.path_gb = QGroupBox("Asset Preview")
        layout.addWidget(self.path_gb)

        path_gb_layout = QVBoxLayout()
        self.path_gb.setLayout(path_gb_layout)

        # Current Asset Preview
        currentasset_layout = QHBoxLayout()
        path_gb_layout.addLayout(currentasset_layout)

        currentasset_icon = QLabel("")
        currentasset_icon.setFixedSize(25, 25)

        currentasset_label = QLabel("Current Asset")
        currentasset_label.setFixedSize(125, 25)
        self.currentasset_edit = QLabel(self.defaults[1])
        self.currentasset_edit.setAlignment(Qt.AlignCenter)

        currentasset_layout.addWidget(self.currentasset_edit)

        # Upversion Icon
        upversion_layout = QHBoxLayout()
        path_gb_layout.addLayout(upversion_layout)

        self.upversion_btn = QLabel("")
        icon = hou.qt.createIcon("BUTTONS_down")
        self.upversion_btn.setPixmap(icon.pixmap(QSize(20,20)))
        upversion_layout.addWidget(self.upversion_btn)
        self.upversion_btn.setAlignment(Qt.AlignCenter)

        # Next Asset Preview

        nextasset_layout = QHBoxLayout()
        path_gb_layout.addLayout(nextasset_layout)

        nextasset_icon = QLabel("")
        nextasset_icon.setFixedSize(25, 25)

        nextasset_label = QLabel("Next Asset")
        nextasset_label.setFixedSize(125, 25)
        self.nextasset_edit = QLabel(self.defaults[2])
        self.nextasset_edit.setAlignment(Qt.AlignCenter)

        nextasset_layout.addWidget(self.nextasset_edit)

        # BUTTONS ----------------------------

        buttons_layout = QHBoxLayout()
        layout.addLayout(buttons_layout)

        buttons_layout.setAlignment(Qt.AlignRight)
        self.OK_btn = QPushButton("Confirm")
        self.Cancel_btn = QPushButton("Cancel")
        self.OK_btn.clicked.connect(self.on_OK)
        self.OK_btn.setDefault(True)
        self.OK_btn.setFixedWidth(100)
        self.Cancel_btn.clicked.connect(self.on_Cancel)
        self.Cancel_btn.setFixedWidth(100)

        buttons_layout.addWidget(self.OK_btn)
        buttons_layout.addWidget(self.Cancel_btn)

        self.setFixedHeight(self.sizeHint().height())


class DeleteVHDADialog(QDialog):
    def __init__(self, parent, defaults):
        super(DeleteVHDADialog, self).__init__(parent)

        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("Delete Assets")
        self.setWindowIcon(hou.qt.createIcon("BUTTONS_clear"))
        self.defaults = defaults
        self.parmvals = []
        self.exitval = None
        self.custom_path_edit = None
        self.buildUI()

    def closeEvent(self, event):
        pass

    def on_OK(self):
        self.exitval = 1

        selected = []

        for idx in self.table_view.selectedIndexes():

            if (idx.column() == 0):
                selected.append(int(idx.data()))

        self.parmvals = selected
        self.close()

    def on_Cancel(self):
        self.exitval = None
        self.close()

    def buildUI(self):

        self.setFixedWidth(1000)
        self.setFixedHeight(700)

        # BASE LAYOUT ----------------------------
        layout = QVBoxLayout()
        self.setLayout(layout)

        # SIMPLE FOLDER - Asset Preview ----------------------------
        self.assetlist_gb = QGroupBox("Asset Selection")
        layout.addWidget(self.assetlist_gb)

        assetlist_gb_layout = QVBoxLayout()
        self.assetlist_gb.setLayout(assetlist_gb_layout)


        # Info Label
        infolabel_layout = QHBoxLayout()
        assetlist_gb_layout.addLayout(infolabel_layout)

        infolabel = QLabel("Select one or more versions to delete. Use Shift+Left mouse to select multiple entries.")
        infolabel_layout.addWidget(infolabel)

        # Asset Items
        table_view_layout = QHBoxLayout()
        assetlist_gb_layout.addLayout(table_view_layout)

        self.table_model = QStandardItemModel()
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)

        self.table_model.setHorizontalHeaderLabels(['Idx', 'User', 'Branch', 'Type', 'Version', 'Last Modified', 'File Path'])


        font_size = 6
        idx = 0
        for entry in self.defaults[0]:

            hda_def = entry[1]

            item_idx = QStandardItem(QIcon(hou.qt.createIcon(hda_def.icon())),str(idx))
            item_idx.setTextAlignment(Qt.AlignCenter)
            item_idx.setFont(QFont(item_idx.font().family(),font_size))

            item_user = QStandardItem(entry[2])
            item_user.setTextAlignment(Qt.AlignCenter)
            item_user.setFont(QFont(item_user.font().family(),font_size))

            item_branch = QStandardItem(entry[3])
            item_branch.setTextAlignment(Qt.AlignCenter)
            item_branch.setFont(QFont(item_branch.font().family(),font_size))

            item_type = QStandardItem(entry[4])
            item_type.setTextAlignment(Qt.AlignCenter)
            item_type.setFont(QFont(item_type.font().family(),font_size))

            item_version = QStandardItem(str(entry[5]) + "." + str(entry[6]))
            item_version.setTextAlignment(Qt.AlignCenter)
            item_version.setFont(QFont(item_version.font().family(),font_size))

            item_time = QStandardItem(entry[7])
            item_time.setTextAlignment(Qt.AlignCenter)
            item_time.setFont(QFont(item_time.font().family(),font_size))

            item_file = QStandardItem(entry[8])
            item_file.setFont(QFont(item_file.font().family(),font_size))

            row = [item_idx,
                   item_user,
                   item_branch,
                   item_type,
                   item_version,
                   item_time,
                   item_file]

            self.table_model.appendRow(row)
            idx += 1

        self.table_view.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_view.resizeColumnsToContents()
        self.table_view.resizeRowsToContents()
        self.table_view.setColumnWidth(1,100)
        self.table_view.setColumnWidth(2,100)
        self.table_view.setColumnWidth(3,150)
        self.table_view.setColumnWidth(4,50)
        self.table_view.setColumnWidth(5,150)

        self.table_view.setSortingEnabled(True)
        self.table_view.setShowGrid(False)

        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.verticalHeader().setVisible(False)

        table_view_layout.addWidget(self.table_view)


        # BUTTONS ----------------------------

        buttons_layout = QHBoxLayout()
        layout.addLayout(buttons_layout)

        buttons_layout.setAlignment(Qt.AlignRight)
        self.OK_btn = QPushButton("Confirm")
        self.Cancel_btn = QPushButton("Cancel")
        self.OK_btn.clicked.connect(self.on_OK)

        self.OK_btn.setFixedWidth(100)
        self.Cancel_btn.clicked.connect(self.on_Cancel)
        self.Cancel_btn.setFixedWidth(100)
        self.Cancel_btn.setDefault(True)

        buttons_layout.addWidget(self.OK_btn)
        buttons_layout.addWidget(self.Cancel_btn)

        height = 115 + self.table_view.horizontalHeader().size().height()
        for i in range(self.table_model.rowCount()):
            height += self.table_view.rowHeight(i)

        self.setFixedHeight(min(height,900))


class DeleteConfirmVHDADialog(QDialog):
    def __init__(self, parent, defaults):
        super(DeleteConfirmVHDADialog, self).__init__(parent)

        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("Delete Assets Confirmation")
        self.setWindowIcon(hou.qt.createIcon("BUTTONS_clear"))
        self.defaults = defaults
        self.parmvals = []
        self.exitval = None
        self.custom_path_edit = None
        self.buildUI()

    def closeEvent(self, event):
        pass

    def on_OK(self):
        self.exitval = 1
        self.close()

    def on_Cancel(self):
        self.exitval = None
        self.close()

    def buildUI(self):

        self.setFixedWidth(400)
        self.setFixedHeight(300)

        # BASE LAYOUT ----------------------------
        layout = QVBoxLayout()
        self.setLayout(layout)

        # SIMPLE FOLDER - Asset Preview ----------------------------
        self.assetlist_gb = QGroupBox("Assets and Instances")
        layout.addWidget(self.assetlist_gb)

        assetlist_gb_layout = QVBoxLayout()
        self.assetlist_gb.setLayout(assetlist_gb_layout)


        # Info Label
        infolabel_layout = QHBoxLayout()
        assetlist_gb_layout.addLayout(infolabel_layout)

        infolabel = QLabel("Click Confirm to permanently remove all listed assets from disk.")
        infolabel_layout.addWidget(infolabel)

        # Asset Items
        tree_view_layout = QHBoxLayout()
        assetlist_gb_layout.addLayout(tree_view_layout)

        self.tree_model = QStandardItemModel()
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.tree_model)

        root = self.tree_model.invisibleRootItem()

        tree_view_layout.addWidget(self.tree_view)

        self.tree_view.setSelectionMode(QAbstractItemView.NoSelection)

        rownum = 0
        for entry in self.defaults[0]:
            hda_name = entry[0]
            hda_def = entry[1]
            nodes = entry[2]

            type_item = QStandardItem(QIcon(hou.qt.createIcon(hda_def.icon())),hda_name)
            rownum += 1

            for node in nodes:
                node_item = QStandardItem(node.path())
                type_item.appendRow(node_item)
                rownum += 1

            root.appendRow(type_item)

        # BUTTONS ----------------------------
        buttons_layout = QHBoxLayout()
        layout.addLayout(buttons_layout)

        buttons_layout.setAlignment(Qt.AlignRight)
        self.OK_btn = QPushButton("Confirm")
        self.Cancel_btn = QPushButton("Cancel")
        self.OK_btn.clicked.connect(self.on_OK)

        self.OK_btn.setFixedWidth(100)
        self.Cancel_btn.clicked.connect(self.on_Cancel)
        self.Cancel_btn.setFixedWidth(100)
        self.Cancel_btn.setDefault(True)

        buttons_layout.addWidget(self.OK_btn)
        buttons_layout.addWidget(self.Cancel_btn)

        self.tree_view.setHeaderHidden(True)
        self.tree_view.setEditTriggers(QAbstractItemView.NoEditTriggers)

        height = 50 + (rownum * 20)

        self.setFixedHeight(self.sizeHint().height())
