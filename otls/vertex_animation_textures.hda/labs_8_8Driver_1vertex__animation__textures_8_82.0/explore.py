# =============================================================================
# IMPORTS
# =============================================================================

import os
import hou
import platform
import subprocess
import toolutils
node = hou.pwd()
path = toolutils.createModuleFromSection("path",node.type(),"path.py")
log = toolutils.createModuleFromSection("log",node.type(),"log.py")
#from LaidlawFX import path
#from LaidlawFX import log

# =============================================================================
# FUNCTIONS
# =============================================================================

# -----------------------------------------------------------------------------
#    Name: path()
#  Raises: N/A
# Returns: None
#    Desc: Launch and explorer window to the defined directory
# -----------------------------------------------------------------------------

def multiparm_path(node,parm):
    path_var = path.vm_filename_plane(node,parm)
    path(node, path_var)

# -----------------------------------------------------------------------------
#    Name: path()
#  Raises: N/A
# Returns: None
#    Desc: Launch and explorer window to the defined directory
# -----------------------------------------------------------------------------

def path(node, path):
    path    = os.path.dirname(os.path.abspath(path)) 
    pl      = platform.system()
    log.node(node, 2, "Your Platform is: " + str(pl))
    log.node(node, 1, "File path to Browse: " + path)
    skp     = 0
    cmd     = "explorer"
    if pl == "Windows":
        cmd = "explorer"
    elif pl == "Linux":
        cmd = "nautilus"        
    elif pl == "Darwin":
        cmd = "open"
    else:        
        skp = 1
        hou.ui.displayMessage("Can't detect operating system to launch file browser.", severity=hou.severityType.ImportantMessage, default_choice=1, close_choice=1, help="Please PM me and tell me the ouptut from the python shell of: 'import platform, platform.system()' and your command line file browser for your operating system and I can add it.", title="Browse Path")
    

    if skp == 0 :        
        if os.path.isdir(path) :
            proc = subprocess.Popen( [cmd, path])
        else:
            hou.ui.displayMessage("This directory currently does not exist. " + path, severity=hou.severityType.ImportantMessage, default_choice=1, close_choice=1, help="This means your file has not yet been written to disk.", title="Browse Path")
            
