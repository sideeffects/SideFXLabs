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

from . import model
from . import proxymodel


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

    def __init__(self, appModel, nodePath="", parent=None):
        """ """
        super(MainWidget, self).__init__(parent)

        # initialize/get the logger
        self._logger = logging.getLogger(__name__)

        # define the application model to use
        self._appModel = appModel
        self._logger.debug("%s is using %s application model." % (__name__, self._appModel.name))

        # get the first selected node to build the spreadsheet
        if not nodePath:
            selectedNodes = self._appModel.selection()
            if selectedNodes:
                nodePath = selectedNodes[0]

        # define the model and its proxy model
        self._model = model.Model(self._appModel, nodePath)
        self._proxyModel = proxymodel.ProxyModel(self._model)

        # define parent in case this widget is not part of a parent widget
        if not parent:
            self.setParent(self._appModel.mainQtWindow, QtCore.Qt.Window)

        # setup the UI
        self.setup_ui(nodePath)

        # some cosmetics
        self.centerWidget()

    def centerWidget(self):
        """ Centers the widget on screen. (source: https://stackoverflow.com/a/20244839) """
        frameGm = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        centerPoint = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def setup_ui(self, nodePath=""):
        """ """
        # build the ui
        uifile = os.path.join(os.path.dirname(__file__), "ui/widget.ui")
        UiLoader(self).load(uifile)        
        self.setWindowTitle(__name__.split(".")[-2].capitalize())

        # tell the view which model to display
        self.uiTableView.setModel(self._proxyModel)

        # configure the view
        self.uiTableView.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        self.uiTableView.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive)
        self.uiTableView.horizontalHeader().resizeSection(0, 200)
        self.uiTableView.horizontalHeader().resizeSection(1, 50)
        self.uiTableView.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        # define the proxy model needed to sort the view
        self._proxyModel.sort(0, QtCore.Qt.AscendingOrder)

        # define a delegate to override the inherited color palette
        delegate = model.MyDelegate(self)
        self.uiTableView.setItemDelegate(delegate)

        # add actions
        self.uiTableView.addAction(self.actionRefresh)

        # connect signals
        self.actionRefresh.triggered.connect(self.refresh)

        # check whether the parent has a refresh() function and connect it
        if hasattr(self.parent(), 'refresh'):
            functionToConnect = self.parent().refresh
        # otherwise connect the refresh() function of self
        elif hasattr(self, 'refresh'):
            functionToConnect = self.refresh
        self.uiLineEdit.textChanged.connect(functionToConnect)
        
        # initialize uiLineEdit with the node path
        self.uiLineEdit.setText(nodePath)

    def closeEvent(self, event):
        name = __name__.split('.')[-2].capitalize() # note: [-2] to get the name of the module above .ui
        self._logger.info("Closing %s..." % (name))
        self.setParent(None)
        event.accept()
        self._logger.info("%s closed." % (name))

    def model(self):
        return self._model

    def refresh(self, lineEditText="", mylist=None):
        self._model.nodePath = str(self.uiLineEdit.text())
        self._logger.debug("Refreshing spreadsheet with node \"%s\"." % self._model._nodePath)
        self._model.refresh(mylist)
