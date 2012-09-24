from AccessControl.SecurityInfo import ClassSecurityInfo
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.CMFCore.utils import getToolByName

from Acquisition import aq_inner

from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin,\
    ICredentialsUpdatePlugin, IUserEnumerationPlugin, IGroupsPlugin
from Products.PluggableAuthService.utils import classImplements
from App.class_init import default__class_init__ as InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile as PTF
from zope.interface import Interface
from base64 import encodestring
from zope.component.hooks import getSite


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

    
    #@property
    #def webmail_tool(self):
    #    context = getSite()
    #    return getToolByName(context, 'webmail_tool')
    
    
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

        login = credentials["login"]
        password = credentials["password"]
        
        context = getSite()
        
        webmail_tool = getToolByName(context, 'webmail_tool')
            
        if self.webmail_tool.authenticateCredentials(login, password):
            self._getPAS().updateCredentials( self.REQUEST, 
                                              self.REQUEST.RESPONSE,
                                              login, 
                                              password )
            return (login, login)
        return None
    
    
    security.declarePrivate('enumerateUsers')
    def enumerateUsers(self, **kwargs):
        context = getSite()
        webmail_tool = getToolByName(context, 'webmail_tool')
        users =  webmail_tool.enumerateUsers(pluginid=self.getId(),**kwargs)
        return users
    
    
    security.declarePrivate( 'getGroupsForPrincipal' )
    def getGroupsForPrincipal( self, principal, request=None ):

        """ See IGroupsPlugin.
        """
        context = getSite()
        webmail_tool = getToolByName(context, 'webmail_tool')
        return webmail_tool.getGroupsForPrincipal(principal, request)



classImplements(IMAPAuthenticationPlugin,
                IAuthenticationPlugin,
                IUserEnumerationPlugin,
                IGroupsPlugin)

InitializeClass(IMAPAuthenticationPlugin)