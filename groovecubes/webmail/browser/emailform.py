from zope import interface, schema
from five import grok
import logging
from plone.directives import form
from z3c.form import button
import z3c.form.interfaces
from plone.formwidget.autocomplete.widget import AutocompleteMultiSelectionWidget
from z3c.relationfield.schema import RelationList, RelationChoice
from plone.formwidget.contenttree import ObjPathSourceBinder
from plone.formwidget.contenttree.interfaces import IContentSource
# from Products.Archetypes.exceptions import AccessControl_Unauthorized
from plone.app.z3cform.wysiwyg import WysiwygFieldWidget
from Products.statusmessages.interfaces import IStatusMessage

from Acquisition import aq_inner, aq_parent
from Products.CMFCore.interfaces import ISiteRoot

from groovecubes.webmail import webmailMessageFactory as _
from groovecubes.webmail.interfaces import IWebmail 
from groovecubes.webmail.browser.attachmentwidget import \
    UploadEnabledMultiContentTreeFieldWidget

from email import MIMEMultipart, MIMENonMultipart

from zope.component import getMultiAdapter

from zope.component.hooks import getSite
from zope.schema.interfaces import IContextSourceBinder

from plone.i18n.normalizer.interfaces import IUserPreferredURLNormalizer
from plone.i18n.normalizer.interfaces import IURLNormalizer

@grok.provider(IContextSourceBinder)
def availableAttachments(context):
    
        path = '/'.join(context.getTmp_folder().getPhysicalPath())
        query = {"portal_type" : ("File","Image"),
                 "path" : {'query' : path }
                 }
        
        Source = ObjPathSourceBinder(navigation_tree_query = query)
        # I spent hours on this piece of code
        # maybe the use of the __call__ method 
        # should be better documented 
        return Source.__call__(context) 
    
       
class IEmailFormSchema(form.Schema):
    # -*- extra stuff goes here -*-

    #form.fieldset('extra',
    #              label=u"extra info",
    #              fields=['body','subject'])
    
    to = schema.TextLine(
        title=_(u'To:'),
        description=_(u'Receiver(s)'),
        required=True,
        readonly=False,
        default=None,
        )
     
    cc = schema.TextLine(
        title=_(u'CC:'),
        description=_(u'Copy to'),
        required=False,
        readonly=False,
        default=None,
        )
     
    subject = schema.TextLine(
        title=_(u'Subject:'),
        description=_(u'The mails subject.'),
        required=True,
        readonly=False,
        default=None,
        )
    
    form.widget(body=WysiwygFieldWidget)
    body = schema.Text(
        title=_(u'Message:'),
        description=u'',
        required=True,
        readonly=False,
        default=None
        )
    
    form.widget(attachments=UploadEnabledMultiContentTreeFieldWidget)
    attachments = RelationList(
        title = _(u'Attachments'),
        description = _(u'Select and upload attachments.'),
        default = [],
        value_type = RelationChoice(
                    title =_(u"attachment"),
                    default = [],
                    source = availableAttachments),
                    
        required = False
        )
    
    ticket = schema.TextLine(
        title = _(u'Session ticket'),
        description = u'',
        required = True,
        readonly = False,
        default = None, 
        )
    



class EmailForm(form.SchemaForm):
    grok.name('write-email') 
    grok.require('zope2.View')
    grok.context(IWebmail)
    schema = IEmailFormSchema
    ignoreContext = True
    
    label = _(u'Write mail')
    description = _(u'')
    
    has_imap_connection = False
    ticket_id = None
    
    @property
    def portal_state(self):
        return getMultiAdapter( (self.context, self.request), 
                                 name="plone_portal_state" )
    
    @property
    def session(self):
        return self.context.session_data_manager.getSessionData(create=True)
    
    
    @button.buttonAndHandler(_(u'Send'))
    def handleSend(self, action):
        data, errors = self.extractData()
        #if errors:
        #    self.status = self.formErrorsMessage
        #    return
        
        print self.request.form['form.widgets.attachment'].filename
        IStatusMessage(self.request).addStatusMessage(
	    u'OK')
        # contextURL = self.context.absolute_url()
        # self.request.response.redirect(contextURL)

    
    @button.buttonAndHandler(_(u'Cancel'))
    def handleCancel(self, action):
        contextURL = self.context.absolute_url()
        self.request.response.redirect(contextURL)
        
    
    def handleAttach(self):
        """ This method handles attachment uploads  and 
            gets triggered by an ajax request.
            
            before we reached this point we checked for:
            
            - authentication
            - session ticket
            
            to make shure, we don't receive unwanted uploads.
        """
        
        portal = getSite()
        file = self.request.form['upload-%s' % self.context.title]
        path = '/'.join(self.context.getTmp_folder().getPhysicalPath())
        encoding = portal.getProperty('email_charset', 'utf-8')
        # get the webmails tmp folder
        container = portal.restrictedTraverse(path)
        # normalize the filename
        filename = unicode(file.filename, encoding, "ignore")
        filename = IUserPreferredURLNormalizer(self.request).normalize(filename)
        
        # maybe that is unneccessary
        type = "File"    
        if filename.endswith(('png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg')):
            type = "Image"
        
        # create upload in tmp folder
        
        # overwrite existing files with same name
        if hasattr(container, filename):          
            del container[filename]
        
        container.invokeFactory(type , filename, file = file)
        # this results in a "tabula rasa" sharing tab, thus
        # only the owner (and admin) should be able to see
        # this items
        container[filename].__ac_local_roles_block__ = True
        
        
    def update(self):
        super(EmailForm, self).update()
        print "##", self.request.form
        
        # get the session ticket-id and lookup in the users 
        # session for this ticket.
        self.ticket_id = self.request.form.get('form.widgets.ticket')
        self.ticket = self.session.get(self.ticket_id, None)
        # print "##", self.ticket_id, self.ticket
        
        # do a redirect in case this form has no session ticket or
        # we have a non authenticated user.
        #if not self.ticket_id or self.portal_state.anonymous():
        
        #    context = aq_inner(self.context)
        #    self.request.response.redirect(context.absolute_url())
    
        # get the webmail that mail originates from        
        self.origin = self.context.getPhysicalPath()
        if self.origin != self.ticket['source_url']:
            portal = getSite()
            self.context = portal.restrictedTraverse(self.ticket['source_url'])
        
        # handle file attachments. I would prefer @buttonhandler,
        # but was not able to get a handler for a foreign button.
        if self.request.form.get('upload-%s'%  self.context.title):
            self.handleAttach()    
            return 

        

        
            
        