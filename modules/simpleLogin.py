#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Palabre - helloworld.py
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


class simpleLogin:
    
    
    def __init__(self,server):
        
        self.server = server
        
        self.name = "simpleLogin"
        
        self.server.registerAction('isAuthorized',self.name)

        
        return
    
    
    def isAuthorized(self,nickName,attrs,client):
        """
            Just do what you have to do ...
        """
        
        # Module is pretty cool ... everybody might have a chance
        ret = True
        
        if attrs.has_key('password'):
            # A password ? what for ?
            if attrs['password'] == 'hacker':
                # Oh dear ...
                mess = 'Wooohoo ! You are a hacker ? I won\'t let you in !'               
                ret = False
            else:
                # Ouray !
                mess = 'You sent a password ! congratulations'
                        
        else:
            # I don't mind 
            mess = 'No password was sent ... but it\'s ok anyway, simpleLogin is cool with that ...'
        
        if ret:
            # If you want to test ...
            mess += "\n"+'If you don\'t want to be authorized, send password="hacker" '
            
        # Creating message
        mess = self.server.formatMessage('simplelogin',[],mess)
        
        # Sending
        client.clientSendMessage(mess)
        
        # Return is VERY IMPORTANT !
        # If False, then client WON'T BE ACCEPTED !
        
        return ret    