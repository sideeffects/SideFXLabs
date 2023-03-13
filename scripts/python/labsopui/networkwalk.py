import nodegraphview as ngv
import hou
## Declare pivot so it can be used as a global variable
pivot = None

##########################################################
## Functions associated with creating Hotkeys
##########################################################
def add_actions():
    """ Adds actions add creates default Hotkey assignments.
    """
    # Declare directions.
    dirs = ('Up','Down','Left','Right')  
    
    ## Key mapping
    key_dict = {'Up':'PageUp',
                'Down':'PageDown',
                'Left':'Insert',
                'Right':'Home'}
     
    # Remove hot key if it exists.  
    remove_actions(dirs=dirs,remove=False)
    
    # Remove PageUp and PageDown
    hou.hotkeys.removeAssignment('h.pane.wsheet.up','PageUp')
    hou.hotkeys.removeAssignment('h.pane.wsheet.down','PageDown')  
    
    # Cycle over directions and add default Hotkey assignments.
    for directory in dirs:
        label = 'labs::networkwalk_{}'.format(directory)
        description = 'Walk {} along the connections in the Network View'.format(directory)
        
        symbol = 'h.pane.wsheet.tool:'+label
        hou.hotkeys.addCommand(symbol, label, description)
        
        # Assign Action to Hotkey.
        key = key_dict[directory]
        re = hou.hotkeys.addAssignment('h.pane.wsheet.tool:'+label, key)
            
    # Save changes
    hou.hotkeys.saveOverrides()

    print ("Network Walk hotkeys assigned.\n\nPageUp = Move Up\nPageDown = Move Down\nInsert = Move Left\nHome = Move Right\n")
    print ("Restart Houdini for the changes to take effect.\n")

    return
    
def remove_actions(dirs=('Up','Down','Left','Right'),remove=True):       
    """ Removes Actions, thereby deleting Hotkey assignments.
    """
    for directory in dirs:
        label = 'labs::networkwalk_{}'.format(directory)
        # Remove hot key if it exists
        symbol = hou.hotkeys.hotkeySymbol('/Houdini/Panes/Network Editor',label)
        if symbol != '':
            hou.hotkeys.removeHotkeySymbol(symbol)  
        
    # Save changes
    hou.hotkeys.addAssignment('h.pane.wsheet.up','PageUp')
    hou.hotkeys.addAssignment('h.pane.wsheet.down','PageDown')
    hou.hotkeys.saveOverrides()
    
    if remove:
        print ("Network Walk hotkeys removed.\n")

    return

##########################################################
# Walking Functions
##########################################################    
def walk(step='up',**kwargs):
    """ Walks a around network based on arguement in Network Graph.
    """
    global pivot

    # Get head.
    # Check theres a good node from last to first and use that as the head.
    selNodes = list(hou.selectedItems())    
    head = None
    selNodes.reverse()    
    for node in selNodes:
    
        # If node type in add as head.
        if isinstance(node,hou.Node):
            head = node
            break
        
        # If subnet in type subnet in.
        if isinstance(node,hou.SubnetIndirectInput):
            head = node
            break
        
        # If subnet in type add as head.
        if isinstance(node,hou.NetworkDot):
            head = node
            break
    
    # If still no head found return apply.
    if head is None:
        return None
    
    ## Network direction in screne space. Used for flash message. 
    dirStep = step
    
    # Reorient if Vop node.
    inputconnection = None
    if isinstance(head,hou.NetworkDot):
        inputconnection = head.input()
    if isinstance(head,hou.VopNode) or isinstance(inputconnection,hou.VopNode):
        isVop = True
        
        # Remap to reorient for Vops.
        remap = {'up':'left','down':'right','left':'up','right':'down' }
        step = remap[step]    
    
    # Get editor.    
    editor = get_network_editor(node=head)       
    if editor is None:
        return None
       
    # Axis of walk.
    axis = 'x' if step in ['left', 'right'] else 'y'               
    orient = get_orientation(head=head)
    pivot = orient['pivot']
    rel=orient['rel']        
        
    # Exit if no orientation found.
    if pivot is None:
        if axis=='x':
            message = 'No {} '.format(step)
            icon = 'error'
            flash_message(editor,icon=step,message=message)
            return None
        else:
            pivot = head
    
    # Get potential items to walk to.
    walkDict = get_walk_list(head=head,step=step,_pivot=pivot,rel=rel)
    
    # Find best spatial match.
    travLength = len(walkDict['nodes'])
    if travLength == 0:
        goTo = None
    else:
        if axis=='y':
            if travLength==1:
                index = 0
            else:
                headPos = head.position()[0]
                relPosList =  [abs(pos-headPos) for pos in walkDict['positions']]
                index = relPosList.index(min(relPosList))
            goTo = walkDict['nodes'][index]  
        
        if axis=='x':
            if travLength==1:  
                goTo = None
            else:
                index = walkDict['nodes'].index(head)
                if step=='left': 
                    offset = -1
                if step=='right': 
                    offset = 1
        
                # Step along walk list and wrap aound when at end of list.
                index = (index + offset)  % len(walkDict['nodes'])
                goTo = walkDict['nodes'][index]
                                
    # Deselect current last selected node and replace with goTo node
    # Calling correct method for item types.
    # Prepare feedback data
    icon = dirStep
    if goTo is not None:
        if isinstance(head,hou.Node):
            head.setCurrent(False)
        else:
            head.setSelected(False)
            
        if isinstance(goTo,hou.Node):
            goTo.setCurrent(True, clear_all_selected=False)
        else:
            goTo.setSelected(True,clear_all_selected=False)
            
        # Store new pivot item.
        if axis=='y':
            headId = str(head.sessionId())
            headType = 'hou.{}'.format(str(head.networkItemType()))            
            message = 'From "{}"'.format(head.name())
        if axis=='x':
            message = 'Pivot "{}"'.format(pivot.name())
            
    else:
        icon = 'error'
        if axis=='y':
            icon = 'error'
            message = 'No {}'.format(step)
        else:
            message = 'No Sibling to Pivot "{}"'.format(pivot.name())     
                
    # Visual feed back.
    ngv.ensureItemsAreVisible(editor, (goTo,), immediate = False)
    flash_message(editor,icon=icon,message=message)
    return
      
