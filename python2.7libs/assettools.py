#!/usr/bin/env python

import hou
import os
import re
from hutil.Qt.QtCore import *
from hutil.Qt.QtGui import *
from hutil.Qt.QtWidgets import *


def getDefaultVHDAPath():
    return os.path.expandvars(hou.getenv("VHDA_PATH", "$HOUDINI_USER_PREF_DIR/otls"))

def isVersionedDefinition(definition):
    name_components = definition.nodeType().nameComponents()
    namespace = name_components[1]
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

def allInstalledDefinitionsInScene(node_type_category_name='Sop'):
    '''
    hou.nodeTypeCategories().keys()
    ['Shop', 'Cop2', 'CopNet', 'ChopNet', 'Object', 'Driver', 'Chop', 'Sop', 'Manager', 'Vop', 'Director', 'Dop', 'VopNet']
    '''
    definitions = []
    for category in hou.nodeTypeCategories().values():
        if category.name() == node_type_category_name:
            for node_type in category.nodeTypes().values():
                for definition in node_type.allInstalledDefinitions():
                    definitions.append(definition)
    return definitions   

def getToolSubmenu(hda_definition):
    import xml.etree.ElementTree as ET
    if hda_definition.hasSection('Tools.shelf'):
        sections = hda_definition.sections()       
        ts_section = sections['Tools.shelf'].contents()   
        root = ET.fromstring(ts_section)    
        tool = root[0]    
        submenus = tool.findall('toolSubmenu')        
        if submenus:   
            tool_submenus = []
            for submenu in submenus:
                tool_submenus.append(submenu.text)
            return tool_submenus

def getLatestVHDAVersion(node, minor_only=False):   
    label, namespace_user, namespace_type, name, major, minor = separateVHDANameComponents(node)

    other_versions = []
    other_versions_paths = []

    for definition in allInstalledDefinitionsInScene(node.type().category().name()):           
        other_label, other_namespace_user, other_namespace_type, other_name, other_major, other_minor = separateVHDANameComponents(node_type=definition.nodeType())
        
        if not minor_only:
            if namespace_user == other_namespace_user and  namespace_type == other_namespace_type and name == other_name and other_minor == minor:
                other_versions.append((other_major, other_minor))
                other_versions_paths.append(definition.libraryFilePath()) 
        else:
            if namespace_user == other_namespace_user and  namespace_type == other_namespace_type and name == other_name and major == other_major:
                other_versions.append((other_major, other_minor))
                other_versions_paths.append(definition.libraryFilePath())

    if len(other_versions) == 0:
        return 1, 0, list(set(other_versions_paths))
    else:
        def major_minor(version):                 
            return version[0], version[1]

        _version = max(other_versions, key=major_minor)
        return _version[0], _version[1], list(set(other_versions_paths))

def hasSpecificVHDA(node, namespace_user, namespace_type, name, major, minor):
    other_versions = []
    other_versions_paths = []

    for definition in allInstalledDefinitionsInScene(node.type().category().name()): 
        other_label, other_namespace_user, other_namespace_type, other_name, other_major, other_minor = separateVHDANameComponents(node_type=definition.nodeType())
        if namespace_user == other_namespace_user and  namespace_type == other_namespace_type and name == other_name:
            other_versions.append((other_major, other_minor))
            other_versions_paths.append(definition.libraryFilePath())

    if len(other_versions) == 0:
        return major, minor, list(set(other_versions_paths))
    else:    
        def major_minor(version):                 
            return version[0], version[1]

        newversion = max(other_versions, key=major_minor)
        return newversion[0] + 1, newversion[1], list(set(other_versions_paths))

def splitVersionComponents(versionstring):
    version_components = versionstring.split(".")
    major = 1
    minor = 0

    if len(version_components) > 0:
        if version_components[0] != '':
            major = int(version_components[0])
    if len(version_components) > 1 and version_components[1] != "":
        minor = int(version_components[1])

    return major, minor

