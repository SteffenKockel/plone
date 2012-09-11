from zope.interface import implements, Interface
from imapclient import IMAPClient

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName

import email as Email

from groovecubes.webmail import webmailMessageFactory as _
from groovecubes.webmail.browser.utils import parsePlaintextEmailBody, parseHTMLEmailBody,\
                                              parseHeadersFromString, decodeHeader
from StringIO import StringIO

# from Acquisition import aq_inner
# from ast import literal_eval

from groovecubes.webmail.config import CHARSETS 
from ast import literal_eval
import uuid
import logging

class IWebmailView(Interface):
    """
    webmail view interface
    """

class WebmailView(BrowserView):
    """
    webmail browser view
    """
    implements(IWebmailView)

    has_imap_connection = False
    messages = False
    imap_folders = None
    sort_order = None
    preview_message = None
    default_textile_type = 'text/plain' 
    
    Logger = logging.getLogger("groovecubes.webmail")
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
           
    
    @property
    def webmail_tool(self):
        return getToolByName(self.context, 'webmail_tool')
    
    
    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    
    @property
    def portal(self):
        return getToolByName(self.context, 'portal_url').getPortalObject()
    
    
    @property
    def session(self):
        return self.context.session_data_manager.getSessionData(create=True)
    
        
    def getTicketId(self):
        return "%s" % uuid.uuid4()

    
    def getChildsOf(self, parent, level):
        folders = self.imap_folders[1:]
        folders = [d[2].split('/') for d in folders ]
        try:
        ## Sorry Guido! But the alternative was really unreadable too. 
            return [f[level] for f in folders if f[level-1] == parent and len(f) > level]
        except IndexError:
            return []
        
    
    def comparePathes(self, actual_path, this_path):
        if actual_path == this_path:
            return 'inPath'
        return ''
    
    
    def parseFlagClasses(self, flag, flags, notclass=''):
        if flag in flags:
            return flag[1:]
        return notclass
    
    
    def parseIsCurrentClass(self, msgid):
        if int(msgid) == self.current_message_id:
            return 'is_current_message'
        return ''
    
         
    def parseMessageFromString(self, message_as_string):
        return Email.message_from_string(message_as_string)
    
    
    def parsePlaintextEmailBody(self, body, encoding):
        return parsePlaintextEmailBody(body, encoding)
   
    
    def parseHeadersFromString(self, headers):
        return parseHeadersFromString(headers)
   
    
    def decodeHeader(self, header, charset=None):
        return decodeHeader(header, charset)
    
    
    def parseHTMLEmailBody(self, text, encoding, strip_tags_list=None):
        return parseHTMLEmailBody(text, encoding, strip_tags_list) 
        
    
    def collect_trash(self, imap_connection, details):
        """ Deal with the trash. Since messages just get a "deleted" flag
            in IMAP, we have to iter over every folder in this account,
            searching for deleted messages.
        """
        self.messages = {}
        self.trash_catalog = {}
        self.sort_order = []
        # For performance reasons, and  message lookup, a trash_map 
        # (dict) is created an stored in the users session.
        session = self.session
        
        if not session.get('webmail_trash_catalog') or self.update_trashmap:
            self.Logger.info("Refreshing trash map.")
            for folder in [a[-1] for a in self.imap_folders]:
                imap_connection.select_folder(folder)
                search = imap_connection.search(['DELETED'])
                self.messages.update(imap_connection.fetch(search, details))
                sort_order = imap_connection.sort(['REVERSE ARRIVAL'], criteria="DELETED")
                self.trash_catalog.update({folder:sort_order})
                self.sort_order += sort_order
            
            session.set('webmail_trash_messages', self.messages)  
            session.set('webmail_trash_catalog', self.trash_catalog)
            session.set('webmail_trash_sort_order', self.sort_order)
            
        else:
            self.messages = session.get('webmail_trash_messages')
            self.trash_catalog = session.get('webmail_trash_catalog')
            self.sort_order = session.get('webmail_trash_sort_order')
        
        # get the actual message, in case no message is picked. 
        if not self.current_message_id:
            self.current_path = self.imap_folders[0][-1]
            self.current_message_id = self.trash_catalog[self.current_path][0]
            
            # get the messages path from the trash_map
        else:
            for k,v in self.trash_catalog.iteritems():
                if self.current_message_id in v:
                    self.current_path = k
                        
        imap_connection.select_folder(self.current_path)
        
        return 
     
    
    def delete_messages(self, imap_connection, messages):
        imap_connection.select_folder(self.current_path)
        imap_connection.delete_messages(messages)
        
        
    def collect_messages(self, imap_connection, details):
        session = self.session
        imap_connection.select_folder(self.current_path)
        if not session.get(self.current_path) or self.update_message_list:
            self.Logger.info("Updating message list.")
            self.messages = imap_connection.fetch(imap_connection.search(['NOT DELETED']), details)
            self.sort_order = imap_connection.sort(['REVERSE ARRIVAL'], criteria='NOT DELETED')
            session.set(self.current_path, self.messages)
            session.set(self.current_path+"_sortorder", self.sort_order)
        else:
            self.messages = session.get(self.current_path)
            self.sort_order = session.get(self.current_path+"_sortorder")
        # get the actual message, in case no message is
        # picked. 
        if not self.current_message_id:
            self.current_message_id = self.sort_order[0]
        
        return
    
    
    def deliver_attachment(self, imap_connection):
        """ Delivers an attachment  
        """
        details = ['BODY[]']
        msg_id = self.current_message_id
        
        imap_connection.select_folder(self.current_path)
        message = imap_connection.fetch(msg_id, details)
        imap_connection.logout()
        
        message = self.parseMessageFromString(message[msg_id]['BODY[]'])
        for part in message.walk():
            
            if part.get_filename() != self.is_download:
                continue
            file = StringIO(part.get_payload(decode=True))
        
        response = self.request.response
        response.setHeader('Content-type', part.get_content_type())
        
        cd = 'attachment; filename=%s' % self.is_download
        response.setHeader('Content-Disposition', cd)
                
        response.write(file.getvalue())
        file.close()
        return response
                
        
    def setup(self, imap_connection):
        # get the folder-structure for the imap-folder portlet ...
        session = self.context.session_data_manager.getSessionData(create=True)
        # either from session or from server
        if not session.get('imap_folders') or self.update_imap_folders:
            self.Logger.info("Refreshing IMAP folderstructure")
            self.imap_folders = imap_connection.list_folders()
            session.set('imap_folders', self.imap_folders)
        else:
            self.imap_folders = session.get('imap_folders')
            
        # Fetch header list from current folder
        # XXX: make details configurable via ZMI
        details = ['BODY[HEADER]','FLAGS','INTERNALDATE',
                   'RFC822.SIZE','BODYSTRUCTURE']
        
        if self.is_trashfolder:
            self.collect_trash(imap_connection, details)
        else:
            self.collect_messages(imap_connection, details)

        # fetch the message and set the body string
        # as view property.
        current_message = imap_connection.fetch(self.current_message_id, details+['BODY[]'])
        self.current_message = current_message[self.current_message_id]
        
        imap_connection.logout()
        
        return
     

    def __call__(self):
        # check and validate the views form data 
        form = self.request.form
        session = self.context.session_data_manager.getSessionData(create=True)
        # there can only be one action per request.
        action = False         
        for i in ('New','Answer','Forward','Delete', 'Refresh'):
            action = form.get('message.actions.%s' % i , False)
            if action:
                break
        
        action_on = form.get('msgid', []) 
            
        self.current_path = form.get('current_path', 'INBOX').decode('UTF-8')
        self.current_message_textile_type = form.get('message_textile_type', self.default_textile_type)
        self.current_message_id = int(form.get('show_message', form.get('current_message', False)))
        self.is_trashfolder = form.get('trash_folder')
        self.update_trashmap = form.get('update_trashmap', False)
        self.is_download = form.get('download_attachment')
        self.update_imap_folders = form.get('update_imap_folders', False)
        self.update_message_list = form.get('message.actions.Refresh', False)
        
        print self.request.form
        print action, action_on, self.current_path
        
        # get the authenticated user and it's email address
        self.member = self.context.portal_membership.getAuthenticatedMember()     
        self.email = self.member.getProperty('email')
        
        try:
            imap_connection =  self.webmail_tool.getIMAPConnection(self.email)
            # if False (default), views can skip rendering safely
            self.has_imap_connection = True
    
        except AttributeError:
            self.request.response.redirect("%s/login" % self.context.absolute_url())
            return 
                
        # if it is a download, we respond in 
        # deliver_attachment() to this request,
        # avoiding unneccessary page reloads
        if self.is_download:
            self.deliver_attachment(imap_connection)
            return
            
            # deal with message actions 
        if action and action in ('New','Answer','Forward'):
            ticket_id = self.getTicketId()
            session = self.session
            ticket = { 'source_url': self.context.getPhysicalPath(),
                       'action': action,
                       'action_on': action_on,
                       'attachments': {}}
            
            session.set(ticket_id, ticket)
            url = '%s/emailform?form.widgets.ticket=%s' 
            url = url % (self.context.absolute_url(), ticket_id)
            self.request.response.redirect(url)
            return
            
        if action == "Delete":
            self.update_message_list = True
            self.delete_messages(imap_connection, action_on)
                  
        
        self.setup(imap_connection) 
        return self.index()