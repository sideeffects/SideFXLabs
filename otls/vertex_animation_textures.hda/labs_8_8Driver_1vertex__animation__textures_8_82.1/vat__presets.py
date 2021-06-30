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
    elif engine == 'popcornfx':
        popcornfx(node,method)

# -----------------------------------------------------------------------------
#    Name: reset(node)
#  Raises: N/A
# Returns: None
#    Desc: Reset all parameters
# -----------------------------------------------------------------------------

def reset(node):
    node.parm('num_frames').revertToDefaults()
    node.parm('speed').revertToDefaults()
    node.parm('posminmax1').revertToDefaults()
    node.parm('posminmax2').revertToDefaults()
    node.parm('pivminmax1').revertToDefaults()
    node.parm('pivminmax2').revertToDefaults()
    node.parm('scaleminmax1').revertToDefaults()
    node.parm('scaleminmax2').revertToDefaults()
    node.parm('widthheight1').revertToDefaults()
    node.parm('widthheight2').revertToDefaults()
    node.parm('normalize_data').revertToDefaults()
    node.parm('activepixels1').revertToDefaults()
    node.parm('activepixels2').revertToDefaults()
    node.parm('paddedsize1').revertToDefaults()
    node.parm('paddedsize2').revertToDefaults()
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
    node.parm('path_mat').deleteAllKeyframes()
    node.parm('path_mat').set('`chs("_project")`/materials/`chs(\"_component\")`_mat.mat')
    node.parm('convertcolorspace').deleteAllKeyframes()
    node.parm('convertcolorspace').set(0)
    node.parm('coord_pos').deleteAllKeyframes()
    node.parm('coord_pos').set(0)
    node.parm('invert_pos').deleteAllKeyframes()
    node.parm('invert_pos').set(1)
    node.parm('coord_rot').deleteAllKeyframes()
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
        #node.parm('target_texture_size').deleteAllKeyframes()
        #node.parm('target_texture_size').setExpression('ch("target_polycount")*3')
    elif method == 3 :
        node.parm('reverse_norm').deleteAllKeyframes()
        node.parm('reverse_norm').set(1)
        node.parm('path_shader').deleteAllKeyframes()
        node.parm('path_shader').set('`chs("_project")`/shaders/SimpleLitVATSprite.shader')

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

# -----------------------------------------------------------------------------
#    Name: popcornfx(node, method)
#  Raises: N/A
# Returns: None
#    Desc: Engine setting.
# -----------------------------------------------------------------------------

def popcornfx(node,method):
    print('Using PopcornFX settings.')
    node.parm('coord_pos').deleteAllKeyframes()
    node.parm('coord_pos').set(1) # X Z Y
    node.parm('invert_pos').deleteAllKeyframes()
    node.parm('invert_pos').set(0) # +X +Y +Z
    node.parm('coord_rot').deleteAllKeyframes()
    node.parm('coord_rot').set(0) # -X -Y -Z +W
    node.parm('convertcolorspace').deleteAllKeyframes()
    node.parm('convertcolorspace').set(0) # Disable convert color space
    node.parm('pack_pscale').deleteAllKeyframes()
    node.parm('pack_pscale').set(0) # Disable pack scale to alpha
    node.parm('normalize_data').deleteAllKeyframes()
    node.parm('normalize_data').set(1) # Enable normalize data
    node.parm('enable_geo').deleteAllKeyframes()
    node.parm('enable_geo').set(1) # Enable geometry export
    node.parm('enable_pos').deleteAllKeyframes()
    node.parm('enable_pos').set(1) # Enable position map export
    node.parm('create_data').deleteAllKeyframes()
    node.parm('create_data').set(0) # Disable JSON export
    if method == 1 : # If rigid body
        node.parm('enable_rot').deleteAllKeyframes()
        node.parm('enable_rot').set(1) # Enable rotation map export
    elif method == 2 : # If fluid (changing topology)
        node.parm('enable_col').deleteAllKeyframes()
        node.parm('enable_col').set(1) # Enable color map export

