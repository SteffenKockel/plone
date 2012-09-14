from AccessControl.SecurityInfo import ClassSecurityInfo
from Products.CMFCore.permissions import ManagePortal
from groovecubes.webmail.interfaces.webmailtool import IWebmailTool
from OFS.SimpleItem import SimpleItem
from Products.CMFCore.utils import UniqueObject
from zope.interface import implements
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from zope.app.component.hooks import getSite
from Products.CMFCore.utils import getToolByName

from groovecubes.webmail.errors import NotInMailgroupError
from imapclient import IMAPClient

from ast import literal_eval
import uuid


class WebmailTool(UniqueObject, SimpleItem):
    """ Webmail tool."""
    id = "webmail_tool"
    implements(IWebmailTool)
    meta_type = "Webmail configuration utility."
    security = ClassSecurityInfo()
    plone_tool = 1

    manage_options = (( { 'label': 'edit',
                          'action': 'manage_overview'
                        },
                        {'label':'mailserver users',
                        'action':'manage_mailserver_users'
                        }
                       )+ SimpleItem.manage_options
                      )
    
    
    active=connections = {}
        
    security.declarePrivate('getWrappedServer')             
    def getWrappedServer(self, server):
        """ A helper function to import the needed wrapper class as 
        defined in webmail_properties sheet. 
        
        @param wrapper_name string # the name of the server to connect 
        
        """
        c = self.getConfig()[server]
        wrapper_args = c['mailserver_args']
        wrapper_class = c['mailserver_type']
        
        wrapper = self.getWrapperList()[wrapper_class]
        wrapper = __import__(wrapper, globals(), locals(), [wrapper_class], -1)
        wrapper = getattr(wrapper, wrapper_class)
        wrapped_mailserver = wrapper(c['server_id'], **c)
        return wrapped_mailserver
        
    
    security.declarePrivate('getUserList')
    def getUserList(self, server):
        server = self.getWrappedServer(server)
        return server.getUserList()
    
    
    security.declarePrivate('getMailGroup')
    def getMailGroup(self, login):
        mailgroups = self.getConfig().keys()
        portal = getSite()
        member =  portal.portal_membership.getAuthenticatedMember()
        
        for group in member.getGroups():
            if group in mailgroups:
                return group
        
        raise NotInMailgroupError(member)
        
        
    
    security.declarePrivate('getConfig')
    def getConfig(self):
        portal = getSite()
        servers = literal_eval(portal.portal_properties.webmail_properties.imap_server)
        return servers
    
    
    security.declarePrivate('setConfig')
    def setConfig(self, dict):
        portal = getSite()
        portal.portal_properties.webmail_properties.imap_server = str(dict)
        
    
    security.declarePrivate('getWrapperList')
    def getWrapperList(self):
        portal = getSite()
        return literal_eval(portal.portal_properties.webmail_properties.wrapper)

    
    security.declareProtected(ManagePortal, 'manage_overview')
    manage_overview = DTMLFile('dtml/webmailtool', globals())
    
    
    security.declareProtected(ManagePortal, 'manage_mailserver_users')
    manage_mailserver_users = DTMLFile('dtml/mailservermembertool', globals())

    
    security.declareProtected(ManagePortal, 'manage_addServer')
    def manage_addServer(self, REQUEST=None):
        """ZMI method - form action for tool form.
        """
        if REQUEST.form.get('add_server'):
            new_server = REQUEST.form
            del new_server['add_server']
            new_server['mailserver_type'] = new_server['mailserver_type'][0]
            
            # stuff additional arguments into a dict
            args = {}
            for i in  [x.split("=") for x in new_server['mailserver_args'].split(";")]:
                args[i[0]] = i[1]
            new_server['mailserver_args'] = args
            
            # save new server in webmail_properties
            portal = getSite()
            servers = self.getConfig()
            servers[new_server['server_id']] = new_server
            portal.portal_properties.webmail_properties.imap_server = str(servers)
            
            # create a group corresponding to the mailservers name
            tabs_message=u'values saved'
            groups_tool = getToolByName(getSite(), 'portal_groups')          
            id = new_server['server_id']            
            if not id in groups_tool.getGroupIds():
                groups_tool.addGroup(id)
                tabs_message=u'values saved & group %s created' % id

            return self.manage_overview(manage_tabs_message=tabs_message)
        
    
    security.declareProtected(ManagePortal, 'manage_delServer')
    def manage_delServer(self, REQUEST=None):
        """ZMI method - form action for tool form.
        """
        if REQUEST.form.has_key('delete_server'):
            id = REQUEST.form.get('server_id')
            servers = self.getConfig()
            del servers[id]
            self.setConfig(servers)
             
            message=u'values saved'
            
            groups_tool = getToolByName(getSite(), 'portal_groups')
            if id in groups_tool.getGroupIds():
                groups_tool.removeGroup(id)
                message=u'values saved & group %s deleted' % id
            return self.manage_overview(manage_tabs_message=message)
        
    
    security.declareProtected(ManagePortal, 'manage_addUser')
    def manage_addUser(self, REQUEST=None):
        """ZMI method - form action form the tool form.
        """
        if REQUEST.form.has_key('add_user'):
            f = REQUEST.form
            server = self.getWrappedServer(f['server'])
            passwd = uuid.uuid1().get_hex()
            server.addUser(f['login'], passwd, f['aliases'].split(','), int(f['quota_max_mb']))
            message = "Added user %s to server %s." % (f['login'],f['server'])
            return self.manage_mailserver_users(manage_tabs_message=message)

    
    security.declareProtected(ManagePortal, 'manage_updateUser')        
    def manage_updateUser(self, REQUEST=None):
        """ ZMI method - form action for the update_user form
        """
        if REQUEST.form.has_key('update_user'):
            f = REQUEST.form
            server = self.getWrappedServer(f['server'])
            server.updateUser(f['userid'],f['login'], f['quota_max_mb'], 
                              f['aliases[]']+f['newaliases'].split(','))
            message = "Modified user %s on server %s." % (f['login'],f['server'])
            return self.manage_mailserver_users(manage_tabs_message=message)
        

    security.declareProtected(ManagePortal, 'manage_removeUser')
    def manage_removeUser(self, REQUEST=None):
        """ ZMI method - form action for the update_user form.
        """
        if self.request.form.has_key('delete_user'):
            f = REQUEST.form
            server = self.getWrappedServer(f['server'])
            server.removeUser()
            message = "Removed user %s from server %s." % (f['login'],f['server'])
            return self.manage_mailserver_users(manage_tabs_message=message)


    security.declarePrivate('getIMAPConnection')
    def getIMAPConnection(self, login):
        server_id = self.getMailGroup(login)
        server = self.getWrappedServer(server_id)
        return server.getIMAPConnection(login)
            
            
    def getSMPTConnection(self, login):
        pass
    
        
InitializeClass(WebmailTool)