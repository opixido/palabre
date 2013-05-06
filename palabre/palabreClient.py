# -*- coding: utf-8 -*-

# Palabre - palabreClient.py
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
import asynchat
import xml.dom.minidom as xmldom
import string

from palabre import logging,logger,config


class PalabreClient(asynchat.async_chat):

    def __init__(self,server, conn, addr):
        """Class Constructor

        @nickName   Nickname to identify the user.
        @server     PalabreServer Instance to which we are connected
        @conn       Connection instance
        @addr       Client IP Addr
        @carTerm    Flash sends 'null character' to end a request : \0
        @data       String to increment until "carTerm"
        @loggedIn   Has he supplied a correct nickName ?
        @isRoot     Is Client Root (supplied Root Password)

        @allMyRooms[ ]  Dictionnaries of all rooms this client has joined



        """
        """
            Constructeur du client
            Définition des variable, du 'terminator'
            etc ...
        """

        # Asynchat initialise son client
        # Asynchat initialisation ... (main class for sending and receiving messages */
        asynchat.async_chat.__init__ (self, conn)

        # Pour que le client retrouve le serveur
        self.server = server

        # Pour que le client retrouve sa connexion
        self.conn = conn

        # Adresse Ip ?
        self.addr = addr[0]

        # Quel caractère détermine la fin de l'envoi d'un message ?
        # Null character
        self.carTerm = "\0"
        # self.carTerm = "\n"
        # Inherited from asynchat ..
        self.set_terminator (self.carTerm) # Ici c'est un caractère null (Flash default)

        # list of client Params

        self.clientParams = {}

        # String de réception des données
        self.data = ""

        # Nickname vide tant qu'on a pas recu la balise nickname
        self.nickName = ""

        # Donc on est pas encore logué
        self.loggedIn = 0

        # Liste des rooms où le client est connecté
        self.allMyRooms = {}

        # A t'il fournit le mot magique ?
        self.isRoot = 0

        logger.info("Connection initialized for %s" % self.addr)
        
        self.server.doAction('onClientInit',self)


    def handle_expt():
        """
            Tried to add this because there is sometimes a strange error in the logs


            Pour essayer de deviner d'où vient une erreur qui apparait parfois
            Pour l'instant cette fonction n'est jamais appellée
        """
        logger.debug("****PalabreClient.handle_expt: %s" % repr(self))

    def collect_incoming_data (self, data):
        """
            Everytime we collect data we add the data to the string self.data
            (Untill we encounter a terminator (\0)
            A chaque caractère recu on concatène
        """
        self.data = self.data + data #.decode("utf-8")


    def found_terminator (self):
        """
            Terminator Character has been found !
            So the Xml string should be ok, we start parsing datas

            On vient de trouver le caractère terminator
            On va donc essayer de parser le tout
        """

        # Ligne complète de données
        # The complete XML string
        line = self.data

        # On réinitialise 'data' pour recevoir d'autres informations
        # Reseting data for more data to come ...
        self.data = ''

        # par défaut on essai de parser ca en XML
        # Trying to parse
        self.doParse = 1

        # On essai
        # If string is not really XML this crash :
        line = "<?xml version='1.0' encoding='utf-8' ?>"+line
        #print line
        #line = unicode(line,'utf-8') #.encode('utf-8')
        #print line


        try:
            # Si parseString plante .... c'est que c'était pas du XML
            # Trying to parse data
            self.doc = xmldom.parseString(line)
        except:
            # Donc on envoi un message d'erreur
            # Faut pas abuser non plus ...
            #
            # Sending error message to inform user
            self.clientSendErrorMessage(msg="This is not a valid XML string")
            # Et donc on ne fait rien avec ce string
            #Stop parsing
            self.doParse = 0

        # Si parseString s'est bien passé, on interprète le XML


        if self.doParse:
            # really parsing Data
            self.parseData (data=self.doc)
            # On supprime le doc ...
            self.doc.unlink()





    def parseData(self,data):
        """
            OK terminator was found, and @data is parsed XML !
            We look for the node name and dispatch information to other methods

            Fonction appellée lors de la réception d'un message
            Cette fonction est appellée par l'instance client via FoundTerminator

            Elle appelle d'autres méthodes pour faire les vérifications nécessaires
        """

        # Data must have child nodes
        if len(data.childNodes):
            # On attaque le XML #
            ## On definie des variables ##

            # The only node
            n = data.childNodes[0]

            # And the name of the node !
            # The name defines the function
            #
            node = str(n.nodeName)

            # All atributes of the node
            attrs = {}

            ## on recupere tous les attributs dans un dico ##
            # Looping the attributes
            for p in n.attributes.items():
                attrs[p[0]] = p[1].encode("utf-8")

            # if there is data inside (like CDATA ...)
            texte = ""

            # Getting inside text
            if len(n.childNodes):
                if n.nodeType == n.TEXT_NODE:
                    texte = n.childNodes[0].nodeValue                    
                else:
                    for p in n.childNodes:
                        texte += p.toxml()
                    
                texte = texte.encode("utf-8")
                
                
                
          
            

            # Ok let's start trying to guess what the request is
            if node == "help":
                self.clientSendHelp()
            elif node == "quit":
                self.clientQuit()

            # Le client doit être logué pour faire la majorité des actions
            #
            # Client must be identified
            #
            elif self.loggedIn:
                
                # Module's nodes
                moduleDone = self.server.doNode(node,{'node':n,'attrs':attrs,'text':texte},self)

                ## Si il envoi un message ##
                # He is sending a message
                if node == "msg" or node == "m":
                    self.clientHandleMessage(attrs,texte,'m')


                # Si il ping on pong
                # sending a ping ... getting a pong
                elif node == "ping":
                    self.clientSendPong()

                # Si il veut la liste des salles
                # Asking for room list
                elif node == "getrooms":
                    # Sending this request to the server
                    self.server.serverSendRoomsToClient(self)

                # Si il veut joindre une salle
                # Asking to join a room
                elif node == "join":
                    self.clientJoinRoom(attrs)


                # Si il veut quitter une salle
                # Leaving a room
                elif node == "leave":
                    self.clientLeaveRoom(attrs)

                # Setting a param for a room
                elif node == "setparam":

                    self.clientSetRoomParam(attrs)

                # removing a param from a room
                elif node == "removeparam":
                    self.clientUnsetRoomParam(attrs)

                # Adding or changing Client Param
                elif node == "clientparam":
                    self.handleClientParam(attrs,texte)
            
                # adding a child room
                elif node == "addchild":
                    self.clientAddChildRoom(attrs)

                # Shutdown server
                elif node == "shutdown":
                    # Must Be root
                    if self.isRoot:
                        self.server.serverShutDown()
                # Kick User from entire server !!
                elif node == "rmuser":
                    # Must be root
                    if attrs.has_key('nickName'):
                        if self.isRoot:
                            self.server.serverRmClient(attrs['nickName'],self)

                # Get Informations about a room
                elif node == "getinfo":
                    # Must be root
                    if attrs.has_key('room'):
                        if self.isRoot:
                            self.clientSendMessage(self.server.serverGetRoom(attrs['room']))
                                        
                # This can possibly be any node with attribute that tells me to send
                # this exact same node to the clients or Room
                # I prefer to encapsulate everything in a MSG node,
                # but obviously people like to have their own nodes
                # This could reduce server bandwidth a 'little'
                elif attrs.has_key('toroom') or attrs.has_key('toclient') or attrs.has_key('r') or attrs.has_key('c'):
                    if node != "error":
                        self.clientHandleMessage(attrs,texte,node)
                # something else ?
                # @TODO : Implement a method to add other nodes in a more simple way
                elif moduleDone == 0:
                    self.clientSendErrorMessage(msg="Not a known node")

            ## Si il se connect ##
            # client is connecting
            elif node == "connect":
                self.clientConnect(attrs)

            # Cross domain policy check
            elif node == "cross-domain-request":
                self.sendCrossDomain()
            elif node == "policy-file-request":
                self.sendCrossDomain()
            # Client should REALLY connect
            else:
                self.clientSendErrorMessage(msg="You must login first")

    def handle_close (self):
        """Client Just left without telling us (closing browser window, ...)
            Le client vient de se déconnecter ... 'ala' goret surement
        """

        # asynchat vire le client ... il est plus là
        # This is done later in the close method
        # asynchat.async_chat.close (self)

        # Pour débuguer
        logger.info("Connection lost for %s(%s)" % (self.nickName, self.addr))

        # On tue l'instance client
        self.close()

    def handleClientParam(self,attrs,texte):
        """
            Setting a client param
        """
        if attrs.has_key('name') and attrs.has_key('value'):
                self.clientParams[attrs['name']] = attrs['value']

        self.sendParam(attrs['name'])

    def getXmlParams(self):
        """
            Returns an XML string containing the list 
            of all params for this user
                <param name="XXX" value="XXX" />
                ...
        """
        liste = ""
        params = self.clientParams
        for param in params:
            liste += "\n<param name='%s' value='%s' />" % (param, params[param])
        
        return liste

    def sendParam(self,paramName):
        """
            Every time a param is modified we send the param to all clients of 
            all the rooms we are in
        """

        msg = ""
        attrs = {}
        attrs['name'] = paramName
        attrs['value'] = self.clientParams[paramName]

        for room in self.allMyRooms:
            self.allMyRooms[room].roomSendToAllClients(msg,self.nickName,True,'clientparam',attrs)
            

    def clientQuit(self):
        """Client told us he was leaving !

            Il a demandé de partir proprement .... bravo !
        """
        # Ca marche d'autant mieux
        self.handle_close()

    def isClientInRoom(self,room):
        """Method to know if this client is in a specific room
            @room Room to test

            Permet de savoir si le client est déjà dans la room X
        """

        # La room est-elle dans mon dico ?
        if self.allMyRooms.has_key(room):
            return True
        else:
            return False



    def clientAddChildRoom(self,attrs):
        """Adding a Child Room (sub-room)

            @attrs      XML attributes sent

            Permet à un client de créer une room fille
        """

        # Xml node must have parentroom and childroom attributes !!
        # which room is the mom and which is the little girl
        #
        if attrs.has_key('parentroom') and attrs.has_key('childroom'):
            thisChild = attrs['childroom']
            thisRoom = attrs['parentroom']
            # Client Must be in the parentroom
            # Client must not be in the childroom
            if self.isClientInRoom(thisRoom) and thisChild != '' and not self.isClientInRoom(thisChild):
                # Asking the server to join the room
                self.allMyRooms[thisChild] = self.server.serverAddClientToRoom(client=self,room=thisChild,parentR=thisRoom)
                # Notifying the parent room
                # (SHOULD BE IN : server.serverAddClientToRoom) BUT Problem with allMyRooms
                #
                self.allMyRooms[thisRoom].roomAddChildRoom(childR=self.allMyRooms[thisChild])



    def clientUnsetRoomParam(self,attrs):
        """Removing a room parameter

            Permet à un client +o dans une room de changer des paramètres
            La vérification du +o se passe dans la room
        """

        # Xml node must have a room and a name of param to remove
        if attrs.has_key('room') and attrs.has_key('name'):
            Proom = attrs['room']
            Pname = attrs['name']
            # Client must be in this room
            if self.isClientInRoom(Proom) and Proom != "" and Pname != "":
                # Notifying room
                self.allMyRooms[Proom].roomRemoveParam(name=Pname,nickName=self.nickName)


    def clientSetRoomParam(self,attrs):
        """Setting a room param

            Permet à un client +o dans une room de changer des paramètres
            La vérification du +o se passe dans la room
        """

        # Xml node must have a room and a name of param to remove and a value for the param
        if attrs.has_key('room') and attrs.has_key('name') and attrs.has_key('value'):
            Proom = attrs['room']
            Pname = attrs['name']
            Pvalue = attrs['value']
            # Client must be in this room
            if self.isClientInRoom(Proom)  and Pname != "" and Pvalue != "":
                # Notifying room
                self.allMyRooms[Proom].roomSetParam(name=Pname,value=Pvalue,nickName=self.nickName)

    def clientConnect(self, attrs):
        """Client Just sent the connect node

            <connect nickname='STR1' password='STR2'  />

            Le client envoit une node 'connect'
            On vérifie s'il a un password, un code ...
            On appelle la fonction de vérification éventuellement

        """

        ## A t'il un nickName ? C'est indispensable ##
        # Needs a nickname
        if attrs.has_key('nickname'):

            nickName = attrs['nickname']

            rootpass = ''

            # Root password ?
            if attrs.has_key('rootpass'):
                rootpass = attrs['rootpass']

            # On vérifie si le serveur valide ce nickName
            # Server Must validate the nickName
            if self.server.isNickOk(nickName):

                # is he a root user
                self.isRoot = self.server.isRootPass(rootpass)
                
                # Est-ce qu'on l'autorise à se connecter
                # Is he authorized anyway ?
                if self.server.isAuthorized(nickName, attrs, self) or self.isRoot:

                    # Whoooo everything went smoothly ...
                    self.loggedIn = 1
                    self.nickName = nickName
                    self.server.serverAddClient(self)

                    # Notifying client
                    self.clientSendMessage("<connect isok='1' msg='Your nickname is now : %s'/>" % nickName)

                    self.server.doAction('onClientConnect',self)

                    if self.isRoot:
                        logger.warning("Admin connected: %s(%s)" % (self.nickName, self.addr))
                    else:
                        logger.info("Client connected: %s(%s)" % (self.nickName, self.addr))
                else:
                    
                    self.clientSendErrorMessage(msg="Authentication Error" )
                    
                    self.server.doAction('onClientUnauthorized',self)
                    
            else:
                # Not a good nickname
                self.clientSendErrorMessage(msg="Nickname empty or already taken")
                self.server.doAction('onClientBadnick',self)
        else:
            # not even a nickname
            self.clientSendErrorMessage(msg="No NickName Attribute")
           

    def clientJoinRoom(self,attrs):
        """
            Clients joins a room

            Le client décide de rejoindre une room
            Méthode appellée par parseData
            <join room='XXX' />
        """

        # Xml node must have a room param
        if attrs.has_key('room'):
            room = attrs['room']
            # Est-il déjà dans cette room ?
            #Client must not be in the room
            if self.isClientInRoom(room):
                # Si oui c'est tant pis ....
                self.clientSendErrorMessage(msg="You are already in this room")
            else:
                # Asking server to join the room
                # The server returns the room instance

                # Sinon on l'ajoute à la liste
                self.allMyRooms[room] = self.server.serverAddClientToRoom(self,room)
                self.server.doAction('onClientJoinRoom',self,room)

        else:
            self.clientSendErrorMessage(msg="No room specified")



    def clientHandleMessage(self,attrs,texte,nodeName):
        """Method to handle classic text messages

            @attrs[back OR b]   Should we send the message back to the user (room messages only)?


            Cette méthode gère les messages classiques
            privés ou vers une room
            Client : <msg toclient='STR1'>STR2</msg> OU SHORT VERSION <m c='XXX'>YYY</m>
            Room   : <msg toroom='STR1' back='BOOL1'>STR2</msg> OU SHORT VERSION <m r='STR1' b='BOOL1'>YYY</m>

        """

        # back définit dans le cas d'un message à une room si il souhaite également recevoir ce message en retour
        # Should we send the message back to the user (room messages only)?
        back = "0"
        if attrs.has_key('back'):
            back = attrs['back']
        elif attrs.has_key('b'):
            back = attrs['b']

        # Private Message
        # Un message prive
        if attrs.has_key('toclient'):
            # Asking the server to send the message to other client
            self.server.serverSendMessageToClient(data=texte,sender=self.nickName, dest=attrs['toclient'],nodeName=nodeName,attrs=attrs)
        # Short Version
        elif attrs.has_key('c'):
            self.server.serverSendMessageToClient(data=texte,sender=self.nickName, dest=attrs['c'],nodeName=nodeName,attrs=attrs)


        # Un message dans une room
        # Room message
        elif attrs.has_key('toroom'):
            self.clientSendToRoom(data=texte,room=attrs['toroom'],back=back,nodeName=nodeName,attrs =attrs)
        # Short Version
        elif attrs.has_key('r'):
            self.clientSendToRoom(data=texte,room=attrs['r'],back=back,nodeName=nodeName,attrs=attrs)


        # Un message a tout le monde
        # Broadcast Message to everyone
        # Must Be root
        elif attrs.has_key('broadcast'):
            if self.isRoot:
                self.server.serverSendToAllClients(data=texte,sender=self.nickName)

        # Sinon Ya un problème on sait pas ou l'envoyer
        # Not a good message node, not enough information
        else:
            self.clientSendErrorMessage(msg="No recipient given")




    def clientSendPong(self):
        """Asking a ping getting a pong ...
            Si on recoit un ping
            on envoit un pong
            <ping />
        """

        # C'est plutot basique
        # pretty simple
        self.clientSendMessage("<pong />")

    def clientSendToRoom(self,data,room,back,nodeName='m',attrs={}):
        """Sending message to a room

            @data   The message
            @room   The room
            @back   Should we send the message back ?


            On envoit un message dans une room
        """

        # suis je dedans ?
        # Client must be in room
        if self.isClientInRoom(room):
            # Alors on envoit ... go go go
            # Asking the room to send the message
            self.allMyRooms[room].roomSendToAllClients(msg=data,nickName=self.nickName,back=back,nodeName=nodeName,attrs=attrs)
        else:
            # Booooooo
            self.clientSendErrorMessage(msg="No room by that name")


    def close (self):
        """Client Left the server
            Quand le client vient de se déconnecter
        """

        # Pour info de débug ...
        # Debug information
        logger.info("Disconnection asked by %s(%s)" % (self.nickName, self.addr))

        self.server.doAction('onClientClose',self)
        # On informe l'instance serveur
        # Elle peut donc le supprimer des rooms et de sa liste
        # Notifying Server
        self.server.serverClientQuit(nickName=self.nickName)

        # En fait non on le fait là ... c'est bizarre ?
        # .... hum ....
        if self.server.allNickNames.has_key(self.nickName):
            del self.server.allNickNames[self.nickName]

        # Ca on est déjà censé l'avoir fait ...
        asynchat.async_chat.close (self)




    def clientSendMessage (self, msg):
        """Method to send an XML message to this client
            Méthode d'envoi d'un message au client
            le message doit déjà être formaté en XML
        """

        # On concatène le terminator
        msg = "%s%s" % (msg, self.terminator)

        # On essai de lui envoyer le message
        try:
            # On envoit ....
            self.push(msg)
        except:
            # Sinon il n'est peut etre plus là ????
            logger.debug("Failed to send message to %s(%s)" % (self.nickName, self.addr))


    def clientSendErrorMessage(self, msg):
        """Error message
            Permet de formater un message en XML indiquant au client qu'une erreur s'est produite
            Passer uniquement le texte de l'erreur
        """

        self.clientSendMessage("<error>%s</error>" % msg)



    def clientSendInfoMessage(self, msg):
        """Info message
            Permet de formater un message en XML indiquant au client qu'une erreur s'est produite
            Passer uniquement le texte de l'erreur
        """

        self.clientSendMessage("<info>%s</info>" % msg)



    def clientLeaveRoom(self, attrs):
        """Client leaves a room
            Le client quitte une room
            <leave room='STR1' />
        """

        # Ya t'il le bon paramètre ?
        # XML must have a room param
        if attrs.has_key('room'):
            room = attrs['room']
            # Est-il bien dans cette room (Si oui c'est qu'elle existe)
            # Client Must be in the room
            if self.isClientInRoom(room):
                # On informe la room
                # Notifying room

                self.allMyRooms[room].roomRemoveClient(nickName=self.nickName)

                # On la suprime
                # deleting the room
                del self.allMyRooms[room]
                # On informe le client que c'est OK
                # Notifying client
                self.clientSendMessage(msg="<leaved room='%s' />" % room)
                self.server.doAction('onClientLeaveRoom',self,room)
            else:
                # arf t'es pas d'dans
                self.clientSendErrorMessage(msg="Not a known room")

        # Si pas de bon paramètre ... on fait rien
        else:
            self.clientSendErrorMessage(msg="No room specified")


    def clientSendHelp(self):
        """
            Liste des paramètres possibles
            à documenter
        """

        # A faire , A faire , A faire , A faire , A faire , A faire , A faire , A faire , A faire , ...
        self.clientSendMessage("<help><![[CDATA][First of all send a <connect nickname='XYZ' /> node]]></help>")

    def sendCrossDomain(self):
        """
            Crossdomain generated file
        """
        strcross = "<cross-domain-policy>"
        cd = config.get("crossdomain", "alloweddomains")
        domains = cd.split(" ")
        for domain in domains:
            
            if len(domain) > 3:
                strcross += "<allow-access-from domain='"+domain+"' to-ports='"+config.get("daemon", "port")+"' />"

        strcross += "</cross-domain-policy>"
        
        self.clientSendMessage(strcross)
        
                
