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
    
    #if namespace != '' and global_ver != '':
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
    if node.canCreateDigitalAsset(): # This is a Subnet 
        return True

def isInternal(node):
    if not node.canCreateDigitalAsset():
        if len(node.children()) == 0:
            return True

def allPossibleRHDANodeTypeNamesInScene(name, node_type_category_name='Sop'):
    '''
    hou.nodeTypeCategories().keys()
    ['Shop', 'Cop2', 'CopNet', 'ChopNet', 'Object', 'Driver', 'Chop', 'Sop', 'Manager', 'Vop', 'Director', 'Dop', 'VopNet']
    '''
    types_dict = {}   
    for category in hou.nodeTypeCategories().values():
        if category.name() == node_type_category_name:
            for node_type in category.nodeTypes().values(): 
                name_components = node_type.nameComponents()                              
                if name_components[2] == name: # finds all similar node types like noise, noise::2.0, user::dev::noise::1.0                     
                    version = name_components[3]   
                    if name_components[1] == '': # NOT A VHDA, only keep the none VHDA types                                  
                        if version == '': # first versions do not have version numbering   
                            version = '1.0'  
                        types_dict[float(version)] = node_type.name()

    type_names = []
    if len(types_dict) == 0: # if no type found (probably this is a brand new vhda node)
        type_names.append(name)
    else:    
        for key in sorted(types_dict.keys()):
            type_names.append(types_dict[key])        

        # Add an extra increased version item
        type_names.append(name + '::' + str(types_dict.keys()[-1] + 1.0))
    return type_names

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

def getAllToolSubmenus(node_type_category_name='Sop'):
    '''
    hou.nodeTypeCategories().keys()
    ['Shop', 'Cop2', 'CopNet', 'ChopNet', 'Object', 'Driver', 'Chop', 'Sop', 'Manager', 'Vop', 'Director', 'Dop', 'VopNet']
    '''

    tool_submenus = []
    for category in hou.nodeTypeCategories().values():
        if category.name() == node_type_category_name:
            for node_type in category.nodeTypes().values():
                for definition in node_type.allInstalledDefinitions():                    
                    submenus = getToolSubmenu(definition)
                    if submenus is not None:
                        for submenu in submenus:
                            if submenu not in tool_submenus:
                                tool_submenus.append(submenu)                               
                                
    tool_submenus.sort()                            
    return tool_submenus

def getLatestVHDAVersion(node, minor_only=False):   
    import re
    label, namespace_user, namespace_type, name, major, minor = separateVHDANameComponents(node)

    other_versions = []
    for definition in allInstalledDefinitionsInScene(node.type().category().name()):        
        if isVersionedDefinition(definition):            
            other_label, other_namespace_user, other_namespace_type, other_name, other_major, other_minor = separateVHDANameComponents(_node_type=definition.nodeType())
            
            if not minor_only:
                if namespace_user == other_namespace_user and  namespace_type == other_namespace_type and name == other_name: # Matching namespace and name
                    other_versions.append((other_major, other_minor))   
            else:
                if namespace_user == other_namespace_user and  namespace_type == other_namespace_type and name == other_name and major == other_major: # Matching namespace, name, and major
                    other_versions.append((other_major, other_minor)) 

    if len(other_versions) == 0:
        return 0, 0
    else:
        def major_minor(version):                 
            return version[0], version[1]

        return max(other_versions, key=major_minor)

def hasSpecificVHDA(node, namespace_user, namespace_type, name):
    other_versions = []
    #rint other_versions
    for definition in allInstalledDefinitionsInScene(node.type().category().name()):        
        if isVersionedDefinition(definition):
            other_label, other_namespace_user, other_namespace_type, other_name, other_major, other_minor = separateVHDANameComponents(_node_type=definition.nodeType())
            if namespace_user == other_namespace_user and  namespace_type == other_namespace_type and name == other_name:
                other_versions.append((other_major, other_minor))

    #print other_versions
    if len(other_versions) == 0:
        return 0, 0
    else:    
        def major_minor(version):                 
            return version[0], version[1]

        return max(other_versions, key=major_minor)

