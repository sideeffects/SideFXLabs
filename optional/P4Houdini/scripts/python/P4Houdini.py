"""
This is the P4Houdini plugin. It provides the backend for an integration into Houdini
for Perforce.
"""

import dataclasses
import json
import os
import platform
import re
import socket
import stat

import hou  # pylint: disable=E0401
import P4Messages
import P4UI
import P4Utils
from P4 import P4, P4Exception, Progress

PLUGIN_NAME = "P4Houdini"


def node_file_automatic(node):
    """
    For the given node, check out or add all files found in the known
    parameters described in P4NodeCheckouts.json
    """
    plugin = P4HoudiniPlugin(headless=True)
    if not plugin.perforce_active:
        return

    if not plugin.preferences.P4_Enabled:
        plugin.disconnect_perforce()
        return

    interests = plugin.dependencies["nodes"]
    node_type_name = node.type().name()
    if node_type_name not in interests:
        plugin.disconnect_perforce()
        return

    parm_val = []
    for parm in interests[node_type_name]:
        _condition = interests[node_type_name][parm]
        # Node parm is simply true or false
        if isinstance(_condition, bool):
            if _condition:
                parm_val.append(os.path.normpath(node.parm(parm).evalAsString()))
        # User needs us to check a parm as condition
        elif isinstance(_condition, dict):
            for _key in _condition:
                if node.parm(_key).eval() == interests[node_type_name][parm][_key]:
                    parm_val.append(os.path.normpath(node.parm(parm).evalAsString()))
    parm_val = list(set(parm_val))
    plugin.add_or_check_out_files(parm_val)

    plugin.disconnect_perforce()


def hda_save_automatic(file):
    """
    Prompts the user to either check out or add the HDA definition
    after hitting save. It only does this if the plugin preferences
    have this enabled. This is used by event callbacks in pythonrc.py
    """

    plugin = P4HoudiniPlugin()
    if not plugin.perforce_active:
        return

    if not plugin.preferences.P4_Enabled:
        plugin.disconnect_perforce()
        return False

    if not plugin.preferences.P4Updates.HDA_Checkout_On_Save:
        plugin.disconnect_perforce()
        return False

    if plugin.verify_file_under_depot_root(file):
        if not plugin.is_file_already_updated_in_perforce(file):
            plugin.add_or_check_out_files(file)
            plugin.disconnect_perforce()
            return True
    plugin.disconnect_perforce()
    return False


def hda_revert(node):
    """
    Reverts the specified node definition to what is found on the depot.
    Also matches the specified node instance to that.
    """
    plugin = P4HoudiniPlugin()
    if not plugin.perforce_active:
        return

    file = node.type().definition().libraryFilePath()

    if plugin.verify_file_under_depot_root(file):
        if P4Messages.confirm_user_revert_file():
            plugin.revert_file_to_latest(file)
            node.matchCurrentDefinition()
    else:
        P4Messages.warn_user_file_not_under_depot()
    plugin.disconnect_perforce()


def hip_before_save_automatic():
    """
    Prompts the user to check out the HIP
    right before the file gets saved. This prevents any permission
    errors due to file locks. It only does this if the
    plugin preferences have this enabled.
    This is used by event callbacks in pythonrc.py
    """
    file = hou.hipFile.path()  # type: ignore
    if not os.path.isfile(file):
        return False

    def __logic(plugin):
        if not plugin.preferences.P4Updates.HIP_Checkout_On_Save:
            return False

        if plugin.verify_file_under_depot_root(file):
            if not plugin.is_file_already_updated_in_perforce(file):
                return plugin.add_or_check_out_files(file)
        return False

    plugin = P4HoudiniPlugin()
    if not plugin.perforce_active:
        return False

    if not plugin.preferences.P4_Enabled:
        plugin.disconnect_perforce()
        return False

    value = __logic(plugin)
    plugin.disconnect_perforce()
    return value


def hip_after_save_automatic():
    """
    Prompts the user to either add the HIP
    after hitting save. It only does this if the plugin preferences
    have this enabled. This is used by event callbacks in pythonrc.py
    """
    file = hou.hipFile.path()  # type: ignore
    if not os.path.isfile(file):
        return False

    def __logic(plugin):
        if not plugin.preferences.P4Updates.HIP_Add_On_Save:
            return False

        if plugin.verify_file_under_depot_root(file):
            if not plugin.is_file_already_updated_in_perforce(file):
                return plugin.add_or_check_out_files(file)
        return False

    plugin = P4HoudiniPlugin()
    if not plugin.perforce_active:
        return False

    if not plugin.preferences.P4_Enabled:
        plugin.disconnect_perforce()
        return False

    value = __logic(plugin)
    plugin.disconnect_perforce()
    return value


