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
        return os.path.join(hou.text.expandString('$HOUDINI_USER_PREF_DIR'), "labs.config")

def getConfigKeys():
    keys = ['ocio', 'alt_grey']
    return keys

def getConfigDefaults():
    defaults = [False, False]
    return defaults


class LabsPreferences(QtWidgets.QDialog):

    def __init__(self, parent):
        super(LabsPreferences, self).__init__(parent)
        self.OCIO_checkbox = None
        self.ALT_GREY_checkbox = None
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
            json.dump(configs, savefile, indent=4) 


    def close_ui(self):
        self.close()

    def apply_settings(self, close_window=False):

        OCIO = self.OCIO_checkbox.checkState() == QtCore.Qt.Checked
        if OCIO:
            labutils.manage_ocio(destination="$HOUDINI_USER_PREF_DIR/packages/Labs_OpenColorIO.json", install=1)
        else:
            labutils.manage_ocio(destination="$HOUDINI_USER_PREF_DIR/packages/Labs_OpenColorIO.json", install=0)

        ALT_GREY = self.ALT_GREY_checkbox.checkState() == QtCore.Qt.Checked
        if ALT_GREY:
            labutils.manage_viewport_alt_grey(destination="$HOUDINI_USER_PREF_DIR/config/3DSceneColors.bw", install=1)
        else:
            labutils.manage_viewport_alt_grey(destination="$HOUDINI_USER_PREF_DIR/config/3DSceneColors.bw", install=0)

        self.saveConfigFile([OCIO, ALT_GREY])

        if close_window:
            self.close_ui()

    def accept_settings(self):
        self.apply_settings(close_window=True)

    def build_ui(self):
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("Labs Add-ons")

        layout = QtWidgets.QVBoxLayout()

        # Label
        config_label = QtWidgets.QLabel("Select add-ons to enable:\n")
        layout.addWidget(config_label)

        # OCIO
        self.OCIO_checkbox = QtWidgets.QCheckBox("OCIO ACES 1.2 (Minimal)")
        if 'ocio' in self.prefstate and self.prefstate['ocio']:
            self.OCIO_checkbox.setCheckState(QtCore.Qt.Checked)
        layout.addWidget(self.OCIO_checkbox)

        # Viewport Alt Grey
        self.ALT_GREY_checkbox = QtWidgets.QCheckBox("Viewport Alternative Grey Background")
        if 'alt_grey' in self.prefstate and self.prefstate['alt_grey']:
            self.ALT_GREY_checkbox.setCheckState(QtCore.Qt.Checked)
        layout.addWidget(self.ALT_GREY_checkbox)

        # Spacing
        layout.addSpacing(self.OCIO_checkbox.iconSize().height())

        # Buttons
        apply_button = QtWidgets.QPushButton("Apply")
        accept_button = QtWidgets.QPushButton("Accept")
        cancel_button = QtWidgets.QPushButton("Cancel")
        apply_button.clicked.connect(self.apply_settings)
        accept_button.clicked.connect(self.accept_settings)
        cancel_button.clicked.connect(self.close_ui)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(apply_button)
        button_layout.addWidget(accept_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.setMaximumSize(self.baseSize())