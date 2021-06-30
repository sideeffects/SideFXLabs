from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QWidget
from PySide2.QtGui import QColor, QPainter, QPen, QCursor
import hou

class SampleColor(QWidget):
    def __init__(self, parent, parms):
        super(SampleColor, self).__init__(parent)

        self.colorparms = parms
        self.samplepositions = []
        self.mouseX = [-1,-1]
        self.mouseY = [-1,-1]
        self.oldMouseX = [-1,-1]
        self.oldMouseY = [-1, -1]
        self._views =[]
        self._canvass = []
        self._scenes = []
        self.configureScene()
        
    def configureScene(self):

        # Take fullscreen screenshot
        self._screenshots = [x.grabWindow(0) for x in QApplication.screens()]
        self._relscreenrect = [x.geometry() for x in QApplication.screens()]

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

            self._views[i].mouseMoveEvent = self.samplePosition
            self._views[i].mouseReleaseEvent = self.calculateOutPut

            self._views[i].showFullScreen()


    def samplePosition(self, event):
        screenid = QApplication.desktop().screenNumber(event.globalPos())
        cursorloc = [event.globalPos().x()-self._relscreenrect[screenid].x(), event.globalPos().y()-self._relscreenrect[screenid].y()]

        self.samplepositions.append([screenid, cursorloc[0], cursorloc[1]])
        self.mouseX = [screenid, cursorloc[0]]
        self.mouseY = [screenid, cursorloc[1]]

        self.update()


    def paintEvent(self, QPaintEvent):
        pass
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

    def calculateOutPut(self, event):

        ramp = self.colorparms[0].eval()
        bases = [hou.rampBasis.Linear] * len(self.samplepositions)
        keys = [i/float(len(self.samplepositions)) for i, x in enumerate(self.samplepositions)]

        values = []
        
        for s, x, y in self.samplepositions:
            _color = QColor(self._screenshots[s].toImage().pixel(x, y))
            values.append((pow(_color.red()/255.0,2.2),pow(_color.green()/255.0,2.2),pow(_color.blue()/255.0,2.2)))

        self.colorparms[0].set(hou.Ramp(bases, keys, values))

        for view in self._views:
            view.close()
        self.close()

def sample_single_color(parms):
    win = SampleColor(hou.ui.mainQtWindow(), parms)
    win.show()
