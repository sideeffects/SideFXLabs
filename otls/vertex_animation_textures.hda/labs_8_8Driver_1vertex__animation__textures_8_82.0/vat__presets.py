# =============================================================================
# IMPORTS
# =============================================================================

import hou
import subprocess
import os
import platform
import toolutils
node = hou.pwd()
vat_utils = toolutils.createModuleFromSection("vat_utils",node.type(),"vat_utils.py")
#from LaidlawFX import vat_utils

# =============================================================================
# FUNCTIONS
# =============================================================================

# -----------------------------------------------------------------------------
#    Name: main(node)
#  Raises: N/A
# Returns: None
#    Desc: Performs the presets for each engine.
# -----------------------------------------------------------------------------

def main(node):
    engine = node.evalParm('engine')
    method = node.evalParm('method')   
    
    reset(node)
    
    if engine == 'ue4':
        ue4(node,method)
    elif engine == 'unity':
        unity(node,method)
    elif engine == 'lumberyard':
        lumberyard(node,method)
    elif engine == 'cryengine':
        cryengine(node,method)
    elif engine == 'gamemaker':
        gamemaker(node,method)
    elif engine == 'mantra':
        mantra(node,method)
    elif engine == 'sop':
        sop(node,method)
    elif engine == 'winter':
        winter(node,method)    
    elif engine == 'hammer':
        hammer(node,method)    
      
# -----------------------------------------------------------------------------
#    Name: reset(node)
#  Raises: N/A
# Returns: None
#    Desc: Reset all parameters
# -----------------------------------------------------------------------------

def reset(node):
    node.parm('num_frames').revertToDefaults()
    node.parm('speed').revertToDefaults()    
    node.parm('max_min_pos1').revertToDefaults() 
    node.parm('max_min_pos2').revertToDefaults()
    node.parm('max_min_piv1').revertToDefaults() 
    node.parm('max_min_piv2').revertToDefaults()     
    node.parm('max_min_scale1').revertToDefaults() 
    node.parm('max_min_scale2').revertToDefaults()
    node.parm('width_height1').revertToDefaults() 
    node.parm('width_height2').revertToDefaults()     
    node.parm('normalize_data').revertToDefaults()
    node.parm('active_pixels1').revertToDefaults()
    node.parm('active_pixels2').revertToDefaults()
    node.parm('padded_size1').revertToDefaults()
    node.parm('padded_size2').revertToDefaults()
    node.parm('enable_geo').revertToDefaults() 
    node.parm('path_geo').revertToDefaults()
    node.parm('enable_pos').revertToDefaults() 
    node.parm('path_pos').revertToDefaults() 
    node.parm('enable_rot').revertToDefaults() 
    node.parm('path_rot').revertToDefaults()
    node.parm('enable_scale').revertToDefaults() 
    node.parm('path_scale').revertToDefaults()     
    node.parm('enable_norm').revertToDefaults() 
    node.parm('path_norm').revertToDefaults() 
    node.parm('enable_col').revertToDefaults() 
    node.parm('path_col').revertToDefaults()
    node.parm('update_mat').revertToDefaults() 
    node.parm('path_mat').revertToDefaults()      
    node.parm('create_shader').revertToDefaults() 
    node.parm('path_shader').revertToDefaults()
    node.parm('reverse_norm').revertToDefaults()     
    node.parm('convertcolorspace').revertToDefaults()
    node.parm('depth').revertToDefaults()     
    node.parm('pack_norm').revertToDefaults()
    node.parm('pack_pscale').revertToDefaults()     
    node.parm('coord_pos').revertToDefaults()
    node.parm('invert_pos').revertToDefaults()
    node.parm('coord_rot').revertToDefaults() 
    node.parm('coord_col').revertToDefaults() 
    node.parm('invert_col').revertToDefaults() 
    node.parm('target_polycount').revertToDefaults() 
    node.parm('target_texture_size').revertToDefaults() 
    node.parm('scale').revertToDefaults()
    node.parm('shop_materialpath').revertToDefaults()

# -----------------------------------------------------------------------------
#    Name: ue4(node)
#  Raises: N/A
# Returns: None
#    Desc: Engine setting.
# -----------------------------------------------------------------------------

def ue4(node,method):
    print('Unreal uses the default settings.')


# -----------------------------------------------------------------------------
#    Name: unity(node)
#  Raises: N/A
# Returns: None
#    Desc: Engine setting.
# -----------------------------------------------------------------------------

def unity(node,method):
    print('unity')
