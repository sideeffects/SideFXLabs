# =============================================================================
# IMPORTS
# =============================================================================

import os
import re
import hou
import datetime
import toolutils
node = hou.pwd()
oppath = toolutils.createModuleFromSection("oppath",node.type(),"oppath.py")
#from LaidlawFX import oppath

# =============================================================================
# GLOBAL VARIABLES
# =============================================================================

hip             = hou.getenv("HIP")
job             = hou.getenv("JOB")
hipname         = hou.getenv("HIPNAME",'default-0001')
user            = hou.getenv("USER",'username')
branch          = hou.getenv("DATA_BRANCH", 'branch')
proj            = hou.getenv("WORLD_NAME", 'main')

# =============================================================================
# FUNCTIONS
# =============================================================================

# -----------------------------------------------------------------------------
#    Name: dir_check(path)
#  Raises: N/A
# Returns: None
#    Desc: Hqueue Rop - project path.  
# -----------------------------------------------------------------------------

def dir_check(path):
    path        = os.path.normpath(path)
    if not os.path.exists(path):
        os.makedirs(path)
    return path
# -----------------------------------------------------------------------------
#    Name: path_create(dirlist,filelist=None)
#  Raises: N/A
# Returns: None
#    Desc: Combines file paths.  
# -----------------------------------------------------------------------------

def path_create(dirlist,filelist=None):
    global hip
    dirpath         = hip    
    if dirlist :       
        dirpath     = os.path.join(*dirlist)
        dirpath     = os.path.normpath(dirpath)
    if filelist :
        file        = ''.join(filelist)    
        path        = dirpath + file
    else :
        path        = dirpath
    path            = os.path.normpath(path) #.replace("\\",'/')
    return path
    
# -----------------------------------------------------------------------------
#    Name: file_type(node)
#  Raises: N/A
# Returns: None
#    Desc: Figures out Load and Write Frame 
# -----------------------------------------------------------------------------

def file_type(node, file_type):
    #default extension
    if   file_type == 'geo':
        ext         = '.bgeo.sc'
    elif file_type == 'img':
        ext         = '.exr'
    if node.parm("file_type") :
        ext         = node.evalParm("file_type")
    return ext
      
# -----------------------------------------------------------------------------
#    Name: frame(node)
#  Raises: N/A
# Returns: None
#    Desc: Figures out Load and Write Frame 
# -----------------------------------------------------------------------------

def frame(node):
    fWrite          ='.0001'
    fLoad           ='.0001'
    if node :
        f           = hou.frame()
        if node.parm("frame") :
            f       = float(    node.evalParm("frame"))       
            
        timeRange   = hou.playbar.timelineRange()
        if node.parm("f1") :        
            f1      = float(int(node.evalParm("f1"))  )
        else :
            f1      = timeRange[0]        
        if node.parm("f2") :    
            f2      = float(int(node.evalParm("f2"))  )
        else :
            f2      = timeRange[1]        
        if node.parm("f3") :    
            f3      = float(    node.evalParm("f3")   )
        else :
            f       = 1        

        fClampWrite = max(min(hou.frame(), f2), f1)
        fClampLoad  = max(min(f,       f2), f1)
        fIntWrite   = "."+ str(int(float(fClampWrite))).zfill(4)
        fIntLoad    = "."+ str(int(float(fClampLoad ))).zfill(4)
        fDecWrite   = str(fClampWrite % 1).strip("0")
        fDecLoad    = str(fClampLoad  % 1).strip("0")
        fWrite      = fIntWrite + ( "" if ( float(fClampWrite) % 1 == 0 ) else fDecWrite )
        fLoad       = fIntLoad  + ( "" if ( float(fClampLoad ) % 1 == 0 ) else fDecLoad  )

    return fWrite, fLoad    
    
# -----------------------------------------------------------------------------
#    Name: asset(node)
#  Raises: N/A
# Returns: None
#    Desc: Defines the asset to be worked on.
# -----------------------------------------------------------------------------

