from PySide2.QtCore import Qt, QPoint, QRect
from PySide2.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QWidget
from PySide2.QtGui import QColor, QPainter, QPen, QPixmap, QGuiApplication
import hou, datetime, os, labutils


class ScreensCapture(QWidget):
    def __init__(self, parent):
        super(ScreensCapture, self).__init__(parent)

        self.mouseX = [-1,-1]
        self.mouseY = [-1,-1]
        self.oldMouseX = [-1,-1]
        self.oldMouseY = [-1, -1]
        self._views =[]
        self._canvass = []
        self._scenes = []
        self._screens = []
        self.configureScenes()

    def configureScenes(self):

        # Take fullscreen screenshot
        self._screenshots = [x.grabWindow(0) for x in QApplication.screens()]
        self._relscreenrect = [x.geometry() for x in QApplication.screens()]
        self._screens = QApplication.screens()

        for i, rect in enumerate(self._relscreenrect):
            self._views.append(QGraphicsView(self))
            self._views[i].setGeometry(rect)

            self._scenes.append(QGraphicsScene(self))
            self._canvass.append(self._screenshots[i].copy())

            self._scenes[i].addPixmap(self._canvass[i])
            self._views[i].setScene(self._scenes[i])

            self._views[i].setWindowFlags(Qt.FramelessWindowHint)
            self._views[i].setWindowFlags(Qt.WindowType_Mask)
            self._views[i].setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self._views[i].setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

            self._views[i].showFullScreen()

    def closeCaptures(self):
        for view in self._views:
            view.close()

    def getMousePos(self, event):
        screen = QGuiApplication.screenAt(event.globalPos())
        screenid = self._screens.index(screen)
        cursorloc = [event.globalPos().x()-screen.geometry().x(), event.globalPos().y()-screen.geometry().y()]
        self.mouseX = [screenid, cursorloc[0]]
        self.mouseY = [screenid, cursorloc[1]]

        return [screenid, cursorloc[0], cursorloc[1]]


class SampleColor(ScreensCapture):
    def __init__(self, parent, parms):
        super(SampleColor, self).__init__(parent)
        self.colorparms = parms
        self.samplepositions = []

        for view in self._views:
            view.mouseMoveEvent = self.sampleColorAtMousePosition
            view.mouseReleaseEvent = self.populateRampAndExit

    def sampleColorAtMousePosition(self, event):
        _mousedata = self.getMousePos(event)
        self.samplepositions.append(_mousedata)
        self.update()

    def paintEvent(self, QPaintEvent):
        if self.oldMouseX[1] >= 0 and self.mouseX[1] >= 0:

            if self.oldMouseX[0] == self.mouseX[0]:
                # Make a painter with the visible pixmap. Have to make a new copy since the original reference gets nuked on self.update() :(
                pixmap = self._scenes[self.mouseX[0]].items()[0].pixmap().copy()
                painter = QPainter(pixmap)

                pen = QPen()
                pen.setWidth(2)
                pen.setColor(QColor('#FFCC4D'))

                # Draw a point
                painter.setPen(pen)
                painter.drawLine(self.oldMouseX[1], self.oldMouseY[1], self.mouseX[1], self.mouseY[1])
                painter.end()

                # Update the visible pixmap
                self._scenes[self.mouseX[0]].items()[0].setPixmap(pixmap)

        self.oldMouseX = self.mouseX
        self.oldMouseY = self.mouseY

    def populateRampAndExit(self, event):

        ramp = self.colorparms[0].eval()
        bases = [hou.rampBasis.Linear] * len(self.samplepositions)
        keys = [i/float(len(self.samplepositions)) for i, x in enumerate(self.samplepositions)]

        values = []

        for s, x, y in self.samplepositions:
            _color = QColor(self._screenshots[s].toImage().pixel(x, y))
            values.append((pow(_color.red()/255.0,2.2),pow(_color.green()/255.0,2.2),pow(_color.blue()/255.0,2.2)))

        self.colorparms[0].set(hou.Ramp(bases, keys, values))

        self.closeCaptures()
        self.close()


class CaptureAndEmbed(ScreensCapture):
    def __init__(self, parent, editor):
        super(CaptureAndEmbed, self).__init__(parent)

        self.captureregionstartpos = QPoint(-1,-1)
        self.startedcropregion = False
        self.captureregion = QRect()
        self.networkeditor = editor

        self.originalscreenshots = []

        for i, view in enumerate(self._views):
            view.mouseReleaseEvent = self.captureRegion
            view.mouseMoveEvent = self.drawCaptureRegionRect
            self.originalscreenshots.append(self._screenshots[i].copy())

    def drawCaptureRegionRect(self, event):
        self.getMousePos(event)

        if not self.startedcropregion:
            self.captureregionstartpos = QPoint(self.mouseX[1], self.mouseY[1])
            self.startedcropregion = True

        self.captureregion = QRect(self.captureregionstartpos, QPoint(self.mouseX[1], self.mouseY[1]))

        pixmap = self.originalscreenshots[self.mouseX[0]].copy()
        painter = QPainter(pixmap)

        pen = QPen()
        pen.setWidth(2)
        pen.setColor(QColor('#FFCC4D'))

        # Draw a point
        painter.setPen(pen)
        painter.drawRect(self.captureregion)
        painter.end()

        # Update the visible pixmap
        self._scenes[self.mouseX[0]].items()[0].setPixmap(pixmap)


    def captureRegion(self, event):

        pixmap = self.originalscreenshots[self.mouseX[0]].copy(self.captureregion)

        filename = hou.text.expandString("$HIP/captures/capture_{}.png".format(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
        if not os.path.isdir(hou.text.expandString("$HIP/captures/")):
            os.makedirs(hou.text.expandString("$HIP/captures/"))

        pixmap.save(filename)
        labutils.add_network_image(self.networkeditor, filename, scale=0.1, embedded=True)

        self.closeCaptures()
        self.close()


# These functions are called from the UI
def sample_ramp_color(parms):
    win = SampleColor(hou.qt.mainWindow(), parms)
    win.show()

def capture_and_embed(editor):
    win = CaptureAndEmbed(hou.qt.mainWindow(), editor)
    win.show()