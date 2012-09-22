from AccessControl.SecurityInfo import ClassSecurityInfo
from Products.CMFCore.permissions import ManagePortal
from groovecubes.webmail.interfaces.webmailtool import IWebmailTool
from OFS.SimpleItem import SimpleItem
from Products.CMFCore.utils import UniqueObject, SimpleItemWithProperties
from zope.interface import implements
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from zope.app.component.hooks import getSite
from Products.CMFCore.utils import getToolByName

from groovecubes.webmail.errors import NotInMailgroupError
from imapclient import IMAPClient

from ast import literal_eval
import uuid
from zope.annotation.interfaces import IAnnotatable, IAnnotations

import logging

from BTrees.OOBTree import OOBTree
from hashlib import sha1

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
                        { 'label': 'mailserver users',
                          'action': 'manage_mailserver_users'
                        }
                       ) + SimpleItem.manage_options
                      )
    
    Logger = logging.getLogger("groovecubes.webmail")
    
    @property
    def _cache(self):
        if getattr(self, '_v_cache', None) is None:
            self._v_cache = OOBTree()
        return self._v_cache
    
    
    def clear_cache(self):
        self._cache.clear()
    
    
    @property
    def portal(self):
        return getSite()
    
    
    @property
    def portal_membership(self):
        return getToolByName(self.portal, 'portal_membership')
    
    
    @property
    def session(self):
        return self.portal.session_data_manager.getSessionData(create=True)
    
    
    @property
    def webmail_properties(self):
        return self.portal.portal_properties.webmail_properties
    
    
    @property
    def servers(self):
        return literal_eval(self.webmail_properties.imap_server)
    
    
    @property
    def wrappers(self):
        return literal_eval(self.webmail_properties.wrapper)
    

    security.declarePrivate('getWrappedServer')             
    def getWrappedServer(self, server, login=None, refresh=False):
        """ 
        A helper function to import the needed wrapper class as 
        defined in webmail_properties sheet. 
        
        @param wrapper_name string # the name of the server to connect 
        """
        _ckey = '%s:%s' % (server, login)
        # print "###############", _ckey, list(self._cache.keys())
        
        if login and self._cache.get(_ckey):
            self.Logger.debug("reuse Wrapper")
            return self._cache[_ckey]

        c = self.servers[server]
        wrapper_args = c['mailserver_args']
        wrapper_class = c['mailserver_type']
        
        wrapper = self.wrappers[wrapper_class]
        
        wrapper = __import__(wrapper, globals(), locals(), [wrapper_class], -1)
        wrapper = getattr(wrapper, wrapper_class)
        wrapped_mailserver = wrapper(c['server_id'], **c)
        
        
        if login and not self._cache.get(_ckey) or refresh:
            self.Logger.info("cache wrapper")
            self._cache.update({_ckey: wrapped_mailserver})
        
        return wrapped_mailserver
    
    
    security.declarePrivate('getIMAPConnection')
    def getIMAPConnection(self, login):
        server = self.getMailGroup(login)
        # print server, "#", login
        _ckey = '%s:%s' % (server, login)
        
        if self._cache.get(_ckey):
            conn = self._cache[_ckey].getIMAPConnection(login)
            return conn
        
        server = self.getWrappedServer(server)
        return server.getIMAPConnection(login)
    
    
    security.declarePrivate('getUserList')
    def getUserList(self, server):
        server = self.getWrappedServer(server)
        return server.getUserList()
        
    
    security.declarePrivate('authenticateCredentials')
    def authenticateCredentials(self, login, password ):
        """
        This extends the plone PAS plugin. Because we don't
        want to register a new plugin for every server, we
        hold a member database here.
         
        Iter over all servers that are
         o registered
         o enabled
        """ 
        if not login or not password or login == 'admin':
            return None
        
        for server in self.servers.keys():
           
            s = self.getWrappedServer(server, login=login)           
            
            if s.authenticateCredentials(login, password):
                return True
        
        return None
    
    
    security.declarePrivate('enumerateUsers')
    def enumerateUsers(self, **kwargs):
        """
        This extends plone PAS plugins abilities to 
        enumerate and look up for users, authenticated
        against external IMAP servers.
        """
        
        key = kwargs.get('id') or kwargs.get('login')
        if not key or key == 'admin':
            return None
        
        # generate a cache key for this query
        _ckey = sha1(repr(kwargs)).hexdigest()
        
        if self._cache.get(_ckey):
            self.Logger.debug("reuse query") # , self._cache.get(_ckey)
            return self._cache[_ckey]
        
        users = []
        for server in self.servers.keys():
            server = self.getWrappedServer(server, login=key)
            users += server.enumerateUsers(**kwargs)
        
        self.Logger.info("cache query")
        self._cache.update({_ckey:users})    
        return users
    
    
    security.declarePrivate('getMailGroup')
    def getMailGroup(self, login):
        mailgroups = self.servers.keys()
        member =  self.portal_membership.getAuthenticatedMember()
        
        for group in member.getGroups():
            if group in mailgroups:
                return group
        
        raise NotInMailgroupError(member)
        
    
    security.declarePrivate('setConfig')
    def setConfig(self, dict):
        self.portal.portal_properties.webmail_properties.imap_server = str(dict)
        
    
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
    
                
InitializeClass(WebmailTool)