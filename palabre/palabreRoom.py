# -*- coding: utf-8 -*-

# Palabre - palabreRoom.py
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
import asynchat
import string
import datetime

from palabre import logging,logger

class PalabreRoom :
    """
    Class for the rooms

    This is the main class instantiated at every room OR child room

    """


    def __init__(self, name, title, client, server, parentR=''):
        """Constructor of the class

        Two main dictionnaries in this Class :
            allNickNames [ client , type ]
                List of clients in this rooms
                Only type for now is +o for operator
            allParams [ name ] = value
                Defines the properties of the room
                (title, closed, password, readonly, ...)
                TODO

        @name : Name of the room
        @title : Title of the room (as a param)
        @client : Instance of the client creating this room (he will be operator)
        @server : instance of the server that handle this room
        @parentR : ParentRoom if this one is a child room


            Constructeur
            allNickNames est une dico [ client , type ]
            type = '+o'
            allParams est aussi un dico
            il permet de définir des propriétés d'une room (title, closed, open, password ...)
        """

        # Serveur ...
        self.server = server

        # Is this a sub room (parentR is defined)
        if parentR != '':
            self.hasParent = 1
            self.parentRoom = self.server.allRooms[parentR]
        else:
            self.hasParent = 0


        # Room Name
        self.name = name


        # Number of messages in this room
        self.nbMessages = 0

        # Creation Time
        self.createdTime = datetime.datetime.utcnow()
                
        # All the clients
        self.allNickNames = {}

        # Client creator of the room is Op
        self.allNickNames[client.nickName] = [client,'+o']

        # Title of the room
        # Si un titre est passe on l'ajoute
        self.allParams = {'title':title,'openParams':'0'}

        # All the sub rooms of this room
        # La liste des rooms filles
        self.childRooms = {}

        # Send message to client that created the room
        # On dit au client qu'il s'est bien connecte à cette room
        msg = "<joined room='%s' />" % self.name
        client.clientSendMessage(msg=msg)

        # And sending him every informations for this room
        # Et on lui montre les rooms filles, les paramètres et les clients
        self.roomShowChildRooms(nickName=client.nickName)
        self.roomShowParams(nickName=client.nickName)
        self.roomShowClients()

        logger.debug("Palabre room '%s' created by %s(%s)" % (name, client.nickName, client.addr))
        
        self.server.doAction('onRoomInit',self)


    def isClientInRoom(self, nickName):
        """Method to check if a client is connected to this room

            Retourne si le nickname donné est présent dans la room

        @nickName : nickName to test

        <Returns Boolean"""
        if self.allNickNames.has_key(nickName):
            return True
        else:
            return False



    def isClientOperator(self, nickName):
        """Method to know if client is OP

            Retourne si le client est opérateur de la room ou non

        @nickName : nickName to test

        <Returns Boolean"""

        # allNickNames[XXX][1] = le statut
        if self.allNickNames[nickName][1] == "+o":
            return True
        else:
            return False


    def roomSetParam(self, name, value, nickName):
        """Method to define parameters of the room

            Client must be in this room AND OP

            Permet de définir les paramètres de cette room


        @name : Name of the parameter
        @value : Value of the parameter
        @nickName : Name of the client that requested this change


        """

        # Le client est il dans la room ?
        if self.isClientInRoom(nickName):

            # Est-il opérateur
            if self.isClientOperator(nickName) or ( ( self.allParams['openParams'] == '1' or self.allParams['openParams'].lower() == 'true')  and name != 'openParams' ):

                #Defining Param
                # On set le param
                self.allParams[name] = value

                # Sending params to everyone

                # On génère un message de mise à jour
                msg = self.roomShowParams('',name)

                # On envoit ce message à tout le monde
                for p in self.allNickNames.values():
                    p[0].clientSendMessage(msg=msg)

                # If this is a child room send everything to parent room
                # Si il a une room parent, on lui dit de renvoyer les informations également
                if self.hasParent:
                    self.parentRoom.roomShowChildRooms()


    def roomRemoveParam(self, name, nickName):
        """Method to remove a parameter

            permet de supprimer un paramètre
            de la room

        @name : Parameter to remove
        @nickName : Nickname of the client that requested the change
            Client must be op in this room
        """

        # Le client est il dans la room ?
        if self.isClientInRoom(nickName):

            # Est-il opérateur
            if name != 'openParams' and ( self.isClientOperator(nickName) or (  self.allParams['openParams'] == '1' or self.allParams['openParams'].lower() == 'true') ) :

                # On supprime le parametre si il existe
                if self.allParams.has_key(name):
                    del self.allParams[name]

                # On fait les mises à jours nécessaires
                msg = self.roomShowParams()
                for p in self.allNickNames.values():
                    p[0].clientSendMessage(msg=msg)



    def roomSendToAllClients (self, msg, nickName, back, nodeName = 'm',attrs={}):
        """Sending a message to everyone in the room

        --On envoit le message à tous les clients de la room

        @msg : Message to send
        @nickName : nickName of the sender
        @back : Should we send the message back to the sender too ?

        """


        # sender must be in the room
        if self.isClientInRoom(nickName):

            # formating message
            # on formate le message
            #msg = "<m f='%s' r='%s'>%s</m>" % (nickName, self.name,msg)
            texte = msg
            attrs['f'] = nickName
            attrs['r'] = self.name
            
            msg = self.server.formatMessage(nodeName,attrs,texte)
            # Should we send the message back ?
            # We split the code here for faster sending if back = true
            self.nbMessages += 1
            # Le sender a t'il demandé un renvoit ?
            if str(back) == "0":
                # Si non on l'envoit à tout le monde sauf lui
                for p in self.allNickNames.values():
                    Tclient = p[0]
                    if Tclient.nickName != nickName:
                        p[0].clientSendMessage(msg=msg)
            else:
                # Si oui on envoit à tout le monde
                for p in self.allNickNames.values():
                    p[0].clientSendMessage(msg=msg)
        else:
            self.server.serverSendToClientByName(nickName=nickName, msg="You are not in this room",type="error")



    def roomShowParams(self, nickName='',onlyParam=''):
        """Method to send informations about this room

        This method is sending the name, the parent, the number of clients, and all the params

            --On formate les différents paramètres de la room
            --Et on envoit au client qui les demande ou on retourne
            --le XML

        @nickName : If we send this only to one person. If empty we return the XML string

        <returns the XML string"""

        # Si cette room a un parent le tag est un peu différent
        if self.hasParent:
            msgP = "<room name='%s' clients='%i' parent='%s' >" % (self.name, len(self.allNickNames), self.parentRoom.name)
        else:
            msgP = "<room name='%s' clients='%i' >" % (self.name, len(self.allNickNames))


        if onlyParam != '' :
            msgP += "\n <param name='%s' value='%s' />" % (onlyParam, self.allParams[onlyParam])

        else:
            # On ajoute tous les paramètres
            for p in self.allParams.items():
                msgP += "\n <param name='%s' value='%s' />" % (p[0], p[1])

        msgP += "\n</room>"

        # On envoit au client qui l'a demandé si il existe
        if self.isClientInRoom(nickName):
            self.allNickNames[nickName][0].clientSendMessage(msgP)
            return msgP
        # Sinon on retourne la liste à la fonction qui m'a appellé
        else:
            return msgP


    def roomGetInfo(self):
        """ Method to get various informations about a room

        """

        xml = "<roominfo name='%s'>" % self.name

        xml += "<params>"

        # Adding parameters
        for p in self.allParams.items():
            xml += "\n <param name='%s' value='%s' />" % (p[0], p[1])

        xml += '</params>'


        xml += "<clients >"
        for p in self.allNickNames.keys():
            xml += "\n <client name='%s' />" % str(p)
            
        xml += "\n</clients>"

        xml += "<childrooms >"
        for p in self.childRooms.keys():
            xml += "\n <room name='%s' />" % str(p)
            
        xml += "\n</childrooms>"

        
        xml += "<childrooms >"
        for p in self.childRooms.keys():
            xml += "\n <room name='%s' />" % str(p)
            
        xml += "\n</childrooms>"

        xml += "<infos>"
                
        xml += "<info name='createdtime' value='%s' />" % str(self.createdTime)
        #xml += "<info name='nbclients' value='%i' />" % self.allNickNames.length
        xml += "<info name='nbmessages' value='%i' />" % self.nbMessages
                
        xml += "</infos>"
        xml += "</roominfo>"


        return xml
        

                
                
                

    def roomAddClient(self,client):
        """ When a client Joins the room

            Client must NOT be in this room already
            then we send him everything

        @client : Client instance


            Que faire quand un client arrive ?
             - On vérifie qu'il n'est pas déjà là
             - On l'ajoute
             - On lui dit qu'il a été ajouté
             - On lui envoit tous les paramètres

        """
        nickName = client.nickName
        if self.isClientInRoom(nickName):
            self.server.serverSendToClientByName(nickName=nickName, msg="You are already in this room", type="error")
        else:

            # Sending information to all clients
            msg = "<client name='%s' joined='%s' />" % (client.nickName,self.name )
            for p in self.allNickNames.values():
                p[0].clientSendMessage(msg=msg)
            
            # Sending information to joined client
            self.allNickNames[nickName] = (client,"")
            msg="<joined room='%s' />" % self.name
            client.clientSendMessage(msg=msg)
            
            self.roomShowChildRooms(nickName=nickName)
            self.roomShowParams(nickName=nickName)
            self.roomShowClients()
            if self.hasParent == 1:
                self.parentRoom.roomShowChildRooms()



    def roomLeaveClient(self, nickName):
        """A client is leaving the room

            Removing everything from allNickNames and notifying parent room

        @nickName : Nickname of the client

             A client leaves
             On le supprime de la liste
        """


        if self.isClientInRoom(nickName):
            del self.allNickNames[nickName]
            if self.hasParent == 1:
                self.parentRoom.roomShowChildRooms()
        else:
            self.server.serverSendToClientByName(nickName=nickName, msg="You are not in this room", type="error")



    def roomShowClients(self):
        """Sends the client list to everyone

            Called when someone join or leave the room

            On envoit la liste des clients de la room
            à tous les clients
        """

        # On formate le tag XML
        liste = "<clients room='%s' nb='%i'>" % (self.name, len(self.allNickNames))
        for p in self.allNickNames.keys():
            
            params = self.allNickNames[p][0].getXmlParams()
            if params == '':
                liste +=  "\n  <client name='%s' />" % str(p)
            else :
               liste +=  "\n  <client name='%s' >" % str(p)
               liste += params
               liste += "\n  </client>" 
        liste = liste + "\n</clients>"

        # On envoit à tout le monde
        for p in self.allNickNames.values():
            p[0].clientSendMessage(msg=liste)




    def roomAddChildRoom(self, childR):
        """Adds a child room

            When we create a child room, we add it to self.childRooms.
            And then we notify every client in this room

            Une sous-room a été créée sous moi
            Je me tiens au courant et j'informe les utilisateurs
        """

        self.childRooms[childR.name] = childR
        self.roomShowChildRooms()
        
        


    def roomRemoveChildRoom(self, child):
        """When a child room is empty we remove it

        @child : child room instance

            Plus personne dans une sous-room ?
            Alors on la supprime de la liste
            et on informe tout le monde
        """

        if self.childRooms.has_key(child.name):
            del self.childRooms[child.name]
            if len(self.allNickNames) == 0 and len(self.childRooms) == 0:
                self.removeRoom()
            else:
                self.roomShowChildRooms()


    def roomShowChildRooms(self, nickName=""):
        """Sends the XML string of the child rooms

        @nickName : if non empty sends only to that specific client

            On envoit la liste des sous-rooms
            à un utilisateur ou à tous selon le paramètre nickName
        """

        # On formate le XML
        msg = "<childrooms name='%s'>" % self.name

        # On demande à chaque room de nous retourner ses paramètres
        for p in self.childRooms.values():
            msg += p.roomShowParams()

        msg += "\n</childrooms>"

        # Si on a un nickName on envoit au client donné
        if self.isClientInRoom(nickName):
            self.allNickNames[nickName][0].clientSendMessage(msg=msg)

        # Sinon à tout le monde
        else:
            for p in self.allNickNames.values():
                p[0].clientSendMessage(msg=msg)

    def removeRoom(self):
        """Removing THIS room

            We notify the server and the parent room that we are removing
        """

        logger.debug("Palabre room '%s' will be removed" % self.name)
        self.server.serverRemoveRoom(room=self.name)

        if self.hasParent:
            self.parentRoom.roomRemoveChildRoom(child=self)


    def roomRemoveClient(self, nickName):
        """Removing a client from the list

        @nickName : Name of the client that leaves

        on Supprime un client de la liste

        """

        if self.isClientInRoom(nickName):
            del self.allNickNames[nickName]
            if len(self.allNickNames) == 0 and len(self.childRooms) == 0:
                self.removeRoom()
            else:
                msg = "<client name='%s' left='%s' />" % (nickName,self.name )
                for p in self.allNickNames.values():
                    p[0].clientSendMessage(msg=msg)
                self.roomShowClients()
                if self.hasParent:
                    self.parentRoom.roomShowChildRooms()