def separateVHDANameComponents(node=None, node_type=None):
    if node_type == None:
        node_type = node.type()
    
    name_components = node_type.nameComponents()
    namespaces = name_components[1].split("::")
    namespace_user = ""
    namespace_type = ""

    if len(namespaces) > 0:
        if namespaces[0] != '':
            namespace_user = namespaces[0]
    if len(namespaces) > 1:
        namespace_type = namespaces[1]

    name = name_components[2]
    major, minor = splitVersionComponents(name_components[3])

    label = node_type.description()
    label = constructHDALabel(label)

    return label, namespace_user, namespace_type, name, major, minor 

def constructVHDAName(namespace_user, namespace_type,name,major,minor):
    vhda_name = ["{}::".format(x) for x in [namespace_user, namespace_type] if x != ""]
    vhda_name += "{0}::{1}.{2}".format(name,major, minor)
    return re.sub("[^0-9a-zA-Z\.:_]+", "", "".join(vhda_name))

def constructVHDALabel(label, namespace_type):
    if namespace_type:
        return "%s (%s)" % (label,namespace_type.capitalize())
    else:
        return label

def constructHDALabel(label):         
    return re.sub("[\(\[].*?[\)\]]", "", label).rstrip()     

def creationInfoWindow(hda_label,hda_name, paths):
    defaults = [ hda_label, hda_name, paths]
    dialog = Confirm_VHDA_Dialog(hou.ui.mainQtWindow(), defaults)
    dialog.exec_()
    button_idx = dialog.exitval
    values = dialog.parmvals

    return button_idx, values

def copyToVHDA(node, node_type, namespace_user, namespace_type, name, major, minor, label, paths):
    hda_name  = constructVHDAName(namespace_user, namespace_type,name,major,minor)
    hda_label = constructVHDALabel(label,namespace_type)
       
    button_idx, parmvals = creationInfoWindow(hda_label,hda_name, paths)

    if button_idx == 1:  
        node_type.definition().save(hou.expandString("$TEMP/temphda.hda"), template_node=node)
        created_definition = hou.hda.definitionsInFile(hou.expandString("$TEMP/temphda.hda"))[0]
        created_definition.copyToHDAFile(parmvals[0],hda_name,hda_label)
        os.remove(hou.expandString("$TEMP/temphda.hda"))
        hou.hda.installFile(parmvals[0])
        reloadAndUpdate(node, hda_name)

def createVHDA(node, namespace_user, namespace_type, name, major, minor, label, paths):
    hda_name  = constructVHDAName(namespace_user, namespace_type,name,major,minor)   
    hda_label = constructVHDALabel(label,namespace_type)

    button_idx, parmvals = creationInfoWindow(hda_label,hda_name, paths)

    if button_idx == 1:

        max_num_inputs = 1
        if node.inputConnectors:
            max_num_inputs = len(node.inputConnectors())

        vhda_node = node.createDigitalAsset(
            name = hda_name,
            hda_file_name = parmvals[0],
            description = hda_label,
            min_num_inputs = 0,
            max_num_inputs = max_num_inputs#,
            # save_as_embedded = parmvals[0] == "Embedded"
        )

        vhda_node.setName(name, unique_name=True)
        vhda_def = vhda_node.type().definition()

        # Update and save new HDA
        vhda_options = vhda_def.options()
        vhda_options.setSaveInitialParmsAndContents(True)
        vhda_def.setOptions(vhda_options)

        vhda_def.save(vhda_def.libraryFilePath(), vhda_node, vhda_options)
        hou.hda.installFile(vhda_def.libraryFilePath())


def reloadAndUpdate(node, name):
    hou.hda.reloadAllFiles(True)
    node.changeNodeType(name)

