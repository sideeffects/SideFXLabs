import os
import hou
import labutils
import json

from hutil.Qt import QtCore, QtGui, QtWidgets

def getLabsConfigFilePath():
    try:
        all_config_files = hou.findFiles("labs.config")
        return hou.text.expandString(all_config_files[-1])
    except hou.OperationFailed:
        return os.path.join(hou.text.expandString('$HOUDINI_USER_PREF_DIR'),"labs.config")

def getConfigKeys():
    keys = ['ocio']
    return keys

def getConfigDefaults():
    defaults = [False]
    return defaults


class LabsPreferences(QtWidgets.QDialog):
    def __init__(self, parent):
        super(LabsPreferences, self).__init__(parent)
        self.OCIO_checkbox = None
        self.prefstate = self.loadConfigFile()
        self.build_ui()

    def loadConfigFile(self):
        file = getLabsConfigFilePath()

        if os.path.isfile(file):
            with open(file, "r") as savefile:
                return json.load(savefile)
        else:
            return dict(zip(getConfigKeys(), getConfigDefaults()))

    def saveConfigFile(self, configlist):
        file = getLabsConfigFilePath()

        configs = dict(zip(getConfigKeys(), configlist))
        
        with open(file, "w") as savefile:
            json.dump(configs, savefile, indent = 4) 


    def close_ui(self):
        self.close()

    def apply_settings(self):

        OCIO = self.OCIO_checkbox.checkState() == QtCore.Qt.Checked

        if OCIO:
            labutils.manage_ocio(destination="$HOUDINI_USER_PREF_DIR/packages/Labs_OpenColorIO.json", install=1)
        else:
            labutils.manage_ocio(destination="$HOUDINI_USER_PREF_DIR/packages/Labs_OpenColorIO.json", install=0)

        self.saveConfigFile([OCIO])

    def build_ui(self):
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("Labs Preferences")

        layout = QtWidgets.QVBoxLayout()

        # Label
        config_label = QtWidgets.QLabel("Select optional plug-ins to enable:")
        layout.addWidget(config_label)

        # OCIO
        self.OCIO_checkbox = QtWidgets.QCheckBox()
        if self.prefstate['ocio']:
            self.OCIO_checkbox.setCheckState(QtCore.Qt.Checked)
        OCIO_label = QtWidgets.QLabel("OCIO ACES 1.2 (Minimal)")
        OCIO_label.setAlignment(QtCore.Qt.AlignLeft)
        OCIO_layout = QtWidgets.QHBoxLayout()
        OCIO_layout.addWidget(self.OCIO_checkbox)
        OCIO_layout.addWidget(OCIO_label)
        layout.addLayout(OCIO_layout)


        apply_button = QtWidgets.QPushButton("Apply")
        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.clicked.connect(self.close_ui)
        apply_button.clicked.connect(self.apply_settings)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(apply_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)