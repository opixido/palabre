#!/usr/bin/python
# -*- coding:utf-8-*-
#
#

import palabre

from palabre.palabreServer import PalabreServer
import asyncore


ip = ""
port = 2468
password = ""
config = palabre.config
# read config
if config.has_option("daemon", "ip") and config.get("daemon", "ip"):
    ip = config.get("daemon", "ip")
if config.has_option("daemon", "port") and config.get("daemon", "port"):
    port = config.getint("daemon", "port")
if config.has_option("admin", "password") and \
    config.get("admin", "password"):
    password = config.get("admin", "password")

            
myServer = PalabreServer(ip,port,password)

asyncore.loop()
