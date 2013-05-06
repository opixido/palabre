# -*- coding: utf-8 -*-

# Palabre - palabreServer.py
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

import socket
import asyncore
import string
import signal
import sys
import os
import sys

from datetime import datetime
from palabre import logger,logging, version,config
from palabreClient import PalabreClient
from palabreRoom import PalabreRoom

useDatabase = False
if config.has_option('database','usedatabase') and config.get('database','usedatabase') == 'true':
    import adodb
    useDatabase = True
    
usePassword  = False
if config.has_option('database','checkpassword') and config.get('database','checkpassword') == 'true':
    usePassword = True
    
    
    
class PalabreServer(asyncore.dispatcher):
    """PalabreServer Class - Main Class

     This class open the port and listen for connections
     It is the first to be initialized and instanciates
     the rooms and clients upon requests.
    """

    # Class to instanciate upon connection
    channel_class = PalabreClient


    def __init__(self, HOST='', PORT=2468, rootPassword=''):
        """ Constructor of the server

        Defines many variables

        @HOST = Which Adress to listen to, Default : listens on all available interfaces
        @PORT = Which Port to listen on, Default : 2468
        @rootPassword = Defines the root password, to administrate the server (shutdown, ...)

        <Returns nothing"""

        # Version
        self.version = version

        # Root password
        self.rootPassword = rootPassword

        # Connection informations
        self.HOST = HOST
        self.PORT = PORT

            
        # Connected clients and available rooms
        self.allNickNames = {}
        self.allRooms = {}

        self.logger = logger

        # Vive asyncore
        try:
            asyncore.dispatcher.__init__(self)

            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.set_reuse_addr()
            self.bind((self.HOST, self.PORT))
            self.listen(5)
        except:
            logger.error("Error while starting: Network address and port already in use ?")
            sys.exit()

        if self.HOST == "":
            showHost = "All interfaces"
        else:
            showHost = self.HOST


        logger.info("Running on: %s" % showHost)
        logger.info("Port: %s" % self.PORT)

        if self.HOST == '127.0.0.1' or self.HOST == 'localhost':
            logger.info('Palabre is running on local Interface')
            logger.info('No other computer will be able to access it')
        else:
            logger.info('Palabre is running on a public interface')
            logger.info('Other computers will be able to access it')


        # Loading modules
        self.loadModules()
        
        # Si la connexion s'est bien passée on se connecte à la BDD
        self.connectToBdd()
             
        # Module Action
        self.doAction('onStartup')



    def loadModules(self):
        # Loading Palabre Modules
        self.modules = []
        if config.has_option('modules','list'):
            modules =  config.get('modules','list')
            modules = modules.strip().split(",")
           
            # Adding modules to self.modules
            for p in modules:
                p = p.strip()
                if len(p) > 0 :
                    self.modules.append(p)
            
        
        # Init Modules vars
        self.loadedModules = {}
        self.modulesActions = {}
        self.nodesActions = {}
        
        # How many modules to load       
        self.logger.info(str(len(self.modules))+' Module(s) to load')
        
        modsPath = os.path.join(os.getcwd(),'modules')
        #print "MODSPATH : "+ str(modsPath)        
        sys.path.append(modsPath)
        # Initating Modules
        for p in self.modules:
            
            
            try:
                
                # Trying to import Module
                #exec("from modules import "+p)
                """
                __import__(p)
                logger.info('Module : %s Loaded',p)
                self.loadedModules[p] = eval(p+"."+p+"(self)")"""
                mod = __import__(p)
                             
                self.loadedModules[p] = eval("mod."+p+"(self)")
                #self.loadedModules[p] = self._modules[]
                logger.info('Module : %s Loaded',p)  
            except Exception, inst:
                
                # Module failed to load
                logger.error('ERROR : %s ',inst)
                logger.error('Module : %s  Failed to load',p)
        
        # How many modules have succesfully loaded
        self.logger.info(str(len(self.loadedModules))+' Module(s) loaded')
        
        
        
        
        
        
        
    def registerAction(self,action,module):
        """
            Allows a module to register a specific action
            Everytime this action while be executed,
            the same module method will be called
        """
        
        # If action is not yet defined ... create array
        if(not self.modulesActions.has_key(action)):
            self.modulesActions[action] = []
            
        # Append modulename to this actions list
        self.modulesActions[action].append(module)
        
        return
    
    
    def removeAction(self,action,module):
        """
            removes an action fo a specific module
        """
        
        if self.modulesActions.has_key(action):
            self.modulesActions[action].remove(module)
        
        
    def registerNode(self,node,module):
        """
            Allows a module to register a specific node
            Everytime this node is received
            the same module method will be called
        """
        
        # If action is not yet defined ... create array
        if(not self.nodesActions.has_key(node)):
            self.nodesActions[node] = []
            
        # Append modulename to this actions list
        self.nodesActions[node].append(module)
        
        return
    
    
    def removeNode(self,action,module):
        """
            removes a node action fo a specific module
        """
        
        if self.nodesActions.has_key(action):
            self.nodesActions[action].remove(module)
            
            
            
    def doAction(self,action,*params):
        """
            Executes a specific module action
        """
        
        if(self.modulesActions.has_key(action)):            
            for mod in self.modulesActions[action]:
                eval("self.loadedModules['"+mod+"']."+action+"(params)")
                
    def doNode(self,nodeName,node,client):
        """
           Executes an action when a specific node is received 
        """
        retr = 0
        if(self.nodesActions.has_key(nodeName)):
             for mod in self.nodesActions[nodeName]:
                retr += 1
                self.loadedModules[mod].doNode(nodeName,node,client)
                
        return retr
        
    def connectToBdd(self):
        """
           Connection to the Database if specified in palabre.conf
        """
        
        self.dbHost = config.get('database','dbHost')
        self.dbUser = config.get('database','dbUser')
        self.dbPassword = config.get('database','dbPassword')
        self.dbDatabase = config.get('database','dbDatabase')
        self.dbType = config.get('database','dbType')
        self.dbRequest = config.get('database','dbRequest')
        
        self.dbOK = False
                
        # Connexion BDD
        if useDatabase:
            db = adodb.NewADOConnection(config.get('database','dbType'))

            if db:
                db.useExceptions = False
                
                conn = False

                try:
                    conn = db.Connect(self.dbHost,self.dbUser,self.dbPassword,self.dbDatabase)
                except Exception,err:
                    logger.error('BDD : '+str(err))
                   
                if conn:
                    logger.info('Connection to BDD      OK')
                    self.dbOK = True
                else:
                    logger.error('Connection to BDD      ERROR')
                
                db.Close()        
            else:

                logger.error('Connection to BDD     ERROR')
                if usePassword:
                    logger.error('Nobody will be able to log in')
            
                
        else:
            logger.info("Connection to BDD      SKIPPED")


    def getDbLink(self):
        """
           Connection to the Database if specified in palabre.conf
        """
        # Connexion BDD
        if useDatabase and self.dbOK :
            
            db = adodb.NewADOConnection(self.dbType)

            if db:
                db.useExceptions = False
                conn = False
                
                try:
                    conn = db.Connect(self.dbHost,self.dbUser,self.dbPassword,self.dbDatabase)
                except Exception,err:
                    logger.error('BDD : '+str(err))
                    return None
                    
                if conn:
                    return db
     
        return None
            
            
    def handle_accept(self):
        """Handle incoming connections
        Defines class variable channel_class
        """
        conn, addr = self.accept()
        self.channel_class(self,conn,addr)


    def handle_close(self):
        """When shuting down the server
        Closes log file
        Shutdown the server
        """
        self.logFile.close()
        self.serverShutDown()




    def writable(self):
        """
            ...
        """
        return 0




    def serverShutDown(self):
        """
            When asked to shutdown the server by root
        """

        self.doAction('onShutdown')
        logger.warning("Server shutdown requested")

        """ On envoit un message à tous les clients """

        for p in self.allNickNames.values():
            p.clientSendErrorMessage(msg="### Server is now going down ... ###")
            p.close()

        self.close()
        # !!!!DIRTY HACK ALERT!!!!
        # we have to find another way to do this
        # os._exit is indeed a very dirty hack and should not be used at all.
        # indeed i suck and don't understand much of what i do
        # the previous comment and its poor english was graciously 
        # brougth to you by lekma
        # indeed (i am so f***ing tired and it's only 20:13)
        #os._exit(0)


    def serverClientExists(self, nickName):
        """Method to know if a user exists and is connected
            @nickName : nickName to test
        """

        if nickName != "" and self.allNickNames.has_key(nickName):
            if isinstance(self.allNickNames[nickName], PalabreClient):
                return True

        return False



    def serverRmClient(self, nickName, rootUser):
        """Method to handle a kick off
            @nickName : Client to kick !
            @rootUser : Root user who asked for the kick

        """
        self.doAction('onRemoveClient',nickName)
        if self.serverClientExists(nickName):
            self.allNickNames[nickName].clientSendErrorMessage("You have been kicked from the server by an administrator")
            self.allNickNames[nickName].clientQuit()
            rootUser.clientSendInfoMessage("Client %s kicked" % nickName);
        else:
            rootUser.clientSendErrorMessage("No user connected with nickname: %s" % nickName);


    def serverClientQuit(self, nickName):
        """Method to handle a client deconnection

        @nickName : Nickname of the client to disconnect.

        <Returns nothing"""
        
        self.doAction('onClientQuit',nickName)
        
        logger.info("Client left: %s" % nickName)



        # Check if it really exists
        if nickName != "" and self.allNickNames.has_key(nickName):
            del self.allNickNames[nickName]

        # Notify every rooms
        # We should only notify its rooms,
        # But PalabreClient Instance might already be detroyed
        # So we lost all informations ....
        for p in self.allRooms.values():
            p.roomRemoveClient(nickName)



    def serverSendToClientByName(self, nickName, msg, type):
        """ Method to send a message to ONE specific clients

        @nickName Nickname of the client
        @msg Body of the message to send
        @type Type = "error" ? or classic message.

        Then passes the message to client Instance via clientSendErrorMessage() or clientSendMessage()

        <Returns nothing"""

        # Client Nickname must exist
        if self.allNickNames.has_key(nickName):

            # Un client peut envoyer un messsage d'erreur ? à vérifier
            if type == "error":
                self.allNickNames[nickName].clientSendErrorMessage(msg)
            else:
                self.allNickNames[nickName].clientSendMessage(msg)



    def serverSendMessageToClient(self, data, sender, dest,nodeName='m',attrs={}):
        """ Method to send a message from a client to another (private message)
        @data : Body of the message to send
        @sender : Nickname of the sender
        @dest : nickName of the recipient

        <returns Nothing """

        # Si le sender existe ainsi que le destinataire c'est ok
        # Normalement le sender existe puisque cette méthode est appellée par une instance client
        attrs['f'] = sender
        msg = self.formatMessage(nodeName,attrs,data)

        # Sender and recipient must exists
        if self.allNickNames.has_key(sender) and self.allNickNames.has_key(dest):
            self.allNickNames[dest].clientSendMessage(msg = msg)




    def serverSendToAllClients(self, data, sender):
        """ Method to broadcast a message to everyone
         @data : Message to broadcast
         @sender : Sender of the message

         Should be only a method for "root"
        """
        # Creating message
        data = "<m f='%s'>%s</m>" % (sender, data)

        # Sending to everyone
        for p in self.allNickNames.values():
            p.clientSendMessage(msg=data)




    def serverSendAdminMessage(self, msg):
        """ Broadcast a technical Message
         @msg Message to send
        """

        # Admin rulez ... Broadcast everything
        for p in self.allNickNames.values():
            p.clientSendMessage(msg=data)



    def serverSendToRoom(self, data, sender, room, back):
        """ Method to send a message from a client to a specific room

         @data Message to send
         @sender Nickname of the sender
         @room Name of the room to send the message to
         @back BOOLEAN Should we send the message back to the sender to ? usefull for debug but use more bandwidth

         Does this room exist ?"""

        if self.allRooms.has_key(room):
            # We call the room
            self.allRooms[room].roomSendToAllClients(msg=data, nickName=sender, back=back)
        else:
            self.allNickNames[sender].clientSendErrorMessage(msg="No room by that name")


    def serverGetRoom(self, room):
            """
                Method to get informations about a particular room

                @room : Room to get information about
            """

            if self.allRooms.has_key(room):
                return self.allRooms[room].roomGetInfo()
            else:
                return "<error>No room by that name</error>"


    def isNickOk(self, nickName):
        """ Before accepting a nickname checking if it acceptable (non empty and non existant)
         @nickName Nickname requested

        return boolean
        """
        # Si il est pas vide et pas déjà prit
        if nickName != "" and not self.allNickNames.has_key(nickName):
            return True
        else:
            return False




    def serverAddClientToRoom(self, client, room='', parentR=''):
        """A client is trying to join a rooms

        This room may not exist, if so, we create it

        @client : Nickname of the client
        @room : Name of the room to join(create)
        @parentR : If we want to create a Sub Room, name of the ParentRoom (must exist)

        <Returns the instance of the Room
        
        """


        # La room existe déjà ?
        if self.allRooms.has_key(room):
            # On demande à la room de rajouter ce client
            self.allRooms[room].roomAddClient(client=client)
        else:
            # On demande à la room de se créer avec comme opérateur ce client
            self.allRooms[room] = PalabreRoom(name=room, title='', client=client, server=self, parentR=parentR)

        # On retourne l'instance room au client
        return self.allRooms[room]


    def serverAddClient(self,client):
        """When a client connects

        After identification (nickname) we add this client to self.allNickNames[]

        @client ; client Instance

        """

        self.allNickNames[client.nickName] = client






    def serverSendRoomsToClient(self, client):
        """A client ask for the list of all rooms (<getrooms />)

        We send him the list in XML :
            <rooms nb="NUMBER_OF_ROOMS">
                <room name="NAME">
                    <param name="PARAM">VALUE</param>
                </room>
            </rooms>

        For room name and params we call the Room Instance.roomShowParams();

        @client : Client Instance
        """

        listeR = "<rooms nb='%i'>" % len(self.allRooms)
        for p in self.allRooms.values():
            listeR += "\n" + p.roomShowParams()
        listeR += "\n</rooms>"
        client.clientSendMessage(msg=listeR)


    def serverRemoveRoom(self, room):
        """When a room is empty it is automaticaly destroyed

        @room : Room name
        """

        if self.allRooms.has_key(room):
            del self.allRooms[room]



    def isRootPass(self, password):
        """Checking Root Password

        @password : password to check

        <Returns Boolean"""

        # On pourrait tout aussi bien le stocker dans la base de donnée
        if password == self.rootPassword and self.rootPassword != '':
            return True
        else:
            return False



    def isAuthorized(self, nickName, attrs,client):
        """
        Done With ADODB

        OLD VERSION :            
                c = self.db.cursor()
                res = c.execute("SELECT * FROM t_connexions WHERE connexion_code LIKE '"+nickName+"'")

                c.execute("DELETE FROM t_connexions WHERE connexion_code LIKE '"+nickName+"'")
        """
        
        if usePassword:
            
             if(self.modulesActions.has_key('isAuthorized')):
                for mod in self.modulesActions['isAuthorized']:
                    res = self.loadedModules[mod].isAuthorized(nickName,attrs,client)
                    if res:
                        return True
                return False

             elif attrs.has_key('password'):
                db = self.getDbLink()
                sql = self.dbRequest
                
                sql = sql.replace("[LOGIN]" , db.quote(nickName))                
                sql = sql.replace("[PASSWORD]", db.quote(attrs['password']))
                
                res = db.Execute(sql)

                db.Close()
                
                if res.RecordCount():
                   return True
                else:
                   return False
             else:
                 return False                
        else:
             return True

  
    def formatMessage(self,nodeName,attrs,texte):
        """
            Returns the XML string of the message
        """

        xml = "<"+nodeName
        for p in attrs:
            if p != "c" and p != "toclient" and p != "toroom" and p !="b" and p != "back":
                # @TODO BUG with the DOUBLE QUOTE CHAR
                # HOW DO I ESCAPE THIS ????
                val = str(attrs[p])
                
                if val.find('"') and not val.find("'"):
                    xml += ' '+p+'=\''+val.replace('"','\\"')+'\''
                else:
                    xml += ' '+p+'="'+val.replace('"','&quot;')+'"'
                

        xml += ">"+texte+"</"+nodeName+">"

        return xml
