"""  
This is my adaptation of nodegraphview.py to be able to have quickmarks with a different quickmark key
Mainly to use for the Education tools, but adding this parameter would be useful for other quickmarks
"""


from __future__ import print_function
from __future__ import division
from builtins import range
from past.builtins import basestring
from past.utils import old_div
import hou
import json
import nodegraphprefs as prefs
import nodegraphutils as utils
from canvaseventtypes import *

theViewBoundsKey = 'viewbounds'
theQuickMarkKey = 'sidefxedu_quickmark_'
theUndoQuickMark = None
theUndoIndex = -1

class QuickMark(object):
    def __init__(self, net, bounds, items, currentnode):
        self.net = net
        self.bounds = bounds
        self.items = list(items)
        self.currentnode = currentnode

    def verify(self):
        if self.net is not None:
            try:
                self.net.isSelected()
            except hou.ObjectWasDeleted:
                self.net = None

        if self.currentnode is not None:
            try:
                self.currentnode.isSelected()
            except hou.ObjectWasDeleted:
                self.currentnode = None

        remove_indices = []
        for (i, item) in enumerate(self.items):
            try:
                item.isSelected()
            except hou.ObjectWasDeleted:
                remove_indices.append(i)

        for i in reversed(remove_indices):
            self.items.pop(i)

        return self.net is not None

    def jump(self, editor):
        if self.net != editor.pwd():
            changeNetwork(editor, self.net,
                          override_bounds = self.bounds,
                          dive_into_dive_target = False)
        else:
            editor.setVisibleBounds(self.bounds,utils.getViewUpdateTime(editor))
        modifySelection(None, editor, self.items, self.currentnode)

    def asJson(self):
        d = {
            'net' :
                self.net.path(),
            'currentnode' :
                '' if self.currentnode is None else self.currentnode.path(),
            'bounds' :
                [
                    self.bounds.min().x(),
                    self.bounds.min().y(),
                    self.bounds.max().x(),
                    self.bounds.max().y(),
                ],
            'items' :
                [ item.name() for item in self.items ]
        }

        return json.dumps(d)

    @staticmethod
    def fromJson(quickmark_str):
        if isinstance(quickmark_str, basestring):
            try:
                d = json.loads(quickmark_str)
                net = hou.node(d['net'])
                currentnode = hou.node(d['currentnode'])
                bounds = hou.BoundingRect(*d['bounds'])
                items = [ net.item(name) for name in d['items'] ]
                items = [ item for item in items if item is not None ]
                quickmark = QuickMark(net, bounds, items, currentnode)
                if quickmark.verify():
                    return quickmark

            except:
                pass

        return None

def scaleAroundMouse(editor, pivot, scale, startbounds = None):
    # Adjust the editor scale and center values to change the scale without
    # moving (on the screen) whatever is under the mouse.
    if startbounds is None:
        bounds = editor.visibleBounds()
    else:
        bounds = hou.BoundingRect(startbounds)
    bounds.translate(-pivot)
    bounds.scale((scale, scale))
    bounds.translate(pivot)
    editor.setVisibleBounds(bounds)

def scaleWithMouseWheel(uievent):
    pct = abs(uievent.wheelvalue / 100.0)
    if uievent.wheelvalue > 0:
        scale = 1.0 / (((utils.getScaleStep() - 1.0) * pct) + 1.0)
    else:
        scale = ((utils.getScaleStep() - 1.0) * pct) + 1.0
    scaleAroundMouse(uievent.editor,
        uievent.editor.posFromScreen(uievent.mousepos), scale)

def frameItems(editor, items, immediate = False):
    bounds = hou.BoundingRect()
    max_scale = utils.getDefaultScale()
    for item in items:
        if isinstance(item, hou.Node) and item.isHidden():
            itemset = set()
            depthfirstlist = []
            utils.getOutputsRecursive(item, itemset, depthfirstlist)
            for output in depthfirstlist:
                if not isinstance(output, hou.Node) or not output.isHidden():
                    bounds.enlargeToContain(editor.itemRect(output))
                    break
        else:
            bounds.enlargeToContain(editor.itemRect(item))

    if bounds.isValid():
        # Put a one unit buffer around the items being framed.
        bounds.expand(hou.Vector2(1.0, 1.0))
        if immediate:
            editor.setVisibleBounds(bounds, 0, max_scale, True) 
        else:
            createUndoQuickMark(editor)
            editor.setVisibleBounds(bounds, utils.getViewUpdateTime(editor),
                                    max_scale, True) 