def hip_checkout_dependencies():
    """
    Crawl through all nodes found in the currently open HIP file,
    and check if its node type name is found in the P4NodeCheckouts.json file.
    If it is, it will look for files in the P4NodeCheckouts.json parameters marked as write.
    """

    def __logic(plugin):

        def check_accessibility(path):
            _parts = path.split(os.sep)
            for i in range(len(_parts) - 1):
                if os.access(os.sep.join(_parts[:-i]), os.W_OK):
                    return True
            return False

        valid = []
        invalid = []
        new = []

        _message = "Scanning for Dependencies"
        with hou.InterruptableOperation(
            _message, open_interrupt_dialog=True
        ) as operation:
            interests = plugin.dependencies["nodes"]
            all_nodes = hou.node("/").allSubChildren(
                top_down=True, recurse_in_locked_nodes=True
            )
            total_nodes = len(all_nodes)

            playbar = hou.playbar
            framerange = playbar.frameRange()  # type: ignore
            framerange = [int(x) for x in framerange]

            for i, node in enumerate(all_nodes):
                node_type_name = node.type().name()
                if node_type_name not in interests:
                    continue
                parm_val = []

                for frame in range(framerange[0], framerange[1] + 1):

                    for parm in interests[node_type_name]:
                        _condition = interests[node_type_name][parm]
                        # Node parm is simply true or false
                        if isinstance(_condition, bool):
                            if _condition:
                                parm_val.append(
                                    os.path.normpath(
                                        node.parm(parm).evalAsStringAtFrame(frame)
                                    )
                                )
                        # User needs us to check a parm as condition
                        elif isinstance(_condition, dict):
                            for _key in _condition:
                                if (
                                    node.parm(_key).eval()
                                    == interests[node_type_name][parm][_key]
                                ):
                                    parm_val.append(
                                        os.path.normpath(
                                            node.parm(parm).evalAsStringAtFrame(frame)
                                        )
                                    )
                parm_val = list(set(parm_val))
                parm_val.sort()

                for file in parm_val:
                    # Parms might not evaluate correctly due to missing data
                    # So we are checking if the evaluated paths make sense on the user machine
                    if not check_accessibility(file):
                        invalid.append(file)
                        continue

                    if os.path.isfile(file):
                        if plugin.verify_file_under_depot_root(file):
                            if not plugin.is_file_already_updated_in_perforce(file):
                                valid.append(file)
                                continue
                    else:
                        new.append(file)
                        continue

                    invalid.append(file)
                operation.updateProgress(float(i) / float(total_nodes))

        def __callback():
            if len(valid) > 0:
                plugin.add_or_check_out_files(valid)
            else:
                P4Messages.warn_user_no_dependencies_found()
            hou.ui.removeEventLoopCallback(__callback)  # type: ignore
            plugin.disconnect_perforce()

        hou.ui.addEventLoopCallback(__callback)  # type: ignore

    plugin = P4HoudiniPlugin()
    if not plugin.perforce_active:
        return

    __logic(plugin)
    # Disconnect happens in the callback to prevent early disconnect


def hip_before_load_automatic():
    """
    Automatically check if the file that is to be loaded is the latest version.
    If not it will prompt for an update. This is used by event callbacks in pythonrc.py
    NOTE: CURRENTLY NOT USED BECAUSE OF A BUG IN HOUDINI CAUSING A FREEZE.
    """

    # if not self.preferences.P4Updates.HIP_Update_Before_Load:
    #     return False

    # if self.verify_file_under_depot_root(file):
    #     if not self.is_file_in_sync(file):
    #         message = "The file you're about to load is not the latest version.\n"
    #         message += "It is recommended to update first."
    #         message += " Do you wish to do so now automatically?"
    #         result = hou.ui.displayConfirmation(message, severity=hou.severityType.Warning,
    #             title=PLUGIN_NAME)
    #         if result:
    #             self.get_latest_file(file)
    #             self.add_or_check_out_files(file)
    #             return True

    # return False


