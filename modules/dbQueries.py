# -*- coding: utf-8 -*-

# Palabre - dbQueries.py
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


# Module to execute arbitrary SQL queries
# DO NOT USE ON PRODUCTION
# ONLY FOR DEMONTRATION PURPOSE !!
# ANY UPDATE / DROP / INSERT QUERY CAN BE DONE !

class dbQueries:
	
	def __init__(self,server):

            # Name ... for future references
            self.name = 'dbQueries'
            
            # Always usefull to have the global server object
            self.server = server

            # When server will load, it will call my onStartup method
            self.server.registerAction('onStartup',self.name)

            # When a DB node is sent by a client,
            # Palabre will forward it to me ...
            self.server.registerNode('db',self.name)            
            
            return

            
            
        
        def onStartup(self,params):
            """
                onStartup is triggered on server load                
            """
            if not self.server.dbOK:
                
                self.server.logger.error('dbQueries:DATABASE ACCESS IS NOT CONFIGURED')
                self.server.logger.error('dbQueries:I won\'t accept any request')
                
                self.server.removeNode('db',self.name)
                
                return
            
            
            
            self.server.logger.error('!!! WARNING !!!')
            self.server.logger.error('!!! DBQUERIES PLUGIN IS HERE FOR DEMO ONLY')
            self.server.logger.error('!!! DON\'T USE ON PRODUCTION ENVIRONMENT')
            
            return
        
        
        
        
        def doNode(self,nodeName,node,client):
            """
                This method is triggered everytime a registered node is received
            """
            
            # If node DB received, then executing query
            # This module is only registered for DB ..
            # so nothing else should append here
            if(nodeName == 'db'):
                
                # Get Database Link
                db = self.server.getDbLink()
                
                # Avoid big fatal exceptions
                db.useExceptions = False
                
                # For Utf 8 - @todo use as parameter
                db.Execute('SET NAMES utf8')
                
                
                # For now ... no error
                error = False
                res = False     
                """ try:
                    # Go query Go !"""
                res = db.Execute(node['text'])
                """except Exception,inst:
                    # Bad query .... better luck next time
                    error = str(inst)
                    self.server.logger.info('DB ERROR : '+error+' / '+node['text'])
                   """
                
                # No result this time ...
                # At least we tell you why ...
                if(not res):                    
                    res = db.ErrorMsg()
                    resstr = str(res)
                    # Sending to the client the db_error node
                    if res[0] != "(":
                        mess = self.server.formatMessage('db_error',{'code':res[0]},res[1]+" / "+resstr)
                    else:
                        mess = self.server.formatMessage('db_error',[],resstr)
                    client.clientSendMessage(mess)                    
                    return
                
               
                # Wohoo at this point we have results !
                curNb = 0
                xml = ""
                
                # Looping over results to return them as XML
                while not res.EOF:
                    
                    # arr has Field Name in Keys and Field value in ... guess ...
                    arr = res.GetRowAssoc(0) # 0 is lower, 1 is upper-case
                    
                    # One more result
                    curNb += 1
                    xml += "\n<row >"
                    
                    # Looping over the fields to create XML
                    for key, val in arr.items():
                        key = str(key)
                        val = str(val)
                        xml += "\n   <"+key+">"+val+"</"+key+">"
                        
                    # End of rows
                    xml += "\n</row>"
                    
                    # As Brel used to sing ... Au suiiiivaaant !!
                    res.MoveNext()
                
                # Formating the XML Message
                # Three parameters are added to the DBRES Node
                # COUNT = number of results
                # AFFECTED = Number of affected Rows (for UPDATES, ...)
                # INSERTED = Last Inserted Id for auto_increment Fields
                mess = self.server.formatMessage('dbres',{'count':res.RecordCount(),'affected':res.Affected_Rows(),'inserted':res.Insert_ID()},xml)
                #print mess
                # Sending all this mess ...
                # Have a good parsing time ...
                client.clientSendMessage(mess)
                
            
            
            return
       
