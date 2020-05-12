# =============================================================================
# IMPORTS
# =============================================================================

import hou

# =============================================================================
# FUNCTIONS
# =============================================================================

# -----------------------------------------------------------------------------
#    Name: node(node)
#  Raises: N/A
# Returns: None
#    Desc: The node definition of the input.
# -----------------------------------------------------------------------------

def node_input(node):
    inputs      = node.inputs()  
    if inputs :
        node    = node.inputs()[0]
    elif node.parm("hq_driver") :
        node_parm = hou.node(node.evalParm("hq_driver"))
        if not node :
            node = None 
        else:
            node = node_parm 
    else :
        node    = None   
    return node

# -----------------------------------------------------------------------------
#    Name: node_valid(node)
#  Raises: N/A
# Returns: None
#    Desc: The string name of the node.
# -----------------------------------------------------------------------------

def node_valid(node):
    node        = node_input(node)
    switch      = 0    
    if node :
         switch = 1    
    return switch

# -----------------------------------------------------------------------------
#    Name: node_name(node)
#  Raises: N/A
# Returns: None
#    Desc: The string name of the node.
# -----------------------------------------------------------------------------

def node_name(node):
    name        = str(node_input(node).name())
    return name

# -----------------------------------------------------------------------------
#    Name: node_type(node)
#  Raises: N/A
# Returns: None
#    Desc: Checks if a node is an hq_sim node.
# -----------------------------------------------------------------------------

def node_sim(node):
    switch      = 0
    ntype       = node_input(node).type()
    name        = ntype.nameComponents()[2]  

    if name == 'dop' or name == 'geometry' or name == 'VFX_dop' or name == 'VFX_geometry': 
        switch  = 1

    return switch
    
# -----------------------------------------------------------------------------
#    Name: node_wiredin(node)
#  Raises: N/A
# Returns: None
#    Desc: Checks if a node is wired into the top
# -----------------------------------------------------------------------------

def node_wiredin(node):
    inputs      = node.inputs()
    switch      = 1    
    if not inputs :
         switch = 0
         
    return switch   

# -----------------------------------------------------------------------------
#    Name: hq_driver(node)
#  Raises: N/A
# Returns: None
#    Desc: Checks for dops nodes
# -----------------------------------------------------------------------------

def hq_driver(node):
    node        = node_input(node)
    if node :
        path    = node.path()
    else :
        path    = ''   
    return path
 