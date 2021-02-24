# -*- coding: utf-8 -*-
# Copyright: (C) 2014 Bruno Ébé
# Author: Bruno Ébé | contact@brunoebe.com
# License: GNU Lesser General Public License v3.0 | https://www.gnu.org/licenses

"""
Module gathering logging related functions.

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
import json
import logging
import logging.config


CWD = os.path.dirname(os.path.abspath(__file__))
LOG_CONFIG = os.path.join(CWD, "config/logconfig.json")


def setup_logging(logger_name, logfile=""):
    """convenience function to setup the logger"""

    configFile = LOG_CONFIG
    
    if configFile and os.path.exists(configFile):
        # create the logfile directory if it does not exist
        logfile = os.path.expanduser(os.path.expandvars(logfile)) 
        directory = os.path.dirname(logfile)
        if not os.path.exists(directory):
            os.makedirs(directory)

        # load the configuration file and configure logging
        with open(configFile) as f:
            logconfig = json.load(f)
            if logfile:
                # change default logfile 
                logconfig['handlers']['file']['filename'] = logfile
            logging.config.dictConfig(logconfig)

    else:
        # if no config file, use the basic configuration from the logging module
        logging.basicConfig(level=logging.INFO)
        logging.warning("No logging configuration file found: using basic configuration.")
        
    logger = logging.getLogger(logger_name)
    return logger

