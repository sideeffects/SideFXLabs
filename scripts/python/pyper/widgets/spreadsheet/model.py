# -*- coding: utf-8 -*-
# Copyright: (C) 2014 Bruno Ébé
# Author: Bruno Ébé | contact@brunoebe.com
# License: GNU Lesser General Public License v3.0 | https://www.gnu.org/licenses

"""
Module dealing with the widget's abstract model.

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


import logging
import copy

from pyper.vendor.Qt import QtGui
from pyper.vendor.Qt import QtCore
from pyper.vendor.Qt import QtWidgets


def enum(*enumerated):
    enums = dict(zip(enumerated, range(len(enumerated))))
    enums["names"] = enumerated
    return type('enum', (), enums)

COLUMNS = enum("Name", "Value")
FLAGS   = enum("NORMAL", "NOTEQUAL", "NA")


class MyDelegate(QtWidgets.QItemDelegate):
    def __init__(self, parent=None):
        QtWidgets.QItemDelegate.__init__(self, parent)


class Model(QtCore.QAbstractTableModel):
    
    def __init__(self, appModel, nodePath="", parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._logger = logging.getLogger(__name__)

        self._appModel = appModel
        self._nodePath = nodePath
        self._nodeDict = {}         # a dictionary with the node's parameters name, value, flag and path
        self._displayList = []      # list of parms to display; it could contain more/less parameters than the nodeDict

    def rowCount(self, parent):
        return len(self._displayList)

    def columnCount(self, parent):
        return 2

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return COLUMNS.names[section]

    def getData(self, row, column):
        return self._displayList[row][column]

    def data(self, index, role):
        if not index.isValid():
            return None

        # get row and column values from the index
        row = index.row()
        column = index.column()
        
        if role == QtCore.Qt.DisplayRole:
            return self._displayList[row][column]

        if role == QtCore.Qt.EditRole:
            if self._displayList[row][2] != FLAGS.NA:
                return self._displayList[row][column]

        if role == QtCore.Qt.TextAlignmentRole:
            if column == 1:
                return (QtCore.Qt.AlignCenter)
            else:
                return QtCore.Qt.AlignVCenter

        if role == QtCore.Qt.ForegroundRole:
            if self._displayList[row][2] == FLAGS.NA:
                return QtGui.QColor(80, 80, 80, 255)

        if role == QtCore.Qt.BackgroundRole:
            if self._displayList[row][2] == FLAGS.NOTEQUAL:
                return QtGui.QColor(253, 103, 33, 100)

        if role == QtCore.Qt.FontRole:
            if self._displayList[row][2] == FLAGS.NA:
                font = QtGui.QFont()
                font.setItalic(True)
                return font

    def setData(self, index, value, role=QtCore.Qt.EditRole, quiet=False):
        if not index.isValid():
            return None

        row = index.row()
        column = index.column()

        if role == QtCore.Qt.EditRole:
            # prepare a parm list containing dictionaries (needed by appModel)
            parms = [{"path": self._displayList[row][3], "value": str(value)}, ]

            # tell appModel to set the parms
            try:
                self._appModel.setParms(parms)
            except (Exception, e):
                self._logger.error(e)

            # emit dataChange signal if not quiet
            if not quiet:
                self.dataChanged.emit(index, index)

            # we don't tell the model to refresh itself
            # because it should be done by the receiver of the 'dataChanged' signal, either in the view or its parent

            return True

        return False

    def flags(self, index):
        res = QtCore.Qt.ItemIsSelectable

        # get row and column values from the index
        row = index.row()
        column = index.column()

        if index.isValid():
            item = index.internalPointer()

            # enable the nodes parameters but not the NA ones (non available)
            if self._displayList[row][2] != FLAGS.NA:
                res = res | QtCore.Qt.ItemIsEnabled

            # allow changes of values 
            if column is 1:
                res = res | QtCore.Qt.ItemIsEditable

        return res

    def nodePath():
        """ Path to the node we want to display the parameters. """
        def fget(self): return self._nodePath
        def fset(self, value): 
            self._logger.debug("Refreshing nodePath with node \"%s\"." % value)
            self._nodePath = value
            self.buildNodeDict()
        return locals()
    nodePath = property(**nodePath())

    def nodeDict():
        """ """
        def fget(self): return self._nodeDict
        return locals()
    nodeDict = property(**nodeDict())

    def buildNodeDict(self):
        """ Builds a dictionary with node's parameters name, value, flag and path. """
        # get the node parameters as a list of paths...
        paths = self._appModel.getParms(self._nodePath)
        # ... then build a list of [name, value, flag, path] ...
        parmlist = [[self._appModel.getName(path), self._appModel.evalAsString(path), FLAGS.NORMAL, path] for path in paths]
        # ... and finally convert to dictionary
        self._nodeDict = dict((k[0], k[0:]) for k in parmlist)

    def buildDisplayList(self):
        """ Defines the list of parameters to display in the spreadsheet.
        Note: this list can be different from the node's full parameter list. 
        It can contain extra parameters that are not available on the node itself.
        For instance if this spreadsheet is used by the Diff widget, then the display
        list could contain spare parameters from one of the other nodes it is compared to.
        """
        # build the list
        parmlist = []
        for key, value in self._nodeDict.items():
            parmlist.append(value)
        # and sort it by the first key of each item
        parmlist.sort(key=lambda x: str(x[0]))

        return parmlist

    def setDisplayList(self, parmlist):
        """ Set the display list to the parm list passed as parameter. 
        This is needed in case we want the parent to define the display list."""
        self._displayList = copy.deepcopy(parmlist)

    def fillDisplayList(self):
        """ This function fills the display list with the parameters from the current node. 
        Note: remember that the display list could be different from the node's full parameter list.
        It could contain extra parameters that are not available on the node itself.
        For instance if this spreadsheet is used by the Diff widget, then the display
        list could contain spare parameters from one of the other nodes it is compared to.
        """
        # update values
        if len(self._nodeDict.keys()):
            for parm in self._displayList:
                if parm[0] in self._nodeDict.keys():
                    name = parm[0]                          # name
                    parm[1] = self._nodeDict[name][1]       # value
                    if parm[2] != FLAGS.NOTEQUAL:
                        parm[2] = self._nodeDict[name][2]   # FLAG
                    parm[3] = self._nodeDict[name][3]       # path
        else:
            self.setDisplayList([])

    def refresh(self, parmlist=None):
        """ Refresh the model, defining and then filling the display list. """
        self._logger.debug("Refreshing model %s" % self)

        self.beginResetModel()
        if not parmlist:
            parmlist = self.buildDisplayList()
        self.setDisplayList(parmlist)
        self.fillDisplayList()
        self.endResetModel()
