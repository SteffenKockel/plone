from zope.interface import Interface
from zope.interface import implements

from plone.app.portlets.portlets import base
#from plone.portlets.interfaces import IPortletDataProvider

from zope import schema
from zope.formlib import form
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName

from groovecubes.webmail.interfaces import IIMAPFolderPortlet
from groovecubes.webmail import webmailMessageFactory as _

from zope.i18nmessageid import MessageFactory
from Products.Archetypes.utils import shasattr


class Assignment(base.Assignment):
    """Portlet assignment.

    This is what is actually managed through the portlets UI and associated
    with columns.
    """

    implements(IIMAPFolderPortlet)

    @property
    def title(self):
        """This property is used to give the title of the portlet in the
        "manage portlets" screen.
        """
        return _(u"IMAP folder")


class Renderer(base.Renderer):
    """Portlet renderer.

    This is registered in configure.zcml. The referenced page template is
    rendered, and the implicit variable 'view' will refer to an instance
    of this class. Other methods can be added and referenced in the template.
    """
    
    
    
    
    def __avail(self):
        return getattr(self.context, "has_imap_connection", False)
    
    @property
    def available(self):
        return self.__avail()
        #return shasattr(self.context, "has_imap_connection")
    
    def getIMAPFolders(self):
        return self.context.webmail_tool.getConfig()
    
    render = ViewPageTemplateFile('imapfolderportlet.pt')


class AddForm(base.NullAddForm):
    """Portlet add form.

    This is registered in configure.zcml. The form_fields variable tells
    zope.formlib which fields to display. The create() method actually
    constructs the assignment that is being added.
    """

    def create(self, data):
        return Assignment(**data)