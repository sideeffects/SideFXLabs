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

FLAGS   = enum("NORMAL", "HIGHLIGHT", "NA")


class MyDelegate(QtWidgets.QItemDelegate):
    def __init__(self, parent=None):
        QtWidgets.QItemDelegate.__init__(self, parent)


class Model(QtCore.QAbstractTableModel):
    
    def __init__(self, appModel, headerNames, nodePath="", parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._logger = logging.getLogger(__name__)

        # manage columns header names and extend the list if it's too short
        self._headerNames = headerNames
        if len(self._headerNames) < self.columnCount(parent):
            n = self.columnCount()-len(self._headerNames)
            self._headerNames.extend([""]*n)

        self._appModel = appModel   # the dcc wrapper
        self._nodePath = nodePath   # the node path
        self._nodeDict = {}         # contains node's parameters name, label, value...
        self._displayList = []      # list of parms to display; it could contain more/less parameters than the nodeDict

    def rowCount(self, parent):
        return len(self._displayList)

    def columnCount(self, parent):
        return 6

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self._headerNames[section]

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
            if self._displayList[row][3] != FLAGS.NA:
                return self._displayList[row][column]

        if role == QtCore.Qt.TextAlignmentRole:
            if column == 2:
                return (QtCore.Qt.AlignCenter)
            # else:
            #     return QtCore.Qt.AlignVCenter

        if role == QtCore.Qt.ForegroundRole:
            if self._displayList[row][3] == FLAGS.NA:
                return QtGui.QColor(80, 80, 80, 255)

        if role == QtCore.Qt.BackgroundRole:
            if self._displayList[row][3] == FLAGS.HIGHLIGHT:
                return QtGui.QColor(253, 103, 33, 100)

        if role == QtCore.Qt.FontRole:
            if self._displayList[row][3] == FLAGS.NA:
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
            parms = [{"path": self._displayList[row][4], "value": str(value)}, ]

            # tell appModel to set the parms
            try:
                self._appModel.setParms(parms)
            except Exception as e:
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
            if column is 2:
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
        """ Builds a dictionary with node's parameters name, value, flag and path. 
        The dictionnary is built as follow:
            {parameter name 1: {dictionnary with name, label, value, path},
             parameter name 2: {dictionnary with name, label, value, path},
             ...
             parameter name n: {dictionnary with name, label, value, path},
            }
        """
        # empty node dictionnary first
        self._nodeDict = {}
        # get the node parameters as a list of paths...
        paths = self._appModel.getParms(self._nodePath)
        # ... then build a list of [name, value, flag, path]...
        parmlist = []
        for path in paths:
            name = self._appModel.getName(path)
            label = "%s (%s)" % (self._appModel.getLabel(path), name)
            value = self._appModel.evalAsString(path)
            flag = FLAGS.NORMAL
            show = True
            parmlist.append({'name': name, 'label': label, 'value': value, 'flag': flag, 'path': path, 'show': show})

        for parm in parmlist:
            self._nodeDict[parm['name']] = parm

    def buildDisplayList(self):
        """ Defines the list of parameters to display in the spreadsheet.
        Note: this list can be different from the node's full parameter list. 
        It can contain extra parameters that are not available on the node itself.
        For instance if this spreadsheet is used by the Diff widget, then the display
        list could contain spare parameters from one of the other nodes it is compared to.
        """
        # nodeDict is a dictionnary built as follow:
        # {parameter name 1: {dictionnary with name, label, value, path},
        #  parameter name 2: {dictionnary with name, label, value, path},
        #  ...
        #  parameter name n: {dictionnary with name, label, value, path},
        # }
        
        # create an empty list
        parmlist = []
        for x in self._nodeDict.values():
            # reminder: x is a dictionnary, see comment above
            parm = list(x.values())
            parmlist.append(parm)

        # and sort it by the first key of each item
        # parmlist.sort(key=lambda x: str(x[0]))

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
            for row in self._displayList:
                if row[0] in self._nodeDict.keys():
                    name = row[0]
                    row[1] = self._nodeDict[name]['label']
                    row[2] = self._nodeDict[name]['value']
                    if row[3] != FLAGS.HIGHLIGHT:
                        row[3] = self._nodeDict[name]['flag']
                    row[4] = self._nodeDict[name]['path']
                    row[5] = self._nodeDict[name]['show']
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
