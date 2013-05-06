# -*- coding: utf-8 -*-

# Palabre - __init__.py
#
# Copyright 2003-2005 Célio Conort
#
# This file is part of Palabre.
#
# Palabre is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2, or (at your option) any later version.
#
# Palabre is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with program; see the file COPYING. If not,
# write to the Free Software Foundation, Inc., 59 Temple Place
# - Suite 330, Boston, MA 02111-1307, USA.

import ConfigParser, logging, os

# version
version = "0.5"
logger = ""


# log setup
levels = {'debug': logging.DEBUG,
              'info': logging.INFO,
              'warning': logging.WARNING,
              'error': logging.ERROR,
              'critical': logging.CRITICAL}



# config file setup
config = ConfigParser.SafeConfigParser()
if os.path.isfile('/etc/palabre.conf'):
    config.readfp(open('/etc/palabre.conf'))
elif os.path.isfile('./etc/palabre.conf'):
    if os.name == "posix":
        print "*** No palabre.conf found in /etc :: Using local one "
    config.readfp(open('./etc/palabre.conf'))
else :
    print "*** No palabre.conf found"
    exit
    
# the following is a workaround, cause contrary to what it claims
# in the documentation, the logging module IS NOT threadsafe!!!
# remember to close it after logging.shutdown()
# 
# now we can configure the logging

#   Old Way
#   logfile = file(config.get("logging", "logfile"), 'a')
#   logging.basicConfig(level=levels[config.get("logging", "loglevel")],
#                    format="%(asctime)s - [%(filename)-24s %(lineno)-4d]: %(process)-5d %(levelname)-8s %(message)s",
#                    stream=logfile)


logger = logging.getLogger("palabre")
logger.setLevel(levels[config.get("logging", "loglevel")])



# Logging to File
if config.get("logging", "logfile") != "" :
    
    hdlr = logging.FileHandler(config.get("logging", "logfile"))
    forma = logging.Formatter("%(asctime)s - [%(filename)-24s %(lineno)-4d]: %(process)-5d %(levelname)-8s %(message)s")
    hdlr.setFormatter(forma)
    logger.addHandler(hdlr)
    if os.name == "nt":
        print "Palabre is logging to : " +config.get("logging", "logfile")
        print "Please see this logfile to know what is going on"
        print "Nothing more will show up here"
        
# Loging to console
else :
    hdlr = logging.StreamHandler()
    forma = logging.Formatter("%(asctime)s : %(levelname)-8s %(message)s")
    hdlr.setFormatter(forma)
    logger.addHandler(hdlr)
    
    logger.info("No log file has been specified")
    logger.info("Palabre will only print log to console")
    