def hip_checkout_manual():
    """
    Prompts the user to check out the currently open HIP file.
    """
    plugin = P4HoudiniPlugin()
    if not plugin.perforce_active:
        return

    file = hou.hipFile.path()  # type: ignore
    if os.path.isfile(file):
        plugin.add_or_check_out_files(file)
    else:
        P4Messages.warn_user_file_doesnt_exist()
    plugin.disconnect_perforce()


def hip_revert():
    """
    Prompts the user to revert the currently open HIP file
    to the state it is on the depot. It will also
    reload the hip file automatically.
    """
    plugin = P4HoudiniPlugin()
    if not plugin.perforce_active:
        return

    file = hou.hipFile.path()  # type: ignore
    if os.path.isfile(file):
        if plugin.verify_file_under_depot_root(file):
            if P4Messages.confirm_user_revert_file():
                hou.hipFile.clear(suppress_save_prompt=True)  # type: ignore
                plugin.revert_file_to_latest(file)
                hou.hipFile.load(file, suppress_save_prompt=True)  # type: ignore
        else:
            P4Messages.warn_user_file_not_under_depot()

    plugin.disconnect_perforce()


def file_revert(file):
    """
    Reverts the specified file to the state found on the depot.
    """
    plugin = P4HoudiniPlugin()
    if not plugin.perforce_active:
        return

    if plugin.verify_file_under_depot_root(file):
        if P4Messages.confirm_user_revert_file():
            plugin.revert_file_to_latest(file)
    else:
        P4Messages.warn_user_file_not_under_depot()
    plugin.disconnect_perforce()


def file_checkout(file):
    """
    Prompts the user to check out the specified file.
    """
    plugin = P4HoudiniPlugin()
    if not plugin.perforce_active:
        return

    if not plugin.is_file_already_updated_in_perforce(file):
        plugin.add_or_check_out_files(file)

    plugin.disconnect_perforce()


def file_edit_changelist(file):
    """
    Prompts the user to edit the changelist belonging to the specified file.
    """
    plugin = P4HoudiniPlugin()
    if not plugin.perforce_active:
        return

    plugin.edit_pending_changelist(file)
    plugin.disconnect_perforce()


def submit_dialog():
    """
    Prompts the user with the P4Houdini submit dialog.
    """
    plugin = P4HoudiniPlugin()
    if not plugin.perforce_active:
        return

    dialog = P4UI.P4HoudiniChangeListChooser(hou.qt.mainWindow(), plugin, "submit")  # type: ignore
    dialog.exec()
    plugin.disconnect_perforce()


def toggle_plugin_active():
    """
    Utility to toggle the P4Houdini plugin enabled or disable.
    """
    enabled = P4UI.P4ChooseYesNo(f"Should the {PLUGIN_NAME} plugin be active?")

    plugin = P4HoudiniPlugin(skip_login=True)
    plugin.preferences.P4_Enabled = enabled
    plugin.save_preferences()
    P4Messages.warn_user_plugin_state_changed(enabled)


class P4HoudiniData(object):
    """
    Data class to store P4Houdini data.
    """


class P4HoudiniProgress(Progress):
    """
    Wrapper that connects the P4API progress bar to the Houdini UI Progress bar.
    """

    def __init__(self, num_files, operation):
        super().__init__()
        self.total_files = num_files
        self.operation = operation
        self.current_files = 0

    def done(self, fail):
        super().done(fail)
        self.current_files += 1
        self.operation.updateProgress(
            float(self.current_files) / float(self.total_files)
        )


@dataclasses.dataclass
class P4ConnectionSettings:
    """
    Dataclass containing the P4 connection settings.
    """

    P4PORT: str = "$P4PORT"
    P4USER: str = "$P4USER"
    P4CLIENT: str = "$P4CLIENT"


@dataclasses.dataclass
class P4CallbackSettings:
    """
    Dataclass containing the callbacks available to configure for P4Houdini.
    """

    HIP_Add_On_Save: bool = True
    HIP_Checkout_On_Save: bool = True
    HIP_Update_Before_Load: bool = True
    HDA_Checkout_On_Save: bool = True


@dataclasses.dataclass
class P4HoudiniPreferences:
    """
    Dataclass containing the definition of the P4Houdini Preferences.
    """

    P4_Enabled: bool = True
    P4Settings: P4ConnectionSettings = dataclasses.field(
        default_factory=P4ConnectionSettings
    )
    P4_AutoConnect: bool = True
    P4CL_Default: str = "Houdini Generated CL"
    P4CL_Icons: bool = True
    P4CL_Remove_Empty: bool = False
    P4Updates: P4CallbackSettings = dataclasses.field(
        default_factory=P4CallbackSettings
    )


