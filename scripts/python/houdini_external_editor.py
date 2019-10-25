# MIT License
# 
# Copyright (c) 2017 Guillaume Jobst, www.cgtoolbox.com
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

# Modified by Luiz Kruel - luiz@sidefx.com

import hou
import os
import sys
import subprocess
import hdefereval
import tempfile

from PySide2 import QtCore
from PySide2 import QtWidgets
Slot = QtCore.Slot(str)

TEMP_FOLDER = os.environ.get("EXTERNAL_EDITOR_TEMP_PATH",
                             tempfile.gettempdir())

def is_valid_parm(parm):

    template = parm.parmTemplate()
    if template.dataType() in [hou.parmData.Float,
                               hou.parmData.Int,
                               hou.parmData.String]:
        return True

    return False

def clean_exp(parm):

    try:
        exp = parm.expression()
        if exp == "":
            exp = None
    except hou.OperationFailed:
        exp = None
                        
    if exp is not None:
        parm.deleteAllKeyframes()

def get_config_file():

    try:
        return hou.findFile("externaleditor.pref")
    except hou.OperationFailed:
        
        ver = hou.applicationVersion()
        if sys.platform in ["darwin", "os2", "os2emx"]:
            verStr = "{}.{}".format(ver[0], ver[1])
        else:
            verStr = "houdini{}.{}".format(ver[0], ver[1])

        cfg_root = hou.expandString("$HOME") + os.sep + verStr
        if not os.path.exists(cfg_root):
            os.makedirs(cfg_root)

        cfg = cfg_root + os.sep + "externaleditor.pref"

        return cfg

def set_external_editor():

    r = QtWidgets.QFileDialog.getOpenFileName(hou.ui.mainQtWindow(),
                                                u"Select an external text editor program")
    if r[0]:

        cfg = get_config_file()

        with open(cfg, 'w') as f:
            f.write(r[0])

        root, file = os.path.split(r[0])

        QtWidgets.QMessageBox.information(hou.ui.mainQtWindow(),
                                          u"Editor set",
                                          u"External editor set to: " + file)

        return r[0]

    return None

def get_external_editor():

    editor = os.environ.get("EDITOR")
    if not editor or not os.path.exists(editor):

        cfg = get_config_file()
        if os.path.exists(cfg):
            with open(cfg, 'r') as f:
                editor = f.read().strip()

        else:
            editor = ""

    if os.path.exists(editor):
        return editor

    else:

        r = QtWidgets.QMessageBox.information(hou.ui.mainQtWindow(),
                                             u"Editor not set",
                                             u"No external editor set, pick one ?",
                                             QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if r == QtWidgets.QMessageBox.No:
            return

        return set_external_editor()

    return None

@QtCore.Slot(str)
def filechanged(file_name):
    """ Signal emitted by the watcher to update the parameter contents.
        TODO: set expression when not a string parm.
    """
    parms_bindings = getattr(hou.session, "PARMS_BINDINGS", None)
    if not parms_bindings:
        return

    parm = parms_bindings.get(file_name)

    try:
        if parm:

            # check if the parm exists, if not, remove the file from watcher
            try:
                parm.parmTemplate()
            except hou.ObjectWasDeleted:
                remove_file_from_watcher(file_name)
                del parms_bindings[file_name]
                return

            with open(file_name, 'r') as f:
                data = f.read()
            
            template = parm.parmTemplate()
            if template.dataType() == hou.parmData.String:
                parm.set(data)
                return

            if template.dataType() == hou.parmData.Float:

                try:
                    data = float(data)

                    clean_exp(parm)
                        
                    parm.set(data)
                    return

                except ValueError:
                    parm.setExpression(data)
                return

            if template.dataType() == hou.parmData.Int:

                try:
                    data = int(data)

                    clean_exp(parm)

                    parm.set(data)
                    return

                except ValueError:
                    parm.setExpression(data)
                return

    except Exception as e:
        print("Watcher error: " + str(e))

def get_file_ext(parm):
    """ Get the file name's extention according to parameter's temaplate.
    """

    template = parm.parmTemplate()
    editorlang = template.tags().get("editorlang", "").lower()

    if editorlang == "vex":
        return ".vfl"

    elif editorlang == "python":
        return ".py"

    else:

        try:
            if parm.expressionLanguage() == hou.exprLanguage.Python:
                return ".py"
            else:
                return ".txt"
        except hou.OperationFailed:
            return ".txt"

def get_file_name(parm):
    """ Construct an unique file name from a parameter with right extension.
    """

    node = parm.node()
    sid = str(node.sessionId())
    file_name = sid + '_' + node.name() + '_' + parm.name() + get_file_ext(parm)
    file_path = TEMP_FOLDER + os.sep + file_name

    return file_path

def get_file_watcher():

    return getattr(hou.session, "FILE_WATCHER", None)

def get_parm_bindings():

    return getattr(hou.session, "PARMS_BINDINGS", None)

def add_watcher(parm):
    """ Create a file with the current parameter contents and 
        create a file watcher, if not already created and found in hou.Session,
        add the file to the list of watched files.
        Link the file created to a parameter where the tool has been executed from
        and when the file changed, edit the parameter contents with text contents.
    """

    file_path = get_file_name(parm)

    if os.path.exists(file_path):
        os.remove(file_path)


    # fetch parm content, either raw value or expression if any
    try:
        data = parm.expression()
    except hou.OperationFailed:
        data = str(parm.eval().encode("utf-8"))

    with open(file_path, 'w') as f:
        f.write(data)

    vsc = get_external_editor()
    if not vsc:
        hou.ui.setStatusMessage("No external editor set",
                                severity=hou.severityType.Error)
        return

    p = QtCore.QProcess(parent=hou.ui.mainQtWindow())
    p.start(vsc, [file_path])
    
    watcher = get_file_watcher()

    if not watcher:
    
        watcher = QtCore.QFileSystemWatcher([file_path],
                                            parent=hou.ui.mainQtWindow())
        watcher.fileChanged.connect(filechanged)
        hou.session.FILE_WATCHER = watcher

    else:
        if not file_path in watcher.files():

            watcher.addPath(file_path)

    parms_bindings = get_parm_bindings()
    if not parms_bindings:
        hou.session.PARMS_BINDINGS = {}
        parms_bindings = hou.session.PARMS_BINDINGS

    parms_bindings[file_path] = parm

def parm_has_watcher(parm):
    """ Check if a parameter has a watcher attached to it
        Used to display or hide "Remove Watcher" menu.
    """
    file_name = get_file_name(parm)
    watcher = get_file_watcher()
    if not watcher:
        return False

    parms_bindings = get_parm_bindings()
    if not parms_bindings:
        return False

    if file_name in parms_bindings.keys():
        return True

    return False

def remove_file_from_watcher(file_name):

    watcher = get_file_watcher()
    if file_name in watcher.files():
        watcher.removePath(file_name)
        return True

    return False

def remove_file_watched(parm):
    """ Check if a given parameter's watched file exist and remove it
        from watcher list, do not remove the file itself.
    """
    
    file_name = get_file_name(parm)
    r = remove_file_from_watcher(file_name)
    if r:
        hou.ui.setStatusMessage("Watcher removed on file: " + file_name, hou.severityType.ImportantMessage)