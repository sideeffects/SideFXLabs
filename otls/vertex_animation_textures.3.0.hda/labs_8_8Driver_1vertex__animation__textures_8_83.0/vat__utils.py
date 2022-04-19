# =============================================================================
# IMPORTS
# =============================================================================

import hou
import os
import json

# =============================================================================
# FUNCTIONS
# =============================================================================

# -----------------------------------------------------------------------------
#    Name: data(node)
#  Raises: N/A
# Returns: None
#    Desc: Updates material values.
# -----------------------------------------------------------------------------

def data(node):
    #print 'Updating Json'
    path            = os.path.abspath(node.evalParm('path_datafile'))
    directory       = os.path.dirname(path)
    #remove file if exist
    try:
        os.remove(path)
    except OSError:
        pass
    #create directory if it does not exist
    if not os.path.exists(directory):
        os.makedirs(directory)

    geo = node.node("objects/TEXTURE/OUT_BOUNDS_IN_ENGINE").geometry()

    data = []
    data.append({
        'Name' : 'VAT',
        'Axis System' : geo.attribValue("__coord_sys"),
        'Bound Max X' : geo.attribValue("__converted_max_x"),
        'Bound Max Y' : geo.attribValue("__converted_max_y"),
        'Bound Max Z' : geo.attribValue("__converted_max_z"),
        'Bound Min X' : geo.attribValue("__converted_min_x"),
        'Bound Min Y' : geo.attribValue("__converted_min_y"),
        'Bound Min Z' : geo.attribValue("__converted_min_z"),
        'Houdini FPS' : geo.attribValue("__fps"),
        'Two Position Textures' : node.evalParm('splitpos')
    })

    with open(path, 'w') as file:
        json.dump(data, file, indent=4, sort_keys=True)


# -----------------------------------------------------------------------------
#    Name: _depth(node)
#  Raises: N/A
# Returns: None
#    Desc: Checks if shader exist and creates it otherwise.
# -----------------------------------------------------------------------------

def _depth(node):
    depth       = node.evalParm('depth')
    usebwpoints = node.evalParm('usebwpoints')
    ntype = 7
    stype = 'float32'
    if (depth == 0 or depth == 'int8') and usebwpoints == 0 :
        ntype = 0
        stype = 'int8'
    if (depth == 0 or depth == 'int8') and usebwpoints == 1 :
        ntype = 1
        stype = 'int8bw'
    if (depth == 1 or depth == 'int16')and usebwpoints == 0 :
        ntype = 2
        stype = 'int16'
    if (depth == 1 or depth == 'int16') and usebwpoints == 1 :
        ntype = 3
        stype = 'int16bw'
    if (depth == 2 or depth == 'int32') and usebwpoints == 0 :
        ntype = 4
        stype = 'int32'
    if (depth == 2 or depth == 'int32') and usebwpoints == 1 :
        ntype = 5
        stype = 'int32bw'
    if (depth == 3 or depth == 'float16'):
        ntype = 6
        stype = 'float16'
    if (depth == 4 or depth == 'float32'):
        ntype = 7
        stype = 'float32'

    return ntype


# -----------------------------------------------------------------------------
#    Name: mat_check(node)
#  Raises: N/A
# Returns: None
#    Desc: Checks if material exist and creates it otherwise.
# -----------------------------------------------------------------------------

def mat_check(node):

    path = os.path.abspath(node.evalParm('path_unitymat'))
    directory = os.path.dirname(path)

    #remove file if exist
    try:
        os.remove(path)
    except OSError:
        pass
    #create directory if it does not exist
    if not os.path.exists(directory):
        os.makedirs(directory)

    if not os.path.isfile(path):

        mode = node.evalParm('mode')

        if   mode == 0:
            smode = 'soft'
        elif mode == 1:
            smode = 'rigid'
        elif mode == 2:
            smode = 'fluid'
        elif mode == 3:
            smode = 'sprite'

        parm = "mat_unity_" + smode
        node.parm(parm).revertToDefaults()
        mat = node.evalParm(parm)

        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(path,'w+') as f:
            f.write(mat)


# -----------------------------------------------------------------------------
#    Name: mat_update(node)
#  Raises: N/A
# Returns: None
#    Desc: Updates material values.
# -----------------------------------------------------------------------------

def mat_update(node):

    mat_check(node)

    path = os.path.abspath(node.evalParm('path_unitymat'))

    geo = node.node("objects/TEXTURE/OUT_BOUNDS_IN_ENGINE").geometry()

    if os.path.isfile(path) :

        _mName      = node.evalParm("assetname") + '_mat'
        _boundMaxX  = str(geo.attribValue("__converted_max_x"))
        _boundMaxY  = str(geo.attribValue("__converted_max_y"))
        _boundMaxZ  = str(geo.attribValue("__converted_max_z"))
        _boundMinX  = str(geo.attribValue("__converted_min_x"))
        _boundMinY  = str(geo.attribValue("__converted_min_y"))
        _boundMinZ  = str(geo.attribValue("__converted_min_z"))
        _houdiniFPS = str(geo.attribValue("__fps"))
        _frameCount = str(node.evalParm("f2") - node.evalParm("f1") + 1)

        mName       = -1
        boundMaxX   = -1
        boundMaxY   = -1
        boundMaxZ   = -1
        boundMinX   = -1
        boundMinY   = -1
        boundMinZ   = -1
        houdiniFPS  = -1
        frameCount  = -1

        with open(path) as f:

            for num, line in enumerate(f, 1):

                if "ASSET_NAME"  in line:
                    mName      = num

                if "_boundMaxX"  in line:
                    boundMaxX  = num

                if "_boundMaxY"  in line:
                    boundMaxY  = num

                if "_boundMaxZ"  in line:
                    boundMaxZ  = num

                if "_boundMinX"  in line:
                    boundMinX  = num

                if "_boundMinY"  in line:
                    boundMinY  = num

                if "_boundMinZ"  in line:
                    boundMinZ  = num

                if "_houdiniFPS" in line:
                    houdiniFPS = num

                if "_frameCount" in line:
                    frameCount = num

        list = open(path).readlines()

        if "m_Name"      != -1:
            list[mName-1]      = '  m_Name: ' + _mName +'\n'

        if "_boundMaxX"  != -1:
            list[boundMaxX-1]  = '    - _boundMaxX: ' + _boundMaxX +'\n'

        if "_boundMaxY"  != -1:
            list[boundMaxY-1]  = '    - _boundMaxY: ' + _boundMaxY +'\n'

        if "_boundMaxZ"  != -1:
            list[boundMaxZ-1]  = '    - _boundMaxZ: ' + _boundMaxZ +'\n'

        if "_boundMinX"  != -1:
            list[boundMinX-1]  = '    - _boundMinX: ' + _boundMinX +'\n'

        if "_boundMinY"  != -1:
            list[boundMinY-1]  = '    - _boundMinY: ' + _boundMinY +'\n'

        if "_boundMinZ"  != -1:
            list[boundMinZ-1]  = '    - _boundMinZ: ' + _boundMinZ +'\n'

        if "_houdiniFPS" != -1:
            list[houdiniFPS-1] = '    - _houdiniFPS: ' + _houdiniFPS +'\n'

        if "_frameCount" != -1:
            list[frameCount-1] = '    - _frameCount: ' + _frameCount +'\n'

        open(path,'w').write(''.join(list))