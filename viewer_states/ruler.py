"""
State:          Ruler
State type:     labs::ruler
Description:    For measuring distances on geometry.
Author:         michaelb
Date Created:   March 24, 2020 - 11:28:31
"""

import hou
import viewerstate.utils as su
import math as mt

from stateutils import ancestorObject

#need to fix commit message

key_context = "h.pane.gview.state.sop.labs::ruler"
hou.hotkeys.addContext(
        key_context, "Ruler State Operation", "These keys apply to the Ruler state operation.")

class Key():
    copy_to_clip = key_context + ".copy_to_clip"
    #undo = key_context + ".undo"
    pop_copy = key_context + ".pop_copy"

g_WorldXform = hou.Matrix4

hou.hotkeys.addCommand(Key.copy_to_clip, "Copy", "Copy last measurement to clip board.", ["q",])
#hou.hotkeys.addCommand(Key.undo, "Undo", "Remove last measurement.", ["z",])
hou.hotkeys.addCommand(Key.pop_copy, "PopCopy", "Copy last measurement and remove it.", ["f",])

def createSphereGeometry():
    geo = hou.Geometry()
    sphere_verb = hou.sopNodeTypeCategory().nodeVerb("sphere")
    hou.SopVerb.setParms(sphere_verb, {'type':2, 'rows':30, 't':(0,0,1)})
    hou.SopVerb.execute(sphere_verb, geo, [])
    return geo

def createLineGeometry():
    geo = hou.Geometry()
    line_verb = hou.sopNodeTypeCategory().nodeVerb("line")
    hou.SopVerb.setParms(line_verb, {'dir': (0, 0, 1)})
    hou.SopVerb.execute(line_verb, geo, [])
    return geo

def createFrustumGeometry():
    geo = hou.Geometry()
    tube_verb = hou.sopNodeTypeCategory().nodeVerb("tube")
    hou.SopVerb.setParms(tube_verb, {
                'type':1, 'cap':1, 'vertexnormals':1, 't':(0,0,0.25),
                'r':(-90, 0, 0), 'rad': (0.5, 1), 'height':0.5, 'cols':10})
    hou.SopVerb.execute(tube_verb, geo, [])
    return geo

def createPointGeometry():
    geo = hou.Geometry()
    hou.Geometry.createPoint(geo)
    return geo

def createCircleGeometry():
    geo = hou.Geometry()
    circle_verb = hou.sopNodeTypeCategory().nodeVerb("circle")
    hou.SopVerb.setParms(circle_verb, {
        'type':1, 'divs':12})
    hou.SopVerb.execute(circle_verb, geo, [])
    hou.Geometry.addAttrib(geo, hou.attribType.Point, "Cd", (1, 0, 0))
    return geo

def createArcGeometry(angle, radius):
    divs_per_degree = 0.12 #arbitary. works out to 12 divs every 90 degrees
    geo = hou.Geometry()
    circle_verb = hou.sopNodeTypeCategory().nodeVerb("circle")
    hou.SopVerb.setParms(circle_verb, {
        'type':1, 'arc':1, 'angle':hou.Vector2(0, angle), 'divs':divs_per_degree * angle, 'scale':radius})
    hou.SopVerb.execute(circle_verb, geo, [])
    return geo