def asset(node):
    name        = 'asset'
    if node and node.parm("asset") :
        default     = node.parent().name()    
        name        = node.evalParm("asset")
        enable      = node.evalParm("asset_enable")
        
        if enable == 1 and name != "" :
            name    = name           
        else :
            name    = default           
                
        name        = re.sub('[. ]','',name)    

    return name    
    
# -----------------------------------------------------------------------------
#    Name: component(node)
#  Raises: N/A
# Returns: None
#    Desc: Defines what component of the asset you are working on.
# -----------------------------------------------------------------------------

def component(node):
    name        = 'component'
    if node and node.parm("component") :    
        default     = node.name()    
        name        = node.evalParm("component")
        enable      = node.evalParm("component_enable")
        
        if enable == 1 and name != "" :
            name    = name           
        else :
            name    = default            
                
        name        = re.sub('[. ]','',name)    

    return name     
    
# -----------------------------------------------------------------------------
#    Name: component(node)
#  Raises: N/A
# Returns: None
#    Desc: Defines what component of the asset you are working on.
# -----------------------------------------------------------------------------

def version(node):
    global hipname
    ver         = hipname
    if node.parm("ver") :
        ver     = node.evalParm("ver")
        if ver == '' :
            ver = hipname
          
    return ver

# -----------------------------------------------------------------------------
#    Name: project(node)
#  Raises: N/A
# Returns: None
#    Desc: Allows you to change the root of the project.
# -----------------------------------------------------------------------------

def project(node):
    global hip
    global job
    global branch
    global proj         
    dirlist     =[hip,branch,proj]    
    path        =path_create(dirlist)    
    return path      

# -----------------------------------------------------------------------------
#    Name: hq_job_name(node)
#  Raises: N/A
# Returns: None
#    Desc: Hqueue Rop - project path.
#          '$JOB/$ASSET/$COMPONENT/$HIPNAME'
# -----------------------------------------------------------------------------

def hq_job_name(node):
    global hipname
    process_node = oppath.node_input(node)

    #print process_node.path()

    filelist    =['Asset : ',asset(process_node), ' Component : ',component(process_node), ' Hipname : ',hipname, ' Submitted : ',datetime.datetime.today().strftime('%Y-%m-%d %H:%M')]    
    job_name    = ''.join(filelist)  

    name        = node.evalParm("job")
    enable      = node.evalParm("job_enable")
    
    if enable == 1 and name != "" :
        job_name= name           
                        
    return job_name

# -----------------------------------------------------------------------------
#    Name: hq_project_path(node)
#  Raises: N/A
# Returns: None
#    Desc: Hqueue Rop - project path.
#          '$JOB/$ASSET/$COMPONENT/$HIPNAME'
# -----------------------------------------------------------------------------

def hq_project_path(node):
    global hipname    
    dirlist     =[project(node), asset(node), component(node), hipname]    
    path        =path_create(dirlist)    
    return path    

# -----------------------------------------------------------------------------
#    Name: hq_hip(node)
#  Raises: N/A
# Returns: None
#    Desc: Hqueue Rop - project path.
#          '$JOB/$ASSET/$COMPONENT/$HIPNAME'
# -----------------------------------------------------------------------------

def hq_hip(node):
    global hipname
    dirlist     =[hq_project_path(node)]
    filelist    =['/',hipname,'.hip']    
    path        =path_create(dirlist,filelist)     
    return path         
    
# -----------------------------------------------------------------------------
#    Name: hq_input_ifd(node)
#  Raises: N/A
# Returns: None
#    Desc: Hqueue Rop - ifd path.
#          '$HIP/ifds/$HIPNAME.$F.ifd'
# -----------------------------------------------------------------------------

def hq_input_ifd(node):   
    dirlist     =[hq_project_path(node),'ifd']    
    filelist    =['/','ifd','.$F4','.ifd']    
    path        =path_create(dirlist,filelist)     
    return path 
    
# -----------------------------------------------------------------------------
#    Name: hq_outputifd(node)
#  Raises: N/A
# Returns: None
#    Desc: Hqueue Rop - ifd path.  
#          '$HIP/ifds/$HIPNAME.$F.ifd'
# -----------------------------------------------------------------------------