def ensureItemsAreVisible(editor, items, immediate = False):
    bounds = hou.BoundingRect()
    max_scale = utils.getDefaultScale()
    for item in items:
        if isinstance(item, hou.NetworkMovableItem):
            if not isinstance(item, hou.Node) or not item.isHidden():
                bounds.enlargeToContain(editor.itemRect(item))

    if bounds.isValid() and \
       (not editor.visibleBounds().contains(bounds.min()) or \
        not editor.visibleBounds().contains(bounds.max())):
        # Put a one unit buffer around the items being framed.
        bounds.expand(hou.Vector2(1.0, 1.0))
        current_bounds = editor.visibleBounds()

        # If the item bounds are bigger than the current bounds, we have to
        # do some scaling. Just set the new visible bounds to the item bounds.
        # Otherwise we just pan the current bounds to cover the item bounds.
        if bounds.size().x() <= current_bounds.size().x() and \
           bounds.size().y() <= current_bounds.size().y():
            diff = bounds.min() - current_bounds.min()
            if diff.x() < 0:
                current_bounds.translate((diff.x(), 0))
            if diff.y() < 0:
                current_bounds.translate((0, diff.y()))
            diff = bounds.max() - current_bounds.max()
            if diff.x() > 0:
                current_bounds.translate((diff.x(), 0))
            if diff.y() > 0:
                current_bounds.translate((0, diff.y()))
            bounds = current_bounds

        if immediate:
            editor.setVisibleBounds(bounds, 0, max_scale, True) 
        else:
            createUndoQuickMark(editor)
            editor.setVisibleBounds(bounds, utils.getViewUpdateTime(editor),
                                    max_scale, True) 

def modifySelection(uievent, editor, items,
                    current = None, shift = None, ctrl = None):
    with hou.undos.group('Change selection'):
        if editor is None:
            editor = uievent.editor
        if shift is None:
            shift = (uievent is not None and uievent.modifierstate.shift)
        if ctrl is None:
            ctrl = (uievent is not None and uievent.modifierstate.ctrl)
        if not shift and not ctrl:
            hou.clearAllSelected()

        # Figure out what operation was requested, and the new selection state
        # of each passed in item implied by this operation.
        togglestate = ctrl and shift
        newselectstate = not ctrl
        traverseitems = [
            (item, not item.isSelected() if togglestate else newselectstate,
             True, True) for item in items]

        # If we are passed a current node, but that current node is going to
        # be deselected by this function call, clear the current value so that
        # any other node that becomes selected can be made current instead.
        if current is not None:
            if (current.isSelected() and togglestate) or \
               (ctrl and not togglestate):
                current = None

        while traverseitems:
            newitems = []
            for (item,newselectstate,traversedown,traverseup) in traverseitems:
                # If a new current node isn't explicitly specified, use the
                # first node that is being selected as the new current node.
                if current is None and newselectstate:
                    if isinstance(item, hou.Node):
                        current = item

                # If we wouldn't be changing the value, skip this item.
                if item.isSelected() == newselectstate:
                    continue

                if isinstance(item, hou.NodeConnection):
                    initem = item.inputItem()
                    outitem = item.outputItem()

                    # Adding or removing a connection that feeds into an
                    # unpinned dot should also add or remove any connections
                    # leading out of that dot.
                    if traversedown and \
                       isinstance(outitem, hou.NetworkDot) and \
                       not outitem.isPinned():
                        for conn in outitem.outputConnections():
                            newitems.append(
                                (conn, newselectstate, True, False))

                    # Adding or removing a connection with an unpinned dot as
                    # its input should add or remove that dots input if all
                    # other outputs of that dot match the new select state
                    # for this connection out of the dot.
                    if traverseup and \
                       isinstance(initem, hou.NetworkDot) and \
                       not initem.isPinned():
                        if initem.inputConnections():
                            conn = initem.inputConnections()[0]
                            addinput = True
                            # Adding a connection only adds the inbound
                            # connection through an unpinned dot if all outputs
                            # from that dot are selected.
                            if newselectstate:
                                for outconn in initem.outputConnections():
                                    if outconn != item and \
                                       not outconn.isSelected():
                                        addinput = False
                                        break
                            if addinput:
                                newitems.append(
                                    (conn, newselectstate, False, True))

                # Actually set the new selection state on the item.
                item.setSelected(newselectstate)

            # Now that we've gone through one chunk of items, go through any
            # items that we need to modify because of the changes we just made.
            traverseitems = newitems

        # If a specific node was passed as current, make it the pane's current
        # node. Otherwise make the last item in the list the pane's current
        # node. When using the Ctrl key to unselect items, don't change the
        # pane's current node at all.
        if current is not None:
            editor.setCurrentNode(current, False)