class DiskMaker(object):
    def __init__(self, radius, divs, arcs, color, gamma):
        self.parms = {"radius": radius, "divs":divs, "arcs":arcs, "geo":None, "color": color, "gamma":gamma}

    def createAttribs(self, geo):
        hou.Geometry.addAttrib(geo, hou.attribType.Point, "Cd", (1.0, 1.0, 1.0))
        hou.Geometry.addAttrib(geo, hou.attribType.Point, "Alpha", 1.0)

    def makePoints(self, geo, r, divs, arcs, color, gamma):
        self.createAttribs(geo)
        pi = mt.pi
        arc_len = 2 * pi / arcs
        div_len = r / float(divs)

        point0 = hou.Geometry.createPoint(geo)
        hou.Point.setAttribValue(point0, "Cd", color)
        hou.Point.setAttribValue(point0, "Alpha", 1.0)
        for i in range(1, divs):
            alpha = pow(1 - (float(i) / divs), gamma)
            for j in range(arcs):
                point = hou.Geometry.createPoint(geo)
                pos = hou.Vector3(mt.cos(j * arc_len), mt.sin(j * arc_len), 0.0) * i * div_len
                hou.Point.setPosition(point, pos)
                hou.Point.setAttribValue(point, "Cd", color)
                hou.Point.setAttribValue(point, "Alpha", alpha)

    def makeFirstRing(self, geo, arcs):
        points = hou.Geometry.points(geo)
        for i in range(1, arcs):
            prim = hou.Geometry.createPolygon(geo)
            hou.Polygon.addVertex(prim, points[0])
            hou.Polygon.addVertex(prim, points[i])
            hou.Polygon.addVertex(prim, points[i+1])
        prim = hou.Geometry.createPolygon(geo)
        hou.Polygon.addVertex(prim, points[0])
        hou.Polygon.addVertex(prim, points[arcs])
        hou.Polygon.addVertex(prim, points[1])

    def makeOtherRings(self, geo, arcs, divs):
        points = hou.Geometry.points(geo)
        for i in range(1, divs - 1):
            for j in range(1, arcs):
                p0 = points[ j + arcs * (i - 1) ]
                p3 = points[ j + 1 + arcs * (i - 1) ]
                p1 = points[ j + arcs * i ]
                p2 = points[ j + 1 + arcs * i ]
                prim = hou.Geometry.createPolygon(geo)
                hou.Polygon.addVertex(prim, p0)
                hou.Polygon.addVertex(prim, p1)
                hou.Polygon.addVertex(prim, p2)
                hou.Polygon.addVertex(prim, p3)
            p0 = points[ arcs + arcs * (i - 1) ]
            p3 = points[ 1 + arcs * (i - 1) ]
            p1 = points[ arcs + arcs * i ]
            p2 = points[ 1 + arcs * i ]
            prim = hou.Geometry.createPolygon(geo)
            hou.Polygon.addVertex(prim, p0)
            hou.Polygon.addVertex(prim, p1)
            hou.Polygon.addVertex(prim, p2)
            hou.Polygon.addVertex(prim, p3)

    def makePrims(self, geo, arcs, divs):
        self.makeFirstRing(geo, arcs)
        self.makeOtherRings(geo, arcs, divs)

    def makeDiskImp(self, parms):
        color = parms["color"]
        geo = parms["geo"]
        r = parms["radius"]
        divs = parms["divs"]
        arcs = parms["arcs"]
        gamma = parms["gamma"]
        self.makePoints(geo, r, divs, arcs, color, gamma)
        self.makePrims(geo, arcs, divs)

    def setColor(self, color):
        self.parms["color"] = color

    def makeDisk(self, direction, color):
        self.setColor(color)
        geo = hou.Geometry()
        self.parms["geo"] = geo
        self.makeDiskImp(self.parms)
        rotate = hou.hmath.buildRotateZToAxis(hou.Vector3(direction))
        hou.Geometry.transform(geo, rotate)
        return geo

class Color(object):
    green = 0
    yellow = 1
    purple = 2
    pink = 3

    colorMap = {
        pink   : (hou.Vector4(1.0, 0.4745, 0.77647, 1),       "#ff79c6"),
        yellow : (hou.Vector4(0.9450, 0.9804, 0.54902, 1),    "#f1fa8c"),
        purple : (hou.Vector4(0.74118, 0.57647, 0.97647, 1),  "#bd93f9"),
        green  : (hou.Vector4(0.31372, 0.980392, 0.48235, 1), "#50fa7b"),
        }

    def __init__(self, color):
        self.vector4, self.hex_str = Color.colorMap[color]

    def getVec(self):
        return self.vector4

    def getVec3(self):
        return hou.Vector3(self.vector4[0], self.vector4[1], self.vector4[2])

    def getHexStr(self):
        return self.hex_str

def getCameraCancellingScale(translate, model_to_camera, camera_to_ndc, value):
    model_to_ndc = translate * model_to_camera * camera_to_ndc
    w = model_to_ndc.at(3, 3)
    if (w == 1):
        w = 2 / abs(camera_to_ndc.at(0,0)) #scale ~* orthowidth
    w *= value
    scale = hou.hmath.buildScale(w, w, w)
    return scale

class Plane:
    X, Y, Z = range(0, 3)