def hq_outputifd(node):       
    dirlist     =[hq_project_path(node),'ifd']    
    filelist    =['/','ifd','.$F4','.ifd']    
    path        =path_create(dirlist,filelist)    
    return path  
# -----------------------------------------------------------------------------
#    Name: soho_diskfile(node)
#  Raises: N/A
# Returns: None
#    Desc: Mantra Rop - ifd path.  
#          '$HIP/mantra.ifd'
# -----------------------------------------------------------------------------

def soho_diskfile(node):   
    path        =hq_input_ifd(node)
    return path 
    
# -----------------------------------------------------------------------------
#    Name: vm_tmpsharedstorage(node)
#  Raises: N/A
# Returns: None
#    Desc: Mantra Rop - temp shared storage path.  
#          '$HIP/ifds/storage'
# -----------------------------------------------------------------------------

def vm_tmpsharedstorage(node):   
    dirlist     =[hq_project_path(node),'ifds','storage']    
    path        =path_create(dirlist)    
    return path 
    
# -----------------------------------------------------------------------------
#    Name: vm_tmplocalstorage(node)
#  Raises: N/A
# Returns: None
#    Desc: Mantra Rop - temp local storage path.  
#          '$HOUDINI_TEMP_DIR/ifds/storage'
# -----------------------------------------------------------------------------

def vm_tmplocalstorage(node):   
    dirlist     =[hou.getenv("HOUDINI_TEMP_DIR"),'ifds','storage']    
    path        =path_create(dirlist)    
    return path     
# -----------------------------------------------------------------------------
#    Name: vm_picture(node)
#  Raises: N/A
# Returns: None
#    Desc: Mantra Rop - render path.  
#          '$HIP/render/$HIPNAME.$OS.$F4.exr'
# -----------------------------------------------------------------------------

def vm_picture(node):
    ext = file_type(node, 'img')
    if ext == 'md' or ext == 'ip' :
        path = ext    
    else :        
        dirlist     =[hq_project_path(node),'render']    
        filelist    =['/','render',frame(node)[0],ext]    
        path        =path_create(dirlist,filelist) 
    return path   

# -----------------------------------------------------------------------------
#    Name: vm_filename_plane(node,i)
#  Raises: N/A
# Returns: None
#    Desc: Mantra Rop - image plane path(s). 
#          '$HIP/render/$HIPNAME.$OS.$F4.exr'
# -----------------------------------------------------------------------------

def vm_filename_plane(node,parm):
    i           =re.match('.*?([0-9]+)$', parm).group(1)
    channel     =str(node.evalParm("vm_variable_plane"+i))
    dirlist     =[hq_project_path(node),'render',channel]    
    filelist    =['/',channel,frame(node)[0],'.exr']    
    path        =path_create(dirlist,filelist)    
    return path   

# -----------------------------------------------------------------------------
#    Name: picture(node)
#  Raises: N/A
# Returns: None
#    Desc: Opengl Rop - render path. 
#          '$HIP/render/$HIPNAME.$OS.$F4.exr'
# -----------------------------------------------------------------------------

def picture(node):
    ext = file_type(node, 'img')
    if ext == 'md' or ext == 'ip' :
        path = ext    
    else :     
        dirlist     =[hq_project_path(node),'flip']    
        filelist    =['/','flip',frame(node)[0],ext]    
        path        =path_create(dirlist,filelist) 
    return path  

# -----------------------------------------------------------------------------
#    Name: copout(node)
#  Raises: N/A
# Returns: None
#    Desc: Composite Rop - render path.  
#          '$HIP/render/$HIPNAME.$OS.$F4.exr'
# -----------------------------------------------------------------------------

def copoutput(node): 
    ext = file_type(node, 'img')
    if ext == 'md' or ext == 'ip' :
        path = ext    
    else :     
        dirlist     =[hq_project_path(node),'comp']    
        filelist    =['/','comp',frame(node)[0],ext]    
        path        = path_create(dirlist,filelist) 
    return path   

# -----------------------------------------------------------------------------
#    Name: copaux(node)
#  Raises: N/A
# Returns: None
#    Desc: Composite Rop - render path.  
#          '$HIP/copaux#/copaux#.$F4.exr'
# -----------------------------------------------------------------------------

