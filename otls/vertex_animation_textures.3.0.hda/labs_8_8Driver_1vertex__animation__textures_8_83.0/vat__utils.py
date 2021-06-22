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
        'Houdini FPS' : geo.attribValue("__fps")
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
#    Name: shader(node)
#  Raises: N/A
# Returns: None
#    Desc: Checks if shader exist and creates it otherwise.
# -----------------------------------------------------------------------------

def shader(node):
    path = os.path.abspath(node.evalParm('path_shader'))
    
    if not os.path.isfile(path) :
        engine = node.evalParm('engine') 
        mode = node.evalParm('mode')
        if   mode == 0:
            smode = 'soft'
            fname = 'Soft'
        elif mode == 1:
            smode = 'rigid'
            fname = 'Rigid'
        elif mode == 2:
            smode = 'fluid'
            fname = 'Fluid'
        elif mode == 3:
            smode = 'sprite'
            fname = 'Sprite'
        parm = smode +"_main_shader_"+str(engine)
        node.parm(parm).revertToDefaults()
        main_shader = node.evalParm(parm)
        parm = smode +"_forward_pass_shader_"+str(engine)
        node.parm(parm).revertToDefaults()
        forward_pass_shader = node.evalParm(parm)
        parm = smode +"_input_shader_"+str(engine)
        node.parm(parm).revertToDefaults()
        input_shader = node.evalParm(parm)
        
        if mode == 3:
            directory = os.path.dirname(path)
            main_shader_path = "%s/VAT_%s_SG.shadergraph" % (directory, fname)
            forward_pass_path = "%s/VAT_%s_SubGgraph.shadersubgraph" % (directory, fname)
            input_path = "%s/SimpleLitVAT%sInput.hlsl" % (directory, fname)
        else:
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
    path = os.path.abspath(node.evalParm('path_unity_mat'))
    if not os.path.isfile(path) :
        print("material doesn't exist")
        engine = node.evalParm('engine') 
        mode = node.evalParm('mode')
        if   mode == 0:
            smode = 'soft'
        elif mode == 1:
            smode = 'rigid'   
        elif mode == 2:
            smode = 'fluid' 
        elif mode == 3:
            smode = 'sprite'
        parm = smode +"_mat_"+str(engine)
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
    #shader(node)
    path = os.path.abspath(node.evalParm('path_unity_mat'))  
    if os.path.isfile(path) :
        engine       = str(node.evalParm('engine'))
        mode       = node.evalParm('mode')
        _numOfFrames = str(node.evalParm('num_frames'))
        _speed       = str(node.evalParm('speed'))
        _posMin      = str(node.evalParm('posminmax1'))
        _posMax      = str(node.evalParm('posminmax2'))
        _scaleMin    = str(node.evalParm('scaleminmax1'))
        _scaleMax    = str(node.evalParm('scaleminmax2'))
        _pivMin      = str(node.evalParm('pivminmax1'))
        _pivMax      = str(node.evalParm('pivminmax2'))
        _packNormSoft    = str(node.evalParm('packnorm_soft'))
        _packNormFluid    = str(node.evalParm('packnorm_fluid'))
        _splitPos   = str(node.evalParm('split_pos'))
        _paddedX = str(node.evalParm('paddedratio1'))
        _paddedY = str(node.evalParm('paddedratio2'))
        _packPscale  = str(node.evalParm('pack_pscale'))
        _normData    = str(node.evalParm('normalize_data'))
        _width       = str(node.evalParm('widthheight1'))
        _height      = str(node.evalParm('widthheight2'))        
        
        numOfFrames  = -1
        speed        = -1
        posMax       = -1
        posMin       = -1
        scaleMax     = -1
        scaleMin     = -1
        pivMax       = -1
        pivMin       = -1
        packNormSoft     = -1
        packNormFluid     = -1
        splitPos    = -1
        paddedX      = -1
        paddedY      = -1
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
                if "_posMin"    in line:
                    posMin      = num
                if "_posMax"    in line:
                    posMax      = num
                if "_scaleMin"  in line:
                    scaleMin    = num
                if "_scaleMax"  in line:
                    scaleMax    = num
                if "_pivMin"    in line:
                    pivMin      = num
                if "_pivMax"    in line:
                    pivMax      = num
                if "_packNormSoft"  in line:
                    packNormSoft    = num
                if "_packNormFluid"  in line:
                    packNormFluid    = num
                if "_splitPos" in line:
                    splitPos   = num
                if "_paddedX" in line:
                    paddedX = num
                if "_paddedY" in line:
                    paddedY = num
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
        if "_posMin"      != -1 :    
            list[posMin-1]      = '    - _posMin: '     +_posMin+'\n'
        if "_posMax"      != -1 :    
            list[posMax-1]      = '    - _posMax: '     +_posMax+'\n'
        if "_scaleMin"    != -1 :   
            list[scaleMin-1]    = '    - _scaleMin: '   +_scaleMin+'\n'
        if "_scaleMax"    != -1 :  
            list[scaleMax-1]    = '    - _scaleMax: '   +_scaleMax+'\n'
        if "_pivMin"      != -1 :   
            list[pivMin-1]      = '    - _pivMin: '     +_pivMin+'\n'
        if "_pivMax"      != -1 :  
            list[pivMax-1]      = '    - _pivMax: '     +_pivMax+'\n'
        if "_packNormSoft"    != -1 :  
            list[packNormSoft-1]    = '    - _packNormSoft: '   +_packNormSoft+'\n'
        if "_packNormSoft"    != -1 :  
            list[packNormFluid-1]    = '    - _packNormFluid: '   +_packNormFluid+'\n'
        if "_splitPos"    != -1 :  
            list[splitPos-1]    = '    - _splitPos: '   +_splitPos+'\n'
        if "_paddedX"    != -1 :  
            list[paddedX-1] = '    - _paddedX: '   +_paddedX+'\n'
        if "_paddedSizeY"    != -1 :  
            list[paddedY-1] = '    - _paddedY: '   +_paddedY+'\n'
        if "_packPscale"  != -1 :    
            list[packPscale-1]  = '    - _packPscale: ' +_packPscale+'\n'
        if "_normData"    != -1 :    
            list[normData-1]    = '    - _normData: '   +_normData+'\n'
        if "_width"      != -1 :   
            list[width-1]       = '    - _width: '      +_width+'\n'
        if "_height"      != -1 :  
            list[height-1]      = '    - _height: '     +_height+'\n'            
        open(path,'w').write(''.join(list))