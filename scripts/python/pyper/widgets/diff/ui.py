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

from pyper.widgets import spreadsheet

import importlib
importlib.reload(spreadsheet)

class UiLoader(_QtUiTools.QUiLoader):
    def __init__(self, baseinstance):
        _QtUiTools.QUiLoader.__init__(self, baseinstance)
        self.baseinstance = baseinstance

    def createWidget(self, class_name, parent=None, name=""):
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
        self._logger.debug("%s is using %s application model." % (__name__, self._appModel.name))

        # get the first two selected nodes... 
        srcNodePath = dstNodePath = ""
        selectedNodes = self._appModel.selection()
        if selectedNodes:
            srcNodePath = self._appModel.getPath(selectedNodes[0])
            if len(selectedNodes) > 1:
                dstNodePath = self._appModel.getPath(selectedNodes[1])
        nodePathes = [srcNodePath, dstNodePath]
        
        #... to create the spreadsheets
        self._spreadsheets = []
        self._spreadsheets = [spreadsheet.ui.MainWidget(appModel=self._appModel, nodepath=nodePath, parent=self) for nodePath in nodePathes]

        # define parent in case this widget is not part of a parent widget
        if not parent:
            self.setParent(self._appModel.mainQtWindow, QtCore.Qt.Window)

        # setup the UI
        self.setup_ui()

        # some cosmetics
        self.centerWidget()

    def centerWidget(self):
        """ Centers the widget on screen. (source: https://stackoverflow.com/a/20244839) """
        frameGm = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        centerPoint = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def setup_ui(self):
        """ """

        # build the ui
        uifile = os.path.join(os.path.dirname(__file__), "ui/widget.ui")
        UiLoader(self).load(uifile)
        self.setWindowTitle(__name__.split(".")[-2].capitalize())

        # add widgets
        for sheet in self._spreadsheets:
            self.uiSplitter.addWidget(sheet)

        # add actions
        # self.uiSplitter.addAction(self.actionRefresh)

        # connect signals
        self.actionRefresh.triggered.connect(self.refresh)
        self.uiCheckBox.stateChanged.connect(self.refresh)
        self.uiRefreshBtn.clicked.connect(self.refresh)
        
        spreadsheets = self._spreadsheets
        for idx, spreadsheet in enumerate(spreadsheets):
            # build a temporary list to pair one element to the next in a circular way 
            # so that the last element is paired with the first one
            tmplist = spreadsheets[idx:] + spreadsheets[:idx]
            tableViewSrc = tmplist[0].uiTableView
            tableViewDst = tmplist[1].uiTableView
            # sync the current spreadsheet scrollbar to the next in list (thanks to the circular pairing above)
            tableViewSrc.verticalScrollBar().valueChanged.connect(tableViewDst.verticalScrollBar().setValue)
            # refresh if spreadsheet changes
            refreshFunction = lambda: self.refresh()
            spreadsheet.uiLineEdit.textChanged.connect(refreshFunction)
            tableViewSrc.model().dataChanged.connect(refreshFunction)
            # tableViewDst.model().dataChanged.connect(refreshFunction)
            # sync selection between the two spreadsheets
            selectionModel = tableViewSrc.selectionModel()
            selectionModel.selectionChanged.connect(lambda selected, deselected, id=idx: self.syncSelection(selected, deselected, id))

        self.refresh()

    def closeEvent(self, event):
        name = __name__.split(".")[-2].capitalize() # note: [-2] to get the name of the module above .ui
        self._logger.debug("Closing %s..." % (name))
        self.setParent(None)
        event.accept()
        self._logger.info("%s closed." % (name))

    def syncData(self, topLeftIndex, bottomRightIndex):
        # get the row and model from the index        
        row = topLeftIndex.row()
        model = topLeftIndex.model().sourceModel()
        
        # define source and destination models
        spreadsheetModels = [x.model() for x in self._spreadsheets]
        modelSrc = model
        modelDst = spreadsheetModels[1-spreadsheetModels.index(model)]

        # tell the destination model that we start resetting it
        modelDst.beginResetModel()

        # get the flag from the destination, to check whether the parameter is available
        flag = modelDst.getData(row, 2)

        # get the value from the source
        value = modelSrc.data(topLeftIndex, QtCore.Qt.DisplayRole)

        # get the index in the destination model that we need to set
        index = modelDst.index(row, 1)

        if flag != spreadsheet.model.FLAGS.NA:
            # use setData() in quiet mode not to emit dataChange signal and avoid recursive call to syncData!``
            modelDst.setData(index, value, quiet=True)

        # tell the destination model we are done resetting it
        modelDst.endResetModel()

    def syncSelection(self, selected, deselected, id):
        """Synchronize the spreadsheet selections"""
        spreadsheets = self._spreadsheets
        if id == 1:
            # reverse the list so the srcSpreadsheet contains the correct spreadsheet
            spreadsheets.reverse()
        # assign spreadsheets to src and dst
        srcSpreadsheet = spreadsheets[0]
        dstSpreadsheet = spreadsheets[1]

        # get selection
        selection = srcSpreadsheet.uiTableView.selectionModel().selectedRows()
        rows = [index.model().mapToSource(index).row() for index in selection]
        
        # initialize and build item selection 
        itemSelection = QtCore.QItemSelection()
        for row in rows:
            topSrc = dstSpreadsheet.model().index(row, 0)
            bottomDst = dstSpreadsheet.model().index(row, 1)
            itemSelection.append(QtCore.QItemSelectionRange(topSrc, bottomDst))
        
        # to avoid signals to be sent recursively, we need to block signals before sending new selection to the destination model
        dstSpreadsheet.uiTableView.selectionModel().blockSignals(True)
        # apply selection to the destination selection model
        dstSpreadsheet.uiTableView.selectionModel().select(itemSelection, QtCore.QItemSelectionModel.ClearAndSelect)
        # and then we can reactivate signals
        dstSpreadsheet.uiTableView.selectionModel().blockSignals(False)
        # the problem is that the widget does not know it needs to refresh the ui so we force it to update itself
        self.update()

    def buildDisplayList(self):
        # get the nodes' dictionaries
        srcNodeDict = self._spreadsheets[0].model().nodeDict
        dstNodeDict = self._spreadsheets[1].model().nodeDict

        # and make a list with all non duplicated names
        names = list(set(srcNodeDict.keys()).union(set(dstNodeDict.keys())))

        # first create an empty list
        mylist = []

        # for each name
        for name in names:
            if name in srcNodeDict.keys():
            # if name is on the source node...
                parm = srcNodeDict[name][:]
                parm[1] = "NA"
                parm[2] = spreadsheet.model.FLAGS.NA
                #... and on the destination node
                if name in dstNodeDict.keys():
                    #... then set the flag if values are different
                    if srcNodeDict[name][1] != dstNodeDict[name][1]:
                        parm[2] = spreadsheet.model.FLAGS.NOTEQUAL
                        # but only add the parm to the display parm list if the checkbox is checked
                        if self.uiCheckBox.isChecked():
                            mylist.append(parm)
            # otherwise name is on the destination node (because names is the union of src and dst keys)
            else:
                parm = dstNodeDict[name][:]
                parm[1] = "NA"
                parm[2] = spreadsheet.model.FLAGS.NA

            # add the parm to the display parm list if the checkbox is NOT checked
            if not self.uiCheckBox.isChecked():
                mylist.append(parm)

        # sort mylist by the first key of each item
        mylist.sort(key=lambda x: str(x[0]))

        return mylist 

    def refresh(self):
        self._logger.info("Refreshing diff %s" % self)
    
        if self._spreadsheets:
            # first refresh the spreadsheets so the model is updated
            # this is needed for nodeDict to be up to date
            for spreadsheet in self._spreadsheets:
                spreadsheet.refresh()
    
            # once nodeDict has been updated for each model, build the displayList
            displayList = self.buildDisplayList()
    
            # finally refresh the spreadsheet with the displayList
            for spreadsheet in self._spreadsheets:
                spreadsheet.model().beginResetModel()
                spreadsheet.model().refresh(displayList)
                spreadsheet.model().endResetModel()