#    node.parm('path_geo').deleteAllKeyframes()
#    node.parm('path_geo').set('`chs(\"_project\")`/meshes/`chs(\"_component\")`_mesh.fbx')
#    node.parm('path_pos').deleteAllKeyframes()
#    node.parm('path_pos').set('`chs("_project")`/textures/`chs(\"_component\")`_pos.tiff')
#    node.parm('path_rot').deleteAllKeyframes()
#    node.parm('path_rot').set('`chs("_project")`/textures/`chs(\"_component\")`_rot.tiff')
#    node.parm('path_scale').deleteAllKeyframes()
#    node.parm('path_scale').set('`chs("_project")`/textures/`chs(\"_component\")`_scale.tiff')    
#    node.parm('path_norm').deleteAllKeyframes()
#    node.parm('path_norm').set('`chs("_project")`/textures/`chs(\"_component\")`_norm.tiff')
#    node.parm('path_col').deleteAllKeyframes()
#    node.parm('path_col').set('`chs("_project")`/textures/`chs(\"_component\")`_col.tiff')
    node.parm('path_mat').deleteAllKeyframes()
    node.parm('path_mat').set('`chs("_project")`/materials/`chs(\"_component\")`_mat.mat')     
    node.parm('convertcolorspace').deleteAllKeyframes()
    node.parm('convertcolorspace').set(0)
#    node.parm('depth').deleteAllKeyframes()
#    node.parm('depth').set("int16")
#    node.parm('pack_pscale').deleteAllKeyframes()
#    node.parm('pack_pscale').set(1)
#    node.parm('pack_norm').deleteAllKeyframes()
#    node.parm('pack_norm').set(1)    
    node.parm('coord_pos').deleteAllKeyframes()
    node.parm('coord_pos').set(0)
    node.parm('invert_pos').deleteAllKeyframes()
    node.parm('invert_pos').set(1)
    node.parm('coord_rot').deleteAllKeyframes()
    node.parm('coord_rot').set(11)     
    if method == 0 :
        node.parm('path_shader').deleteAllKeyframes()
        node.parm('path_shader').set('`chs("_project")`/shaders/SimpleLitVATSoft.shader')         
    elif method == 1 :
        node.parm('path_shader').deleteAllKeyframes()
        node.parm('path_shader').set('`chs("_project")`/shaders/SimpleLitVATRigid.shader')         
    elif method == 2 :
        vat_utils.primcount(node)
        node.parm('path_shader').deleteAllKeyframes()
        node.parm('path_shader').set('`chs("_project")`/shaders/SimpleLitVATFluid.shader')
        node.parm('target_texture_size').deleteAllKeyframes()
        node.parm('target_texture_size').setExpression('ch("target_polycount")*3')
    elif method == 3 :
        node.parm('reverse_norm').deleteAllKeyframes()
        node.parm('reverse_norm').set(1)    
        node.parm('path_shader').deleteAllKeyframes()
        node.parm('path_shader').set('`chs("_project")`/shaders/SimpleLitVATSprite.shader')
#    vat_utils.mat_check(node) 
#    vat_utils.shader(node)     
    
# -----------------------------------------------------------------------------
#    Name: (node)
#  Raises: N/A
# Returns: None
#    Desc: Engine setting.
# -----------------------------------------------------------------------------

def lumberyard(node,method):
    print('Lumberyard settings not yet implemented.')

# -----------------------------------------------------------------------------
#    Name: cryengine(node)
#  Raises: N/A
# Returns: None
#    Desc: Engine setting.
# -----------------------------------------------------------------------------

def cryengine(node,method):
    print('Cryengine settings not yet implemented.')

# -----------------------------------------------------------------------------
#    Name: gamemaker(node)
#  Raises: N/A
# Returns: None
#    Desc: Engine setting.
# -----------------------------------------------------------------------------

def gamemaker(node,method):
    print('Gamemaker settings not yet implemented.')

# -----------------------------------------------------------------------------
#    Name: mantra(node)
#  Raises: N/A
# Returns: None
#    Desc: Engine setting.
# -----------------------------------------------------------------------------

def mantra(node,method):
    print('Mantra settings not yet implemented.')

# -----------------------------------------------------------------------------
#    Name: alta(node)
#  Raises: N/A
# Returns: None
#    Desc: Engine setting.
# -----------------------------------------------------------------------------

def alta(node,method):
    #print('alta')
    node.parm('convertcolorspace').deleteAllKeyframes()
    node.parm('convertcolorspace').set(0)
    node.parm('pack_pscale').deleteAllKeyframes()
    node.parm('pack_pscale').set(0)
    node.parm('coord_pos').deleteAllKeyframes()
    node.parm('coord_pos').set(0)
    node.parm('invert_pos').deleteAllKeyframes()
    node.parm('invert_pos').set(1)
    node.parm('coord_rot').deleteAllKeyframes()
    node.parm('coord_rot').set(0)    

# -----------------------------------------------------------------------------
#    Name: altb(node)
#  Raises: N/A
# Returns: None
#    Desc: Engine setting.
# -----------------------------------------------------------------------------

def altb(node,method):
    print('Alternate B settings not yet implemented.')

