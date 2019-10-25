from __future__ import print_function
from stateutils import ancestorObject

import hou, math
import viewerstate.utils as util

# A minimal state handler implementation. 
class MyState(object):
    def __init__(self, state_name, scene_viewer):
        self.state_name = state_name
        self.scene_viewer = scene_viewer
        self.startpos = hou.Vector3()
        self.endpos1 = hou.Vector3()
        self.endpos2 = hou.Vector3()
        self.clickstarted = False
        self.guide_geo1 = None
        self.drawable1 = None
        self.guide_geo2 = None
        self.drawable2 = None
        self.measuremode = 0 # 0 = distance, 1 = angle

        self.initializeDrawable()
        
    def initializeDrawable(self):

        # Measure Line 1
        self.guide_geo1 = hou.Geometry()
        line_verb = hou.sopNodeTypeCategory().nodeVerb("line")

        line_verb.setParms({
            "origin": self.startpos,
            "dir": hou.Vector3(0,1,0),
            "dist": 1
        })

        line_verb.execute(self.guide_geo1, [])

        self.drawable1 = hou.Drawable(self.scene_viewer, self.guide_geo1, "guide_1")
        self.drawable1.enable(True)
        self.drawable1.show(True)

        # Measure Line 2
        self.guide_geo2 = hou.Geometry()
        line_verb = hou.sopNodeTypeCategory().nodeVerb("line")

        line_verb.setParms({
            "origin": self.startpos,
            "dir": hou.Vector3(0,1,0),
            "dist": 1
        })

        line_verb.execute(self.guide_geo2, [])

        self.drawable2 = hou.Drawable(self.scene_viewer, self.guide_geo2, "guide_2")
        self.drawable2.enable(True)
        self.drawable2.show(True)

    def getSelectedGeometry(self):
        SelectedNodes = hou.selectedNodes()
        if len(SelectedNodes) > 0:
            return SelectedNodes[0].geometry()
        else:
            return None

    def getSelectedNode(self):
        SelectedNodes = hou.selectedNodes()
        if len(SelectedNodes) > 0:
            return SelectedNodes[0]
        else:
            return None

    def createGuideTransform(self, a_position, a_direction, a_scale):
        # translation
        trans = hou.hmath.buildTranslate(a_position)

        # rotation
        rot = hou.Vector3(0,1,0).matrixToRotateTo(a_direction) 
        if a_direction.dot(hou.Vector3(0,1,0)) <= -0.9999:
            rot = hou.hmath.buildRotateAboutAxis(hou.Vector3(1,0,0), 180)

        # scale
        scale = hou.hmath.buildScale(a_scale, a_scale, a_scale)

        # combine
        xform = rot.__mul__(scale)
        xform = xform.__mul__(trans)

        return xform




    # Handler methods go here
    def onMouseEvent(self, kwargs):
        ui_event = kwargs["ui_event"]
        dev = ui_event.device()

        # ray cast
        origin, direction, snapped = ui_event.snappingRay()
        

        # selected geometry
        selectedGeometry = self.getSelectedGeometry()

        # no geometry selected, so no measurement
        if not selectedGeometry: 
            return
        
        # get intersection position
        intersection = util.sopGeometryIntersection(selectedGeometry, origin, direction)
        intersectpos = intersection[1]
        if intersection[0] < 0:
            intersectpos = util.cplaneIntersection(self.scene_viewer, origin, direction)

        parentxform = ancestorObject(self.getSelectedNode()).worldTransform()

        if dev.isLeftButton():
            self.measuremode = 0
            if not self.clickstarted:
                self.startpos = intersectpos * parentxform
                self.clickstarted = True

            if not dev.isCtrlKey():
                self.endpos1 = self.endpos2 = intersectpos * parentxform
            else:
                self.measuremode = 1
                self.endpos2 = intersectpos * parentxform
        else:
            self.clickstarted = False

        distance1 = self.startpos.distanceTo(self.endpos1)
        distance2 = self.startpos.distanceTo(self.endpos2)
        drawdirection1 = hou.Vector3(self.endpos1 - self.startpos).normalized()
        drawdirection2 = hou.Vector3(self.endpos2 - self.startpos).normalized()

        self.drawable1.setTransform(self.createGuideTransform(self.startpos, drawdirection1, distance1))
        self.drawable2.setTransform(self.createGuideTransform(self.startpos, drawdirection2, distance2))

        # Screen Messages
        self.scene_viewer.clearPromptMessage()


        if self.measuremode == 0:
            self.scene_viewer.setPromptMessage("Distance: %.3f" % round(distance1, 3))
        else:
            angle = math.degrees(math.acos(round(drawdirection1.dot(drawdirection2), 5)))
            self.scene_viewer.setPromptMessage("Angle: %.2f Degrees" % round(angle, 2))



# A registration entry-point
def createViewerStateTemplate():
    # Choose a name and label 
    state_name = "viewportmeasuretool"
    state_label = "Measurement State"
    category = hou.sopNodeTypeCategory()

    # Create the template
    template = hou.ViewerStateTemplate(state_name, state_label, category)
    template.bindFactory(MyState)

    # Other optional bindings will go here...

    # returns the 'mystate' template
    return template