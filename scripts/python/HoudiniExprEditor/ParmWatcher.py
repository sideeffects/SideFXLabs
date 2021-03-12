# -*- coding: utf-8 -*-

# MIT License
# 
# Copyright (c) 2017-2020 Guillaume Jobst, www.cgtoolbox.com
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

import hou
import os
import sys
import time
import subprocess
import hdefereval
import tempfile
import hashlib

try:
    from PySide2 import QtCore
    from PySide2 import QtWidgets
    Slot = QtCore.Slot(str)
except ImportError:

    try:
        from PySide import QtCore
        from PySide import QtGui as QtWidgets
        Slot = QtCore.Slot(str)
    except ImportError:
        from PyQt import QtCore
        from PyQt import QtGui as QtWidgets
        Slot = QtCore.pyqtSlot(str)

TEMP_FOLDER = os.environ.get("EXTERNAL_EDITOR_TEMP_PATH",
                             tempfile.gettempdir())

def is_valid_parm(parm):

    template = parm.parmTemplate()
    if template.dataType() in [hou.parmData.Float,
                               hou.parmData.Int,
                               hou.parmData.String]:
        return True

    return False

def is_python_node(node):

    node_def = node.type().definition()
    if not node_def:
        return False

    if node_def.sections().get("PythonCook") is not None:
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

def get_extra_file_scripts(node):
    
    node_def = node.type().definition()

    if node_def is None:
        return []

    extra_file_options = node_def.extraFileOptions()
    pymodules = [m.split('/')[0] for m in extra_file_options.keys() \
                 if "IsPython" in m \
                 and extra_file_options[m]]

    return pymodules

def get_config_file():

    try:
        return hou.findFile("ExternalEditor.cfg")
    except hou.OperationFailed:
        return os.path.join(hou.expandString("$HOUDINI_USER_PREF_DIR"), "ExternalEditor.cfg")

def set_external_editor():

    r = QtWidgets.QFileDialog.getOpenFileName(hou.ui.mainQtWindow(),
                                                "Select an external editor program")
    if r[0]:

        cfg = get_config_file()

        with open(cfg, 'w') as f:
            f.write(r[0])

        root, file = os.path.split(r[0])

        QtWidgets.QMessageBox.information(hou.ui.mainQtWindow(),
                                          "Editor set",
                                          "External editor set to: " + file)

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
                                             "Editor not set",
                                             "No external editor set, pick one ?",
                                             QtWidgets.QMessageBox.Yes,
                                             QtWidgets.QMessageBox.Cancel)
        if r == QtWidgets.QMessageBox.Cancel:
            return

        return set_external_editor()

    return None

def _read_file_data(file_name):
    # Some external editor ( like VSCode ) empty the file before saving it
    # this will trigger the file watcher and will read empty data. We try
    # to read it again after half a second to be sure the data is really empty or not.
    # For VSCode: https://github.com/microsoft/vscode/pull/62296

    with open(file_name, 'r') as f:
        data = f.read()
                
    if data == '':
        time.sleep(0.5)
        with open(file_name, 'r') as f:
            data = f.read()

    return data

@QtCore.Slot(str)
def filechanged(file_name):
    """ Signal emitted by the watcher to update the parameter contents.
        TODO: set expression when not a string parm.
    """
    parms_bindings = getattr(hou.session, "PARMS_BINDINGS", None)
    if not parms_bindings:
        return

    parm = None
    node = None
    tool = None

    try:
        binding = parms_bindings.get(file_name)
        if isinstance(binding, hou.Parm):
            parm = binding
        elif isinstance(binding, hou.Tool):
            tool = binding
        else:
            node = binding
        
        try:
            if binding == "__temp__python_source_editor":

                data = _read_file_data(file_name)
                try:
                    hou.setSessionModuleSource(data)
                except hou.OperationFailed:
                    print("Watcher error: Invalid source code.")
                return
        except hou.ObjectWasDeleted:
            remove_file_from_watcher(file_name)
            del parms_bindings[file_name]
            return

        if tool is not None:
            data = _read_file_data(file_name)
            try:
                tool.setScript(data)
            except hou.ObjectWasDeleted:
                remove_file_from_watcher(file_name)
                del parms_bindings[file_name]
                return
            return

        if node is not None:
            try:
                data = _read_file_data(file_name)

                section = "PythonCook"
                if "_extraSection_" in file_name:
                    section = file_name.split("_extraSection_")[-1].split('.')[0]
                
                # Block file watcher during module section update to prevent infinite loops in certain cases
                watcher = get_file_watcher()
                watcher.blockSignals(True)
                node.type().definition().sections()[section].setContents(data)
                watcher.blockSignals(False)
                
            except hou.OperationFailed as e:
                print("HoudiniExprEditor: Can't update module content {}, watcher will be removed.".format(e))
                remove_file_from_watcher(file_name)
                del parms_bindings[file_name]
            return

        if parm is not None:

            # check if the parm exists, if not, remove the file from watcher
            try:
                parm.parmTemplate()
            except hou.ObjectWasDeleted:
                remove_file_from_watcher(file_name)
                del parms_bindings[file_name]
                return

            data = _read_file_data(file_name)
            
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

def get_file_ext(parm, type_="parm"):
    """ Get the file name's extention according to parameter's temaplate.
    """

    if type_ == "python_node":
        return ".py"

    template = parm.parmTemplate()
    editorlang = template.tags().get("editorlang", "").lower()

    if editorlang == "vex":
        return ".vfl"

    elif editorlang == "python":
        return ".py"

    elif editorlang == "opencl":
        return ".cl"


    else:

        try:
            if parm.expressionLanguage() == hou.exprLanguage.Python:
                return ".py"
            else:
                return ".txt"
        except hou.OperationFailed:
            return ".txt"