def clearViewBoundsData(editor, currentpath):
    # Clear all our saved view bounds.
    if theViewBoundsKey in editor.eventContextData():
        editor.eventContextData().pop(theViewBoundsKey)

    # Home on our current context, or whatever is in the view now.
    currentnode = hou.node(currentpath)
    if currentnode is None:
        currentnode = editor.pwd()

    # Because we are called when handling a ContextClearEvent (in response to
    # a File->New command), the editor.pwd() may actually be None at this
    # moment, because the nodes have all been deleted but our path gadget has
    # not yet had a chance to update. If this happens, there are no items to
    # frame, so do nothing.
    if currentnode is not None:
        frameItems(editor, currentnode.allItems(), True)

def handleNetworkChange(editor, oldpath, newpath, override_bounds,
                        ignore_next_change):
    newnode = hou.node(newpath)
    context = editor.eventContextData()

    # Make sure we have a place to save our view bounds.
    if context.get(theViewBoundsKey) is None:
        context[theViewBoundsKey] = {}

    if not context[theViewBoundsKey].get('ignorenextchange', False):
        # Remember the view bounds for the oldpath, and set the bounds to
        # whatever they were last time we looked at the newpath.
        if oldpath != '':
            oldnode = hou.node(oldpath)
            if oldnode is not None:
                context[theViewBoundsKey][oldnode.sessionId()] = {
                        'bounds' : editor.visibleBounds()
                }

        if override_bounds is None:
            if newnode is None:
                data = None
            else:
                data = context[theViewBoundsKey].get(newnode.sessionId())

            if data is not None:
                editor.setVisibleBounds(data['bounds'])
            elif newnode is not None:
                frameItems(editor, newnode.allItems(), True)
        else:
            editor.setVisibleBounds(override_bounds)

        # Set up the flag footprints based on the network type.
        if newnode is not None:
            category = newnode.childTypeCategory()
            footprints = utils.getFootprints(category)
            editor.setFootprints(footprints)

        # Set the background images from the newnode's user data.
        editor.setBackgroundImages(utils.loadBackgroundImages(newnode))

    # Record whether or not we should ignore the next call to this function.
    context[theViewBoundsKey]['ignorenextchange'] = ignore_next_change

def changeNetwork(editor, newnet, override_bounds = None,
        moving_up = False, dive_into_dive_target = True):
    if newnet is None or not newnet.isNetwork():
        return

    oldnet = editor.pwd()
    if moving_up:
        selectnet = oldnet
        childnet = oldnet
        parent = childnet.parent()
        while parent and not parent.isEditable():
            childnet = parent
            parent = parent.parent()
            if parent and childnet.isLockedHDA() and childnet.type():
                hdadef = childnet.type().definition()
                if hdadef and hdadef.hasSection('DiveTarget'):
                    target = hdadef.sections()['DiveTarget'].contents()
                    # It doesn't matter what the dive target is. If the parent
                    # has a dive target, we want to jump out of the parent.
                    if target is not None:
                        target = target.strip()
                        if target:
                            selectnet = childnet
                            newnet = parent

        # Set the selection so we see the parm dialog of the node from which
        # we just came up.
        selectnet.setSelected(True, clear_all_selected = True)

    elif dive_into_dive_target:
        if newnet.isLockedHDA() and newnet.type():
            hdadef = newnet.type().definition()
            if hdadef and hdadef.hasSection('DiveTarget'):
                target = hdadef.sections()['DiveTarget'].contents()
                # It doesn't matter what the dive target is. If the parent
                # has a dive target, we want to jump out of the parent.
                if target is not None:
                    target = target.strip()
                    target = newnet.node(target)
                    if target and target.isNetwork():
                        newnet = target

    if newnet is None or not newnet.isNetwork() or newnet == oldnet:
        return
    oldpath = oldnet.path()
    newpath = newnet.path()

    # We want to update the view bounds before changing the current network
    # so we don't see the view flash to the new network, then change bounds.
    # But we will also get a context change event right after the network
    # changes, which we need to ignore because we've already switched to the
    # view bounds for the new network.
    handleNetworkChange(editor, oldpath, newpath, override_bounds, True)
    editor.setDecoratedItem(None, False)
    editor.cd(newpath)

