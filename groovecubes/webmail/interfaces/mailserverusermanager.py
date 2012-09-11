from zope.interface import Interface, Attribute
# -*- Additional Imports Here -*-
from groovecubes.webmail import webmailMessageFactory as _


class IMailserverUserManager(Interface):
    """ An Interface for the membership management 
        of a specific mailserver """
    
    id = Attribute('id', 'must be set to corresponding user group')
    
    def addUser(self, login, password, aliases, max_mailbox_size, **kwargs):
        """Create a user in this Mailserver"""
        

    def removeUser(self, id):
        """Remove user from this Mailserver"""
        

    def setPassword(self, id, password):
        """Change the password for given user"""
        
    
    def getCredentials(self, login):
        """ Returns the users password for later use in 
            imaplib to connect to the server
            
            returns:
            
            password = [md5,plain]:secretpasw0rd
            """
        
    
    def addAlias(self, id, alias):
        """set an alias for given user """
        
    
    def removeAlias(self, id, alias):
        """ remove an alias for a given user"""
        
    
    def getUserList(self):
        """ should return a dict with all necessary user information
        
        {'paul': 'login':'paul',
                 'aliases': ['paul@example.com','p.aul@example.com'],
                 'quota_max_mb': 1000,
                 'quota_cur_mb': 50 
                  }
        """ 