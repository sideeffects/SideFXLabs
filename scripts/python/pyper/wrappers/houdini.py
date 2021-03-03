# -*- coding: utf-8 -*-
# Copyright: (C) 2014 Bruno Ébé
# Author: Bruno Ébé | contact@brunoebe.com
# License: GNU Lesser General Public License v3.0 | https://www.gnu.org/licenses

"""
Wrapper to interact with Houdini application.

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
import sys
import logging
import importlib

from pyper.__about__ import *

# import base class
from . import standalone 

# add houdini python libraries to the path
sys.path.append(os.path.join(os.environ['HFS'], "houdini/python2.7libs"))
sys.path.append(os.path.join(os.environ['HFS'], "houdini/python3.7libs"))


class Model(standalone.Model):
    """ Model derived for Houdini from the base class 'standalone.Model'. """

    name = "Houdini"

    def __init__(self, filename=None):
        standalone.Model.__init__(self)

        # import hou module
        self._houmodule = importlib.import_module("hou")
        self._toolutils = importlib.import_module("toolutils")

        # initialize logger
        self._logger = logging.getLogger(__name__)
        self._iconpath = os.path.join(os.environ['HFS'], "houdini/help/icons/small")

        # get and store some environment variables
        self._tempdir = self.getenv("HOUDINI_TEMP_DIR")

        # if a filename is specified, load this file
        if filename and os.path.isfile(filename):
            self._logger.info("Loading houdini scene file: %s" % filename)
            self._houmodule.hipFile.load(filename)

        # define main parent window
        self.mainQtWindow = self._houmodule.ui.mainQtWindow()

    def getenv(self, name):
        return self._houmodule.getenv(name)

    def childCount(self, path):
        return len(self.getChildren(path))

    def evalAsString(self, path):
        return self._houmodule.parm(path).evalAsString()

    def getName(self, path):
        return self.getHoudiniObject(path).name()

    def getPath(self, path):
        return self.getHoudiniObject(path).path()

    def getChildren(self, path):
        return [child.path() for child in self._houmodule.node(path).children()]

    def getHoudiniObject(self, path):
        obj = self._houmodule.node(path)
        if not obj:
            obj = self._houmodule.parm(path)
        return obj

    def getParms(self, path):
        node = self.getHoudiniObject(path)
        if not node:
            return []

        return [p.path() for p in node.parms()]

    def hasChild(self, path):
        if self.childCount(path):
            return True
        return False

    def hasParameter(self, path):
        if self.parmCount(path):
            return True
        return False

    def icon(self, path):
        # if path returns a parameter
        if self._houmodule.parm(path):
            return self._houmodule.qt.createIcon('')

        # path returns a node
        icon = self._houmodule.node(path).type().icon()
        return self._houmodule.qt.createIcon(icon)

        # deprecated: this previous method used icon path to load icons
        #iconPath = os.path.join(self._iconpath, self.getHoudiniObject(path).type().icon().replace("_", "/"))
        #return iconPath

    def isParameter(self, path):
        if self._houmodule.parm(path):
            return True
        return False

    def getLabel(self, path):
        if self.isParameter(path):
            return self._houmodule.parm(path).description()
        else:
            return ''

    #def listParameters(self, path):
    #    node = self.getHoudiniObject(path)
    #    if not node:
    #        return {}
    #
    #    d = {}
    #    for p in node.parms():
    #        d[p.name()] = {"path": p.path(), "value": p.eval()}
    #    return d

    def parmCount(self, path):
        return len(self.getParms(path))

    def playblast(self, outputName):
        if not outputName:
            self._logger.error("No output name specified")
            return

        self._logger.info("Saving playblast to \"%s\"." % outputName)


        # get the current viewpath
        curDesktop  = self._houmodule.ui.curDesktop()
        sceneViewer = self._toolutils.sceneViewer()
        curViewport = sceneViewer.curViewport()
        viewpath    = "%s.%s.%s.%s" % (curDesktop.name(), sceneViewer.name(), "world", curViewport.name())

        # define the options
        options = {}
        options["output"]     = outputName
        options["fstart"]     = self._houmodule.playbar.playbackRange()[0]
        options["fend"]       = self._houmodule.playbar.playbackRange()[1]
        options["step"]       = 1
        options["resx"]       = 960
        options["resy"]       = 540
        options["initsimops"] = True

        # build the command with the options
        cmd = "viewwrite"

        if options.get("fstart") and options.get("fend"):
            cmd = "%s -f %s %s" % (cmd, options.get("fstart"), options.get("fend"))

        if options.get("step"):
            cmd = "%s -i %s" % (cmd, options.get("step"))

        if options.get("resx") and options.get("resy"):
            cmd = "%s -r %s %s" % (cmd, options.get("resx"), options.get("resy"))

        if options.get("initsimops"):
            cmd = "%s -I" % cmd

        cmd = "%s %s '%s'" % (cmd, viewpath, options.get("output"))

        # run the command
        res = self._houmodule.hscript(cmd)
        if res[1]:
            self._logger.error("Error during playblast: %s" % res[1])
            return False

        return True

    def selection(self):
        return [node.path() for node in self._houmodule.selectedNodes()]

    def setParms(self, parms=[]):
        """
        Receives a list of parameters to set.
        Each parameter should be a dictionary with the following keys: ["name", "path", "value", "icon", "type"]
        """
        if not parms:
            self._logger.info("No parameter to set: parm is empty")
            return

        for parm in parms:
            self._logger.info("Setting parameter: %s to %s" % (parm["path"], parm["value"]))
            self._houmodule.parm(parm["path"]).set(parm["value"])

    def translatePath(self, path):
        """
        convenient function to allow each package to convert a
        unix style path to it's own path format
        for instance houdini uses "/"
        """
        return path

    def type(self, path):
        return self.getHoudiniObject(path).type().name()