def moveCurrent(editor, direction):
    current = editor.currentNode()
    newcurrent = None
    if current is not None:
        inputs = current.inputs()
        inputs = list(input for input in inputs if input is not None)
        outputs = list(current.outputs())
        if direction == 'up' and inputs:
            newcurrent = inputs[0]
        elif direction == 'down' and outputs:
            newcurrent = outputs[0]
        elif (direction == 'left' or direction == 'right'):
            siblings = []
            if outputs and len(outputs[0].inputs()) > 1:
                siblings = outputs[0].inputs()
            elif inputs and len(inputs[0].outputs()) > 1:
                siblings = inputs[0].outputs()
            if siblings:
                for idx in range(0, len(siblings)):
                    if siblings[idx] == current:
                        bump = -1 if direction == 'left' else 1
                        newidx = (idx + bump) % len(siblings)
                        newcurrent = siblings[newidx]
                        # Skip over multiple siblings of this node.
                        while newidx != idx and newcurrent == current:
                            newidx = (newidx + bump) % len(siblings)
                            newcurrent = siblings[newidx]
                        break

    if newcurrent is not None:
        editor.setCurrentNode(newcurrent)
        ensureItemsAreVisible(editor, [newcurrent])

def diveIntoNode(editor, node = None):
    # If we weren't given a specific node (user hit Enter), pick the first
    # selected node to dive into.
    if node is None:
        epwd = editor.pwd()
        selected = epwd.selectedChildren()
        if selected:
            node = selected[0]

    if node is not None and node.matchesCurrentDefinition():
        if not prefs.allowDiveIntoHDAs(editor):
            hdadef = node.type().definition()
            if hdadef is not None and hdadef.options().lockContents():
                if not hdadef.hasSection('EditableNodes'):
                    node = None

    if node is not None:
        changeNetwork(editor, node)

def jumpToNode(editor, node, frame_nodes):
    createUndoQuickMark(editor)
    bounds = hou.BoundingRect()
    bounds.enlargeToContain(editor.itemRect(node))
    for frame_node in frame_nodes:
        bounds.enlargeToContain(editor.itemRect(frame_node))
    # Adjust the bounds so we end up at roughly the "default" zoom level.
    minwidth = old_div(editor.screenBounds().size().x(), utils.getDefaultScale())
    minheight = old_div(editor.screenBounds().size().y(), utils.getDefaultScale())
    if bounds.size().x() < minwidth:
        bounds.expand(hou.Vector2((minwidth - bounds.size().x()) * 0.5, 0.0))
    if bounds.size().y() < minheight:
        bounds.expand(hou.Vector2(0.0, (minheight - bounds.size().y()) * 0.5))
    changeNetwork(editor, node.parent(),
                  override_bounds = bounds,
                  dive_into_dive_target = False)
    node.setSelected(True, clear_all_selected = True)
    editor.setCurrentNode(node, False)

def getQuickMark(index, qmKey=theQuickMarkKey):
    if index == theUndoIndex:
        quickmark = theUndoQuickMark
    else:
        key = qmKey + str(index)
        value = hou.node('/').userData(key)
        quickmark = QuickMark.fromJson(value)

    if quickmark is not None and not quickmark.verify():
        quickmark = None

    return quickmark

def setQuickMark(index, quickmark, qmKey=theQuickMarkKey):
    if quickmark is not None and not quickmark.verify():
        quickmark = None

    if index == theUndoIndex:
        global theUndoQuickMark
        theUndoQuickMark = quickmark
    else:
        key = qmKey + str(index)
        value = quickmark.asJson()
        hou.node('/').setUserData(key, value)

def createQuickMark(editor, index):
    net = editor.pwd()
    bounds = editor.visibleBounds()
    items = net.selectedItems()
    currentnode = [item for item in items
                   if isinstance(item, hou.Node) and item.isCurrent()]
    currentnode = currentnode[0] if currentnode else None
    setQuickMark(index, QuickMark(net, bounds, items, currentnode))

def createUndoQuickMark(editor):
    createQuickMark(editor, theUndoIndex)

def jumpToQuickMark(editor, index):
    quickmark = getQuickMark(index)
    createUndoQuickMark(editor)
    if quickmark is not None:
        quickmark.jump(editor)

def quickmarkMenuLabel(index):
    label = 'Quickmark ' + str(index + 1)
    quickmark = getQuickMark(index)
    if quickmark is None:
        label += ' - not set'
    else:
        label += ' - '
        if quickmark.currentnode:
            name = quickmark.currentnode.name() + ' in '
        else:
            name = ''
        path = name + quickmark.net.path()
        if len(path) > 100:
            path = '...' + path[-100:-1]
        label += path

    return label

