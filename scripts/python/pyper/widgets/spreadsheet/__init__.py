# -*- coding: utf-8 -*-
# Copyright: (C) 2014 Bruno Ébé
# Author: Bruno Ébé | contact@brunoebe.com
# License: GNU Lesser General Public License v3.0 | https://www.gnu.org/licenses

"""
A widget example that display a list of parameters as spreadsheets.

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

from pyper.__about__ import *
from pyper.utils import logs
from pyper import wrappers
from . import ui

import importlib
importlib.reload(ui)

# global variables
NAME = __name__.split(".")[-1].capitalize()


def run():
    """main run function"""

    # Load the application wrapper
    wrapper = wrappers.importwrapper()
    if not wrapper:
        logger.error("Could not load wrapper %s." % (NAME))
        logger.error("Exiting.")
        return

    # setup logger
    logfile = os.path.join(wrapper.tempdir, "sidefxlabs/%s.log" % NAME.lower())
    logger = logs.setup_logging(__name__, logfile)
    logger.debug("Initializing %s..." % (NAME))

    # Build the UI with the wrapper
    widget = ui.MainWidget(wrapper)
    if not widget:
        logger.error("Could not build %s's widget." % (NAME))
        logger.error("Exiting.")
        return

    # Show the widget
    widget.show()
    logger.debug("%s's interface has been created: %s" % (NAME, widget))
    logger.info("Running %s in %s." % (NAME, wrapper.name.capitalize()))

    # return the widget in case it is needed 
    return widget