class Measurement(object):
    default_font_size = 18.0
    default_text = ""
    disk_maker = DiskMaker(10, 8, 20, (1.0, 1.0, 1.0), 3)

    def __init__(self, scene_viewer, color, show_text, text_scale):
        line = createLineGeometry()
        frustum = createFrustumGeometry()
        self.color = color
        self.disk_x = Measurement.disk_maker.makeDisk((1, 0, 0), (.7, .2, .2))
        self.disk_y = Measurement.disk_maker.makeDisk((0, 1, 0), (.2, .7, .2))
        self.disk_z = Measurement.disk_maker.makeDisk((0, 0, 1), (.2, .2, .7))
        self.scene_viewer = scene_viewer
        self.tail_spot_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Line, "tail_spot", frustum)
        self.head_spot_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Line, "head_spot", frustum)
        self.line_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Line, "line", line)
        self.tail_disk_drawable = None
        self.head_disk_drawable = None
        self.text_drawable = hou.TextDrawable(scene_viewer, "text_drawable")
        self.text_params = {'text': None, 'translate': hou.Vector3(0.0, 0.0, 0.0), 'highlight_mode':hou.drawableHighlightMode.MatteOverGlow, 'glow_width':10, 'color2':hou.Vector4(0,0,0,0.5), 'scale':hou.Vector3(text_scale, text_scale, text_scale)}
        self.spot_params = {'color1': color.getVec(), 'fade_factor': 0.5,'highlight_mode':hou.drawableHighlightMode.MatteOverGlow, 'glow_width':5 }
        self.line_params = {'line_width': 4.0, 'style': (10.0, 5.0), 'color1': color.getVec(),  'fade_factor':0.3, 'highlight_mode':hou.drawableHighlightMode.MatteOverGlow, 'glow_width':5}
        self.tail_pos = hou.Vector3(0.0, 0.0, 0.0)
        self.head_pos = hou.Vector3(0.0, 0.0, 0.0)
        self.spot_size = 0.01
        self.measurement = 0.0
        self.font_size = Measurement.default_font_size
        self.font_color = color.getHexStr()
        self.text = Measurement.default_text
        self.curPlane = None
        self.angle_snapping = False
        self.name = ""
        self.show_text = show_text
        self.updateTextField()

    def getLength(self):
        return self.measurement

    def setTextScale(self, scale):
        self.text_params['scale'] = hou.Vector3(scale, scale, scale)

    def getTailPos(self):
        return self.tail_pos

    def getHeadPos(self):
        return self.head_pos

    def getColor(self):
        return self.color.getVec3()

    def getDir(self):
        return hou.Vector3.normalized(self.head_pos - self.tail_pos)

    def show(self, visible):
        """ Display or hide drawables.
        """
        self.text_drawable.show(self.show_text)
        self.tail_spot_drawable.show(visible)
        self.head_spot_drawable.show(visible)
        self.line_drawable.show(visible)
        if self.tail_disk_drawable is not None:
            self.tail_disk_drawable.show(visible)
        if self.head_disk_drawable is not None:
            self.head_disk_drawable.show(visible)

    def setText(self, measurement):
        self.text = str(round(measurement, 5))
        self.updateTextField()

    def setFontSize(self, size):
        self.font_size = size
        self.updateTextField()

    def setFontColor(self, color):
        self.font_color = color
        self.updateTextField()

    def setTextPos(self, x, y):
        self.text_params['translate'][0] = x
        self.text_params['translate'][1] = y

    def updateTextField(self):
        font_string = '<font size={1} color="{2}"><b> {0} </b></font>'.format(self.text, self.font_size, self.font_color)
        self.text_params['text'] = font_string

    def draw( self, handle ):
        """ This callback is used for rendering the drawables
        """
        if self.tail_disk_drawable is not None:
            hou.GeometryDrawable.draw(self.tail_disk_drawable, handle)
        if self.head_disk_drawable is not None:
            hou.GeometryDrawable.draw(self.head_disk_drawable, handle)
        hou.GeometryDrawable.draw(self.line_drawable, handle, self.line_params)
        hou.GeometryDrawable.draw(self.tail_spot_drawable, handle, self.spot_params)
        hou.GeometryDrawable.draw(self.head_spot_drawable, handle, self.spot_params)
        hou.TextDrawable.draw(self.text_drawable, handle, self.text_params)

    def drawInterrupt(self, handle, geometry_viewport):
        screen_pos = hou.GeometryViewport.mapToScreen(geometry_viewport, self.head_pos)
        self.setTextPos(screen_pos[0], screen_pos[1])
        if self.tail_disk_drawable is not None:
            hou.GeometryDrawable.draw(self.tail_disk_drawable, handle)
        if self.head_disk_drawable is not None:
            hou.GeometryDrawable.draw(self.head_disk_drawable, handle)
        hou.GeometryDrawable.draw(self.line_drawable, handle, self.line_params)
        hou.GeometryDrawable.draw(self.tail_spot_drawable, handle, self.spot_params)
        hou.GeometryDrawable.draw(self.head_spot_drawable, handle, self.spot_params)
        hou.TextDrawable.draw(self.text_drawable, handle, self.text_params)

    def setPlane(self, plane):
        self.curPlane = plane

    def angleSnapping(self, yes):
        if (yes):
            self.angle_snapping = True
        else:
            self.angle_snapping = False

    def setSpotTransform(self, drawable, model_to_camera, camera_to_ndc):
        initToCurDir = (self.head_pos - self.tail_pos).normalized()
        if (drawable == self.tail_spot_drawable):
            initToCurDir *= -1
            translate = hou.hmath.buildTranslate(self.tail_pos)
        else:
            translate = hou.hmath.buildTranslate(self.head_pos)
        rotate = hou.hmath.buildRotateZToAxis(initToCurDir)
        scale = getCameraCancellingScale(translate, model_to_camera, camera_to_ndc, self.spot_size)
        transform = g_WorldXform.inverted()
        transform = transform * rotate * scale * translate
        hou.GeometryDrawable.setTransform(drawable, transform)

    def setDiskTransform(self, disk, pos, model_to_camera, camera_to_ndc):
        translate = hou.hmath.buildTranslate(pos)
        scale = getCameraCancellingScale(translate, model_to_camera, camera_to_ndc, self.spot_size)
        transform = g_WorldXform.inverted()
        transform = transform * scale * translate
        hou.GeometryDrawable.setTransform(disk, transform)

    def setLineTransform(self, drawable):
        initToCurDir = (self.head_pos - self.tail_pos).normalized()
        rotate = hou.hmath.buildRotateZToAxis(initToCurDir)
        translate = hou.hmath.buildTranslate(self.tail_pos)
        scale = hou.hmath.buildScale(self.measurement, self.measurement, self.measurement)
        #worldRot = hou.Matrix4(g_WorldXform.extractRotationMatrix3())
        #initToCurDir = initToCurDir * worldRot.inverted()
        transform = g_WorldXform.inverted()
        transform = transform * rotate * scale * translate
        hou.GeometryDrawable.setTransform(drawable, transform)

    def setTailPos(self, pos):
        self.tail_pos = pos

    def setTailDisk(self, plane, scene_viewer,  model_to_camera, camera_to_ndc):
        if plane == Plane.X: self.tail_disk_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Line, "circle", self.disk_x)
        if plane == Plane.Y: self.tail_disk_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Line, "circle", self.disk_y)
        if plane == Plane.Z: self.tail_disk_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Line, "circle", self.disk_z)
        self.setDiskTransform(self.tail_disk_drawable, self.tail_pos, model_to_camera, camera_to_ndc)

    def setHeadDisk(self, plane, scene_viewer):
        if plane == Plane.X:
            self.head_disk_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Line, "circle", self.disk_x)
        elif plane == Plane.Y:
            self.head_disk_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Line, "circle", self.disk_y)
        elif plane == Plane.Z:
            self.head_disk_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Line, "circle", self.disk_z)
        else:
            return

    def updateHeadPos(self, pos):
        self.head_pos = pos
        self.measurement = (pos - self.tail_pos).length()

    def updateText(self, screen_pos):
        self.setTextPos(screen_pos[0], screen_pos[1])
        self.setText(self.measurement)

    def updateDrawables(self, model_to_camera, camera_to_ndc, plane, scene_viewer):
        self.setSpotTransform(self.tail_spot_drawable, model_to_camera, camera_to_ndc)
        self.setSpotTransform(self.head_spot_drawable, model_to_camera, camera_to_ndc)
        self.setLineTransform(self.line_drawable)
        if plane is None:
            self.head_disk_drawable = None
            return
        self.setHeadDisk(plane, scene_viewer)
        self.setDiskTransform(self.head_disk_drawable, self.head_pos, model_to_camera, camera_to_ndc)

    def update(self, intersection, screen_pos, model_to_camera, camera_to_ndc, scene_viewer):
        self.updateHeadPos(intersection.pos)
        self.updateText(screen_pos)
        if (intersection.plane is not None):
            self.updateDrawables(model_to_camera, camera_to_ndc, self.curPlane, scene_viewer)
        else:
            self.updateDrawables(model_to_camera, camera_to_ndc, None, scene_viewer)

