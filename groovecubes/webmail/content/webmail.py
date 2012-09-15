"""Definition of the Webmail content type
"""
from zope.interface import implements
from Acquisition import aq_inner

from BTrees.OOBTree import OOBTree
from AccessControl import ClassSecurityInfo
from archetypes.referencebrowserwidget.widget import ReferenceBrowserWidget
from Products.Archetypes import atapi
from Products.Archetypes.Storage import annotation
from Products.Archetypes.Widget import SelectionWidget, BooleanWidget
from Products.ATContentTypes.content import schemata, folder

# -*- Message Factory Imported Here -*-
from groovecubes.webmail import webmailMessageFactory as _
# from groovecubes.webmail.config import NO_NO
from groovecubes.webmail.interfaces import IWebmail
from groovecubes.webmail.config import PROJECTNAME




def IMAPCacheTree():
    """ 
    This returns a pre-defined tree structure to store
    a users imap cache.
    """
    return OOBTree({
            'trash_catalog': OOBTree(),
            'trash_messages': OOBTree(), 
            'sort_orders': OOBTree(),
            })
    
    
    
WebmailSchema = folder.ATFolderSchema.copy() + atapi.Schema((

    atapi.ReferenceField(
        'tmp_folder',
        storage = atapi.AnnotationStorage(),
        relationship = 'webmail_tmp_folder',
        allowed_types = ("Folder"), 
        widget = ReferenceBrowserWidget(
            label = _(u'TMP folder for attachments'),
            description = _(u'Temp folder for attachments'),
        ),
    ),
                                                             
    atapi.BooleanField(
        'use_imap_cache',
        storage = atapi.AnnotationStorage(),
        default = True,
        widget = BooleanWidget(
            title = _(u'Imap cache'),
            description = _(u'Use local cache to store IMAP folders, sort order and trashmap.')),
    ),
                                                             
    atapi.ObjectField(
        'imap_cache',
        storage = atapi.AnnotationStorage(),
        default = OOBTree(),
        accessor = 'getImap_cache',
        mutator = 'setImap_cache',
        ),
                                                             
                                                        
    # -*- Your Archetypes field definitions here ... -*-
))

# Set storage on fields copied from ATContentTypeSchema, making sure
# they work well with the python bridge properties.

WebmailSchema['title'].storage = atapi.AnnotationStorage()
WebmailSchema['description'].storage = atapi.AnnotationStorage()

#WebmailSchema['title'].widget.visible = 1
WebmailSchema['imap_cache'].widget.visible = 0

schemata.finalizeATCTSchema(WebmailSchema, moveDiscussion=False)


class Webmail(folder.ATFolder):
    """A Plone4 webmail interface."""
    implements(IWebmail)
    security = ClassSecurityInfo()
    meta_type = "Webmail"
    schema = WebmailSchema
    
    title = atapi.ATFieldProperty('title')
    description = atapi.ATFieldProperty('description')

    # -*- Your ATSchema to Python Property Bridges Here ... -*-
    
    tmp_folder = atapi.ATFieldProperty('tmp_folder')
    use_imap_cache = atapi.ATFieldProperty('use_imap_cache')
    imap_cache = atapi.ATFieldProperty('imap_cache')
    
    
    def getImap_cache(self, user, **kwargs):
        """ setter for imap_cache 
        """
        tree  = self.getField('imap_cache').get(self)
        # check for user_key in OOBTree, create one,
        # if not present.
        if not tree.get(user):
            tree.insert(user , IMAPCacheTree())
        # just return the users chunk
        # of this tree at all
        return tree.get(user)
    
    
    def setImap_cache(self, user, **kwargs):
        """ mutator for imap_cache 
        """
        print "setImapCache"
        # retrieve the field
        # self.getField('imap_cache').set(self, OOBTree())
        tree  = self.getField('imap_cache').get(self)
        # re-set
        if kwargs.get("purge", False):
            if kwargs.get("purge") == "all":
                print "!all"
                # clear the whole cache
                tree.clear()
            
            # clear the users cache
            if tree.get(user):
                print "!purge"
                tree[user] == IMAPCacheTree()
            
            
                
            
            return
        
        key = kwargs.get("key", False)
        val = kwargs.get("val", False)
        
        if key and val:
            tree(user).update({key: val})
        
        return
            
atapi.registerType(Webmail, PROJECTNAME)