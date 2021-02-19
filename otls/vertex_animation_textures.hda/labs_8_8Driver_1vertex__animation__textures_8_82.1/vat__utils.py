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
    _posMin      = str(node.evalParm('posminmax1'))
    _posMax      = str(node.evalParm('posminmax2'))
    _scaleMin    = str(node.evalParm('scaleminmax1'))
    _scaleMax    = str(node.evalParm('scaleminmax2'))
    _pivMin      = str(node.evalParm('pivminmax1'))
    _pivMax      = str(node.evalParm('pivminmax2'))
    _packNorm    = str(node.evalParm('pack_norm'))
    _doubleTex   = str(node.evalParm('double_textures'))
    _paddedX     = str(node.evalParm('paddedratio1'))
    _paddedY     = str(node.evalParm('paddedratio2'))
    _packPscale  = str(node.evalParm('pack_pscale'))
    _normData    = str(node.evalParm('normalize_data'))
    _width       = str(node.evalParm('widthheight1'))
    _height      = str(node.evalParm('widthheight2'))        

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
            '_paddedX'      : _paddedX,
            '_paddedY'      : _paddedY,
            '_packPscale'   : _packPscale,
            '_normData'     : _normData,
            '_width'        : _width,
            '_height'       : _height         
        })
    else:
        data = []
        data.append({
            'Name' : ['Soft', 'Rigid', 'Fluid', 'Sprite'][min(max(int(method), 0), 3)],
            'numOfFrames'  : int(_numOfFrames),
            'speed'        : float(_speed),
            'posMax'    : float(_posMax),
            'posMin'    : float(_posMin),
            'scaleMax'  : float(_scaleMax),
            'scaleMin'  : float(_scaleMin),
            'pivMax'    : float(_pivMax),
            'pivMin'    : float(_pivMin),
            'packNorm'  : int(_packNorm),
            'doubleTex' : int(_doubleTex),
            'paddedX'   : float(_paddedX),
            'paddedY'   : float(_paddedY),
            'packPscale' : int(_packPscale),
            'normData'  : int(_normData),
            'width'     : float(_width),
            'height'    : float(_height)
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
        
        if method == 3:
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
    #shader(node)
    path = os.path.abspath(node.evalParm('path_mat'))  
    if os.path.isfile(path) :
        engine       = str(node.evalParm('engine'))
        method       = node.evalParm('method')
        _numOfFrames = str(node.evalParm('num_frames'))
        _speed       = str(node.evalParm('speed'))
        _posMin      = str(node.evalParm('posminmax1'))
        _posMax      = str(node.evalParm('posminmax2'))
        _scaleMin    = str(node.evalParm('scaleminmax1'))
        _scaleMax    = str(node.evalParm('scaleminmax2'))
        _pivMin      = str(node.evalParm('pivminmax1'))
        _pivMax      = str(node.evalParm('pivminmax2'))
        _packNorm    = str(node.evalParm('pack_norm'))
        _doubleTex   = str(node.evalParm('double_textures'))
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
        packNorm     = -1
        doubleTex    = -1
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
                if "_packNorm"  in line:
                    packNorm    = num
                if "_doubleTex" in line:
                    doubleTex   = num
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
        if "_packNorm"    != -1 :  
            list[packNorm-1]    = '    - _packNorm: '   +_packNorm+'\n'
        if "_doubleTex"    != -1 :  
            list[doubleTex-1]    = '    - _doubleTex: '   +_doubleTex+'\n'
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

# -----------------------------------------------------------------------------
#    Name: build_popcornfx_renderer(node)
#  Raises: N/A
# Returns: None
#    Desc: Builds a PopcornFX renderer and stores it into clipboard.
# -----------------------------------------------------------------------------
def build_popcornfx_renderer(node):
    engine       = str(node.evalParm('engine'))
    method       = node.evalParm('method')
    component    = node.evalParm('_component')        
    numFrames    = str(node.evalParm('num_frames'))
    posMin       = str(node.evalParm('posminmax1'))
    posMax       = str(node.evalParm('posminmax2'))
    pivMin       = str(node.evalParm('pivminmax1'))
    pivMax       = str(node.evalParm('pivminmax2'))
    packNorm     = node.evalParm('pack_norm')
    padPow2      = node.evalParm('padpowtwo')
    paddedX      = str(node.evalParm('paddedratio1'))
    paddedY      = str(node.evalParm('paddedratio2'))
    packPscale   = str(node.evalParm('pack_pscale'))
    normData     = node.evalParm('normalize_data')
    enableGeo    = node.evalParm('enable_geo')
    pathGeo      = str(node.evalParm('path_geo'))
    enablePos    = node.evalParm('enable_pos')
    pathPos      = str(node.evalParm('path_pos'))
    enableRot    = node.evalParm('enable_rot')
    pathRot      = str(node.evalParm('path_rot'))
    enableCol    = node.evalParm('enable_col')
    pathCol      = str(node.evalParm('path_col'))
    enableNorm   = node.evalParm('enable_norm')
    pathNorm     = str(node.evalParm('path_norm'))
    length       = 1/node.evalParm('speed')
    
    outputNormals = (not packNorm) and enableNorm and (method == 0 or method == 2)

    defaultWhite = 'Library/PopcornFXCore/Materials/DefaultTextures/White.dds'
    defaultNormal = 'Library/PopcornFXCore/Materials/DefaultTextures/NMap_Flat.dds'
    if method > 2 :
        print('PopcornFX renderer : method not supported')
        return
    featureSetPath = ['Library/Houdini/Materials/VAT_Soft.pkma', 'Library/Houdini/Materials/VAT_Rigid.pkma', 'Library/Houdini/Materials/VAT_Fluid.pkma'][method]
    feature = ['VertexAnimation_Soft', 'VertexAnimation_Rigid', 'VertexAnimation_Fluid'][method]

    output = ''
    output += \
        'PKFX\n' +\
        'File = GeneratedFromSideFXLabs\n' +\
        'Version = 2.7.0.0;\n' +\
        \
        'CParticleNodeRendererMesh\t$D7A245F0\n'+\
        '{\n'+\
        '\tInputPins = {\n'  +\
        '\t\t"$ED658E02",\n' +\
        '\t\t"$A9A3B3C6",\n' +\
        '\t\t"$4C440259",\n' +\
        '\t\t"$92AC3294",\n' +\
        '\t\t"$89BE37AD",\n' +\
        '\t\t"$BF666592",\n' +\
        '\t\t"$080DFB07",\n' +\
        '\t\t"$5255127B",\n' +\
        '\t\t"$D8736519",\n' +\
        ('\t\t"$7F785A44",\n' if ((method == 0) or (method == 2)) else '') +\
        '\t\t"$CA882D03",\n' +\
        '\t\t"$E30C8889",\n' +\
        '\t\t"$F30C8889",\n' +\
        '\t\t"$3B21F68B",\n' +\
        '\t\t"$ABEBB67D",\n' +\
        '\t\t"$F3A0C720",\n' +\
        '\t\t"$9F8CF278",\n' +\
        '\t\t"$BCE23494",\n' +\
        '\t\t"$855BADAB",\n' +\
        '\t\t"$1E2B8FB1",\n' +\
        ('\t\t"$588B6EE0",\n' if method == 1 else '') +\
        ('\t\t"$588B6FE0",\n' if (method == 0 or method == 2) else '') +\
        ('\t\t"$1E4B471E",\n' if method == 1 else '') +\
        ('\t\t"$36765749",\n' if method == 2 else '') +\
        ('\t\t"$EC8D6D1B",\n' if normData else '') +\
        ('\t\t"$FC8D6D1B",\n' if padPow2 else '') +\
        '\t};\n' +\
        '\t	WorkspacePosition = int2(0, 0);\n' +\
        '\tFeatureSetPath = "{}";\n'.format(featureSetPath) +\
        '\tRendererFeatures = {\n' +\
        '\t\t"GeometryMesh",\n' +\
        '\t\t"Opaque",\n' +\
        '\t\t"Diffuse",\n' +\
        '\t\t"Lit",\n' +\
        '\t\t"MeshAtlas",\n' +\
        '\t\t"{}",\n'.format(feature) +\
        '\t\t"VertexAnimation_NormalizedData",\n' +\
        '\t\t"VertexAnimation_PadToPowerOf2",\n' +\
        '\t};\n' +\
        '}\n' +\
        \
        'CParticleNodePinIn\t$ED658E02\n' +\
        '{\n' +\
        '\tSelfName = "General.Position";\n' +\
        '\tType = float3;\n' +\
        '\tOwner = "$D7A245F0";\n' +\
        '\tBaseType = float3;\n' +\
        '\tConnectedPins = {\n' +\
        '\t\t"$3A7F3823",\n' +\
        '\t};\n' +\
        '}\n' +\
        \
        'CParticleNodePinIn\t$A9A3B3C6\n' +\
        '{\n' +\
        '\tSelfName = "General.Scale";\n' +\
        '\tType = float3;\n' +\
        '\tOwner = "$D7A245F0";\n' +\
        '\tBaseType = float3;\n' +\
        '\tValueF = float4(1.0, 1.0, 1.0, 1.0);\n' +\
        '}\n' +\
        \
        'CParticleNodePinIn\t$4C440259\n' +\
        '{\n' +\
        '\tSelfName = "General.Orientation";\n' +\
        '\tType = orientation;\n' +\
        '\tOwner = "$D7A245F0";\n' +\
        '\tBaseType = orientation;\n' +\
        '\tValueF = float4(0.0, 0.0, 0.0, 1.0);\n' +\
        '}\n' +\
        \
        'CParticleNodePinIn\t$92AC3294\n' +\
        '{\n' +\
        '\tSelfName = "General.Mesh";\n' +\
        '\tType = dataGeometry;\n' +\
        '\tVisible = false;\n' +\
        '\tOwner = "$D7A245F0";\n' +\
        '\tBaseType = dataGeometry;\n' +\
        '\tValueD = "{}";\n'.format(pathGeo) +\
        '}\n' +\
        \
        'CParticleNodePinIn\t$89BE37AD\n' +\
        '{\n' +\
        '\tSelfName = "Opaque.Type";\n' +\
        '\tType = int;\n' +\
        '\tVisible = false;\n' +\
        '\tOwner = "$D7A245F0";\n' +\
        '\tBaseType = int;\n' +\
        '}\n' +\
        \
        'CParticleNodePinIn\t$BF666592\n' +\
        '{\n' +\
        '\tSelfName = "Diffuse.DiffuseMap";\n' +\
        '\tType = dataImage;\n' +\
        '\tVisible = false;\n' +\
        '\tOwner = "$D7A245F0";\n' +\
        '\tBaseType = dataImage;\n' +\
        '\tValueD = "Library/PopcornFXCore/Materials/DefaultTextures/White.dds";\n' +\
        '}\n' +\
        \
        'CParticleNodePinIn\t$080DFB07\n' +\
        '{\n' +\
        '\tSelfName = "Diffuse.Color";\n' +\
        '\tType = float4;\n' +\
        '\tOwner = "$D7A245F0";\n' +\
        '\tBaseType = float4;\n' +\
        '\tValueF = float4(1.0, 1.0, 1.0, 1.0);\n' +\
        '}\n' +\
        \
        'CParticleNodePinIn\t$5255127B\n' +\
        '{\n' +\
        '\tSelfName = "{}.PositionMap";\n'.format(feature) +\
        '\tType = dataImage;\n' +\
        '\tVisible = false;\n' +\
        '\tOwner = "$D7A245F0";\n' +\
        '\tBaseType = dataImage;\n' +\
        '\tValueD = "{}";\n'.format(pathPos) +\
        '}\n' +\
        \
        'CParticleNodePinIn\t$D8736519\n' +\
        '{\n' +\
        '\tSelfName = "{}.NumFrames";\n'.format(feature) +\
        '\tType = int;\n' +\
        '\tVisible = false;\n' +\
        '\tOwner = "$D7A245F0";\n' +\
        '\tBaseType = int;\n' +\
        '\tValueI = int4({}, 0, 0, 0);\n'.format(numFrames) +\
        '}\n' +\
        \
        ('CParticleNodePinIn\t$7F785A44\n' +\
        '{\n' +\
        '\tSelfName = "{}.PackedData";\n'.format(feature) +\
        '\tType = bool;\n' +\
        '\tVisible = false;\n' +\
        '\tOwner = "$D7A245F0";\n' +\
        '\tBaseType = bool;\n' +\
        '\tValueB = bool4({}, false, false, false);\n'.format('true' if packNorm else 'false') +\
        '}\n' if ((method == 0) or (method == 2)) else '') +\
        \
        'CParticleNodePinIn\t$CA882D03\n' +\
        '{\n' +\
        '\tSelfName = "{}.Cursor";\n'.format(feature) +\
        '\tType = float;\n' +\
        '\tOwner = "$D7A245F0";\n' +\
        '\tConnectedPins = {\n' +\
        '\t\t"$39E613F8",\n' +\
        '\t};\n' +\
        '\tBaseType = float;\n' +\
        '}\n' +\
        \
        'CParticleNodePinIn\t$E30C8889\n' +\
        '{\n' +\
        '\tSelfName = "VertexAnimation_NormalizedData";\n' +\
        '\tType = bool;\n' +\
        '\tVisible = false;\n' +\
        '\tOwner = "$D7A245F0";\n' +\
        '\tBaseType = bool;\n' +\
        '\tValueB = bool4({}, false, false, false);\n'.format('true' if normData else 'false') +\
        '}\n' +\
        \
        'CParticleNodePinIn\t$F30C8889\n' +\
        '{\n' +\
        '\tSelfName = "VertexAnimation_PadToPowerOf2";\n' +\
        '\tType = bool;\n' +\
        '\tVisible = false;\n' +\
        '\tOwner = "$D7A245F0";\n' +\
        '\tBaseType = bool;\n' +\
        '\tValueB = bool4({}, false, false, false);\n'.format('true' if padPow2 else 'false') +\
        '}\n' +\
        \
        'CParticleNodePinIn	$3B21F68B\n' +\
        '{\n' +\
        '\tSelfName = "MeshAtlas";\n' +\
        '\tType = bool;\n' +\
        '\tVisible = false;\n' +\
        '\tOwner = "$D7A245F0";\n' +\
        '\tBaseType = bool;\n' +\
        '}\n' +\
        \
        'CParticleNodePinIn\t$ABEBB67D\n' +\
        '{\n' +\
        '\tSelfName = "Lit";\n' +\
        '\tType = bool;\n' +\
        '\tVisible = false;\n' +\
        '\tOwner = "$D7A245F0";\n' +\
        '\tBaseType = bool;\n' +\
        '\tValueB = bool4(true, false, false, false);\n' +\
        '}\n' +\
        \
        'CParticleNodePinIn\t$F3A0C720\n' +\
        '{\n' +\
        '\tSelfName = "Lit.NormalMap";\n' +\
        '\tType = dataImage;\n' +\
        '\tVisible = false;\n' +\
        '\tOwner = "$D7A245F0";\n' +\
        '\tBaseType = dataImage;\n' +\
        '\tValueD = "Library/PopcornFXCore/Materials/DefaultTextures/NMap_Flat.dds";\n' +\
        '}\n' +\
        \
        'CParticleNodePinIn\t$9F8CF278\n' +\
        '{\n' +\
        '\tSelfName = "Lit.CastShadows";\n' +\
        '\tType = bool;\n' +\
        '\tVisible = false;\n' +\
        '\tOwner = "$D7A245F0";\n' +\
        '\tBaseType = bool;\n' +\
        '}\n' +\
        \
        'CParticleNodePinIn\t$BCE23494\n' +\
        '{\n' +\
        '\tSelfName = "Lit.Roughness";\n' +\
        '\tType = float;\n' +\
        '\tVisible = false;\n' +\
        '\tOwner = "$D7A245F0";\n' +\
        '\tBaseType = float;\n' +\
        '\tValueF = float4(1.0, 0.5, 0.5, 0.5);\n' +\
        '}\n' +\
        \
        'CParticleNodePinIn\t$855BADAB\n' +\
        '{\n' +\
        '\tSelfName = "Lit.Metalness";\n' +\
        '\tType = float;\n' +\
        '\tVisible = false;\n' +\
        '\tOwner = "$D7A245F0";\n' +\
        '\tBaseType = float;\n' +\
        '}\n' +\
        \
        'CParticleNodePinIn\t$1E2B8FB1\n' +\
        '{\n' +\
        '\tSelfName = "Lit.RoughMetalMap";\n' +\
        '\tType = dataImage;\n' +\
        '\tVisible = false;\n' +\
        '\tOwner = "$D7A245F0";\n' +\
        '\tBaseType = dataImage;\n' +\
        '\tValueD = "Library/PopcornFXCore/Materials/DefaultTextures/White.dds";\n' +\
        '}\n' +\
        \
        ('CParticleNodePinIn\t$588B6EE0\n' +\
        '{\n' +\
        '\tSelfName = "VertexAnimation_Rigid.RotationMap";\n' +\
        '\tType = dataImage;\n' +\
        '\tVisible = false;\n' +\
        '\tOwner = "$D7A245F0";\n' +\
        '\tBaseType = dataImage;\n' +\
        '\tValueD = "{}";\n'.format(pathRot) +\
        '}\n' if method == 1 else '') +\
        \
        ('CParticleNodePinIn\t$588B6FE0\n' +\
        '{\n' +\
        '\tSelfName = "{}.NormalMap";\n'.format(feature) +\
        '\tType = dataImage;\n' +\
        '\tVisible = false;\n' +\
        '\tOwner = "$D7A245F0";\n' +\
        '\tBaseType = dataImage;\n' +\
        '\tValueD = "{}";\n'.format(pathNorm if outputNormals else defaultNormal) +\
        '}\n' if (method == 0 or method == 2) else '') +\
        \
        ('CParticleNodePinIn\t$1E4B471E\n' +\
        '{\n' +\
        '\tSelfName = "VertexAnimation_Rigid.BoundsPivot";\n' +\
        '\tType = float2;\n' +\
        '\tVisible = false;\n' +\
        '\tOwner = "$D7A245F0";\n' +\
        '\tBaseType = float2;\n' +\
        '\tValueF = float4({}, {}, 0.0, 0.0);\n'.format(pivMin, pivMax) +\
        '}\n' if method == 1 else '') +\
        \
        ('CParticleNodePinIn\t$36765749\n' +\
        '{\n' +\
        '\tSelfName = "VertexAnimation_Fluid.ColorMap";\n' +\
        '\tType = dataImage;\n' +\
        '\tOwner = "$510DD54D";\n' +\
        '\tBaseType = dataImage;\n' +\
        '\tValueD = "{}";\n'.format(pathCol if enableCol else defaultWhite) +\
        '\t}' if method == 2 else '') +\
        \
         ('CParticleNodePinIn\t$EC8D6D1B\n' +\
        '{\n' +\
        '\tSelfName = "VertexAnimation_NormalizedData.BoundsPosition";\n' +\
        '\tType = float2;\n' +\
        '\tVisible = false;\n' +\
        '\tOwner = "$D7A245F0";\n' +\
        '\tBaseType = float2;\n' +\
        '\tValueF = float4({}, {}, 0.0, 0.0);\n'.format(posMin, posMax) +\
        '}\n' if normData else '') +\
        \
        ('CParticleNodePinIn\t$FC8D6D1B\n' +\
        '{\n' +\
        '\tSelfName = "VertexAnimation_PadToPowerOf2.PaddedRatio";\n' +\
        '\tType = float2;\n' +\
        '\tVisible = false;\n' +\
        '\tOwner = "$D7A245F0";\n' +\
        '\tBaseType = float2;\n' +\
        '\tValueF = float4({}, {}, 0.0, 0.0);\n'.format(paddedX, paddedY) +\
        '}\n' if padPow2 else '')+\
        \
        'CParticleNodeTemplate\t$CF13AF03\n' +\
        '{\n' +\
        '\tOutputPins = {\n' +\
        '\t\t"$39E613F8",\n' +\
        '\t};\n' +\
        '\tWorkspacePosition = int2(-440, 280);\n' +\
        '\tSubGraphFilePath = "Library/PopcornFXCore/Templates/Core.pkfx";\n' +\
        '\tSubGraphName = "self.lifeRatio";\n' +\
        '}\n' +\
        \
        'CParticleNodePinOut\t$39E613F8\n' +\
        '{\n' +\
        '\tSelfName = "LifeRatio";\n' +\
        '\tOwner = "$CF13AF03";\n' +\
        '\tConnectedPins = {\n' +\
        '\t\t"$CA882D03",\n' +\
        '\t};\n' +\
        '}\n' +\
        \
        'CParticleNodeTemplate\t$62F4224C\n' +\
        '{\n' +\
        '\tExecStage = Spawn;\n' +\
        '\tInputPins = {\n' +\
        '\t\t"$B2167C92",\n' +\
        '\t\t"$487B49E7",\n' +\
        '\t};\n' +\
        '\tOutputPins = {\n' +\
        '\t\t"$3A7F3823",\n' +\
        '\t};\n' +\
        '\tWorkspacePosition = int2(-440, 0);\n' +\
        '\tSubGraphFilePath = "Library/PopcornFXCore/Templates/Core.pkfx";\n' +\
        '\tSubGraphName = "local position to world";\n' +\
        '\t}\n' +\
        \
        '\tCParticleNodePinIn\t$B2167C92\n' +\
        '\t{\n' +\
        '\t\tSelfName = "Position";\n' +\
        '\t\tType = float3;\n' +\
        '\t\tOwner = "$62F4224C";\n' +\
        '\t\tBaseType = float3;\n' +\
        '\t\tValueF = float4(0.0, 0.0, 0.0, 0.0);\n' +\
        '\t}\n' +\
        \
        '\tCParticleNodePinIn	$487B49E7\n' +\
        '\t{\n' +\
        '\t\tSelfName = "ApplyScale";\n' +\
        '\t\tType = bool;\n' +\
        '\t\tVisible = false;\n' +\
        '\t\tOwner = "$62F4224C";\n' +\
        '\t\tBaseType = bool;\n' +\
        '\t}\n' +\
        \
        '\tCParticleNodePinOut	$3A7F3823\n' +\
        '\t{\n' +\
        '\t\tSelfName = "Position";\n' +\
        '\t\tType = float3;\n' +\
        '\t\tOwner = "$62F4224C";\n' +\
        '\t\tBaseType = float3;\n' +\
        '\t\tConnectedPins = {\n' +\
        '\t\t\t"$ED658E02",\n' +\
        '\t\t};\n' +\
        '\t}\n' +\
        \
        '\tCParticleNodeSetLife	$88F280DA\n' +\
        '\t{\n' +\
        '\t\tInputPins = {\n' +\
        '\t\t\t"$DC41E5E5",\n' +\
        '\t\t};\n' +\
        '\t\tWorkspacePosition = int2(-440, -180);\n' +\
        '\t}\n' +\
        \
        '\tCParticleNodePinIn\t$DC41E5E5\n' +\
        '\t{\n' +\
        '\t\tSelfName = "Life";\n' +\
        '\t\tType = float;\n' +\
        '\t\tOwner = "$88F280DA";\n' +\
        '\t\tBaseType = float;\n' +\
        '\t\tValueF = float4({}, 1.0, 1.0, 1.0);\n'.format(length) +\
        '\t}\n'

    hou.ui.copyTextToClipboard(output)
    print('PopcornFX renderer copied to clipboard')