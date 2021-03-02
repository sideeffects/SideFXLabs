# -*- coding: utf-8 -*-
# Copyright: (C) 2014 Bruno Ébé
# Author: Bruno Ébé | contact@brunoebe.com
# License: GNU Lesser General Public License v3.0 | https://www.gnu.org/licenses

"""
Module dealing with the widget abstract proxy model.

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

from pyper.vendor.Qt import QtCore

from .model import FLAGS

class ProxyModel(QtCore.QSortFilterProxyModel):

    def __init__(self, model, parent=None):
        QtCore.QSortFilterProxyModel.__init__(self, parent)
        self._logger = logging.getLogger(__name__)

        self.setSourceModel(model)
        self.setDynamicSortFilter(True)
        
        self._showdiffonly = False

    def showdiffonly():
        """ """
        def fget(self): return self._showdiffonly
        def fset(self, value): 
            self._logger.debug("Set showdiffonly to \"%s\"." % value)
            self._showdiffonly = value
        return locals()
    showdiffonly = property(**showdiffonly())

    def filterAcceptsRow(self, rownum, parent):
        model = self.sourceModel()

        cell = model.index(rownum, 2)
        if self._showdiffonly and (cell.data() != FLAGS.NOTEQUAL):
            return False
        else:
            return True

    def filterAcceptsColumn(self, colnum, parent):
        model = self.sourceModel()

        if colnum in [0, 1, 2, 3, 4]:
            return True
        else:
            return False
