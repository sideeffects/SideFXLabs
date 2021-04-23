# 
# This file contains functions dealing with notes dedicated to Education purposes
# Like color coded sticky notes...
# 

import os
import hou

# define colors
COLOR_BG = {
    "bestpractice": (255, 119, 0),
    "info": (162, 84, 255),
    "tip": (105, 204, 0),
    "warning": (255, 51, 0)
}

COLOR_TXT = {
    "bestpractice": (255, 255, 255),
    "info": (255, 255, 255),
    "tip": (255, 255, 255),
    "warning": (255, 255, 255)
}

def normalize_color(color):
    return tuple(x/255.0 for x in color)

# create a sticky info in current node
def createNotes(kwargs, stickytype="info"):

    ctrlclick = kwargs['ctrlclick']
    shiftclick = kwargs['shiftclick']
    altclick = kwargs['altclick']
    cmdclick = kwargs['cmdclick']

    stickytype = 'info'
    if(ctrlclick):
        stickytype = 'warning'
    elif(shiftclick):
        stickytype = 'bestpractice'
    elif(altclick):
        stickytype = 'tip'

    # get the network editor
    editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    
    # get the current node in the network editor
    node = editor.pwd()
    # position = pane.overviewPosFromScreen(hou.Vector2(0, 0))

    sticky = node.createStickyNote()
    sticky.setBounds(hou.BoundingRect(0, 0, 4, 4))
    # sticky.setPosition(position)
    sticky.setText(("#%s" % stickytype))
    sticky.setColor(hou.Color(normalize_color(COLOR_BG[stickytype])))
    sticky.setTextColor(hou.Color(normalize_color(COLOR_TXT[stickytype])))

# This code attaches background images to nodes 
def numberItems(kwargs):

    ctrlclick = kwargs['ctrlclick']
    shiftclick = kwargs['shiftclick']
    altclick = kwargs['altclick']
    cmdclick = kwargs['cmdclick']

    # get the network editor
    editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)

    # collect already existing images
    images = []
    bgimages = editor.backgroundImages()
    bgimagepaths = [image.path() for image in bgimages]
    images.extend(bgimages)

    # if CTRL+SHIFT, clear all numbered images
    index = 1
    if(ctrlclick & shiftclick):
        for index in range(1, 30):
            # define image path (must be full path)
            fullpath = os.path.expandvars('${SIDEFXLABS}/misc/stickers/Font/SIDEFX_CUSTOM_EMBLEMS %02d.png' % (index+66))
            # fullpath = os.path.expandvars('${SIDEFXLABS}/misc/stickers/Edu/SIDEFX_CUSTOM_EMBLEMS_%02d.png' % (index))

            # check if the image number is already used
            try:
                # if it is, remove it
                id = bgimagepaths.index(fullpath)
                images.pop(id)
                bgimagepaths.pop(id)
            except:
                # if not, don't do anything
                pass

            # set the background images 
            editor.setBackgroundImages(images)
        return

    # otherwise create images
    index = 1
    for item in hou.selectedItems():
        # define image path (must be full path)
        fullpath = os.path.expandvars('${SIDEFXLABS}/misc/stickers/Font/SIDEFX_CUSTOM_EMBLEMS %02d.png' % (index+66))
        # fullpath = os.path.expandvars('${SIDEFXLABS}/misc/stickers/Edu/SIDEFX_CUSTOM_EMBLEMS_%02d.png' % (index))
        
        # check if the image number is already used
        try:
            # if it is, remove it
            id = bgimagepaths.index(fullpath)
            images.pop(id)
            bgimagepaths.pop(id)
        except:
            # if not, don't do anything
            pass

        # create a background image and add it to the list
        image = hou.NetworkImage()
        image.setPath(fullpath)
        image.setRelativeToPath(item.path())
        image.setRect(hou.BoundingRect(-0.1, 0.1, -1.1, 1.1))
        images.append(image)
        index += 1
    
    # set the background images 
    editor.setBackgroundImages(images)


def setquickmarks(kwargs):
    import nodegraphview
    nodegraphview.createQuickMark(kwargs['pane'], 101)
    nodegraphview.createQuickMark(kwargs['pane'], 102)
    nodegraphview.createQuickMark(kwargs['pane'], 103)
    nodegraphview.createQuickMark(kwargs['pane'], 104)

def jumpQuickmark(kwargs):
    import nodegraphview

    index = 101
    
    ctrlclick = kwargs['ctrlclick']
    shiftclick = kwargs['shiftclick']

    if ctrlclick:
        index+=1
    elif shiftclick:
        index-=1

    nodegraphview.jumpToQuickMark(kwargs['pane'], index)


#  explore also
# nodegraphview.QuickMark()
# nodegraphview.setQuickMark()