def separateVHDANameComponents(node=None, _node_type=None):
    node_type = None
    
    if _node_type:
        node_type = _node_type 
    else:
        node_type = node.type()
    
    name_components = node_type.nameComponents()
    _namespaces = name_components[1].split("::")
    namespace_user = None
    namespace_type = None

    if len(_namespaces) > 0:
        if _namespaces[0] != '':
            namespace_user = _namespaces[0]
    if len(_namespaces) > 1:
        namespace_type = _namespaces[1]

    name = name_components[2]
    major = 1
    minor = 0
    
    _versioncomponents = name_components[3].split(".")

    if len(_versioncomponents) > 0:
        if _versioncomponents[0] != '':
            major = int(_versioncomponents[0])
    if len(_namespaces) > 1:
        minor = int(_versioncomponents[1])

    label = node_type.description()
    label = constructHDALabel(label)

    return label, namespace_user, namespace_type, name, major, minor 

def constructVHDAName(namespace_user, namespace_type,name,major,minor):
    _vhdaname = ["{}::".format(x) for x in [namespace_user, namespace_type] if x != None]
    _vhdaname += "{0}::{1}.{2}".format(name,major, minor)
    #_vhdaname = 
    return re.sub("[^0-9a-zA-Z\.:]+", "", "".join(_vhdaname))


def constructVHDAFile(namespace_user, namespace_type,name,major,minor, path):
    _vhdafile = ["{}.".format(x) for x in [namespace_user, namespace_type] if x != None]
    _vhdafile += "{0}_v{1}.{2}.hda".format(name, major, minor)
    return  os.path.join(path, re.sub("[^0-9a-zA-Z\.:]+", "", "".join(_vhdafile)))

def constructVHDALabel(label, namespace_type):
    if namespace_type:
        return "%s (%s)" % (label,namespace_type.capitalize())
    else:
        return label

def constructHDALabel(label): 
    import re          
    return re.sub("[\(\[].*?[\)\]]", "", label).rstrip()     

def creationInfoWindow(hda_label,hda_name,file_path):

    message = "The following digital asset will be created: \n\nAsset Label     :    %s\n\nAsset Name    :    %s\n\nFile Name        :    %s" % (hda_label,hda_name,file_path)
    button_idx = hou.ui.displayMessage(message, buttons=('Create and Install', 'Cancel'), default_choice=0, close_choice=1, title='Confirm New Versioned Digital Asset', details_expanded=True)

    return button_idx

def copyToVHDA(node, node_type, namespace_user, namespace_type, name, major, minor, label, path):
    import os    
    
    hda_name  = constructVHDAName(namespace_user, namespace_type,name,major,minor)
    hda_label = constructVHDALabel(label,namespace_type)
    file_path = constructVHDAFile(namespace_user, namespace_type,name,major,minor, path)
       
    button_idx = creationInfoWindow(hda_label,hda_name,file_path)
    
    if button_idx == 0:
        #node_type.definition().copyToHDAFile(file_path,hda_name,hda_label)    
        node_type.definition().save(file_path, template_node=node)
        created_definition = hou.hda.definitionsInFile(file_path)[0]
        created_definition.copyToHDAFile(file_path,hda_name,hda_label)
        created_definition.destroy()
        hou.hda.installFile(file_path)
        reloadAndUpdate(node, hda_name)
     

def createVHDA(node, namespace_user, namespace_type, name, major, minor, label, path):
    # Create new digital asset from temp node

    hda_name  = constructVHDAName(namespace_user, namespace_type,name,major,minor)   
    hda_label = constructVHDALabel(label,namespace_type)
    file_path = constructVHDAFile(namespace_user, namespace_type,name,major,minor, path)

    button_idx = creationInfoWindow(hda_label,hda_name,file_path)

    if button_idx == 0:
        max_num_inputs = 1
        if node.inputConnectors:
            max_num_inputs = len(node.inputConnectors())
        vhda_node = node.createDigitalAsset(
            name = hda_name,
            hda_file_name = file_path,
            description = hda_label,
            min_num_inputs = 0,
            max_num_inputs = max_num_inputs,
        )

        vhda_node.setName(name)

        # Get HDA definition
        vhda_def = vhda_node.type().definition()

        # Update and save new HDA
        vhda_options = vhda_def.options()
        vhda_options.setSaveInitialParmsAndContents(True)
        vhda_def.setOptions(vhda_options)

        vhda_def.save(vhda_def.libraryFilePath(), vhda_node, vhda_options)
        hou.hda.installFile(file_path)

