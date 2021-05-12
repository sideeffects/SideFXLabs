# 
# This file contains functions dealing with notes dedicated to Education purposes
# Like color coded sticky notes...
# 

import os
import hou
import importlib

from past.utils import old_div
import nodegraphutils as utils
import sidefxedu_nodegraphview as edu_nodegraphview

try:
  reload(edu_nodegraphview)
except NameError:
  from importlib import reload
  reload(edu_nodegraphview)



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
SIDEFXEDU_QUICKMARK_KEY = 'sidefxedu_quickmark_'

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

    # get the network editor pane
    pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    
    # get the current node in the network editor pane
    node = pane.pwd()
    # position = pane.overviewPosFromScreen(hou.Vector2(0, 0))

    sticky = node.createStickyNote()
    sticky.setBounds(hou.BoundingRect(0, 0, 4, 4))
    # sticky.setPosition(position)
    sticky.setText(("#%s" % stickytype))
    sticky.setColor(hou.Color(normalize_color(COLOR_BG[stickytype])))
    sticky.setTextColor(hou.Color(normalize_color(COLOR_TXT[stickytype])))

class Quickmarks(object):

    # TODO: 
    # - delete all previous quickmarks when creating new ones
    # - use quickmark().jump() instead of jumpTo(value)

    def __init__(self):
        super(Quickmarks, self).__init__()
        self._pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
        self._qmlist = []
        self._qmcurrent = 0

    def reset(self):
        self._qmcurrent = 0

    def updateQmlist(self, keyword='sidefxedu_quickmark_'):
        self._qmlist = [int(qm.replace(keyword, '')) for qm in self.listQuickmarks()]
        # print(self._qmlist)

    def listQuickmarks(self, keyword='sidefxedu_quickmark_'):
        qmlist = [key for key in hou.node('/').userDataDict().keys() if keyword in key]
        qmlist.sort()
        return qmlist

    def createQuickMark(self, item, index, quickMarkKey):
        # Define the network 
        net = item.parent() # net = self._pane.pwd() 
        
        # Define the visualization bounds (frame the item in the network)
        pos = item.position() + hou.Vector2(0, item.size().y())
        bounds = hou.BoundingRect(pos[0], pos[1], pos[0], pos[1]) 
        # Adjust the bounds so we end up at roughly the "default" zoom level.
        minwidth = old_div(self._pane.screenBounds().size().x(), utils.getDefaultScale())
        minheight = old_div(self._pane.screenBounds().size().y(), utils.getDefaultScale())
        if bounds.size().x() < minwidth:
            expandVec = hou.Vector2((minwidth - bounds.size().x()) * 0.5, 0.0)
        if bounds.size().y() < minheight:
            expandVec += hou.Vector2(0.0, (minheight - bounds.size().y()) * 0.5)
        bounds.expand(expandVec)
            
        # Define the items to 
        items = [item]
        currentnode = item if isinstance(item, hou.Node) else None
        edu_nodegraphview.setQuickMark(index, edu_nodegraphview.QuickMark(net, bounds, items, currentnode))
        self.updateQmlist()

    def deleteQuickmarks(self, keyword='sidefxedu_quickmark_'):
        self.updateQmlist()
        for k in hou.node('/').userDataDict().keys():
            if keyword in k:
                hou.node('/').destroyUserData(k)

    def jumpToNext(self):
        value = min(self._qmlist[-1], self._qmcurrent+1)
        self.jumpTo(value)
        # print("Jump to next :: ", value)

    def jumpToPrev(self):
        value = max(self._qmlist[0], self._qmcurrent-1)
        self.jumpTo(value)
        # print("Jump to prev :: ", value)
        
    def jumpToFirst(self):
        self.updateQmlist()
        value = self._qmlist[0]
        self.jumpTo(value)
    
    def jumpToLast(self):
        self.updateQmlist()
        value = self._qmlist[-1]
        self.jumpTo(value)

    def jumpTo(self, value):
        self._qmcurrent = value
        edu_nodegraphview.jumpToQuickMark(self._pane, value)
        # print("Jump to :: ", value)

    def jumpToQuickMark(editor, index):
        quickmark = getQuickMark(index)
        createUndoQuickMark(editor)
        if quickmark is not None:
            quickmark.jump(editor)

    def numberItems(self, kwargs):
        # This code attaches background images to nodes 

        ctrlclick = kwargs['ctrlclick']
        shiftclick = kwargs['shiftclick']
        altclick = kwargs['altclick']
        cmdclick = kwargs['cmdclick']

        # get the network editor
        pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)

        # collect already existing images
        images = []
        bgimages = pane.backgroundImages()
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
                pane.setBackgroundImages(images)
            return

        # otherwise create images
        index = 1
        items = hou.selectedItems()
        for item in items:
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

            # define a quickmark 
            self.createQuickMark(item, index, SIDEFXEDU_QUICKMARK_KEY)

            # move index forward
            index += 1
            
        
        # set the background images 
        pane.setBackgroundImages(images)