def copaux(node,parm):
    i           =re.match('.*?([0-9]+)$', parm).group(1)
    channel     =str("copaux"+i)
    ext = file_type(node, 'img')
    if ext == 'md' or ext == 'ip' :
        path = ext    
    else :     
        dirlist     =[hq_project_path(node),channel]    
        filelist    =['/',channel,frame(node)[0],ext]    
        path        = path_create(dirlist,filelist) 
    return path  
             
# -----------------------------------------------------------------------------
#    Name: vm_dcmfilename(node)
#  Raises: N/A
# Returns: None
#    Desc: Mantra Rop - deep camera path. 
#          '$HIP/dcm.rat'
# -----------------------------------------------------------------------------

def vm_dcmfilename(node):   
    dirlist     =[hq_project_path(node),'dcm']    
    filelist    =['/','dcm','.rat']    
    path        =path_create(dirlist,filelist)    
    return path

# -----------------------------------------------------------------------------
#    Name: vm_dsmfilename(node)
#  Raises: N/A
# Returns: None
#    Desc: Mantra Rop - deep shadow path.  
#          '$HIP/dsm.rat'
# -----------------------------------------------------------------------------

def vm_dsmfilename(node):   
    dirlist     =[hq_project_path(node),'dsm']    
    filelist    =['/','dsm','.rat']    
    path        =path_create(dirlist,filelist)    
    return path       

# -----------------------------------------------------------------------------
#    Name: dopout(node)
#  Raises: N/A
# Returns: None
#    Desc: Dynamic Rop - render path.  
#          '$HIP/sim/$HIPNAME.$OS.$SF.sim'
# -----------------------------------------------------------------------------

def dopoutput(node):   
    dirlist     =[hq_project_path(node),'sim']    
    filelist    =['/','sim','.$SF','.sim']    
    path        =path_create(dirlist,filelist).replace("\\",'/')   
    return path      

# -----------------------------------------------------------------------------
#    Name: sopout(node)
#  Raises: N/A
# Returns: None
#    Desc: Geometry Rop - render path.  
#          '$HIP/geo/$HIPNAME.$OS.$F.bgeo.sc'
# -----------------------------------------------------------------------------

def sopoutput(node):   
    dirlist     =[hq_project_path(node),'geo']    
    filelist    =['/','geo','.$F4','.bgeo.sc']    
    path        =path_create(dirlist,filelist).replace("\\",'/')    
    return path    

# -----------------------------------------------------------------------------
#    Name: file_write(node)
#  Raises: N/A
# Returns: None
#    Desc: File Cache Sop - render path.  
#          '$HIP/geo/$HIPNAME.$OS.$F.bgeo.sc'
# -----------------------------------------------------------------------------

def file(node):          
    path        =sopoutput(node)   
    return path 

# -----------------------------------------------------------------------------
#    Name: file_write(node)
#  Raises: N/A
# Returns: None
#    Desc: File Cache Sop - render path.  
#          '$HIP/geo/$HIPNAME.$OS.$F.bgeo.sc'
# -----------------------------------------------------------------------------

def file_load(node):          
    dirlist     =[project(node), asset(node), component(node), version(node),'geo']    
    filelist    =['/','geo',frame(node)[0],'.bgeo.sc']    
    path        =path_create(dirlist,filelist)    
    return path       



# -----------------------------------------------------------------------------
#    Name: MakeList(node)
#  Raises: N/A
# Returns: None
#    Desc: Search directory for rendered folders
# -----------------------------------------------------------------------------

def file_version(node):
    try:
        dirlist     =[project(node), asset(node), component(node)]      
        path        =path_create(dirlist)        
        dirList     = os.listdir(path)
        dirs        = []
        for dirName in dirList:
                      fullPath = os.path.normpath(os.path.join(path, dirName))
                      if os.path.isdir(fullPath):
                                     dirs += [dirName, dirName]
        
        return dirs
    except WindowsError:
        return ["ElementNotRendered", "ElementNotRendered"]
    except :
        return ["ElementNotRendered", "ElementNotRendered"]  