def reloadAndUpdate(node, name):

    hou.hda.reloadAllFiles(True)
    node.changeNodeType(name)

def increaseMajorVersion(node):
    label, namespace_user, namespace_type, name, major, minor = separateVHDANameComponents(node)

    major, minor = getLatestVHDAVersion(node)
    major += 1
    minor = 0

    copyToVHDA(node, node.type(), namespace_user, namespace_type, name, major, minor, label, getDefaultVHDAPath())    

def increaseMinorVersion(node):
    label, namespace_user, namespace_type, name, major, minor = separateVHDANameComponents(node)

    major, minor = getLatestVHDAVersion(node,True)  
    minor += 1

    copyToVHDA(node, node.type(), namespace_user, namespace_type, name, major, minor, label, getDefaultVHDAPath())    

def newVHDAWindow(name,label,path,namespace_user=hou.userName(),namespace_type='dev'):

    defaults = [ namespace_user, namespace_type, name, label, path ]
    dialog = New_VHDA_Dialog(hou.ui.mainQtWindow(), defaults)
    dialog.exec_()

    button_idx = dialog.exitval
    values = dialog.parmvals

    return button_idx, values

def copyToNewVHDA(node):
    label, namespace_user, namespace_type, name, major, minor = separateVHDANameComponents(node)
    
    button_idx, values = newVHDAWindow(name,label,getDefaultVHDAPath(), namespace_user)
    
    if button_idx == 1:
        namespace_user   = values[0]
        namespace_type   = values[1]
        name             = values[2]
        label            = values[3]
        location         = values[4]
    
        major, minor = getLatestVHDAVersion(node)
        major = 1
        minor = 0

        copyToVHDA(node, node.type(), namespace_user, namespace_type, name, major, minor, label, location)        

def createNewVHDA(node):    
    
    name = "default"
    label = "Default"
    namespace = hou.userName()

    if isSubnet(node):
        full_name = node.name()
        name = ''.join(i for i in full_name if not i.isdigit()) 
        label = name.replace("_"," ")
        label = label.title()
    elif isHDA(node):
        # node.type().name() would return 'noise:2.0', however we only need 'noise', so get the name component instead
        name = node.type().nameComponents()[2]
        label = node.type().description()
        namespace = node.type().nameComponents()[1]

    if name != "default":

        button_idx, values = newVHDAWindow(name,label,getDefaultVHDAPath(),namespace_user=namespace)

        if button_idx == 1:
            namespace_user   = values[0]
            namespace_type   = values[1]
            name             = values[2]
            label            = values[3]
            location         = values[4]
            
            major, minor = hasSpecificVHDA(node, namespace_user, namespace_type, name)
            major += 1
            minor = 0

            createVHDA(node, namespace_user, namespace_type, name, major, minor, label, location) 