def increaseMajorVersion(node):
    label, namespace_user, namespace_type, name, major, minor = separateVHDANameComponents(node)
    major, minor, paths= getLatestVHDAVersion(node)
    major = 2 if major == 0 else major + 1
    minor = 0
    
    copyToVHDA(node, node.type(), namespace_user, namespace_type, name, major, minor, label, paths)    

def increaseMinorVersion(node):
    label, namespace_user, namespace_type, name, major, minor = separateVHDANameComponents(node)
    major, minor, paths = getLatestVHDAVersion(node,True) 
    major = 1 if major == 0 else major
    minor += 1
    
    copyToVHDA(node, node.type(), namespace_user, namespace_type, name, major, minor, label, paths)    

def newVHDAWindow(name,label,path,namespace_user,namespace_type, major, minor):
    defaults = [ namespace_user, namespace_type, name, label, path, major, minor]
    dialog = New_VHDA_Dialog(hou.ui.mainQtWindow(), defaults)
    dialog.exec_()
    button_idx = dialog.exitval
    values = dialog.parmvals

    return button_idx, values

def copyToNewVHDA(node):
    label, namespace_user, namespace_type, name, major, minor = separateVHDANameComponents(node)
    button_idx, values = newVHDAWindow(name,label,getDefaultVHDAPath(), namespace_user, namespace_type, major, minor)
    
    if button_idx == 1:
        namespace_user   = values[0]
        namespace_type   = values[1]
        name             = values[2]
        label            = values[3]
        major            = values[4]
        minor            = values[5]

        major, minor, paths = hasSpecificVHDA(node, namespace_user, namespace_type, name, major, minor)
        
        copyToVHDA(node, node.type(), namespace_user, namespace_type, name, major, minor, label, paths)    

def createNewVHDAFromSubnet(node):    
    
    button_idx, values = newVHDAWindow("default", "Default", getDefaultVHDAPath(), namespace_user="", namespace_type="", major="1", minor="0")

    if button_idx == 1:
        namespace_user   = values[0]
        namespace_type   = values[1]
        name             = values[2]
        label            = values[3]
        major            = values[4]
        minor            = values[5]
        
        major, minor, paths = hasSpecificVHDA(node, namespace_user, namespace_type, name, major, minor)
        createVHDA(node, namespace_user, namespace_type, name, major, minor, label, paths) 