class MeasurementContainer(object):
    colors = (
            Color(Color.green), Color(Color.yellow),
            Color(Color.pink), Color(Color.purple))

    def __init__(self, viewport, text_size):
        self.measurements = []
        self.viewport = viewport
        self.show_text = True
        self.text_scale = text_size

    def showAll(self):
        for m in self.measurements:
            m.show(True)

    def showText(self, val):
        self.show_text = val
        for m in self.measurements:
            m.show_text = val
            m.show(True)

    def setScale(self, scale):
        self.text_scale = scale
        for m in self.measurements:
            m.setTextScale(scale)

    def hideAll(self):
        for m in self.measurements:
            m.show(False)

    def removeAll(self):
        while (self.count() > 0):
            self.removeMeasurement()

    def count(self):
        return len(self.measurements)

    def addMeasurement(self, scene_viewer):
        colorIndex = self.count() % len(MeasurementContainer.colors)
        self.measurements.append(Measurement(scene_viewer, MeasurementContainer.colors[colorIndex], self.show_text, self.text_scale))
        self.measurements[-1].show(False)

    def removeMeasurement(self):
        if self.count() < 1: return 0
        self.current().show(False)
        m = self.measurements.pop()
        hou.GeometryViewport.draw(self.viewport)
        return m

    def redoMeasurement(self, measurement):
        self.measurements.append(measurement)
        hou.GeometryViewport.draw(self.viewport)

    def draw(self, handle):
        for m in self.measurements:
            m.draw(handle)

    def drawInterrupt(self, handle, geometry_viewport):
        for m in self.measurements:
            m.drawInterrupt(handle, geometry_viewport)

    def current(self):
        if self.count() < 1:
            raise hou.Error("No measurements available!") #this check is for debugging. we should never be in this place if things work correctly.
        return self.measurements[-1]

    def __getitem__(self, index):
        return self.measurements[index]