class New_VHDA_Dialog(QDialog):
    def __init__(self, parent, defaults):
        super(New_VHDA_Dialog, self).__init__(parent)

        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("New Versioned Digital Asset")
        self.defaults = defaults
        self.exitval = None
        self.parmvals = defaults
        self.user_edit = None
        self.type_edit = None
        self.assettype_edit = None
        self.assetlabel_edit = None
        self.assetlocation_edit = None
        self.user_namespace_enable = None
        self.type_enable = None
        self.build_ui()

    def closeEvent(self, event):
        pass

    def on_OK(self):
        self.exitval = 1
        self.parmvals = [self.user_edit.text(), self.type_edit.text(), self.assettype_edit.text(), self.assetlabel_edit.text(), self.assetlocation_edit.text()]

        if not self.type_enable.isChecked():
            self.parmvals[1] = None
        if not self.user_namespace_enable.isChecked():
            self.parmvals[0] = None
        self.close()

    def on_Cancel(self):
        self.exitval = None
        self.close()

    def on_InputFileButtonClicked(self):
        filename = str(QFileDialog.getExistingDirectory(self, "Select Directory"))

        if filename:
            self.assetlocation_edit.setText(filename)
    
    def on_LineEditChange(self):
        branch = self.type_edit.text() if self.type_enable.isChecked() else None
        namespace = self.user_edit.text() if self.user_namespace_enable.isChecked() else None

        self.namespace_preview.setText(constructVHDAName(namespace, branch, self.assettype_edit.text(),1,0))

    def build_ui(self):

      layout = QVBoxLayout()

      self.user_namespace_enable = QCheckBox()
      self.user_namespace_enable.clicked.connect(self.on_LineEditChange)
      self.user_namespace_enable.setChecked(True)
      user_namespace = QLabel("Namespace")
      user_namespace.setFixedSize(100, 20)
      self.user_edit = QLineEdit(self.defaults[0])
      self.user_edit.textChanged.connect(self.on_LineEditChange)
      user_namespace_layout = QHBoxLayout()
      user_namespace_layout.addWidget(self.user_namespace_enable)
      user_namespace_layout.addWidget(user_namespace)
      user_namespace_layout.addWidget(self.user_edit)

      self.type_enable = QCheckBox()
      self.type_enable.clicked.connect(self.on_LineEditChange)
      type_label = QLabel("Branch")
      type_label.setFixedSize(100, 20)
      self.type_edit = QLineEdit(self.defaults[1])
      self.type_edit.textChanged.connect(self.on_LineEditChange)
      type_layout = QHBoxLayout()
      type_layout.addWidget(self.type_enable)
      type_layout.addWidget(type_label)
      type_layout.addWidget(self.type_edit)
      
      assettype_label = QLabel("Asset Type")
      assettype_label.setFixedSize(126, 20)
      self.assettype_edit = QLineEdit(self.defaults[2])
      self.assettype_edit.textChanged.connect(self.on_LineEditChange)
      assettype_layout = QHBoxLayout()
      assettype_layout.addWidget(assettype_label)
      assettype_layout.addWidget(self.assettype_edit)

      assetlabel_label = QLabel("Asset Label")
      assetlabel_label.setFixedSize(126, 20)
      self.assetlabel_edit = QLineEdit(self.defaults[3])
      assetlabel_layout = QHBoxLayout()
      assetlabel_layout.addWidget(assetlabel_label)
      assetlabel_layout.addWidget(self.assetlabel_edit)

      assetlocation_label = QLabel("Asset Location")
      assetlocation_label.setFixedSize(126, 20)
      self.assetlocation_edit = QLineEdit(self.defaults[4])
      assetlocation_btn = QPushButton("...")
      assetlocation_btn.clicked.connect(self.on_InputFileButtonClicked)
      assetlocation_layout = QHBoxLayout()
      assetlocation_layout.addWidget(assetlocation_label)
      assetlocation_layout.addWidget(self.assetlocation_edit)
      assetlocation_layout.addWidget(assetlocation_btn)


      self.namespace_preview = QLabel()
      self.on_LineEditChange()

      OK_btn = QPushButton("OK")
      Cancel_btn = QPushButton("Cancel")

      OK_btn.clicked.connect(self.on_OK)
      Cancel_btn.clicked.connect(self.on_Cancel)

      buttons_layout = QHBoxLayout()
      buttons_layout.addWidget(OK_btn)
      buttons_layout.addWidget(Cancel_btn)


      layout.addLayout(user_namespace_layout)
      layout.addLayout(type_layout)
      layout.addLayout(assettype_layout)
      layout.addLayout(assetlabel_layout)
      layout.addLayout(assetlocation_layout)
      layout.addWidget(self.namespace_preview)
      layout.addLayout(buttons_layout)

      self.setLayout(layout)
      self.setFixedHeight(self.sizeHint().height()) 