from PySide2.QtCore import Qt, QRect, QEvent, QSize
from PySide2.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QWidget, QLabel, QGraphicsPixmapItem, QGraphicsItem
from PySide2.QtGui import QColor, QPainter, QPen, QCursor, QPixmap, QFont
import hou, datetime, os

class NetworkEditorPainter(QWidget):
    def __init__(self, parent, editor):
        super(NetworkEditorPainter, self).__init__(parent)

        self.networkeditor = editor
        self.mouseX = [-1,-1, 0]
        self.mouseY = [-1,-1, 0]
        self.oldMouseX = [-1,-1, 0]
        self.oldMouseY = [-1, -1, 0]
        self.colorpickeractive = False

        self.brushcolor = QColor('#FFCC4D')
        self.brushsize = 8

        self.startdragpos = -1
        self.configureScene()
        self.updateBrush()
        
    def configureScene(self): 

        _networkeditorsize = self.networkeditor.sizeToScreen(self.networkeditor.visibleBounds().size())

        # Get bottom left screen position of network editor
        self.networkeditor.setCursorPosition(hou.Vector2(0, 0))
        _bottomleftglobalpos = QCursor.pos()
        _bottomleftlocalpos = self.mapFromGlobal(_bottomleftglobalpos)

        # Get top right screen position of network editor
        self.networkeditor.setCursorPosition(hou.Vector2(_networkeditorsize[0], _networkeditorsize[1]))
        _toprightglobalpos = QCursor.pos()
        _toprightlocalpos = self.mapFromGlobal(_toprightglobalpos)

        _networkeditorlocalrect = QRect(_bottomleftlocalpos.x(), _toprightlocalpos.y()-1, _networkeditorsize[0], _networkeditorsize[1])
        _networkeditorglobalrect = QRect(_bottomleftglobalpos.x()+1, _toprightglobalpos.y()+1, _networkeditorsize[0], _networkeditorsize[1])

        self.setGeometry(_networkeditorlocalrect)
        self.graphicsview = QGraphicsView(self)
        self.graphicsview.setSceneRect(0,0,_networkeditorsize[0], _networkeditorsize[1])
        self.graphicsview.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphicsview.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.outputdrawingcanvas = QPixmap(_networkeditorlocalrect.width(), _networkeditorlocalrect.height())
        self.outputdrawingcanvas.fill(Qt.transparent)

        self.graphicsscene = QGraphicsScene(self)
        self.screens = QApplication.screens()

        self.screendimensionrects = [x.geometry() for x in self.screens]
        self.screenshots = [x.grabWindow(0) for x in self.screens]

        screenid = QApplication.desktop().screenNumber(_bottomleftglobalpos)
        _adjustedcrop = QRect(_bottomleftglobalpos.x()-self.screendimensionrects[screenid].x(),_toprightglobalpos.y()-self.screendimensionrects[screenid].y(), _networkeditorsize[0], _networkeditorsize[1])

        self.graphicsscene.addPixmap(self.screenshots[screenid].copy(_adjustedcrop))
        self.instructiontext = QLabel("Hold LMB to draw. ENTER to store drawing or ESC to cancel\nPress i to enable the color picker, then LMB click canvas to pick color\nScrollwheel changes brush size")
        self.instructiontext.setAlignment(Qt.AlignCenter)
        self.instructiontext.setFocusPolicy(Qt.NoFocus)
        self.instructiontext.adjustSize()

        self.instructiontext.move((_networkeditorsize[0]/2) - (self.instructiontext.width()/2), 0)
        
        self.graphicsscene.addWidget(self.instructiontext)
        self.graphicsview.setScene(self.graphicsscene)
        self.graphicsview.viewport().installEventFilter(self)

    def eventFilter(self, source, event):

        if source == self.graphicsview.viewport():
            try:
                screenid = QApplication.desktop().screenNumber(event.globalPos())
                cursorloc = [event.globalPos().x()-self.screendimensionrects[screenid].x(), event.globalPos().y()-self.screendimensionrects[screenid].y()] 
            except: pass

            # LMB Click
            if event.type() == QEvent.MouseButtonPress:
                
                if event.button() == Qt.LeftButton:
                    
                    self.startdragpos = event.pos()
                    self.mouseX = [screenid, event.x(), cursorloc[0]]
                    self.mouseY = [screenid, event.y(), cursorloc[1]]
                    
                    if self.colorpickeractive:
                        self.pickScreenColorForBrush(screenid)
                        self.colorpickeractive = False

                    self.resetMouse()
                    return True
            
            # LMB Drag
            if event.type() == QEvent.MouseMove:

                if self.startdragpos != -1:
                    if (event.pos() - self.startdragpos).manhattanLength() > QApplication.startDragDistance():
                        self.mouseX = [screenid, event.x(), cursorloc[0]]
                        self.mouseY = [screenid, event.y(), cursorloc[1]]
                        self.update()
                        return True

            # Done painting
            if event.type() == QEvent.MouseButtonRelease:
                self.resetMouse()
                self.startdragpos = -1
                return True

        return False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.exportPaintingToEditor()
        if event.key() == Qt.Key_I:
            self.storeScreenColors()
        if event.key() == Qt.Key_Escape:
            self.closeWidget()

    def wheelEvent(self,event):
        if not self.colorpickeractive:
            self.brushsize = max(1, self.brushsize + event.delta()/120)
            self.updateBrush()
        event.setAccepted(True)

    def paintEvent(self, QPaintEvent):

        if self.oldMouseX[1] >= 0 and self.mouseX[1] >= 0 and not self.colorpickeractive:

            if self.oldMouseX[0] == self.mouseX[0]:
                # Make a painter with the visible pixmap. Have to make a new copy since the original reference gets nuked on self.update() :(
                visiblecanvas = [x.pixmap().copy() for x in self.graphicsscene.items() if type(x) == QGraphicsPixmapItem][0]
                pixmaps = [self.outputdrawingcanvas, visiblecanvas]

                for pix in pixmaps:
                    painter = QPainter(pix)
                    pen = QPen()
                    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
                    painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
                    pen.setWidth(self.brushsize)
                    pen.setColor(self.brushcolor)
                    pen.setCapStyle(Qt.RoundCap)
                    painter.setPen(pen)
                    painter.drawLine(self.oldMouseX[1], self.oldMouseY[1], self.mouseX[1], self.mouseY[1])
                    painter.end()

                [x for x in self.graphicsscene.items() if type(x) == QGraphicsPixmapItem][0].setPixmap(visiblecanvas)

        self.oldMouseX = self.mouseX
        self.oldMouseY = self.mouseY

    def pickScreenColorForBrush(self, screenid):
        self.brushcolor = QColor(self.screenshots[screenid].toImage().pixel(self.mouseX[2], self.mouseY[2]))
        self.updateBrush()

    def resetMouse(self):
        self.mouseX, self.mouseY, self.oldMouseX, self.oldMouseY = [[-1,-1, 0] for x in range(4)]
        
    def storeScreenColors(self):
        self.graphicsview.setCursor(QCursor(Qt.PointingHandCursor))
        self.screenshots = [x.grabWindow(0) for x in QApplication.screens()]
        self.colorpickeractive = True

    def updateBrush(self):
        newbrushpix = QPixmap(self.brushsize, self.brushsize)
        newbrushpix.fill(Qt.transparent)
        painter = QPainter(newbrushpix) 
        painter.setBrush(self.brushcolor) 
        painter.drawEllipse(QRect(0,0, self.brushsize, self.brushsize))
        painter.end()
        self.cursor = QCursor(newbrushpix)
        self.graphicsview.setCursor(self.cursor)

    def closeWidget(self):
        self.graphicsview.close()
        self.close()

    def exportPaintingToEditor(self):

        pixmap = [x.pixmap().copy() for x in self.graphicsscene.items() if type(x) == QGraphicsPixmapItem][0]
        pixmap = self.outputdrawingcanvas

        filename = hou.expandString("$HIP/drawings/networkpainting_{}.png".format(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
        if not os.path.isdir(hou.expandString("$HIP/drawings/")):
            os.makedirs(hou.expandString("$HIP/drawings/"))
        pixmap.save(filename)

        image = hou.NetworkImage()
        image.setPath(filename)
        image.setRect(self.networkeditor.visibleBounds())

        background_images = self.networkeditor.backgroundImages() + (image,)
        self.networkeditor.setBackgroundImages(background_images)

        self.closeWidget()

def paint(editor):
    win = NetworkEditorPainter(hou.ui.mainQtWindow(), editor)
    win.show()
