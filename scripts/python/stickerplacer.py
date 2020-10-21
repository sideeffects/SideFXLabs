import sys, os, hou
from hutil.Qt.QtCore import *
from hutil.Qt.QtGui import *
from hutil.Qt.QtWidgets import *

sticker_source_dirs = ["$SIDEFXLABS/misc/stickers"]

if hou.getenv("STICKER_PATH", None) != None:
    sticker_source_dirs.extend(hou.getenv("STICKER_PATH").split(";"))

class StickerPlacer(QDialog):
    def __init__(self, parent):
        super(StickerPlacer, self).__init__(parent)
        self.build_ui()
        self.populate_widget_icons()

    def show_help(self):
        hou.ui.curDesktop().displayHelpPath("/nodes/other/labs--sticker_picker") 
        

    def get_source_dirs(self):
        sticker_dirs = []
        for sourcedir in sticker_source_dirs:
            _expandeddir = hou.expandString(sourcedir)

            if os.path.isdir(_expandeddir):
                subdirs = os.listdir(_expandeddir)

                for file in subdirs:
                    if os.path.isdir(os.path.join(_expandeddir, file)):
                        sticker_dirs.append(os.path.normpath(os.path.join(sourcedir, file)))

        return sticker_dirs

    # def addSectionFromFile(hda_definition, section_name, file_name):
    #     section_file = open(file_name, "r")
    #     hda_definition.addSection(section_name, section_file.read())
    #     section_file.close()
    #     return "SOME PATH"


    def create_sticker(self, item):

        pane_tab = [t for t in hou.ui.paneTabs() if t.type() == hou.paneTabType.NetworkEditor and t.isCurrentTab()]

        if len(pane_tab) > 0 :
            pane_tab = pane_tab[0]

            image = hou.NetworkImage()
            image.setPath(item.data(Qt.UserRole))

            bounds = pane_tab.visibleBounds()
            bounds.expand((-bounds.size()[0]*0.4, -bounds.size()[1]*0.4))
            image.setRect(bounds)

            background_images = pane_tab.backgroundImages() + (image,)
            pane_tab.setBackgroundImages(background_images)

        #self.close()

    
    def build_ui(self):
        
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("Sticker Picker")

        self.listwidget = QListWidget()
        self.listwidget.setViewMode(QListView.IconMode)
        self.listwidget.setDragEnabled(False)


        self.listwidget.setFixedWidth(512)

        self.listwidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.listwidget.setIconSize(QSize(64, 64))

        self.listwidget.itemDoubleClicked.connect(self.create_sticker)
        self.iconset = QComboBox()
        
        self.iconset.addItems(self.get_source_dirs())
        self.iconset.currentIndexChanged.connect(self.populate_widget_icons)

        dialog_box = QVBoxLayout()
        dialog_box.addWidget(self.iconset)
        dialog_box.addWidget(self.listwidget)

        help_box = QHBoxLayout()

        controls_label = QLabel("Press Control + i to edit placed stickers!")
        help_button = QPushButton("More Information")
        help_button.clicked.connect(self.show_help)

        help_box.addWidget(controls_label)
        help_box.addWidget(help_button)
        dialog_box.addLayout(help_box)

        self.setLayout(dialog_box)
        self.setFixedWidth(534)


    def populate_widget_icons(self):

        self.listwidget.clear()

        stickers = []
        active_dir = hou.expandString(self.iconset.currentText())
        if active_dir != "":
            for file in os.listdir(active_dir):
                if os.path.splitext(file)[-1] in [".png", ".jpg"]:
                    _relpath = os.path.normpath(os.path.join(self.iconset.currentText(), file))
                    _abspath = hou.expandString(_relpath)

                    item = QListWidgetItem()
                    icon = QIcon()
                    icon.addPixmap(QPixmap(_abspath), QIcon.Normal, QIcon.Off)
                    item.setIcon(icon)
                    item.setData(Qt.UserRole, _relpath)
                    self.listwidget.addItem(item)

            self.listwidget.update()