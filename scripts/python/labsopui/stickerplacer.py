import os
import hou

from hutil.Qt import QtCore, QtGui, QtWidgets

sticker_source_dirs = ["$SIDEFXLABS/misc/stickers"]

if hou.getenv("STICKER_PATH", None) is not None:
    sticker_source_dirs.extend(hou.getenv("STICKER_PATH").split(";"))

class StickerPlacer(QtWidgets.QDialog):
    def __init__(self, parent):
        super(StickerPlacer, self).__init__(parent)
        self.build_ui()
        self.populate_widget_icons()

    def show_help(self):
        hou.ui.curDesktop().displayHelpPath("/nodes/other/labs--sticker_picker")


    def get_source_dirs(self):
        sticker_dirs = []
        for sourcedir in sticker_source_dirs:
            _expandeddir = hou.text.expandString(sourcedir)

            if os.path.isdir(_expandeddir):
                subdirs = os.listdir(_expandeddir)

                for file in subdirs:
                    if os.path.isdir(os.path.join(_expandeddir, file)):
                        sticker_dirs.append(os.path.normpath(os.path.join(sourcedir, file)))

        return sticker_dirs



    def create_sticker(self, item):

        pane_tab = [t for t in hou.ui.paneTabs() if t.type() == hou.paneTabType.NetworkEditor and t.isCurrentTab()]

        if len(pane_tab) > 0 :
            pane_tab = pane_tab[0]

            image = hou.NetworkImage()
            image.setPath(item.data(QtCore.Qt.UserRole))

            bounds = pane_tab.visibleBounds()
            bounds.expand((-bounds.size()[0]*0.4, -bounds.size()[1]*0.4))
            image.setRect(bounds)

            background_images = pane_tab.backgroundImages() + (image,)
            pane_tab.setBackgroundImages(background_images)

        #self.close()


    def build_ui(self):

        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("Sticker Picker")

        self.listwidget = QtWidgets.QListWidget()
        self.listwidget.setViewMode(QtWidgets.QListView.IconMode)
        self.listwidget.setDragEnabled(False)


        self.listwidget.setFixedWidth(512)

        self.listwidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.listwidget.setIconSize(QtCore.QSize(64, 64))

        self.listwidget.itemDoubleClicked.connect(self.create_sticker)
        self.iconset = QtWidgets.QComboBox()

        self.iconset.addItems(self.get_source_dirs())
        self.iconset.currentIndexChanged.connect(self.populate_widget_icons)

        dialog_box = QtWidgets.QVBoxLayout()
        dialog_box.addWidget(self.iconset)
        dialog_box.addWidget(self.listwidget)

        help_box = QtWidgets.QHBoxLayout()

        controls_label = QtWidgets.QLabel("Press Control + i to edit placed stickers!")
        help_button = QtWidgets.QPushButton("More Information")
        help_button.clicked.connect(self.show_help)

        help_box.addWidget(controls_label)
        help_box.addWidget(help_button)
        dialog_box.addLayout(help_box)

        self.setLayout(dialog_box)
        self.setFixedWidth(534)


    def populate_widget_icons(self):

        self.listwidget.clear()

        stickers = []
        active_dir = hou.text.expandString(self.iconset.currentText())
        if active_dir != "":
            for file in os.listdir(active_dir):
                if os.path.splitext(file)[-1] in [".png", ".jpg"]:
                    _relpath = os.path.normpath(os.path.join(self.iconset.currentText(), file))
                    _abspath = hou.text.expandString(_relpath)

                    item = QtWidgets.QListWidgetItem()
                    icon = QtGui.QIcon()
                    icon.addPixmap(QtGui.QPixmap(_abspath), QtGui.QIcon.Normal, QtGui.QIcon.Off)
                    item.setIcon(icon)
                    item.setData(QtCore.Qt.UserRole, _relpath)
                    self.listwidget.addItem(item)

            self.listwidget.update()
