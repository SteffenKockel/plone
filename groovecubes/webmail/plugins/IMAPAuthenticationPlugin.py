from AccessControl.SecurityInfo import ClassSecurityInfo
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.CMFCore.utils import getToolByName

from Acquisition import aq_inner

from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin,\
    ICredentialsUpdatePlugin
from Products.PluggableAuthService.utils import classImplements
from App.class_init import default__class_init__ as InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile as PTF
from zope.interface import Interface
from base64 import encodestring


_n = "addIMAPAuthenticationPlugin"


manage_addIMAPAuthenticationPluginForm = PTF( 'www/addIMAPAuthenticationPlugin',
                                          globals(),
                                          __name__='manage_addIMAPAuthenticationPluginForm'
                                        )
                                  
class IIMAPAuthenticationPlugin(Interface):
      """Marker"""
      
def addIMAPAuthenticationPlugin(self, id, title='', REQUEST=None):
    """ Add this plugin to Plone PAS """
    o = IMAPAuthenticationPlugin(id, title)
    self._setObject(o.getId(), o)
    
    if REQUEST is not None:
        url = '%s/manage_main?manage_tabs_message=IMAP-Auth+PAS-Plugin+added'  
        REQUEST['RESPONSE'].redirect(url % self.absolute_url())
    
    
    
class IMAPAuthenticationPlugin(BasePlugin):
    """ Map credentials to a user ID.
    """
    meta_type = "IMAP-Authentication PAS plugin"
    security = ClassSecurityInfo()
    
    
    def __init__(self, id, title=None):
        self._setId(id)
        self.title = title

    security.declarePrivate('authenticateCredentials')
    def authenticateCredentials(self, credentials):

        """ credentials -> (userid, login)

        o 'credentials' will be a mapping, as returned by IExtractionPlugin.

        o Return a  tuple consisting of user ID (which may be different
          from the login name) and login

        o If the credentials cannot be authenticated, return None.
        """

        if "login" not in credentials or "password" not in credentials:
            return None
        
        
        #server_tool = getToolByName(self.context, 'webmail_tool')
        #self.servers = server_tool.getDict()

        login=credentials["login"]
        password=credentials["password"]
        
        from imapclient import IMAPClient
        
        context = aq_inner(self)
        server_tool = getToolByName(context, 'webmail_tool')
        servers = server_tool.getDict()
         
        for i in servers.values():
            
            try:
                S = IMAPClient(i["host"], use_uid=True, ssl=True) #@TODO (ssl)          
                S.login(login, password)
                S.logout()
        
                self._getPAS().updateCredentials(self.REQUEST, self.REQUEST.RESPONSE,
                                                 login, password)
                return (login, login)
        
            except StandardError, e:            
                print e  
                continue
        
        return None
       
    #security.declarePrivate('updateCredentials')
    #def updateCredentials(self, request, response, login, new_password):
    #   """ Respond to change of credentials (NOOP for basic auth). """
    #    cookie_str = '%s:%s' % (login.encode('hex'), new_password.encode('hex'))
    #    cookie_val = encodestring(cookie_str)
    #    cookie_val = cookie_val.rstrip()
    #    response.setCookie(self.cookie_name, quote(cookie_val), path='/')


classImplements(IMAPAuthenticationPlugin,
                IIMAPAuthenticationPlugin)
    #            IAuthenticationPlugin)
    #            ICredentialsUpdatePlugin)

InitializeClass(IMAPAuthenticationPlugin)