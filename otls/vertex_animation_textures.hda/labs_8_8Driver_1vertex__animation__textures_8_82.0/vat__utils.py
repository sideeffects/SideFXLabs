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
    path            = os.path.abspath(node.evalParm('path_data'))
    directory       = os.path.dirname(path)
    #remove file if exist
    try:
        os.remove(path)
    except OSError:
        pass       
    #create directory if it does not exist    
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    engine       = str(node.evalParm('engine'))
    method       = node.evalParm('method')
    component    = node.evalParm('_component')        
    _numOfFrames = str(node.evalParm('num_frames'))
    _speed       = str(node.evalParm('speed'))
    _posMax      = str(node.evalParm('max_min_pos1'))
    _posMin      = str(node.evalParm('max_min_pos2'))
    _scaleMax    = str(node.evalParm('max_min_scale1'))
    _scaleMin    = str(node.evalParm('max_min_scale2'))
    _pivMax      = str(node.evalParm('max_min_piv1'))
    _pivMin      = str(node.evalParm('max_min_piv2'))
    _packNorm    = str(node.evalParm('pack_norm'))
    _doubleTex   = str(node.evalParm('double_textures'))
    _padPowTwo   = str(node.evalParm('padpowtwo'))
    _textureSizeX= str(node.evalParm('active_pixels1'))
    _textureSizeY= str(node.evalParm('active_pixels2'))
    _paddedSizeX = str(node.evalParm('padded_size1'))
    _paddedSizeY = str(node.evalParm('padded_size2'))
    _packPscale  = str(node.evalParm('pack_pscale'))
    _normData    = str(node.evalParm('normalize_data'))
    _width       = str(node.evalParm('width_height1'))
    _height      = str(node.evalParm('width_height2'))        
       
    data = {}
    if engine == 'unity':
        data[component] = []  
        data[component].append({ 
            '_numOfFrames'  : _numOfFrames,
            '_speed'        : _speed,
            '_posMax'       : _posMax,
            '_posMin'       : _posMin,
            '_scaleMax'     : _scaleMax,
            '_scaleMin'     : _scaleMin,
            '_pivMax'       : _pivMax,
            '_pivMin'       : _pivMin,
            '_packNorm'     : _packNorm,
            '_doubleTex'    : _doubleTex,
            '_padPowTwo'    : _padPowTwo,
            '_textureSizeX' : _textureSizeX,
            '_textureSizeY' : _textureSizeY,
            '_paddedSizeX' : _paddedSizeX,
            '_paddedSizeY' : _paddedSizeY,
            '_packPscale'   : _packPscale,
            '_normData'     : _normData,
            '_width'        : _width,
            '_height'       : _height         
        })
    else:
        data = []
        data.append({
            'Name' : "Soft",
            'numOfFrames'  : int(_numOfFrames),
            'speed'        : float(_speed),
            'posMax' : float(_posMax),
            'posMin' : float(_posMin),
            'scaleMax' : float(_scaleMax),
            'scaleMin' : float(_scaleMin),
            'pivMax' : float(_pivMax),
            'pivMin' : float(_pivMin),
            'packNorm' : int(_packNorm),
            'doubleTex' : int(_doubleTex),
            'padPowTwo' : int(_padPowTwo),
            'textureSizeX' : int(_textureSizeX),
            'textureSizeY' : int(_textureSizeY),
            'paddedSizeX' : int(_paddedSizeX),
            'paddedSizeY' : int(_paddedSizeY),
            'packPscale' : int(_packPscale),
            'normData' : int(_normData),
            'width' : float(_width),
            'height' : float(_height)
        })
    with open(path, 'w') as f:  
        json.dump(data, f, indent=4, sort_keys=True)
                  
# -----------------------------------------------------------------------------
#    Name: _project()
#  Raises: N/A
# Returns: None
#    Desc: Defines what the component should be called.
# -----------------------------------------------------------------------------

def _project(node):
    project           = node.evalParm("project")
    project_enable    = node.evalParm("enable_project")
    
    if project_enable == 1 and project != "" :
        project       = project           
    else :
        project       = hou.hscriptExpression('$JOB')  
    
    return project

# -----------------------------------------------------------------------------
#    Name: primcount(node)
#  Raises: N/A
# Returns: None
#    Desc: Detects the prim count based on the current frame.
# -----------------------------------------------------------------------------

def primcount(node):
    polyNode    = hou.node("objects/TEXTURE/OUT_MESH")
    geo         = polyNode.geometry()
    count       = geo.countPrimType('Poly')

    if count != 0:
        node.parm('target_polycount').deleteAllKeyframes()
        node.parm('target_polycount').set(count)

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
#    Name: shader(node)
#  Raises: N/A
# Returns: None
#    Desc: Checks if shader exist and creates it otherwise.
# -----------------------------------------------------------------------------