def get_file_name(data, type_="parm"):
    """ Construct an unique file name from a parameter with right extension.
    """

    if type_ == "parm":
        node = data.node()
        sid = str(node.sessionId())
        file_name = sid + '_' + node.name() + '_' + data.name() + get_file_ext(data)
        file_path = TEMP_FOLDER + os.sep + file_name

    elif type_ == "python_node" or "extra_section|" in type_:
        sid = hashlib.sha1(data.path().encode("utf-8")).hexdigest()

        name = data.name()
        if "extra_section|" in type_:
            name += "_extraSection_" + type_.split('|')[-1]

        file_name = sid + '_' + name + get_file_ext(data, type_="python_node")
        file_path = TEMP_FOLDER + os.sep + file_name

    elif type_.startswith("__shelf_tool|"):

        language = type_.split('|')[-1]
        if language == "python":
            file_name = "__shelf_tool_" + data.name() + ".py"
        else:
            file_name = "__shelf_tool_" + data.name() + ".txt"
        file_path = TEMP_FOLDER + os.sep + file_name

    elif type_ == "__temp__python_source_editor":
        
        file_name = "__python_source_editor.py"
        file_path = TEMP_FOLDER + os.sep + file_name

    return file_path

def get_file_watcher():

    return getattr(hou.session, "FILE_WATCHER", None)

def get_parm_bindings():

    return getattr(hou.session, "PARMS_BINDINGS", None)

def clean_files():

    try:
        bindings = get_parm_bindings()
        watcher = get_file_watcher()
        keys_to_delete = []

        if bindings is not None and watcher is not None:
            for k, v in bindings.items():
                
                if isinstance(v, str) and v == "__temp__python_source_editor":
                    # never clean python source editor as it can't be deleted.
                    continue
                elif not os.path.exists(k):
                    remove_file_from_watcher(k)
                    keys_to_delete.append(k)
                elif isinstance(v, hou.Tool):
                    try:
                        v.filePath()
                    except hou.ObjectWasDeleted:
                        remove_file_from_watcher(k)
                        keys_to_delete.append(k)
                else:
                    try:
                        v.path()
                    except hou.ObjectWasDeleted:
                        remove_file_from_watcher(k)
                        keys_to_delete.append(k)

                if not k in watcher.files():
                    keys_to_delete.append(k)

        for k in keys_to_delete:
            del bindings[k]
            
    except Exception as e:
        print("HoudiniExprEditor: Can't clean files: " + str(e))

def _node_deleted(node, **kwargs):

    try:
        file_name = get_file_name(node, type_="python_node")
        bindings = get_parm_bindings()
        if bindings:
            if file_name in bindings.keys():
                del bindings[file_name]
        remove_file_from_watcher(file_name)
    except Exception as e:
        print("Error un callback: onDelete: " + str(e))

def add_watcher_to_section(selection):
    
    sel_def = selection.type().definition()
    if not sel_def: return

    sections = get_extra_file_scripts(selection)
    r = hou.ui.selectFromList(sections, exclusive=True,
                              title="Pick a section:")
    if not r: return

    section = sections[r[0]]
    add_watcher(selection, type_="extra_section|" + section)

def add_watcher(selection, type_="parm"):
    """ Create a file with the current parameter contents and 
        create a file watcher, if not already created and found in hou.Session,
        add the file to the list of watched files.

        Link the file created to a parameter where the tool has been executed from
        and when the file changed, edit the parameter contents with text contents.
    """

    file_path = get_file_name(selection, type_=type_)
    
    if type_ == "parm":
    # fetch parm content, either raw value or expression if any
        try:
            data = selection.expression()
        except hou.OperationFailed:
            if os.environ.get("EXTERNAL_EDITOR_EVAL_EXPRESSION") == '1':
                data = str(selection.eval())
            else:
                data = str(selection.rawValue())
    elif type_ == "python_node":
        data = selection.type().definition().sections()["PythonCook"].contents()

    elif "extra_section|" in type_:

        sec_name = type_.split('|')[-1]
        sec = selection.type().definition().sections().get(sec_name)
        if not sec:
            print("Error: No section {} found.".format(sec))
        data = sec.contents()
    
    elif type_ == "__temp__python_source_editor":
        
        data = hou.sessionModuleSource()

    elif type_.startswith("__shelf_tool|"):
    
        data = selection.script()

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

    if not file_path in parms_bindings.keys():

        parms_bindings[file_path] = selection

        # add "on removed" callback to remove file from watcher
        # when node is deleted
        if type_ == "python_node" or "extra_section|" in type_:
            
            selection.addEventCallback((hou.nodeEventType.BeingDeleted,),
                                       _node_deleted)

    clean_files()

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

def tool_has_watcher(tool, type_=""):
    """ Check if a shelf tool has a watcher attached to it
        Used to display or hide "Remove Watcher" menu.
    """
    file_name = get_file_name(tool, type_=type_)
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

def remove_file_watched(parm, type_="parm"):
    """ Check if a given parameter's watched file exist and remove it
        from watcher list, do not remove the file itself.
    """
    
    file_name = get_file_name(parm, type_=type_)
    r = remove_file_from_watcher(file_name)
    if r:
        clean_files()
        QtWidgets.QMessageBox.information(hou.ui.mainQtWindow(),
                                          "Watcher Removed",
                                          "Watcher removed on file: " + file_name)
