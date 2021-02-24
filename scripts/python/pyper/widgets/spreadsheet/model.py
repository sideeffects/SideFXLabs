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
        self._nodeDict = {}
        self._displayParmList = []  # list meant for display; it could contain more/less parameters than the nodeParmList

        self.refresh()

    def nodePath():
        """path to the node we want to display the parameters."""
        def fget(self): return self._nodePath
        def fset(self, value): 
            self._nodePath = value
        return locals()
    nodePath = property(**nodePath())

    def nodeDict():
        """ """
        def fget(self): return self._nodeDict
        return locals()
    nodeDict = property(**nodeDict())

    def rowCount(self, parent):
        return len(self._displayParmList)

    def columnCount(self, parent):
        return 2

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return COLUMNS.names[section]

    def getData(self, row, column):
        return self._displayParmList[row][column]

    def data(self, index, role):
        if not index.isValid():
            return None

        # get row and column values from the index
        row = index.row()
        column = index.column()
        
        if (role == QtCore.Qt.DisplayRole) | (role == QtCore.Qt.EditRole):
            return self._displayParmList[row][column]

        if role == QtCore.Qt.TextAlignmentRole:
            if column == 1:
                return (QtCore.Qt.AlignCenter)
            else:
                return QtCore.Qt.AlignVCenter

        if role == QtCore.Qt.BackgroundRole:
            if self._displayParmList[row][2] == FLAGS.NOTEQUAL:
                return QtGui.QColor(253, 103, 33, 200)

    def setData(self, index, value, role=QtCore.Qt.EditRole, quiet=False):
        if not index.isValid():
            return None

        row = index.row()
        column = index.column()

        if role == QtCore.Qt.EditRole:
            # prepare a parm list containing dictionaries (needed by the appModel)
            parms = [{"path": self._displayParmList[row][3], "value": str(value)}, ]

            # tell the appModel to set the parms in the scene
            try:
                self._appModel.setParms(parms)
            except (Exception, e):
                self._logger.error(e)

            # emit the dataChange signal if not quiet
            if not quiet:
                self.dataChanged.emit(index, index)

            # and tell the model to refresh itself
            self.refresh()
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
            if self._displayParmList[row][2] != FLAGS.NA:
                res = res | QtCore.Qt.ItemIsEnabled

            # allow changes of values 
            if column is 1:
                res = res | QtCore.Qt.ItemIsEditable

        return res

    def buildNodeDict(self):
        """ Builds a dictionary with node's parameters name, value, flag and path. """
        # get the node parameters as a list of paths...
        paths = self._appModel.getParms(self._nodePath)
        # ... then build a list of [name, value, flag, path] ...
        mylist = [[self._appModel.getName(path), self._appModel.evalAsString(path), FLAGS.NORMAL, path] for path in paths]
        # ... and finally convert to dictionary
        self._nodeDict = dict((k[0], k[0:]) for k in mylist)

    def buildDisplayParmList(self):
        """ Builds the list of parameters to display from the node's dictionary. """
        # empty the current parameter list and fill it
        mylist = []
        for key, value in self._nodeDict.items():
            mylist.append(value)

        # sort it by the first key of each item
        mylist.sort(key=lambda x: str(x[0]))

        return mylist

    def setDisplayParmList(self, parmList):
        """ Set the display list to the argument parmList. """
        self._displayParmList = copy.deepcopy(parmList)

    def fillDisplayParmList(self):
        """ This function fills the display list with the parameters available on the current node. """
        # update values
        for parm in self._displayParmList:
            if parm[0] in self._nodeDict.keys():
                name = parm[0]
                parm[1] = self._nodeDict[name][1]
                parm[3] = self._nodeDict[name][3]
                if parm[2] != FLAGS.NOTEQUAL:
                    parm[2] = self._nodeDict[name][2]

    def refresh(self, mylist=None):
        self._logger.debug("Refreshing spreadsheet's model.")
        self.beginResetModel()

        # first build the node dictionary
        self.buildNodeDict()
        # if no display parameter list is provided, build it 
        if not mylist:
            mylist = self.buildDisplayParmList()
        # set the display parameter list
        self.setDisplayParmList(mylist)
        # fill the display parameter list
        self.fillDisplayParmList()
        
        self.endResetModel()


