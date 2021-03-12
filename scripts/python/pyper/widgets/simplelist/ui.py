# -*- coding: utf-8 -*-
# Copyright: (C) 2014 Bruno Ébé
# Author: Bruno Ébé | contact@brunoebe.com
# License: GNU Lesser General Public License v3.0 | https://www.gnu.org/licenses

"""
Module dealing with the widget's UI.

Copyright: (C) 2014 Bruno Ébé
Author: Bruno Ébé | contact@brunoebe.com
License:
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.
    
    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


import os
import logging

from pyper.vendor.Qt import QtGui
from pyper.vendor.Qt import QtCore
from pyper.vendor.Qt import QtWidgets
from pyper.vendor.Qt import _QtUiTools


class UiLoader(_QtUiTools.QUiLoader):
    def __init__(self, baseinstance):
        _QtUiTools.QUiLoader.__init__(self, baseinstance)
        self.baseinstance = baseinstance

    def createWidget(self, class_name, parent=None, name=''):
        if parent is None and self.baseinstance:
            return self.baseinstance
        else:
            widget = _QtUiTools.QUiLoader.createWidget(self, class_name, parent, name)
            if self.baseinstance:
                setattr(self.baseinstance, name, widget)
            return widget


class MainWidget(QtWidgets.QWidget):

    def __init__(self, appModel, parent=None):
        """ """
        super(MainWidget, self).__init__(parent)

        # initialize/get the logger
        self._logger = logging.getLogger(__name__)

        # define the application model to use
        self._appModel = appModel
        self._logger.debug("Module %s is using %s application model." % (__name__, self._appModel.name))

        # define parent in case this widget is not part of a parent widget
        if not parent:
            self.setParent(self._appModel.mainQtWindow, QtCore.Qt.Window)

        # setup the UI
        self.setup_ui()

    def setup_ui(self):
        """ """
        
        # build the ui
        uifile = os.path.abspath(os.path.join(os.path.dirname(__file__), "ui/widget.ui"))
        UiLoader(self).load(uifile)
        self.setWindowTitle(__name__.split(".")[-2].capitalize())

        # add a button
        button = QtWidgets.QPushButton("Add item")
        button.clicked.connect(self.addItem)
        self.uiLayout.addWidget(button)

        # add actions
        self.uiList.addAction(self.actionAddItem)

        # create context menu
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.contextMenu = QtWidgets.QMenu(self)
        self.contextMenu.setGeometry(QtCore.QRect(0, 0, 300, 26))
        self.contextMenu.setObjectName("contextMenu")
        self.contextMenu.addAction(self.actionAddItem)
        self.contextMenu.addSeparator()

        # connect actions
        self.actionAddItem.triggered.connect(self.addItem)
        self.customContextMenuRequested.connect(self.showCustomContextMenu)

        # perform some initial actions
        for i in range(10):
            self.addItem("Item %02d" % (i+1))

        # some cosmetics
        self.centerWidget()

    def centerWidget(self):
        """ Centers the widget on screen. (source: https://stackoverflow.com/a/20244839) """
        frameGm = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        centerPoint = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def closeEvent(self, event):
        """ Redefine closeEvent() function to add some logs and eventually file management before quitting the widget. """
        name = __name__.split('.')[-2].capitalize() # note: [-2] to get the name of the module above .ui
        self._logger.info("Closing %s..." % (name))
        self.setParent(None)
        event.accept()
        self._logger.info("%s closed." % (name))

    def showCustomContextMenu(self, point):
        """ Show my custom context menu. """
        self.contextMenu.move(QtGui.QCursor.pos())
        self.contextMenu.show()

    def addItem(self, name="New item"):
        """ Adds item to the uiList element. """
        self.uiList.addItem(name)