def get_walk_list(head=None,step=None,_pivot=None,rel=None): 
    """ Gets list on nodes that met relation conditions.
    Sorted from right to left with their positions.
    """
    if step=='up':
        cons = get_inputs(node=head)
    if step=='down':
        cons = get_outputs(node=head)
    if step in ['left', 'right']:
        if rel=='OUT':
            cons = get_outputs(node=_pivot)
            flow = 'IN'
        if rel=='IN':
            cons = get_inputs(node=_pivot)
       
    # Get connections and x position to sort by.    
    travList = list()
    posList = list()
    for con in cons:
        if con not in travList:
            if con not in travList:
                relPos = con.position()[0]
                posList.append(relPos)
                travList.append(con)
    
    # Order by x position.           
    zipTup = sorted(zip(posList,travList))
    travList = [b for a,b in zipTup]
    posList.sort()
    return {'nodes':travList,'positions':posList}

def get_orientation(head=None):
    """ Find pivot and the relationship to it the head node.
    If no pivot from global var then derive from it's inputs. 
    """   
    global pivot
    rel = None
    if pivot is not None:
        rel = None
        inputs = get_inputs(node=head)
        if pivot in inputs:
            rel = 'OUT'
        else:
            if pivot in get_outputs(node=head):
                rel = 'IN'               
        if rel is None:            
            pivot = None
    
    # If not pivot found infer from first input.
    if pivot is None:
        # Get first input and break.
        inputCons = get_inputs(node=head)
        for con in inputCons:
            pivot = con
            rel = 'OUT'
            break          
        else:
            outputCons = get_outputs(node=head)
            for con in outputCons:
                pivot = con
                rel = 'IN'
                break  
                
    return {'pivot':pivot,'rel':rel}

def get_network_editor(node=None):
    """ Get all Network editors. 
    If there's not one under curser than get the first one.
    """
    # Find all network editors in that are showing this node.   
    paneTabs = hou.ui.paneTabs()
    editors = list()
    for paneTab in paneTabs:
        if paneTab.type() == hou.paneTabType.NetworkEditor:
            if node.parent() == paneTab.pwd():
                try:
                    isUnder = paneTab.isUnderCursor()
                except:
                    isUnder = False
                if isUnder:
                    editor = paneTab                    
                    return editor
               
                editors.append(editor)
                
    # TO DO: check tab is current?    
    # Pick first.
    if len(editors)>0:
        editor = editors[0]
    else:
        editor = None    
    return editor

def flash_message(editor=None,icon='error',message='Error'):
    """ Flash message for user in Network Editor.
    """
    imageDict = {'up':'hicon:/SVGIcons.index?BUTTONS_up.svg',
                'down':'hicon:/SVGIcons.index?BUTTONS_down.svg',
                'left':'hicon:/SVGIcons.index?BUTTONS_back.svg',
                'right':'hicon:/SVGIcons.index?BUTTONS_forward.svg',
                'error':'hicon:/SVGIcons.index?BUTTONS_do_not.svg'}
    
    # Note: Had to remove keywords as was causing error in pre 18.5 Houdini version
    editor.flashMessage(imageDict[icon],message,0.5) 
    return None
    
def get_inputs(node=None):
    """ Get input Network Items.
    """
    cons = node.inputConnections()
    items = list()
    for con in cons:
        items.append(con.inputItem())
    return items

def get_outputs(node=None):
    """ Get output Network Items.
    """
    cons = node.outputConnections()
    items = list()
    for con in cons:
        items.append(con.outputItem())
    return items