class P4HoudiniPlugin:
    """
    Class that allows for interfacing with Perforce.
    The class provides a lot of methods most commonly used by people.
    """

    def __init__(self, headless=False, skip_login=False):
        self.perforce = P4()
        self.perforce_active = False
        self.headless = headless
        self.preferences = P4HoudiniPreferences()
        self.load_preferences()
        self.dependencies = {}
        self.__load_dependencies()
        self.client_info = {}

        if self.preferences.P4_Enabled and not skip_login:
            if P4Utils.check_perforce_installed() and self.preferences.P4_AutoConnect:
                self.connect_perforce()
        else:
            return

    def attempt_login(self):
        """
        Attempts logging into the P4 client based on the configured workspace settings.
        """
        try:
            self.perforce_active = False
            self.perforce = P4()
            user = hou.text.expandString(str=self.preferences.P4Settings.P4USER)  # type: ignore
            port = hou.text.expandString(str=self.preferences.P4Settings.P4PORT)  # type: ignore
            client = hou.text.expandString(str=self.preferences.P4Settings.P4CLIENT)  # type: ignore

            if user == "" or port == "":
                P4Messages.warn_user_workspace_not_valid()
                return False, "missing_credentials"

            self.perforce.user = user
            self.perforce.port = port
            self.perforce.client = client

            self.perforce.connect()
            users = [x["User"] for x in self.perforce.run("users")]
            self.perforce.run_login("-s")

            if self.perforce.user in users:
                self.perforce_active = True
                return True, ""
        except P4Exception as e:  # pylint: disable=W0718
            if "Perforce password (P4PASSWD) invalid or unset" in str(e):
                P4Messages.warn_user_to_login()
                return False, "expired_login"
            if "This may be your first attempt to connect to this P4PORT" in str(e):
                P4Messages.warn_user_to_login()
                return False, "expired_login"
            if "Your session has expired, please login again." in str(e):
                P4Messages.warn_user_to_login()
                return False, "expired_login"
            print("Something Failed. Please contact Support!", str(e))
        return False, "generic"

    def connect_perforce(self):
        """
        Connects to the P4D client.
        """
        success, _ = self.attempt_login()
        if success:
            self.client_info = self.__get_client_info()

    def load_preferences(self):
        """
        Loads preferences file when found in PATH, otherwise uses defaults.
        """
        with open(P4Utils.get_preferences_file(), encoding="utf-8") as file:
            data = json.load(file)

            self.preferences = P4HoudiniPreferences(
                P4_Enabled=data["P4_Enabled"],
                P4Settings=P4ConnectionSettings(**data["P4Settings"]),
                P4_AutoConnect=data["P4_AutoConnect"],
                P4CL_Default=data["P4CL_Default"],
                P4CL_Icons=data["P4CL_Icons"],
                P4CL_Remove_Empty=data["P4CL_Remove_Empty"],
                P4Updates=P4CallbackSettings(**data["P4Updates"]),
            )

    def save_preferences(self):
        """
        Saves preferences file when found in PATH, otherwise uses default location.
        """
        with open(P4Utils.get_preferences_file(), "w", encoding="utf-8") as file:
            json.dump(dataclasses.asdict(self.preferences), file, indent=4)

    def __load_dependencies(self):
        dependencies_file = hou.text.expandString("$P4HOUDINI/P4NodeCheckouts.json")  # type: ignore
        with open(dependencies_file, encoding="utf-8") as file:
            self.dependencies = json.load(file)

    def __get_client_info(self):
        """
        Returns the client depot root that is being used.
        """
        return self.perforce.run("info")[0]

    def get_pending_changelists(self):
        """
        Finds all pending changelists.
        """
        changelists = self.perforce.run_changes(
            "-l", "--me", "-c", self.perforce.client, "-s", "pending"
        )
        return changelists

    def disconnect_perforce(self):
        """
        Disconnects from the P4D client.
        """
        try:
            self.perforce.disconnect()
        except:  # pylint: disable=W0702
            pass

    def get_local_workspaces(self):
        """
        "Returns a list of workspaces supported by this host.
        """
        clients = self.perforce.run(
            "clients",
            "-u",
            hou.text.expandString(str=self.preferences.P4Settings.P4USER),  # type: ignore
        )
        current_hostname = socket.gethostname()
        return [
            x["client"]
            for x in clients
            if x["Host"] == "" or x["Host"] == current_hostname
        ]

    def verify_file_under_depot_root(self, file):
        """
        Returns whether or not the specified file is part of the client depot root.
        """
        depot_root = os.path.normpath(self.client_info["clientRoot"])
        if platform.system() == "Windows":
            return os.path.normpath(file).lower().startswith(depot_root.lower())

        return os.path.normpath(file).startswith(depot_root)

    def get_description_of_changelist(self, changelist):
        """
        Returns the description of a specific changelist number.
        """
        changelists = self.get_pending_changelists()
        for change in changelists:
            if int(change["change"]) == changelist:
                return change["desc"]
        if changelist == -1:
            return "New Changelist..."
        return changelist

    def get_is_checked_out_by_others(self, file):
        """
        Returns if the specified file has been checked out by someone else.
        """
        return self.get_owner_of_file(file) != self.client_info["userName"]

    def get_owner_of_file(self, file):
        """
        Returns the owner of the specified file.
        """
        status = self.perforce.run_fstat(file)[0]
        if "actionOwner" in status:
            return status["actionOwner"]
        if "otherOpen" in status:
            return status["otherOpen"][0]
        return self.client_info["userName"]

    def get_files_in_changelist(self, changelist):
        """
        Returns all files found in a changelist, as well as the action for that file.
        Format: [[action, file, client]]
        """
        changes = self.perforce.run_opened("-c", changelist)
        return [[x["action"], x["depotFile"], x["client"]] for x in changes]

    def delete_changelist_if_empty(self, changelist):
        """
        For the specified changelist, check if it is empty.. And if it is, delete the empty changelist.
        """
        if len(self.get_files_in_changelist(changelist)) == 0:
            self.perforce.run_change("-d", changelist)

    def find_changelist_by_description(self, description):
        """
        Finds the changelist number by its description.
        """

        existing = self.get_pending_changelists()
        lookup = {}
        for changelist in existing:
            lookup[changelist["desc"].strip()] = changelist["change"]
            if description in lookup:
                return lookup[description]
        return None

    def create_empty_changelist(self, desc=None):
        """
        Creates an empty changelist with the provided description.
        """
        if desc is None:
            desc = self.preferences.P4CL_Default
        result = self.perforce.save_change({"Change": "new", "Description": desc})[0]
        return int(result.split()[1])

    def request_new_or_existing_changelist(self, description):
        """
        Preferred method to use to get or create a changelist.
        It will search existing pending changelists for the specified
        description. If found it will use that, else create a new one.
        """
        existing_changelist = self.find_changelist_by_description(description)
        if existing_changelist:
            return existing_changelist
        return self.create_empty_changelist(description)

    def move_file_to_changelist(self, file, changelist):
        """
        Moves a file to a specific changelist.
        """
        self.perforce.run_reopen("-c", changelist, file)

    def find_latest_revision_of_file(self, file):
        """
        Returns the latest revision found in the depot for the specified file.
        """
        status = self.perforce.run_fstat(file)[0]["headRev"]
        return status

    def find_current_revision_of_file(self, file):
        """
        Returns the currently checked out local revision of the specified file.
        """
        status = self.perforce.run_have(file)[0]["haveRev"]
        return status

    def get_last_changelist_for_file(self, file):
        """
        Finds the last changelist number for the specified file. If a file is currently
        checked out and in a changelist that changelist will be returned. If the file
        is not currently checked out, the changelist containing the file's head revision
        will be returned.
        """
        status = self.perforce.run_fstat(file)[0]
        if "change" in status:
            return status["change"]
        return status["headChange"]

    def is_file_in_sync(self, file):
        """
        Returns whether or not the specified file is in sync with the latest version
        found in the depot.
        """
        current = int(self.find_current_revision_of_file(file))
        latest = int(self.find_latest_revision_of_file(file))
        return current >= latest

    def get_latest_file(self, file):
        """
        Get the latest revision of the specified file.
        """
        self.perforce.run_sync(file)
        hou.ui.setStatusMessage("File has been synced to latest.")  # type: ignore

    def revert_file_to_latest(self, file):
        """
        Revert the specified file to the latest version found on the repository.
        """
        if self.verify_file_under_depot_root(file):
            changelist = self.get_last_changelist_for_file(file)
            try:
                self.perforce.run_revert(file)
                if self.preferences.P4CL_Remove_Empty:
                    self.delete_changelist_if_empty(changelist)
                hou.ui.setStatusMessage("File changes have been reverted.")  # type: ignore

            except P4Exception:  # pylint: disable=W0718
                pass
        else:
            P4Messages.warn_user_file_not_under_depot()

    def add_new_file_to_changelist(self, changelist, file):
        """
        Adds a new file on disk not yet registered to a specific changelist number.
        """
        if self.verify_file_under_depot_root(file):
            try:
                self.perforce.run_add("-c", changelist, file)
                hou.ui.setStatusMessage("File has been added to changelist.")  # type: ignore
            except P4Exception:  # pylint: disable=W0718
                pass
        else:
            P4Messages.warn_user_file_not_under_depot()

    def check_out_file_to_changelist(self, changelist, file):
        """
        Checks out an already registered file on disk and adds it to a specific changelist number.
        """
        if self.verify_file_under_depot_root(file):
            try:
                self.perforce.run_edit("-c", changelist, file)
                hou.ui.setStatusMessage("File has been checked out to changelist.")  # type: ignore
            except P4Exception:  # pylint: disable=W0718
                pass
        else:
            P4Messages.warn_user_file_not_under_depot()

    def make_file_writeable(self, file):
        """
        Makes the specified file writeable.
        """
        os.chmod(file, stat.S_IWRITE)

    def submit_changelist(self, changelist, num_files=-1):
        """
        Submit a changelist number to the depot.
        """

        _message = "Submitting"
        with hou.InterruptableOperation(
            _message, open_interrupt_dialog=True
        ) as operation:
            self.perforce.progress = P4HoudiniProgress(num_files, operation)
            self.perforce.run_submit("-c", changelist, "-f submitunchanged")
            hou.ui.setStatusMessage("Changelist has been submitted.")  # type: ignore

    def set_changelist_description(self, changelist, description):
        """
        Sets the description of a specific changelist number.
        """
        change = self.perforce.fetch_change(changelist)
        change["Description"] = description
        self.perforce.save_change(change)
        hou.ui.setStatusMessage("Changelist has been modified.")  # type: ignore

    def get_file_statuses(self, files):
        """
        Returns a dictionary of file statuses in a single batch operation.
        Includes handling for untracked files and checks for sync status and checkouts by others.
        """
        status_dict = {}
        try:
            # Process statuses for all files in one go
            status_dict = self.process_file_statuses(files)
        except P4Exception as e:
            # Parse error message to identify untracked files and adjust the list
            untracked_files, remaining_files = self.parse_untracked_files(e, files)

            # Update dictionary with untracked files marked
            for file in untracked_files:
                status_dict[file] = {"tracked": False, "error": "not in depot"}

            # Retry fetching statuses for remaining files if there are any
            if remaining_files:
                try:
                    additional_statuses = self.process_file_statuses(remaining_files)
                    status_dict.update(additional_statuses)
                except P4Exception as e2:
                    print(f"Failed to fetch statuses on retry: {str(e2)}")

        return status_dict

    def process_file_statuses(self, files):
        """
        Fetch and process file statuses from Perforce, using a single fstat call.
        This version uses the 'path' field directly from fstat output to map statuses to local file system paths.
        """
        status_output = self.perforce.run_fstat("-Op", *files)
        status_dict = {}
        for status in status_output:
            # Use the 'path' field, which contains the absolute local path
            local_path = status.get("path").replace("\\", "/")

            # Assess sync status
            is_in_sync = int(status.get("haveRev", 0)) >= int(status.get("headRev", 0))

            # Check if the file is checked out by others
            checked_out_by_others = (
                "otherOpen" in status and status["otherOpen"][0] != self.perforce.user
            )

            # Current user already performing some action
            edited_by_self = "action" in status

            # Map the file status to the local path
            status_dict[local_path] = {
                "tracked": True,
                "status": status,
                "is_in_sync": is_in_sync,
                "checked_out_by_others": checked_out_by_others,
                "edited_by_self": edited_by_self,
            }

        return status_dict

    def parse_untracked_files(self, exception, files):
        """
        Parse error messages to identify untracked files and adjust file list.
        """
        untracked_files = []
        error_lines = str(exception).split("\n")
        remaining_files = list(files)  # Make a copy of the file list

        for line in error_lines:
            match = re.match(
                r"^(?:\s*\[Warning\]:\s*')?(.+?)(?:'?\s+- no such file\(s\)\.?)", line.strip()
            )
            if match:
                untracked_file = match.group(1)
                untracked_files.append(untracked_file)
                if untracked_file in remaining_files:
                    remaining_files.remove(untracked_file)

                else:
                    for rf in remaining_files[:]:
                        if rf.replace("\\", "/").lower() == untracked_file.replace("\\", "/").lower():
                            remaining_files.remove(rf)
                            break

        return untracked_files, remaining_files

    def is_file_registered_in_depot(self, file):
        """
        Returns whether or not Perforce is aware of the specified file.
        True meaning it has already been registered in Perforce, False being it has not.
        """
        try:
            self.perforce.run_fstat(file)
            return True
        except:  # pylint: disable=W0702
            return False

    def is_file_already_updated_in_perforce(self, file):
        """
        Returns whether or not perforce is currently doing something with the specified file. (boolean)
        Examples are: Is file already marked for add?, Is file already checked out? etc.
        """
        try:
            status = self.perforce.run_fstat(file)[0]
            return "action" in status.keys()
        except:  # pylint: disable=W0702
            return False

    def edit_pending_changelist(self, file):
        """
        Allows editing the changelist for a given file.
        """
        if not self.verify_file_under_depot_root(file):
            if not self.headless:
                P4Messages.warn_user_file_not_under_depot()
            return False

        if not self.is_file_already_updated_in_perforce(file):
            if not self.headless:
                P4Messages.warn_user_file_not_checked_out()
            return False

        changelist = self.get_last_changelist_for_file(file)

        if not self.headless:
            dialog = P4UI.P4HoudiniChangeListChooser(
                hou.qt.mainWindow(), self, "edit", [file], changelist  # type: ignore
            )
            dialog.exec()
            description = dialog.cl_description
            state = dialog.state
            changelist = dialog.selected_changelist
        else:
            state = False
            description = ""

        if state:
            self.set_changelist_description(changelist, description)
        return state

    def add_or_check_out_files(self, files):
        """
        Detect if each file should be added or checked out based on its status in Perforce,
        handling both single and multiple files. Filter files before opening the UI dialog to exclude
        those that are already checked out or do not need processing.
        """
        if isinstance(files, str):
            files = [files]  # Ensure the parameter is always a list

        file_statuses = self.get_file_statuses(files)
        files_to_process = []
        files_to_add = []
        files_to_edit = []

        # Categorize files based on their statuses
        for file, status in file_statuses.items():
            if not status.get("tracked"):
                files_to_add.append(file)
                continue
            if status.get("edited_by_self"):
                continue
            # File is in depot but not opened for edit
            files_to_edit.append(file)

        files_to_process = files_to_add + files_to_edit

        if len(files_to_process) <= 0:
            return True

        # UI Dialog for selecting changelist and confirming operation
        if not self.headless:
            dialog = P4UI.P4HoudiniChangeListChooser(
                hou.qt.mainWindow(), self, "add", files_to_process  # type: ignore
            )
            dialog.exec()
            cl_name = dialog.selected_changelist
            files_to_process = dialog.files_to_add  # User may deselect some files
            files_to_add = [file for file in files_to_add if file in files_to_process]
            files_to_edit = [file for file in files_to_edit if file in files_to_process]
            description = dialog.cl_description
            state = dialog.state
            if not state:
                return False  # User cancelled the operation
        else:
            cl_name = self.preferences.P4CL_Default
            description = self.preferences.P4CL_Default

        with hou.InterruptableOperation(
            "Checking Out / Adding Files", open_interrupt_dialog=True
        ):
            if not isinstance(cl_name, int):
                cl_name = self.request_new_or_existing_changelist(cl_name)
            else:
                if cl_name == -1:
                    cl_name = self.create_empty_changelist(description)
            self.set_changelist_description(cl_name, description)

            # Execute batch operations
            if files_to_add:
                self.perforce.run_add("-c", cl_name, *files_to_add)
                hou.ui.setStatusMessage(
                    f"{len(files_to_add)} files have been added to changelist."  # type: ignore
                )

            if files_to_edit:
                self.perforce.run_edit("-c", cl_name, *files_to_edit)
                hou.ui.setStatusMessage(
                    f"{len(files_to_edit)} files have been checked out to changelist."  # type: ignore
                )

        return True
