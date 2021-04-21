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

# get network editor
editors = [pane for pane in hou.ui.paneTabs() if isinstance(pane, hou.NetworkEditor)]
pane = editors[-1]

# get current node in network editor
node = pane.pwd()

# create a sticky info in current node
def createNotes(stickytype="info"):
    sticky = node.createStickyNote()
    sticky.setBounds(hou.BoundingRect(0, 0, 4, 4))
    position = pane.overviewPosFromScreen(hou.Vector2(0, 0))
    sticky.setPosition(position)
    sticky.setColor(hou.Color(normalize_color(COLOR_BG[stickytype])))
    sticky.setTextColor(hou.Color(normalize_color(COLOR_TXT[stickytype])))
    sticky.setText(("#%s" % stickytype))

# This code attaches background images to nodes 
def numberItems():
    # initialize variables
    index = 0
    images = []

    # get the selected nodes
    nodes = hou.selectedNodes()
    # get the network editor
    editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    for node in nodes:
        image = hou.NetworkImage()
        # must be full path
        fullpath = os.path.expandvars('${SIDEFXLABS}/misc/stickers/Edu/SIDEFX_CUSTOM_EMBLEMS_%02d.png' % (index+1))
        image.setPath(fullpath)
        image.setRelativeToPath(node.path())
        image.setRect(hou.BoundingRect(-0.1, 0.1, -1.1, 1.1))
        index += 1
        images.append(image)

    editor.setBackgroundImages(images)