default_install_options = ["Custom - Default", "Custom - User Preferences", "Custom - $HIP"]
class Confirm_VHDA_Dialog(QDialog):
    def __init__(self, parent, defaults):
        super(Confirm_VHDA_Dialog, self).__init__(parent)

        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("New Versioned Digital Asset")
        self.defaults = defaults
        self.parmvals = []
        self.exitval = None
        self.custom_path_edit = None
        self.build_ui()

    def closeEvent(self, event):
        pass

    def on_OK(self):
        self.exitval = 1

        value = self.pathmode.currentText()
        savepath = value

        # if value == "Embedded in current HIP":
        #     savepath = "Embedded"
        if value in default_install_options:
            savepath = self.custom_path_edit.text()

        self.parmvals = [savepath]
        self.close()

    def on_Cancel(self):
        self.exitval = None
        self.close()

    def on_InputFileButtonClicked(self):
        filename = str(QFileDialog.getSaveFileName(self, "Browse Save Path", getDefaultVHDAPath(), "HDA (*.hda)")[0])

        if filename:
            self.custom_path_edit.setText(filename)

    def on_PathModeChange(self):
        value = self.pathmode.currentText()
        self.custom_path_edit.setDisabled(value not in default_install_options)
        self.assetlocation_btn.setDisabled(value not in default_install_options)

        if value in default_install_options:
            self.custom_path_edit.setText(self.buildDefaultPathFromPreset(value))

    def buildDefaultPathFromPreset(self, preset):
        if preset == default_install_options[1]:
            _path = hou.expandString("$HOUDINI_USER_PREF_DIR/otls")
        elif preset == default_install_options[2]:
            _path = hou.expandString("$HIP")
        else:
            _path = getDefaultVHDAPath()

        return os.path.join(_path, self.defaults[1].replace("::", ".")+".hda").replace("\\", "/")

    def build_ui(self):

        layout = QVBoxLayout()
        dialogdescription = QLabel("The following digital asset will be created:")

        assetlabel_layout = QHBoxLayout()
        _label = QLabel("Label:")
        _label.setFixedSize(100, 25)
        assetlabel_layout.addWidget(_label)
        assetlabel_layout.addWidget(QLabel(self.defaults[0]))

        assetname_layout = QHBoxLayout()
        _label2 = QLabel("Name:")
        _label2.setFixedSize(100, 25)
        assetname_layout.addWidget(_label2)
        assetname_layout.addWidget(QLabel(self.defaults[1]))

        verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)

        savepath_layout = QHBoxLayout()
        _label3 = QLabel("Save Path:")
        _label3.setFixedSize(100, 25)
        self.pathmode = QComboBox()
        self.pathmode.addItems(default_install_options)
        self.pathmode.addItems(self.defaults[2])
        
        if len(self.defaults[2]) > 0:
            index = self.pathmode.findText(self.defaults[2][0], Qt.MatchFixedString)
            self.pathmode.setCurrentIndex(index)
            
        self.pathmode.currentIndexChanged.connect(self.on_PathModeChange)
        savepath_layout.addWidget(_label3)
        savepath_layout.addWidget(self.pathmode)


        custompath_layout = QHBoxLayout()
        pathlabel = QLabel("Path:")
        pathlabel.setFixedSize(100, 25)
        self.custom_path_edit = QLineEdit(self.buildDefaultPathFromPreset(default_install_options[0]))
        self.assetlocation_btn = QPushButton("...")
        self.assetlocation_btn.clicked.connect(self.on_InputFileButtonClicked)
        custompath_layout.addWidget(pathlabel)
        custompath_layout.addWidget(self.custom_path_edit)
        custompath_layout.addWidget(self.assetlocation_btn)
        self.on_PathModeChange()

        buttons_layout = QHBoxLayout()
        OK_btn = QPushButton("Create")
        Cancel_btn = QPushButton("Cancel")
        OK_btn.clicked.connect(self.on_OK)
        Cancel_btn.clicked.connect(self.on_Cancel)
        buttons_layout.addWidget(OK_btn)
        buttons_layout.addWidget(Cancel_btn)

        layout.addWidget(dialogdescription)
        layout.addItem(verticalSpacer)
        layout.addLayout(assetlabel_layout)
        layout.addLayout(assetname_layout)
        layout.addLayout(savepath_layout)
        layout.addLayout(custompath_layout)
        layout.addItem(verticalSpacer)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        self.setFixedHeight(self.sizeHint().height()) 



