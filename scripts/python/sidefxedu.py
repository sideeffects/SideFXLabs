import os
import shutil
import contextlib
import json
import zipfile
import platform
import hou
import ssl
import glob
import sys
import getopt
import re

if sys.version_info.major >= 3:
    from urllib.request import urlopen, Request
else:
    from urllib2 import urlopen, Request

from hutil.Qt.QtCore import *
from hutil.Qt.QtGui import *
from hutil.Qt.QtWidgets import *

########################################################################################################################
# GLOBAL VARIABLES #####################################################################################################

REPO_URL = 'https://raw.githubusercontent.com/sideeffects/SideFXEDU/Experimental/releases/releases.json'

# store the major and minor version of Houdini (aka XX.YY)
APP_VERSION = ".".join(map(str, hou.applicationVersion()[:2]))

SETTINGS_FILE = os.path.join(os.getenv("HOUDINI_USER_PREF_DIR"), "packages", "SideFXEDU%s.json" % APP_VERSION)
HOUDINI_ENV = os.path.join(os.getenv("HOUDINI_USER_PREF_DIR"), "houdini.env")

LOCAL_ZIPS = glob.glob(os.path.normpath(os.path.join(hou.getenv("HH"), "public", "SideFXEDU*.zip")))
LOCAL_TOOLSET_ZIP = LOCAL_ZIPS[0] if LOCAL_ZIPS else None
LOCAL_TOOLSET_VERSION = ".".join(re.findall(r'\d+', os.path.split(LOCAL_TOOLSET_ZIP)[-1])) if LOCAL_TOOLSET_ZIP else None

HOU_TEMP_PATH = os.path.normpath(os.path.join(os.getenv("HOUDINI_USER_PREF_DIR"), "SideFXEDU"))
ONLINE_ZIP_DICT = {}

def get_launcher_bin_file_path(launcher_path):
    if platform.system() == "Darwin":
        bin_path = os.path.join(launcher_path, "Contents", "MacOS", "houdini_launcher")
    elif platform.system() == "Linux":
        bin_path = os.path.join(launcher_path, "bin", "houdini_launcher")
    else:
        bin_path = os.path.join(launcher_path, "bin", "houdini_launcher.exe")
    return bin_path

class LauncherDialog(QDialog):
    def __init__(self, launcher_path, settings, parent=None):
        super(LauncherDialog, self).__init__(parent)

        self.setWindowTitle("No Houdini Launcher Found")
        spacer = QLabel("")

        self.settings = settings

        self.path_label = QLabel("Installed elsewhere? Houdini Launcher installation path: ")
        self.launcher_path_lineedit = QLineEdit(self)
        self.launcher_path_lineedit.setText(launcher_path)
        self.resize(500, 150)

        self.url_label = QLabel()
        self.url_label.setOpenExternalLinks(True)
        self.url_label.setText("Get latest Houdini Launcher <a href=\"https://www.sidefx.com/download/daily-builds/?show_launcher=true\">here</a>")


        self.launch_button = QPushButton("Launch")
        self.cancel_button = QPushButton("Cancel")

        self.launch_button.clicked.connect(self.on_launchbtn_press)
        self.cancel_button.clicked.connect(self.on_cancelbtn_press)

        button_layout = QHBoxLayout()
        button_layout.addWidget(spacer)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.launch_button)

        layout = QVBoxLayout()
        layout.addWidget(self.path_label)
        layout.addWidget(self.launcher_path_lineedit)
        layout.addWidget(spacer)
        layout.addWidget(self.url_label)
        layout.addLayout(button_layout)

        self.setLayout(layout)


    def on_launchbtn_press(self):
        p = QProcess()
        launcher_path = get_launcher_bin_file_path(self.launcher_path_lineedit.text())
        if os.path.isfile(launcher_path):
            p.setProgram(launcher_path)
            p.startDetached()
            self.settings.setValue("launcher_install_path", self.launcher_path_lineedit.text())
            self.close()
        else:
            message = launcher_path + " is not a valid Launcher path."
            hou.ui.displayMessage(message, title= "Invalid Launcher Path")

    def on_cancelbtn_press(self):
        self.close()


