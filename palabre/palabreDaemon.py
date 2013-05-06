# -*- coding: utf-8 -*-

# Palabre - palabreDaemon.py
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

# This module is used to fork the current process into a daemon.
# Almost none of this is necessary (or advisable) if your daemon 
# is being started by inetd. In that case, stdin, stdout and stderr are 
# all set up for you to refer to the network connection, and the fork()s 
# and session manipulation should not be done (to avoid confusing inetd). 
# Only the chdir() and umask() steps remain as useful.
# References:
#     UNIX Programming FAQ
#         1.7 How do I get my program to act like a daemon?
#             http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
#     Advanced Programming in the Unix Environment
#         W. Richard Stevens, 1992, Addison-Wesley, ISBN 0-201-56317-7.
#
# History:
#     2001/07/10 by Jürgen Hermann
#     2002/08/28 by Noah Spurrier
#     2003/02/24 by Clark Evans
#
#     http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012

import sys, os, signal, time, threading, traceback, asyncore
from signal import SIGTERM, SIGINT

from palabre import config, logger, logging, logger, version, palabreServer


class palabreMain(threading.Thread):

    def __init__(self):

        threading.Thread.__init__(self)
        self.setDaemon(True)

        # some default
        self.ip = ""
        self.port = 2468
        self.password = ""

        # read config
        if config.has_option("daemon", "ip") and config.get("daemon", "ip"):
            self.ip = config.get("daemon", "ip")
        if config.has_option("daemon", "port") and config.get("daemon", "port"):
            self.port = config.getint("daemon", "port")
        if config.has_option("admin", "password") and \
            config.get("admin", "password"):
            self.password = config.get("admin", "password")

        # These are used to catch startup errors of the asyncore server
        self.startError = None
        self.startedEvent = threading.Event()
    
    def start(self):

        threading.Thread.start(self)
        # as the asyncore.loop doesn't return, we wait 1 sec. to catch errors
        # before the server is declared as started
        self.startedEvent.wait(1.0)
        if self.startError:
            raise self.startError

    def run(self):

        try:
            server = palabreServer.PalabreServer(self.ip, self.port, \
                                                 self.password)
            asyncore.loop()
        except Exception, e:
            logger.exception(str(e))
            self.startError = e
            return


class palabreLogFile:
    """File object class to redirect stdout and stderr."""
    def __init__(self, level):
        """Implement logging levels.
        @level : int -- can be any of:
            CRITICAL    50
            ERROR       40
            WARNING     30
            INFO        20
            DEBUG       10
            NOTSET      0
        """
        self.level = level

    def write(self, msg):
        """Implement the needed write method."""
        logger.log(self.level, msg)


class palabreDaemon:

    def __init__(self):

        self.pidfile = config.get("daemon", "pidfile")
        self.daemon = config.getboolean("daemon", "startdaemon")
                
        if not self.daemon:
            signal.signal(SIGINT, self.sig_handler)

    def control(self, action):

        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if action == 'stop':
            self.stop(pid, False)
        elif action == 'start':
            self.start()
        elif action == 'restart':
            self.stop(pid, True)
            self.start()
        elif action == 'status':
            self.status(pid)

    def start(self):

        logger.info("Starting Palabre...")
        if os.path.exists(self.pidfile):
            if self.daemon:
                sys.stderr.write("Could not start, Palabre is already running (pid file '%s' exists).\n" % self.pidfile)
            logger.warning("Could not start, Palabre is already running (pid file '%s' exists)." % self.pidfile)
            #logger.shutdown()
            #logfile.close()
            sys.exit(1)
        else:
            if self.daemon:
                # Do first fork.
                try: 
                    pid = os.fork () 
                    if pid > 0:
                        # Exit first parent.
                        sys.exit (0)
                except OSError, e: 
                    sys.stderr.write("fork #1 failed: (%d) %s\n" % (e.errno, e.strerror))
                    sys.exit(1)
                    
                # Decouple from parent environment.
                os.chdir("/") 
                os.umask(0) 
                os.setsid() 
                
                # Do second fork.
                try: 
                    pid = os.fork() 
                    if pid > 0:
                        # Exit second parent.
                        sys.exit(0)
                except OSError, e: 
                    sys.stderr.write("fork #2 failed: (%d) %s\n" % (e.errno, e.strerror))
                    sys.exit(1)
    
            # close stdin
            sys.stdin.close()
            # redirect stdout and stderr to logging
            # in case we're not a daemon logging redirects
            # everything to sys.stderr anyway
            sys.stdout = palabreLogFile(20)  # level INFO
            sys.stderr = palabreLogFile(40)  # level ERROR
            # our process id
            pid = int(os.getpid())

            # main call
            try:
                # we send the main server in another thread (i forgot why)
                server = palabreMain()
                server.start()
                # if we get this far, we're started, write pidfile, log...
                file(self.pidfile,'w+').write("%s" % pid)
                logger.info("...started with pid: %s." % pid)
                # ...and sleep.
                while True:
                    time.sleep(1)
                #server.join()
            except Exception, e:
                sys.stdin = sys.__stdin__
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__
                traceback.print_exc()
                sys.exit(1)

    def stop(self, pid, restart):

        logger.info("Stopping Palabre...")
        if not pid:
            if self.daemon:
                sys.stderr.write("Could not stop, Palabre is not running (pid file '%s' is missing).\n" % self.pidfile)
            logger.warning("Could not stop, Palabre is not running (pid file '%s' is missing)." % self.pidfile)
            if not restart:
                #logger.shutdown()
                #logfile.close()
                sys.exit(1)
        else:
            ## There should be a better way, but i'm too lazy to search... but
            ## i'm sure there's a better way
            
            # if we're not a daemon we should clean up before committing suicide
            if not self.daemon:
                os.remove(self.pidfile)
                #logger.shutdown()
                #logfile.close()
            try:
                while True:
                    os.kill(pid,SIGTERM)
                    time.sleep(1)
            except OSError, e:
                if e.strerror.find("No such process") >= 0:
                    os.remove(self.pidfile)
                    if not restart:
                        logger.info("...stopped.")
                        #logger.shutdown()
                        #logfile.close()
                        sys.exit(0)
                else:
                    logger.error("%s" % e.strerror)
                    #logger.shutdown()
                    #logfile.close()
                    sys.exit(1)

    def status(self, pid):

        sys.stdout.write("Palabre %s\n" % version)
        if not pid:
            sys.stdout.write("Palabre is not running.\n")
        else:
            sys.stdout.write("Palabre is running, pid: %s.\n" % pid)

    def sig_handler(self, signo, frame):
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except Exception, e:
            raise
        self.stop(pid, False)