def shader(node):
    path = os.path.abspath(node.evalParm('path_shader'))
    
    if not os.path.isfile(path) :
        engine = node.evalParm('engine') 
        method = node.evalParm('method')
        if   method == 0:
            smethod = 'soft'
            fname = 'Soft'
        elif method == 1:
            smethod = 'rigid'
            fname = 'Rigid'
        elif method == 2:
            smethod = 'fluid'
            fname = 'Fluid'
        elif method == 3:
            smethod = 'sprite'
            fname = 'Sprite'
        parm = smethod +"_main_shader_"+str(engine)
        node.parm(parm).revertToDefaults()
        main_shader = node.evalParm(parm)
        parm = smethod +"_forward_pass_shader_"+str(engine)
        node.parm(parm).revertToDefaults()
        forward_pass_shader = node.evalParm(parm)
        parm = smethod +"_input_shader_"+str(engine)
        node.parm(parm).revertToDefaults()
        input_shader = node.evalParm(parm)
        
        directory = os.path.dirname(path)
        main_shader_path = "%s/SimpleLitVAT%s.shader" % (directory, fname)
        forward_pass_path = "%s/SimpleLitVAT%sForwardPass.hlsl" % (directory, fname)
        input_path = "%s/SimpleLitVAT%sInput.hlsl" % (directory, fname)

        
        print("path is: %s" % path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        if not os.path.isfile(main_shader_path):
            print("main shader doesn't exist")
            with open(main_shader_path,'w+') as f:
                f.write(main_shader)
        if not os.path.isfile(forward_pass_path):
            print("forward pass shader doesn't exist")
            with open(forward_pass_path,'w+') as f:
                f.write(forward_pass_shader)
        if not os.path.isfile(input_path):
            print("input shader doesn't exist")
            with open(input_path,'w+') as f:
                f.write(input_shader)

# -----------------------------------------------------------------------------
#    Name: mat_check(node)
#  Raises: N/A
# Returns: None
#    Desc: Checks if material exist and creates it otherwise.
# -----------------------------------------------------------------------------

def mat_check(node):
    path = os.path.abspath(node.evalParm('path_mat'))
    if not os.path.isfile(path) :
        print("material doesn't exist")
        engine = node.evalParm('engine') 
        method = node.evalParm('method')
        if   method == 0:
            smethod = 'soft'
        elif method == 1:
            smethod = 'rigid'   
        elif method == 2:
            smethod = 'fluid' 
        elif method == 3:
            smethod = 'sprite'
        parm = smethod +"_mat_"+str(engine)
        node.parm(parm).revertToDefaults()
        mat = node.evalParm(parm)  

        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            os.makedirs(directory)   
        with open(path,'w+') as f:
            f.write(mat)
    
    component   = str(node.evalParm('_component')) + '_mat'
    componentPath = '/mat/'+ component
    matNode     = hou.node(componentPath)
    if not matNode:
        matNode = hou.node('/mat').createNode('materialbuilder', component)
        matNode.moveToGoodPosition()
        matNode.setColor(hou.Color( (0.0, 0.6, 1.0) ) )   

# -----------------------------------------------------------------------------
#    Name: mat_update(node)
#  Raises: N/A
# Returns: None
#    Desc: Updates material values.
# -----------------------------------------------------------------------------

def mat_update(node):
    #print 'Updating Material'
    mat_check(node)
    shader(node)
    path = os.path.abspath(node.evalParm('path_mat'))  
    if os.path.isfile(path) :
        engine       = str(node.evalParm('engine'))
        method       = node.evalParm('method')
        _numOfFrames = str(node.evalParm('num_frames'))
        _speed       = str(node.evalParm('speed'))
        _posMax      = str(node.evalParm('max_min_pos1'))
        _posMin      = str(node.evalParm('max_min_pos2'))
        _scaleMax    = str(node.evalParm('max_min_scale1'))
        _scaleMin    = str(node.evalParm('max_min_scale2'))
        _pivMax      = str(node.evalParm('max_min_piv1'))
        _pivMin      = str(node.evalParm('max_min_piv2'))
        _packNorm    = str(node.evalParm('pack_norm'))
        _doubleTex   = str(node.evalParm('double_textures'))
        _padPowTwo   = str(node.evalParm('padpowtwo'))
        _textureSizeX= str(node.evalParm('active_pixels1'))
        _textureSizeY= str(node.evalParm('active_pixels2'))
        _paddedSizeX = str(node.evalParm('padded_size1'))
        _paddedSizeY = str(node.evalParm('padded_size2'))
        _packPscale  = str(node.evalParm('pack_pscale'))
        _normData    = str(node.evalParm('normalize_data'))
        _width       = str(node.evalParm('width_height1'))
        _height      = str(node.evalParm('width_height2'))        
        
        numOfFrames  = -1
        speed        = -1
        posMax       = -1
        posMin       = -1
        scaleMax     = -1
        scaleMin     = -1
        pivMax       = -1
        pivMin       = -1
        packNorm     = -1
        doubleTex    = -1
        padPowTwo    = -1
        textureSizeX = -1
        textureSizeY = -1
        paddedSizeX  = -1
        paddedSizeY  = -1
        packPscale   = -1
        normData     = -1
        width        = -1
        height       = -1        
        
        with open(path) as f:
            for num, line in enumerate(f, 1):
                if "_numOfFrames" in line:
                    numOfFrames = num
                if "_speed"     in line:
                    speed       = num
                if "_posMax"    in line:
                    posMax      = num
                if "_posMin"    in line:
                    posMin      = num
                if "_scaleMax"  in line:
                    scaleMax    = num
                if "_scaleMin"  in line:
                    scaleMin    = num
                if "_pivMax"    in line:
                    pivMax      = num
                if "_pivMin"    in line:
                    pivMin      = num
                if "_packNorm"  in line:
                    packNorm    = num
                if "_doubleTex" in line:
                    doubleTex   = num
                if "_padPowTwo" in line:
                    padPowTwo   = num
                if "_textureSizeX" in line:
                    textureSizeX= num
                if "_textureSizeY" in line:
                    textureSizeY= num
                if "_paddedSizeX" in line:
                    paddedSizeX = num
                if "_paddedSizeY" in line:
                    paddedSizeY = num
                if "_packPscale" in line:
                    packPscale  = num 
                if "_normData"  in line:
                    normData    = num
                if "_width"    in line:
                    width       = num
                if "_height"    in line:
                    height      = num                    

        list = open(path).readlines()
        if "_numOfFrames" != -1 :
            list[numOfFrames-1] = '    - _numOfFrames: '+_numOfFrames+'\n'
        if "_speed"       != -1 :    
            list[speed-1]       = '    - _speed: '      +_speed+'\n'
        if "_posMax"      != -1 :    
            list[posMax-1]      = '    - _posMax: '     +_posMax+'\n'
        if "_posMin"      != -1 :    
            list[posMin-1]      = '    - _posMin: '     +_posMin+'\n'
        if "_scaleMax"    != -1 :   
            list[scaleMax-1]    = '    - _scaleMax: '   +_scaleMax+'\n'
        if "_scaleMin"    != -1 :  
            list[scaleMin-1]    = '    - _scaleMin: '   +_scaleMin+'\n'
        if "_pivMax"      != -1 :   
            list[pivMax-1]      = '    - _pivMax: '     +_pivMax+'\n'
        if "_pivMin"      != -1 :  
            list[pivMin-1]      = '    - _pivMin: '     +_pivMin+'\n'
        if "_packNorm"    != -1 :  
            list[packNorm-1]    = '    - _packNorm: '   +_packNorm+'\n'
        if "_doubleTex"    != -1 :  
            list[doubleTex-1]    = '    - _doubleTex: '   +_doubleTex+'\n'
        if "_padPowTwo"    != -1 :  
            list[padPowTwo-1]    = '    - _padPowTwo: '   +_padPowTwo+'\n'
        if "_textureSizeX"    != -1 :  
            list[textureSizeX-1] = '    - _textureSizeX: '   +_textureSizeX+'\n'
        if "_textureSizeY"    != -1 :  
            list[textureSizeY-1] = '    - _textureSizeY: '   +_textureSizeY+'\n'
        if "_paddedSizeX"    != -1 :  
            list[paddedSizeX-1] = '    - _paddedSizeX: '   +_paddedSizeX+'\n'
        if "_paddedSizeY"    != -1 :  
            list[paddedSizeY-1] = '    - _paddedSizeY: '   +_paddedSizeY+'\n'
        if "_packPscale"  != -1 :    
            list[packPscale-1]  = '    - _packPscale: ' +_packPscale+'\n'
        if "_normData"    != -1 :    
            list[normData-1]    = '    - _normData: '   +_normData+'\n'
        if "_width"      != -1 :   
            list[width-1]       = '    - _width: '      +_width+'\n'
        if "_height"      != -1 :  
            list[height-1]      = '    - _height: '     +_height+'\n'            
        open(path,'w').write(''.join(list))
    
def padding_pow_two(node):
    size = hou.node(node.path() + "/textures/size")
    scale1 = hou.node(node.path() + "/textures/scale1")
    x = size.evalParm('size1')
    y = size.evalParm('size2')
    size = [x,y]
    padded_size = [4,4]
    max_size = max(x, y)
    
    for i in range(2):
        if size[i] > 4096:
            padded_size[i] = 8192
        elif size[i] > 2048:
            padded_size[i] = 4096
        elif size[i] > 1024:
            padded_size[i] = 2048
        elif size[i] > 512:
            padded_size[i] = 1024
        elif size[i] > 256:
            padded_size[i] = 512
        elif size[i] > 128:
            padded_size[i] = 256
        elif size[i] > 64:
            padded_size[i] = 128
        elif size[i] > 32:
            padded_size[i] = 64
        elif size[i] > 16:
            padded_size[i] = 32
        else:
            padded_size[i] = 16
        
    return padded_size 