# UPDATE DIALOG ########################################################################################################
class UpdateDialog(QDialog):
    def __init__(self, parent, updater_object):
        super(UpdateDialog, self).__init__(parent)

        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)

        self.setWindowTitle("SideFX EDU")
        self.updater_object = updater_object

        self.current_version = None
        self.current_file_path = None
        self.settings = QSettings("SideFX", "EDU Shelf Tool")

        if self.updater_object.current_version:
            self.current_version = self.updater_object.current_version
        if self.updater_object.current_file_path:
            self.current_file_path = self.updater_object.current_file_path

        self.build_ui()

    def build_ui(self):
        installed_group = QGroupBox("Installed Release")
        change_group = QGroupBox("Change To")
        spacer = QLabel("")

        # Current Version
        current_version_layout = QHBoxLayout()
        current_version_lbl = QLabel("Version: ")
        current_version = self.current_version
        if not current_version:
            current_version = "None"

        # Current File Path
        current_file_path_layout = QHBoxLayout()
        current_file_path_lbl = QLabel("File path: ")
        current_file_path = self.current_file_path
        if not current_file_path:
            current_file_path = "None"

        current_version_value_lbl = QLabel(current_version)
        current_file_path_value_lbl = QLabel(current_file_path)
        current_file_path_value_lbl.setWordWrap(True)

        current_version_layout.addWidget(current_version_lbl)
        current_version_layout.addWidget(current_version_value_lbl)
        current_file_path_layout.addWidget(current_file_path_lbl)
        current_file_path_layout.addWidget(current_file_path_value_lbl)

        installedgroup_layout = QVBoxLayout(installed_group)

        installedgroup_layout.addLayout(current_version_layout)
        installedgroup_layout.addLayout(current_file_path_layout)

        # Update
        version_layout = QHBoxLayout()
        update_version_label = QLabel("Release:")

        self.version_combo = QComboBox(self)
        for release in self.updater_object.production_releases[:10]:
            self.version_combo.addItem(release)

        self.production_builds_check = QCheckBox("Production Builds Only")
        self.production_builds_check.setChecked(True)
        self.production_builds_check.stateChanged.connect(self.on_production_check)

        version_layout.addWidget(update_version_label)
        version_layout.addWidget(self.version_combo)
        version_layout.addWidget(self.production_builds_check)

        changedgroup_layout = QVBoxLayout(change_group)
        changedgroup_layout.addLayout(version_layout)
        self.button = QPushButton("Update")
        self.uninstallButton = QPushButton("Uninstall")
        self.launcherButton = QPushButton("Start Launcher")

        self.button.clicked.connect(self.on_updatebtn_press)
        self.uninstallButton.clicked.connect(self.on_uninstallbtn_press)
        self.launcherButton.clicked.connect(self.on_launcherbtn_press)
        layout = QVBoxLayout()

        layout.addWidget(installed_group)
        layout.addWidget(change_group)

        layout.addWidget(spacer)


        if hou.getenv("SIDEFXEDU_ADMIN_UPDATES", "0") == "1":
            warning_layout = QHBoxLayout()
            admin_warninglabel = QLabel(self)
            admin_warninglabel.setText("The system administrator has disabled updating on this machine.\nPlease contact the administrator for any changes")
            admin_warninglabel.setStyleSheet('color: red')
            warning_layout.addWidget(admin_warninglabel)
            layout.addLayout(warning_layout)
            self.button.setEnabled(False)
            self.uninstallButton.setEnabled(False)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.launcherButton)
        button_layout.addWidget(spacer)
        button_layout.addWidget(self.button)
        button_layout.addWidget(self.uninstallButton)
        
        layout.addLayout(button_layout)
    
        self.setLayout(layout)

    def show_success_dialog(self, mode):        
        message = ""
        
        if mode == "change":
            message = "SideFX EDU updated successfully"
            message += "\nPlease Restart Houdini to load all of the new tools"
        
        elif mode == "uninstall":
            message = "SideFX EDU uninstalled successfully"
            message += "\nPlease restart Houdini for changes to take effect"
        
        elif mode == "localbuild":
            message = "SideFX EDU installed successfully"
            message += "\nA local copy has been installed. If you wish to update to a newer (online) version, update again"
            message += "\nPlease restart Houdini to load all of the new tools"

        elif mode == "help":
            message = "Unable to uninstall EDU?"
            message += "\n\nEDU shelf tool could have difficulty to remove those EDU not installed by itself."
            message += "\nWe suggest Houdini Launcher for better Houdini Package management."
            message += "\nYou could download Houdini Launcher from:"
            message += "\nhttps://www.sidefx.com/download/daily-builds/?show_launcher=true"

        hou.ui.displayMessage(message, title= "Help" if mode == "help" else "Success")

    def on_production_check(self, state=None):
        self.version_combo.clear()
        if not self.production_builds_check.isChecked():
            for release in self.updater_object.development_releases[:10]:
                self.version_combo.addItem(release)
        for release in self.updater_object.production_releases[:10]:
            self.version_combo.addItem(release)

    def on_updatebtn_press(self):
        version = str(self.version_combo.currentText())
        if version != "":
            if LOCAL_TOOLSET_VERSION != version:
                self.updater_object.update_toolset_version(version)
                self.show_success_dialog("change")
            else:
                self.updater_object.update_toolset_version(version)
                self.show_success_dialog("localbuild")
        self.close()

    def on_uninstallbtn_press(self):
        version = self.current_version
        if version is not None:
            self.updater_object.uninstall_toolset()
            self.show_success_dialog("uninstall")
        self.close()

    def on_helpbtn_press(self):
        self.show_success_dialog("help")

    def on_launcherbtn_press(self):
        p = QProcess()
        if self.settings.value('launcher_install_path'):
            launcher_path = self.settings.value('launcher_install_path')
        elif platform.system() == "Darwin":
            launcher_path =  "/Applications/Houdini Launcher"
        elif platform.system() == "Linux":
            launcher_path = "/opt/sidefx/launcher"
        else:
            launcher_path = "C:/Program Files/Side Effects Software/Launcher"
        launcher_bin_file_path = get_launcher_bin_file_path(launcher_path)
        if os.path.isfile(launcher_bin_file_path):
            p.setProgram(launcher_bin_file_path)
            p.startDetached()
            self.close()
        else:
            dialog = LauncherDialog(launcher_path, self.settings, self)
            dialog.show()


