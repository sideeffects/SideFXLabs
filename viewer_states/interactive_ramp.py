"""
State:          Ryan interactive ramp tool
State type:     ryan_interactive_ramp_tool
Description:    Ryan interactive ramp tool
Author:         ryan
Date Created:   October 07, 2020 - 12:53:58
"""

# Usage: This sample demonstrates how to use gadgets to highlight the
# geometry components when hovering over the geometry. Picking a component
# will draw it in a different color.
#
# Make sure to add an input on the node, connect a polygon mesh geometry and
# hit enter in the viewer.

import hou
import viewerstate.utils as su
import math

class State(object):
    MSG = ("Click on points to enable scale handle.\n"
           "Click and drag points to move.\n"
           "Shift-click line to add a point.\n"
           "Ctrl-click a point to remove it.\n"
           "Click on line to display gadgets.")

    def __init__(self, state_name, scene_viewer):
        self.state_name = state_name
        self.scene_viewer = scene_viewer
        self.geometry = None
        self.node = None

        self.id = -1
        self.prev_id = -1

        # A drawable to display the active gadget information at the
        # cursor.
        self.cursor = su.CursorLabel(scene_viewer)

        self.circle_gadget = None
        self.point_vis = None
        self.circle_gadget_vis = False
        self.circle_guide = None
        self.interrupted = False
        self.viewport = None
        self.prim = None
        self.ramp_parm = None
        self.ramp_name = None
        self.center = None
        self.point_handle = None
        self.point_gadget = None
        self.point = None
        self.line_gadget = None
        self.circle_handle = None

        #creates the handle dragger
        self.handle_dragger = hou.ViewerStateDragger("dragger")

    def clamp(self, num, min_value, max_value):
        return max(min(num, max_value), min_value)

    def createPoints(self):
        self.point_handle = hou.Geometry()

        rampKeys = self.ramp_parm.eval().keys()
        numPoints = len(rampKeys)

        for i in range(numPoints):
            u = self.node.parm('{}{}pos'.format(self.ramp_name, i+1)).eval()
            pos = self.prim.positionAt(u)

            pt = self.point_handle.createPoint()
            pt.setPosition(pos)

        self.point_gadget = self.state_gadgets["point_gadget"]
        self.point_gadget.setGeometry(self.point_handle)
        self.point_gadget.setParams({"radius":10, "draw_color":[0,0.5,1,1], "locate_color":[0,0.5,1,1], "pick_color":[0,0.5,1,1]})


    def createVisPoint(self, i):
        self.point = hou.Geometry()

        u = self.node.parm('{}{}pos'.format(self.ramp_name, i+1)).eval()
        pos = self.prim.positionAt(u)

        pt = self.point.createPoint()
        pt.setPosition(pos)

        self.point_vis = self.state_gadgets["point_vis"]
        self.point_vis.setGeometry(self.point)
        self.point_vis.setParams({"radius":10, "draw_color":[1,1,0,1], "locate_color":[1,0,0,1], "pick_color":[1,1,0,1]})

    def createLineGadget(self):
        self.line_gadget = self.state_gadgets["line_gadget"]
        self.line_gadget.setGeometry(self.geometry)
        self.line_gadget.setParams({"draw_color":[1,1,1,1], "locate_color":[1,1,1,1], "pick_color":[1,1,1,1], "line_width":1.0})

    def createCircle(self, i):
        sops = hou.sopNodeTypeCategory()
        circle_verb = sops.nodeVerb('circle')
        self.circle_handle = hou.Geometry()

        u = self.node.parm('{}{}pos'.format(self.ramp_name, i+1)).eval()
        pos = self.prim.positionAt(u)
        rot = self.prim.attribValueAt("rot", u)
        n = self.prim.attribValueAt("tangentu", u)
        scale = self.node.parm('{}{}value'.format(self.ramp_name, i+1)).eval()
        scale_mult = self.node.parm('handle_scale').eval()

        circle_verb.setParms({
            "t": pos,
            "r": rot,
            "scale": scale*scale_mult+0.05,
            "type": 1,
            "divs": 256,
            "arc": 1
        })

        circle_verb.execute(self.circle_handle, [None])

        self.circle_gadget = self.state_gadgets["circle_gadget"]
        self.circle_gadget.setGeometry(self.circle_handle)
        self.circle_gadget.setParams({"draw_color":[1,0.5,0,1], "locate_color":[1,0,0,1], "pick_color":[1,1,0,1], "line_width":1.0})

    def createCircles(self):
        sops = hou.sopNodeTypeCategory()
        circle_verb = sops.nodeVerb('circle')
        circle_guide = hou.Geometry()
        circle_guide_temp = hou.Geometry()

        rampKeys = self.ramp_parm.eval().keys()
        numPoints = len(rampKeys)

        for i in range(numPoints):
            u = self.node.parm('{}{}pos'.format(self.ramp_name, i+1)).eval()
            pos = self.prim.positionAt(u)
            rot = self.prim.attribValueAt("rot", u)
            scale = self.node.parm('{}{}value'.format(self.ramp_name, i+1)).eval()
            scale_mult = self.node.parm('handle_scale').eval()

            circle_verb.setParms({
                "t": pos,
                "r": rot,
                "scale": scale*scale_mult+0.05,
                "type": 1,
                "divs": 256,
                "arc": 1
            })

            circle_verb.execute(circle_guide_temp, [None])
            circle_guide.merge(circle_guide_temp)

        color_attrib = circle_guide.addAttrib(hou.attribType.Prim, "Cd", (1.0, 1.0, 1.0))
        for prim in circle_guide.prims():
            prim.setAttribValue(color_attrib, hou.Color(0.5,0.5,0.5).rgb())

        self.circle_guide = hou.SimpleDrawable(self.scene_viewer, circle_guide, "circle_guide")
        self.circle_guide.setDisplayMode(hou.drawableDisplayMode.WireframeMode)
        self.circle_guide.enable(True)

    def show(self, visible):
        """ Display or hide drawables/gadgets.
        """
        self.point_gadget.show(visible)
        self.circle_guide.show(visible)
        self.line_gadget.show(visible)

    def onEnter(self, kwargs):
        """ Assign the node input geometry to gadgets
        """
        self.node = kwargs["node"]
        hparms = kwargs["state_parms"]
        self.viewport = self.scene_viewer.curViewport()

        # Setup geometry and ramp parameters from node
        self.geometry = self.node.node('CURVE').geometry()
        self.prim = self.geometry.prim(0)
        self.ramp_parm = self.node.parm('attrib_ramp')
        self.ramp_name = self.node.parm('attrib_ramp').name()

        self.createLineGadget()
        self.createPoints()
        self.createCircles()

        self.show(True)
        self.scene_viewer.setPromptMessage( State.MSG )

    def onResume(self, kwargs):
        self.createPoints()
        self.createCircles()
        self.createLineGadget()
        self.show(True)
        if self.circle_gadget is not None and self.circle_gadget_vis is True:
            self.createCircle(self.id)
            self.createVisPoint(self.id)
            self.circle_gadget.show(True)
            self.point_vis.show(True)
        self.interrupted = False
        self.scene_viewer.setPromptMessage( State.MSG )

    def onInterrupt(self,kwargs):
        self.show(False)
        if self.circle_gadget is not None:
            self.circle_gadget.show(False)
            self.point_vis.show(False)
            self.interrupted = True

    def onMouseEvent(self, kwargs):
        """ Demonstrates how to access the active gadget info from the
            gadget context.
        """
        hcontext = self.state_context
        hparms = kwargs["state_parms"]
        ui_event = kwargs["ui_event"]
        reason = ui_event.reason()
        device = ui_event.device()
        origin, direction = ui_event.ray()

        gadget_name = self.state_context.gadget()

        # Pick line to display gadgets
        if self.geometry:
            gi = su.GeometryIntersector(self.geometry, scene_viewer=self.scene_viewer, tolerance=0.05)
            gi.intersect(origin, direction)
            hit = gi.prim_num
            position = gi.position
            norm = gi.normal
            uvw = gi.uvw

            if reason == hou.uiEventReason.Start:
                self.scene_viewer.beginStateUndo("Edit Ramp")

            if hit != -1 and gadget_name == "line_gadget":

                if reason in [hou.uiEventReason.Start, hou.uiEventReason.Picked]:
                    self.prim = self.geometry.prim(hit)
                    self.createLineGadget()
                    self.createPoints()
                    self.createCircles()
                    if self.id != -1:
                        self.createCircle(self.id)
                        self.createVisPoint(self.id)
                    self.show(True)

            # Show ramp key values at cursor
            if gadget_name == "point_gadget":
                c1 = self.state_context.component1()
                self.cursor.setParams(kwargs)
                u_label = self.node.parm('{}{}pos'.format(self.ramp_name, c1+1)).eval()
                self.cursor.setLabel('Position: {}'.format(round(u_label, 3)))
                self.cursor.show(True)
            elif self.id > -1:
                if gadget_name == "point_gadget":
                    c1 = self.state_context.component1()
                    if c1 == self.id:
                        self.cursor.setParams(kwargs)
                        u_label = self.node.parm('{}{}pos'.format(self.ramp_name, self.id+1)).eval()
                        self.cursor.setLabel('Position: {}'.format(round(u_label, 3)))
                        self.cursor.show(True)
                elif gadget_name == "circle_gadget":
                    self.cursor.setParams(kwargs)
                    val_label = self.node.parm('{}{}value'.format(self.ramp_name, self.id+1)).eval()
                    ramp_min = self.node.parm('ramp_min').eval()
                    ramp_max = self.node.parm('ramp_max').eval()
                    val_label_remap = ((val_label - 0) / (1 - 0)) * (ramp_max - ramp_min) + ramp_min
                    self.cursor.setLabel('Value: {} Remapped: {}'.format(round(val_label, 3), round(val_label_remap, 3)))
                    self.cursor.show(True)
                else:
                    self.cursor.show(False)
            else:
                self.cursor.show(False)

            # Create circle handle at selected point
            if gadget_name == "point_gadget":
                if not device.isCtrlKey():
                    if reason in [hou.uiEventReason.Start, hou.uiEventReason.Picked]:
                        self.id = self.state_context.component1()
                        if self.id != self.prev_id:
                            self.createCircle(self.id)
                            self.createVisPoint(self.id)
                            self.circle_gadget.show(True)
                            self.point_vis.show(True)
                            self.circle_gadget_vis = True
                            self.prev_id = self.id

            if hit != -1:
                # Add points to ramp
                if device.isShiftKey():
                    if reason in [hou.uiEventReason.Start, hou.uiEventReason.Picked]:

                        u = uvw[0]
                        val = self.prim.attribValueAt("attrib", u)

                        ramp_val = self.ramp_parm.eval()

                        bases = list(ramp_val.basis())
                        keys = list(ramp_val.keys()) + [u]
                        values = list(ramp_val.values()) + [val]
                        ramp_new = hou.Ramp(bases, keys, values)

                        self.ramp_parm.set(ramp_new)

                        ramp_val = self.ramp_parm.eval()
                        keys = list(ramp_val.keys())
                        keys.sort()
                        index = keys.index(u)

                        self.id = index

                        self.createPoints()
                        self.createCircles()

                        self.createCircle(self.id)
                        self.createVisPoint(self.id)
                        self.circle_gadget.show(True)
                        self.point_vis.show(True)
                        self.circle_gadget_vis = True
                        self.prev_id = self.id


            # Remove points from ramp
            if gadget_name == "point_gadget":
                if device.isCtrlKey():
                    if reason in [hou.uiEventReason.Start, hou.uiEventReason.Picked]:

                        self.id = self.state_context.component1()
                        u = self.node.parm('{}{}pos'.format(self.ramp_name, self.id+1)).eval()

                        ramp_val = self.ramp_parm.eval()
                        keys = list(ramp_val.keys())
                        index = keys.index(u)

                        bases = list(ramp_val.basis())
                        bases.pop(index)
                        keys.pop(index)
                        values = list(ramp_val.values())
                        values.pop(index)
                        ramp_new = hou.Ramp(bases, keys, values)

                        self.ramp_parm.set(ramp_new)

                        self.createPoints()
                        self.createCircles()

                        if self.id == self.prev_id and len(keys) >= 2:
                            if self.id == len(keys):
                                self.id = self.id-1
                            self.createCircle(self.id)
                            self.createVisPoint(self.id)
                            self.circle_gadget.show(True)
                            self.point_vis.show(True)
                            self.circle_gadget_vis = True
                            self.prev_id = self.id
                        elif len(keys) >= 2:
                            self.id = self.id-1
                        else:
                            self.id = 0

            # Move points along line
            if gadget_name == "point_gadget":
                if hit != -1:
                    if reason == hou.uiEventReason.Start:
                        self.id = self.state_context.component1()

                    if reason == hou.uiEventReason.Active:
                        u = uvw[0]
                        self.node.parm('{}{}pos'.format(self.ramp_name, self.id+1)).set(u)

                        self.createPoints()
                        self.createCircles()
                        self.createCircle(self.id)
                        self.createVisPoint(self.id)
                        self.circle_gadget.show(True)
                        self.point_vis.show(True)
                        self.circle_gadget_vis = True
                        self.prev_id = self.id

            # Scale circle handle
            if gadget_name == "circle_gadget":
                if reason == hou.uiEventReason.Start:

                    hit, position, norm, uvw = su.sopGeometryIntersection(self.circle_handle, origin, direction)

                    u = self.node.parm('{}{}pos'.format(self.ramp_name, self.id+1)).eval()
                    self.center = self.prim.positionAt(u)

                    self.handle_dragger.startDrag(ui_event, self.center)

                elif reason == hou.uiEventReason.Active:
                    if self.handle_dragger.valid():
                        drag_values = self.handle_dragger.drag(ui_event)
                        pos = drag_values["position"]

                        pos_screen = self.viewport.mapToScreen(pos)

                        dist = math.sqrt( (pos[0] - self.center[0])**2 + (pos[1] - self.center[1])**2 + (pos[2] - self.center[2])**2 )
                        scale = self.node.parm('{}{}value'.format(self.ramp_name, self.id+1)).eval()

                        u = self.node.parm('{}{}pos'.format(self.ramp_name, self.id+1)).eval()

                        if self.node.parm('scale_clamp').eval() == 1:
                            dist = self.clamp(dist, 0, 1)

                        self.node.parm('{}{}value'.format(self.ramp_name, self.id+1)).set(dist)

                        self.createCircle(self.id)
                        self.createCircles()
                        self.show(True)

            if reason == hou.uiEventReason.Changed:
                self.scene_viewer.endStateUndo()

    def onDraw( self, kwargs ):
        """ Draw drawables and gadgets.
        """
        handle = kwargs["draw_handle"]

        gadget_name = self.state_context.gadget()

        self.cursor.draw(handle)
        self.line_gadget.draw(handle)
        self.point_gadget.draw(handle)
        if self.circle_gadget is not None:
            self.point_vis.draw(handle)
            self.circle_gadget.draw(handle)