# SAVE AS NEW VHDA DIALOG
class New_VHDA_Dialog(QDialog):
    def __init__(self, parent, defaults):
        super(New_VHDA_Dialog, self).__init__(parent)

        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("New Versioned Digital Asset")
        self.defaults = defaults
        self.exitval = None
        self.parmvals = defaults
        self.user_edit = ""
        self.type_edit = ""
        self.assettype_edit = None
        self.assetlabel_edit = None
        self.assetversion_edit = None
        self.user_namespace_enable = None
        self.type_enable = None
        self.build_ui()

    def closeEvent(self, event):
        pass

    def on_OK(self):
        self.exitval = 1
        major, minor = splitVersionComponents(self.assetversion_edit.text())
        self.parmvals = [self.user_edit.text(), self.type_edit.text(), self.assettype_edit.text(), self.assetlabel_edit.text(), major, minor]

        if not self.type_enable.isChecked():
            self.parmvals[1] = ""
        if not self.user_namespace_enable.isChecked():
            self.parmvals[0] = ""
        self.close()

    def on_Cancel(self):
        self.exitval = None
        self.close()

    
    def on_LineEditChange(self):
        branch = self.type_edit.text() if self.type_enable.isChecked() else ""
        namespace = self.user_edit.text() if self.user_namespace_enable.isChecked() else ""

        self.user_edit.setDisabled(not self.user_namespace_enable.isChecked())
        self.type_edit.setDisabled(not self.type_enable.isChecked())
        
        major, minor = splitVersionComponents(self.assetversion_edit.text())
        self.namespace_preview.setText(constructVHDAName(namespace, branch, self.assettype_edit.text(),major,minor))

    def build_ui(self):
        layout = QVBoxLayout()

        self.user_namespace_enable = QCheckBox()
        self.user_namespace_enable.clicked.connect(self.on_LineEditChange)
        self.user_namespace_enable.setChecked(self.defaults[0] != "")

        user_namespace_layout = QHBoxLayout()
        user_namespace = QLabel("Namespace")
        user_namespace.setFixedSize(100, 20)
        self.user_edit = QLineEdit(self.defaults[0] if self.defaults[0] != "" else hou.userName())
        self.user_edit.textChanged.connect(self.on_LineEditChange)
        user_namespace_layout.addWidget(self.user_namespace_enable)
        user_namespace_layout.addWidget(user_namespace)
        user_namespace_layout.addWidget(self.user_edit)

        type_layout = QHBoxLayout()
        self.type_enable = QCheckBox()
        self.type_enable.clicked.connect(self.on_LineEditChange)
        self.type_enable.setChecked(self.defaults[1] != "")
        type_label = QLabel("Branch")
        type_label.setFixedSize(100, 20)
        self.type_edit = QLineEdit(self.defaults[1] if self.defaults[1] != "" else "dev")
        self.type_edit.textChanged.connect(self.on_LineEditChange)
        type_layout.addWidget(self.type_enable)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_edit)

        assettype_layout = QHBoxLayout()
        assettype_label = QLabel("Type and Version")
        assettype_label.setFixedSize(126, 20)
        self.assettype_edit = QLineEdit(self.defaults[2])
        self.assettype_edit.textChanged.connect(self.on_LineEditChange)
        _major = self.defaults[5] if self.defaults[5] != None else 1
        _minor = self.defaults[6] if self.defaults[6] != None else 0
        versionstring = "{0}.{1}".format(_major, _minor)
        self.assetversion_edit = QLineEdit(versionstring)
        self.assetversion_edit.textChanged.connect(self.on_LineEditChange)
        self.assetversion_edit.setFixedWidth(30)
        assettype_layout.addWidget(assettype_label)
        assettype_layout.addWidget(self.assettype_edit)
        assettype_layout.addWidget(self.assetversion_edit)

        assetlabel_layout = QHBoxLayout()
        assetlabel_label = QLabel("Label")
        assetlabel_label.setFixedSize(126, 20)
        self.assetlabel_edit = QLineEdit(self.defaults[3])
        assetlabel_layout.addWidget(assetlabel_label)
        assetlabel_layout.addWidget(self.assetlabel_edit)

        verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.namespace_preview = QLabel()
        self.on_LineEditChange()

        buttons_layout = QHBoxLayout()
        OK_btn = QPushButton("Continue")
        Cancel_btn = QPushButton("Cancel")
        OK_btn.clicked.connect(self.on_OK)
        Cancel_btn.clicked.connect(self.on_Cancel)
        buttons_layout.addWidget(OK_btn)
        buttons_layout.addWidget(Cancel_btn)

        layout.addLayout(user_namespace_layout)
        layout.addLayout(type_layout)
        layout.addLayout(assettype_layout)
        layout.addLayout(assetlabel_layout)
        layout.addWidget(self.namespace_preview)
        layout.addItem(verticalSpacer)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        self.setFixedHeight(self.sizeHint().height()) 