# UPDATER ##############################################################################################################
class SideFXEDUUpdater(object):
    """
        Main updater object, gets called with the shelf button press


    """

    def __init__(self, updater_dialog=False):
        # Store Releases and Production Releases
        self.development_releases = []
        self.production_releases = []
        
        self.current_version = self.get_current_version()
        self.current_file_path = self.get_current_file_path()
        self.get_available_releases()

        disabling_message = os.getenv("SIDEFXEDU_NOINSTALL_MESSAGE")
        if disabling_message:
            if updater_dialog:
                hou.ui.displayMessage(disabling_message)
                return
            else:
                return disabling_message

        if updater_dialog:
            self.show_updater_dialog()
            self.clean_old_installs()


    def clean_old_installs(self):
        if not os.path.isdir(HOU_TEMP_PATH):
            return
        for item in os.listdir(HOU_TEMP_PATH):
            if os.path.isdir(os.path.join(HOU_TEMP_PATH, item)):
                if item != self.current_version:
                    shutil.rmtree(os.path.join(HOU_TEMP_PATH, item), ignore_errors=True)

    # This functions is used to clean edu installed by H18.0.499
    def clean_18_0_499_installs(self):
        packages_dir = os.path.join(os.getenv("HOUDINI_USER_PREF_DIR"), "packages")
        edu_contents_path = os.path.join(packages_dir, "SideFXEDU%s" % APP_VERSION)
        if os.path.isdir(edu_contents_path):
            shutil.rmtree(edu_contents_path, ignore_errors=True)

    # We've renamed the SideFXEDU.json to be SideFXEDU[VER_MM].json, so need to 
    # remove previous SideFXEDU.json file. Otherwise, we end up with having two EDU
    def clean_sidefxedu_json(self):
        packages_dir = os.path.join(os.getenv("HOUDINI_USER_PREF_DIR"), "packages")
        json_file_path = os.path.join(packages_dir, "SideFXEDU.json")
        if os.path.isfile(json_file_path):       
            os.remove(json_file_path)

    def get_available_releases(self):
        # Attempt to download things from github
        try:
            with contextlib.closing(urlopen(Request(REPO_URL), context=ssl._create_unverified_context())) as response:
                data = response.read()
                if data == "":
                    raise ValueError("Unable to get the release list")
        except:
            if LOCAL_TOOLSET_VERSION is not None:
                self.production_releases.append(LOCAL_TOOLSET_VERSION)
                self.development_releases.append(LOCAL_TOOLSET_VERSION)
            return

        if LOCAL_TOOLSET_VERSION is not None:
            self.production_releases.append(LOCAL_TOOLSET_VERSION)

        # Parse the data and filter out versions we don't care about
        j_data = json.loads(data)
        for release in j_data['packages']:
            version_of_release = str(release['version'])
            if version_of_release[0:4] == str(APP_VERSION):
                if release['display_name'].endswith("Production Build"):
                    self.production_releases.append(version_of_release)
                    ONLINE_ZIP_DICT[version_of_release] = release['url']
                elif release['display_name'].endswith("Daily Build"):
                    self.development_releases.append(version_of_release)
                    ONLINE_ZIP_DICT[version_of_release] = release['url']
        if self.production_releases:
            self.production_releases.reverse()
        if self.development_releases:
            self.development_releases.reverse()

    def show_updater_dialog(self):
        dialog = UpdateDialog(hou.qt.mainWindow(), self)
        dialog.show()

    def download_url(self, url):
        """
            Download the zip file from sidefx.com
        :param url:
        :return:
        """
        local_path = os.path.join(HOU_TEMP_PATH, "SideFXEDU_tmp.zip")
        if not os.path.exists(os.path.dirname(local_path)):
            os.makedirs(os.path.dirname(local_path))

        try:
            zipfile = urlopen(url, context=ssl._create_unverified_context())
            with open(local_path, 'wb') as output:
                output.write(zipfile.read())
        except:
            raise ValueError("Unable to download the package file :" + url)
            return

        return local_path

    def unzip_file(self, zip_file, destination_path):
        zipf = zipfile.ZipFile(zip_file, 'r', zipfile.ZIP_DEFLATED)
        zipf.extractall(destination_path)
        zipf.close()

    def get_current_version(self):
        package_info = json.loads(hou.ui.packageInfo())
        for package, info in package_info.items():
            if package.startswith('SideFXEDU'):
                if 'Version' in info:
                    return info['Version']
                elif 'sidefxedu_current_version' in info:
                    return info['sidefxedu_current_version']
        return None

    def get_current_file_path(self):
        package_info = json.loads(hou.ui.packageInfo())
        for package, info in package_info.items():
            if package.startswith('SideFXEDU'):
                if 'File path' in info:
                    return info['File path']
        return None

    def generate_settings_file(self, target_version, dst_path, unzip_dst_path):
        sidefxedu_json = {}
        contents_folder = ""
        compatiable_hou_version = ""
        try:
            if os.path.isdir(unzip_dst_path):
                for file_name in os.listdir(unzip_dst_path):
                    abs_path = os.path.join(unzip_dst_path, file_name)
                    if os.path.isdir(abs_path) and re.match("SideFXEDU[0-9][0-9].[0-9]", file_name):
                        contents_folder = file_name
                        compatiable_hou_version = file_name.split("SideFXEDU")[-1]
                    if os.path.isfile(abs_path) and re.match("SideFXEDU[0-9][0-9].[0-9].json", file_name):
                        with open(abs_path) as json_data:
                            sidefxedu_json = json.load(json_data)
        except:
            print("unabled to load json file in: %s" % unzip_dst_path)
        
        sidefxedu_contents_dir = \
            os.path.join("$HOUDINI_PACKAGE_PATH/../SideFXEDU/%s" % target_version, contents_folder)
        sidefxedu_json['env'] = \
                [ {'SIDEFXEDU': sidefxedu_contents_dir },
                  {'PATH': {'method': "prepend",
                            'value': ["$SIDEFXEDU/bin"]
                           }
                  }
                ]
        sidefxedu_json['version'] = target_version
        sidefxedu_json['path'] = "$SIDEFXEDU"
        if 'enable' not in sidefxedu_json:
            if compatiable_hou_version == "":
                compatiable_hou_version = APP_VERSION
            sidefxedu_json['enable'] = \
                "houdini_version >= '%s'" % compatiable_hou_version + \
                " and houdini_version < '%s'" % str((float(compatiable_hou_version) + 0.1))
        JSON = json.dumps(sidefxedu_json, indent=4)
        f = open(dst_path, 'w')
        f.write(JSON)
        f.close()

    # Delete Installed Files -- EXPOSED TO USER
    def uninstall_toolset(self):
        if self.current_version is not None:
            removedir = os.path.join(HOU_TEMP_PATH, self.current_version)
            if os.path.exists(removedir):
                shutil.rmtree(removedir, ignore_errors=True)

            if os.path.isfile(SETTINGS_FILE):
                os.remove(SETTINGS_FILE)

        self.clean_old_installs()

    # Install embedded toolset Files -- EXPOSED TO USER
    def install_latest_production_toolset(self):
        version = self.production_releases[0]
        self.update_toolset_version(version)

    # Install latest development build -- EXPOSED TO USER
    def install_latest_development_toolset(self):
        version = self.development_releases[0]
        self.update_toolset_version(version)

    # Install embedded toolset Files -- EXPOSED TO USER
    def install_embedded_toolset(self):
        self.update_toolset_version(LOCAL_TOOLSET_VERSION)

    def update_toolset_version(self, target_version):
        """ Call back from the Updater Dialog """

        is_local_zip = 0
        if LOCAL_TOOLSET_VERSION == target_version:
            is_local_zip = 1

        # Create Packages Folder if non-existent
        packages_dir = os.path.join(os.getenv("HOUDINI_USER_PREF_DIR"), "packages")
        if not os.path.exists(packages_dir):
            os.makedirs(packages_dir)

        with hou.InterruptableOperation("Installing SideFX EDU", open_interrupt_dialog=True) as Operation:

            if is_local_zip == 0:
                download_url = ONLINE_ZIP_DICT[target_version]
                local_path = self.download_url(download_url)
            else:
                local_path = LOCAL_TOOLSET_ZIP

            if not os.path.isdir(os.path.join(HOU_TEMP_PATH, target_version)):
                self.unzip_file(local_path, os.path.join(HOU_TEMP_PATH, target_version))

            if is_local_zip == 0:
                os.remove(local_path)

            InstallPath = os.path.join(HOU_TEMP_PATH, target_version).replace("\\", "/")

            self.generate_settings_file(target_version, SETTINGS_FILE, InstallPath)
            self.clean_18_0_499_installs()
            self.clean_sidefxedu_json()

        self.current_version = target_version


def main(argv):
    try:
        updater = SideFXEDUUpdater()
        optlist, args = getopt.getopt(argv, "pdev:u", ['latestproduction', 'latestdevelopment', 'embedded', 'version=', 'uninstall'])
        for opt, arg in optlist:
            if opt in ["--latestproduction", "-p"]:
                updater.install_latest_production_toolset()
            if opt in ["--latestdevelopment", "-d"]:
                updater.install_latest_development_toolset()
            if opt in ["--embedded", "-e"]:
                updater.install_embedded_toolset()
            if opt in ["--version", "-v"]:
                updater.update_toolset_version(arg)
            if opt in ["--uninstall", "-u"]:
                updater.uninstall_toolset()
    except:
        pass

if __name__ == "__main__":
    main(sys.argv[1:])