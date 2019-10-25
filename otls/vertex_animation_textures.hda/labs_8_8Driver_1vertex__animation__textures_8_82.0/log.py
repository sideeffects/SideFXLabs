# =============================================================================
# IMPORTS
# =============================================================================

import hou
import os
import sys
import json
from subprocess import Popen, PIPE, STDOUT
from itertools import izip

# =============================================================================
# FUNCTIONS
# =============================================================================

# -----------------------------------------------------------------------------
#    Name: node(node,level,string)
#  Raises: N/A
# Returns: N/A
#    Desc: A verbosity print function that handles ui based logging levels.
# -----------------------------------------------------------------------------      
def node(node,level,string):
    
    if node.parm("enableVerbosity") :
        eVil = node.evalParm("enableVerbosity")    
        if eVil >= level:
            print string
    else :
        print string

# -----------------------------------------------------------------------------
#    Name: script(level,string)
#  Raises: N/A
# Returns: N/A
#    Desc: A verbosity print function that handles script based logging levels.
#          0 = Always print.
#          1 = Print if HOUDINI_ADMIN variable is also set.
# -----------------------------------------------------------------------------      
def script(level,string):
    if hou.getenv("HOUDINI_ADMIN", False) and level >= 1:   
        print string    
    elif level == 0 :
        print string      

# -----------------------------------------------------------------------------
#    Name: env(node,path)
#  Raises: N/A
# Returns: N/A
#    Desc: A verbosity print function that handles ui based logging levels.
# -----------------------------------------------------------------------------      
def env(node,path):
    output  = Popen(["hconfig"], stdin=PIPE, stdout=PIPE, stderr=STDOUT, shell=True)
    output  = output.stdout.read()
    lst     = output.replace("'","").split("\n")
    lst     = [j for i in lst for j in i.split(" := ")]
    lst     = dict(zip(lst[::2], lst[1::2]))
    data    = json.dumps(lst, sort_keys=True, indent=4, separators=(',', ': '))
    with open(path, 'w') as f:
        f.write(data)          