class Intersection():
    def __init__(self, pos, plane, snapped = False):
        #if plane == None:
        #    if not snapped:
        #        self.pos = pos * g_WorldXform
        #    else:
        #        self.pos = pos * g_WorldXform
        #else:
        #    self.pos = pos * g_WorldXform
        self.pos = pos * g_WorldXform
        self.has_plane = (plane is not None)
        self.plane = plane

class Mode:
    idle = 0
    pre_measurement = 1
    measuring = 2

class Undo():
    def __init__(self, measurements):
        self.measurements = measurements
        self.measurement = None

    def undo(self):
        if self.measurements.count() > 0:
            self.measurement = self.measurements.removeMeasurement()

    def redo(self):
        self.measurements.redoMeasurement(self.measurement)

class State(object):
    msg = """
    Click and drag on the geometry to measure it.
    Press the '{}' key to copy the last measurement to clip board.
    Press the '{}' key to copy to clip and remove last measurement.
    """.format(hou.hotkeys.assignments(Key.copy_to_clip)[0], hou.hotkeys.assignments(Key.pop_copy)[0])

    planes = (hou.Vector3(1, 0, 0), hou.Vector3(0, 1, 0), hou.Vector3(0, 0, 1))
    plane_to_next = {Plane.X : hou.Vector3(0, 0, -1), Plane.Y : hou.Vector3(1, 0, 0), Plane.Z : hou.Vector3(1, 0, 0)}
    text_size = 1.0 #mutable by changing the text size parm

    def __init__(self, state_name, scene_viewer):
        self.state_name = state_name
        self.scene_viewer = scene_viewer
        self.geometry_viewport = hou.SceneViewer.curViewport(self.scene_viewer)
        self.geo_intersector = None
        self.geometry = None
        self.measurements = MeasurementContainer(self.geometry_viewport, State.text_size)
        self.current_node = None
        self.curPlane = None
        self.show(False)
        self.angle_snapping = False
        self.cur_angle = 0
        point = createPointGeometry()
        self.point_drawable = hou.GeometryDrawable(scene_viewer, hou.drawableGeometryType.Point, "point", point)
        self.point_params = {'style': hou.drawableGeometryPointStyle.SmoothCircle, 'radius': 2, 'color2': hou.Vector4(0, 1, 1, 1),
                'color1' : hou.Vector4(.9, .8, .1, 1.), 'highlight_mode':hou.drawableHighlightMode.MatteOverGlow, 'glow_width': 20}
        self.active = False
        self.angle_text_drawable = hou.TextDrawable(self.scene_viewer, "angle_text")
        self.angle_text_params = {'text': "Fizz", 'translate': hou.Vector3(0.0, 0.0, 0.0),'highlight_mode':hou.drawableHighlightMode.MatteOverGlow, 'glow_width':10, 'color2':hou.Vector4(0,0,0,0.5) }
        self.arc_drawable = hou.GeometryDrawable(self.scene_viewer, hou.drawableGeometryType.Line, "arc")
        self.mode = Mode.idle

    def setWorldXform(self, node):
        global g_WorldXform
        parent = ancestorObject(node)
        if parent:
            g_WorldXform = parent.worldTransform()
            g_WorldXform = hou.GeometryViewport.modelToGeometryTransform(self.geometry_viewport).inverted()
            #print(g_WorldXform)
        else:
            g_WorldXform.setToIdentity()

    def show(self, visible):
        """ Display or hide drawables.
        """
        if visible:
            self.measurements.showAll()
        else:
            self.measurements.hideAll()

    def setActive(self, val):
        self.active = val
        hou.GeometryDrawable.show(self.point_drawable, not val)

    def drawAngle(self, angle_snapping_on, handle):
        if not angle_snapping_on:
            return
        if self.curPlane is None:
            return
        plane_vec = State.planes[self.curPlane]
        #rot = hou.Matrix4.extractRotationMatrix3(g_WorldXform)
        #plane_vec = plane_vec * rot
        arc_geo = createArcGeometry(self.cur_angle, 1)
        hou.GeometryDrawable.setGeometry(self.arc_drawable, arc_geo)

        color = hou.Vector4(plane_vec[0], plane_vec[1], plane_vec[2], 1)
        scale = self.measurements.current().getLength() * .5

        translate = hou.hmath.buildTranslate(self.measurements.current().getTailPos())
        rotate = hou.hmath.buildRotateZToAxis(plane_vec)
        transform = g_WorldXform.inverted() * rotate * translate

        self.arc_drawable.setTransform(transform)
        self.arc_drawable.setParams({'line_width':3, 'color1':color, 'style':(5, 20), 'fade_factor':0.5, 'scale':hou.Vector3(scale, scale, scale)})

        text = str(self.cur_angle) + u'\u00b0'
        font_string = '<font size="{1}"<b> {0} </b></font>'.format(text.encode('utf-8'), 30)
        self.angle_text_params['text'] = font_string

        self.angle_text_drawable.show(True)
        self.arc_drawable.show(True)

        self.arc_drawable.draw(handle)
        self.angle_text_drawable.draw(handle, self.angle_text_params)

    def getMousePos(self, ui_event):
        device = hou.UIEvent.device(ui_event)
        return device.mouseX(), device.mouseY()

    def findBestPlane(self, origin, ray):
        rot = hou.Matrix4.extractRotationMatrix3(g_WorldXform)
        ray = ray * rot
        ray = (abs(ray[0]), abs(ray[1]), abs(ray[2]))
        index = ray.index(max(ray))
        return index

    def getIntersectionCplane(self, scene_viewer, ray_origin, ray_dir):
        return Intersection(su.cplaneIntersection(scene_viewer, ray_origin, ray_dir), None)

    def intersectWithPlane(self, origin, ray):
        rot = hou.Matrix4.extractRotationMatrix3(g_WorldXform)
        plane = State.planes[self.curPlane] * rot.inverted()
        planePoint = hou.Vector3(0, 0, 0) * g_WorldXform.inverted()
        return Intersection(hou.hmath.intersectPlane(planePoint, plane, origin, ray), self.curPlane)

    def getIntersectionRegular(self, ui_event):
        snapping_dict = hou.ViewerEvent.snappingRay(ui_event)
        origin = snapping_dict["origin_point"]
        ray = snapping_dict["direction"]
        if self.geo_intersector.intersect(origin, ray):
            if self.geo_intersector.snapped:
                return Intersection(self.geo_intersector.snapped_position, None, True)
            else:
                return Intersection(self.geo_intersector.position, None)
        elif self.scene_viewer.constructionPlane().isVisible():
            return self.getIntersectionCplane(self.scene_viewer, origin, ray)
        else:
            return self.intersectWithPlane(origin, ray)

    def getIntersection(self, ui_event):
        return self.getIntersectionRegular(ui_event)

    def setMeasurementPlane(self, ui_event):
        snapping_dict = hou.ViewerEvent.snappingRay(ui_event)
        snap_mode = self.scene_viewer.snappingMode()
        cur_viewport = hou.SceneViewer.curViewport(self.scene_viewer)
        vt = hou.GeometryViewport.type(cur_viewport)
        if snap_mode == hou.snappingMode.Grid:
            if vt in (hou.geometryViewportType.Perspective, hou.geometryViewportType.Top, hou.geometryViewportType.Bottom):
                plane = Plane.Y
            if vt in (hou.geometryViewportType.Front, hou.geometryViewportType.Back):
                plane = Plane.Z
            if vt in (hou.geometryViewportType.Left, hou.geometryViewportType.Right):
                plane = Plane.X
        else:
            ray = snapping_dict["direction"]
            origin = snapping_dict["origin_point"]
            plane = self.findBestPlane(origin, ray)
        if (self.active):
            self.measurements.current().setPlane(plane)
        self.curPlane = plane

    def setPointTransform(self, pos):
        translate = hou.hmath.buildTranslate(pos)
        translate = g_WorldXform.inverted() * translate
        hou.GeometryDrawable.setTransform(self.point_drawable, translate)

    def angleSnapping(self, yes):
        self.measurements.current().angleSnapping(yes)
        self.angle_snapping = yes

    def worldToScreen(self, pos):
        return hou.GeometryViewport.mapToScreen(self.geometry_viewport, pos)

    def getModelToNDC(self):
        model_to_camera = hou.GeometryViewport.cameraToModelTransform(self.geometry_viewport).inverted()
        camera_to_ndc = hou.GeometryViewport.ndcToCameraTransform(self.geometry_viewport).inverted()
        return model_to_camera * camera_to_ndc

    def getModelToCamera(self):
        model_to_camera = hou.GeometryViewport.cameraToModelTransform(self.geometry_viewport).inverted()
        return model_to_camera

    def getCameraToNDC(self):
        camera_to_ndc = hou.GeometryViewport.ndcToCameraTransform(self.geometry_viewport).inverted()
        return camera_to_ndc

    def removeMeasurement(self):
        self.measurements.removeMeasurement()

    def onGenerate(self, kwargs):
        """ Assign the geometry to drawabled
        """
        self.scene_viewer.setPromptMessage( State.msg )
        self.current_node = hou.SceneViewer.pwd(self.scene_viewer).displayNode()
        self.setWorldXform(self.current_node)
        self.geometry = hou.SopNode.geometry(self.current_node)
        self.geo_intersector = su.GeometryIntersector(self.geometry, self.scene_viewer)
        self.setActive(False)

    def onResume(self, kwargs):
        self.scene_viewer.setPromptMessage( State.msg )
        self.show(True)

    def onExit(self, kwargs):
        hou.SceneViewer.clearPromptMessage(self.scene_viewer)
        self.show(False)

    def onInterrupt(self,kwargs):
        pass

    def updateInactive(self, ui_event):
        self.setMeasurementPlane(ui_event)
        intersection = self.getIntersection(ui_event)
        self.setPointTransform(intersection.pos)

    def onMouseActive(self, ui_event):
        intersection = self.getIntersection(ui_event)
        screen_pos = self.worldToScreen(intersection.pos)
        self.measurements.current().update(intersection, screen_pos, self.getModelToCamera(), self.getCameraToNDC(), self.scene_viewer)
        self.show(True)

    def setAngleTextPos(self, ui_event):
        dev = hou.UIEvent.device(ui_event)
        self.angle_text_params['translate'] = hou.Vector3(dev.mouseX(), dev.mouseY(), 0)

    def onMouseStart(self, ui_event):
        self.measurements.addMeasurement(self.scene_viewer)
        self.setMeasurementPlane(ui_event)
        self.setAngleTextPos(ui_event)
        intersection = self.getIntersection(ui_event)
        self.measurements.current().setTailPos(intersection.pos)
        if intersection.plane is not None:
            self.measurements.current().setTailDisk(intersection.plane, self.scene_viewer, self.getModelToCamera(), self.getCameraToNDC())

    def onMouseEvent(self, kwargs):
        ui_event = kwargs["ui_event"]
        reason = hou.UIEvent.reason(ui_event)
        if (reason == hou.uiEventReason.Start):
            self.setActive(True)
            self.onMouseStart(ui_event)
            self.mode = Mode.pre_measurement
        elif (reason == hou.uiEventReason.Active):
            if self.mode == Mode.pre_measurement:
                self.mode = Mode.measuring
                hou.undos.add(Undo(self.measurements), "ruler")
            if self.mode == Mode.measuring:
                self.onMouseActive(ui_event)
        elif (reason == hou.uiEventReason.Changed):
            if self.mode == Mode.pre_measurement:
                self.measurements.removeMeasurement()
            self.curPlane = None
            self.setActive(False)
            self.mode = Mode.idle
        else:
            self.updateInactive(ui_event)

    def onKeyEvent(self, kwargs):
        ui_event = kwargs["ui_event"]
        device = ui_event.device()
        if device.isKeyPressed():
            if hou.hotkeys.isKeyMatch(device.keyString(), Key.copy_to_clip):
                if self.measurements.count() < 1: return False
                m = self.measurements.current().getLength()
                hou.ui.copyTextToClipboard(str(m))
                return True
            if hou.hotkeys.isKeyMatch(device.keyString(), Key.pop_copy):
                if self.measurements.count() < 1: return False
                m = self.measurements.current().getLength()
                hou.ui.copyTextToClipboard(str(m))
                self.measurements.removeMeasurement()
                return True
        return False

    def onParmChangeEvent(self, kwargs):
        parm_name = kwargs["parm_name"]
        parm_value = kwargs["parm_value"]
        if parm_name == "show_text":
            if parm_value is True:
                self.measurements.showText(True)
            else:
                self.measurements.showText(False)
            self.geometry_viewport.draw()
        elif parm_name == "text_size_menu":
            State.text_size = float(parm_value)
            self.measurements.setScale(float(parm_value))
            self.geometry_viewport.draw()

    def onDraw( self, kwargs ):
        """ This callback is used for rendering the drawables
        """
        handle = kwargs["draw_handle"]
        if not self.active:
            hou.GeometryDrawable.draw(self.point_drawable, handle, self.point_params)
        self.measurements.draw(handle)
        self.drawAngle(self.angle_snapping, handle)

    def onDrawInterrupt(self, kwargs):
        handle = kwargs["draw_handle"]
        self.measurements.drawInterrupt(handle, self.geometry_viewport)

text_size_item_info = [
        ('0.25', '0.25'),
        ('0.375', '0.375'),
        ('0.5', '0.5'),
        ('0.75', '0.75'),
        ('1', '1.0'),
        ('1.5', '1.5')]

def createViewerStateTemplate():
    """ Mandatory entry point to create and return the viewer state
        template to register. """

    state_typename = "labs::ruler"
    state_label = "Labs Ruler"
    state_cat = hou.sopNodeTypeCategory()

    template = hou.ViewerStateTemplate(state_typename, state_label, state_cat)
    template.bindFactory(State)
    template.bindIcon("$SIDEFXLABS/help/icons/ruler.svg")

    template.bindParameter(hou.parmTemplateType.Menu, name="text_size_menu", label="Text Size", menu_items=text_size_item_info, default_value='1')

    return template
