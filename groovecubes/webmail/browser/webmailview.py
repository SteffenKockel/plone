from zope.interface import implements, Interface
from imapclient import IMAPClient

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName

import email as Email

from groovecubes.webmail import webmailMessageFactory as _
from groovecubes.webmail.browser.utils import parsePlaintextEmailBody, parseHTMLEmailBody,\
                                              parseHeadersFromString, decodeHeader



from groovecubes.webmail.errors import NoAccountError, NotInMailgroupError,\
                                       NoEmailAddressError, AnonymousAccessError
from Acquisition import aq_inner
from StringIO import StringIO


from zope.annotation.interfaces import IAnnotations
# from Acquisition import aq_inner
# from ast import literal_eval

from groovecubes.webmail.config import CHARSETS
from groovecubes.webmail.config import MESSAGE_PREVIEW_DETAILS as DETAILS 
from ast import literal_eval
import uuid
import logging
from BTrees.OOBTree import OOBTree, OOTreeSet
from zope.annotation.interfaces import IAnnotations, IAttributeAnnotatable

class IWebmailView(Interface):
    """
    webmail view interface
    """


class WebmailView(BrowserView):
    """
    webmail browser view
    """
    implements(IWebmailView)

    _imap_connection = False
    _update_message_list = None
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
    def member(self):
        return self.context.portal_membership.getAuthenticatedMember()
    

    @property
    def imap_cache(self):
        return self.context.getImap_cache(self.member.getName())
    
    
    @property
    def form(self):
        return self.request.form
    
    
    @property
    def action(self): 
    # there can only be one action per request.             
        for i in ('New','Answer','Forward','Delete', 'Refresh'):
            action = self.form.get('message.actions.%s' % i)
            if not action:
                continue
            return action
        return None
    
    
    @property
    def action_on(self):
        return self.form.get('msgid', [])   
    
    
    @property
    def current_path(self):
        # we are not dealing with trash
        if not self.is_trashfolder:
            return self.form.get('current_path', 'INBOX').decode('UTF-8')
        
        
        # get the actual message, in case no message has been picked. 
        if not self.current_message_id:
            path = self.imap_folders[0][-1]
            self.current_message_id = self.trash_catalog[path][0]
            return path
        # get the messages path from the trash_map
        else:
            for path , messages in self.trash_catalog.iteritems():
                if self.current_message_id in messages:
                    return path
    
    
    @property
    def current_message(self):
        # fetch the message and set the body string
        # as view property.
        message = self.imap_connection.fetch(self.current_message_id, DETAILS+['BODY[]'])
        return message[self.current_message_id]
    
    #@property
    #def current_message_id(self):
    #    return 
   
    
    @property
    def current_message_text_type(self):
        return self.form.get('message_textile_type', self.default_textile_type)
    
    
    @property
    def is_trashfolder(self):
        return self.form.get('trash_folder')
        
    
    @property
    def is_download(self):
       return self.form.get('download_attachment')
   
    @property
    def is_anonymous(self):
        return self.context.portal_membership.isAnonymousUser()
    
    
    @property
    def update_trashmap(self):
        return self.form.get('update_trashmap')
   
    
    @property
    def update_imap_folders(self):
        return self.form.get('update_imap_folders', False)
    
    
    @property
    def update_message_list(self):
        return self.form.get('message.actions.Refresh') or self._update_message_list
        
    
    @property
    def session(self):
        return self.context.session_data_manager.getSessionData(create=True)
    
    
    @property
    def imap_connection(self):
        return self._imap_connection
    
    
    @property
    def imap_folders(self):
        return self.imap_cache.get("imap_folders")
    
    
    def generateTicketID(self):
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
        
    
    def collect_trash(self):
        """ Deal with the trash. Since messages just get a "deleted" flag
            in IMAP, we have to iter over every folder in this account,
            searching for deleted messages.
        """
        
        if not self.imap_cache.get('trash_catalog') or self.update_trashmap:
            
            self.Logger.info("Refreshing trash map.")
            # this resets the users cache
            self.context.setImap_cache(self.member.getName(), purge=True)
            # set a default for the sort order            
            self.imap_cache["sort_orders"].get("trash") or\
                self.imap_cache["sort_orders"].setdefault("trash", [])
            
            for folder in [a[-1] for a in self.imap_folders]:
            
                self.imap_connection.select_folder(folder)
                search = self.imap_connection.search(['DELETED'])
                messages = self.imap_connection.fetch(search, DETAILS)
                sort_order = self.imap_connection.sort(['REVERSE ARRIVAL'],\
                                                        criteria="DELETED")
                
                self.imap_cache["sort_orders"]["trash"] += sort_order
                self.imap_cache['trash_messages'].update(messages)
                self.imap_cache['trash_catalog'].update({folder : sort_order})
                 
        self.messages = self.imap_cache.get("trash_messages")
        self.sort_order = self.imap_cache["sort_orders"].get("trash")
        self.trash_catalog = self.imap_cache.get("trash_catalog")
                        
        ## ?
        self.imap_connection.select_folder(self.current_path)
        return 
     
    
    def delete_messages(self, messages):
        self.imap_connection.select_folder(self.current_path)
        self.imap_connection.delete_messages(messages)
        
        
    def collect_messages(self):
        # select the folder
        self.imap_connection.select_folder(self.current_path)
        
        cache_path = "messages:%s" % self.current_path
        if not self.imap_cache.get(cache_path) or self.update_message_list:
            # refresh the cache for this folder
            self.Logger.info("Updating message list for %s" % self.current_path)
            
            search = self.imap_connection.search(['NOT DELETED'])
            self.imap_cache.update({
                        cache_path : self.imap_connection.fetch(search , DETAILS )
            })
                
        self.sort_order = self.imap_connection.sort(['REVERSE ARRIVAL'], criteria='NOT DELETED')
        self.messages = self.imap_cache[cache_path]
        # get the actual message, in case no message is
        # picked. 
        if not self.current_message_id:
            self.current_message_id = self.sort_order[0]
        
        return
    
    
    def deliver_attachment(self):
        """ Delivers an attachment  
        """
        details = ['BODY[]']
        msg_id = self.current_message_id
        
        self.imap_connection.select_folder(self.current_path)
        message = self.imap_connection.fetch(msg_id, details)
        self.imap_connection.logout()
        
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
                
        
    def setup(self):
        # get the folder-structure for the imap-folder portlet ...
        # either from cache or from server
        if not self.imap_cache.get("imap_folders") or self.update_imap_folders:
            
            self.Logger.info("Refreshing IMAP folderstructure")
            self.imap_cache.update({"imap_folders":self.imap_connection.list_folders()})
            
        if self.is_trashfolder:
            self.collect_trash()
        else:
            self.collect_messages()

        # shut down the connection
        # self.imap_connection.logout()
        return 
     

    def __call__(self):
        # self.context.setImap_cache(self.member.getName(), purge="all")
        # first of all, we check permissions and try to get a 
        # connection for this user from the webmail tool  
        try:
                     
            if self.is_anonymous:
                raise AnonymousAccessError(self.member)
                
            email = self.member.getId()
            # XXX There could be situations where we don't need the connection
            # but have rights t oget one, if we display local cached data. 
            # Though it would be nice, to skip any unneccessary connections.
            self._imap_connection = self.webmail_tool.getIMAPConnection(email)
            self.has_imap_connection = True
            
        except (NoAccountError, NotInMailgroupError, NoEmailAddressError), e:
            # no account, no email-address, wrong webmail group. The template
            # checks has_imap_connection to be true, before rendering any 
            # content. If has_imap_connection is False the user will see the 
            # webmail at all, but with a blank page body. 
            self.Logger.info(e)
            return self.index()
        
        except AnonymousAccessError:
            # redirect non authenticated to login
            self.Logger.warn("Anonymous tried to access webmail %s. Check permissions." % self.context.title ) 
            return self.request.response.redirect("%s/login" % self.context.absolute_url())
        
        # XXX check, if context is really content_type "webmail"
        # tmp
        self.current_message_id = int(self.form.get('show_message', self.form.get('current_message', False))) 
            
        print self.request.form
        print self.action, self.action_on , self.is_trashfolder
          
        # if it is a download, we respond in 
        # deliver_attachment() to this request,
        # avoiding unneccessary page reloads
        if self.is_download:
            self.deliver_attachment()
            return
            
        # deal with message specific actions 
        if self.action and self.action in ('New','Answer','Forward'):
            ticket_id = self.generateTicketID()
            
            ticket = { 'source_url': self.context.getPhysicalPath(),
                       'action': self.action,
                       'action_on': self.action_on}
            
            self.session.set(ticket_id, ticket)
            url = '%s/emailform?form.widgets.ticket=%s' 
            url = url % (self.context.absolute_url(), ticket_id)
            self.request.response.redirect(url)
            return
            
        elif self.action == "Delete":
             self._update_message_list = True
             self.delete_messages(self.action_on)
                  
        
        self.setup() 
        return self.index()