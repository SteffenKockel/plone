"""Definition of the Webmail content type
"""




from zope.interface import implements


from plone.i18n.normalizer.interfaces import IFileNameNormalizer, IURLNormalizer
from Products.Archetypes import atapi
from Products.ATContentTypes.content import base
from Products.ATContentTypes.content import schemata, folder
from Products.CMFCore.utils import getToolByName

from imapclient import IMAPClient

from AccessControl import ClassSecurityInfo

#from Products.ATContentTypes.lib import constraintypes


# -*- Message Factory Imported Here -*-
from groovecubes.webmail import webmailMessageFactory as _
from groovecubes.webmail.config import NO_NO
from groovecubes.webmail.interfaces import IWebmail
from groovecubes.webmail.config import PROJECTNAME
from Products.Archetypes.Widget import SelectionWidget
from archetypes.referencebrowserwidget.widget import ReferenceBrowserWidget


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
                                                            
    # -*- Your Archetypes field definitions here ... -*-
))

# Set storage on fields copied from ATContentTypeSchema, making sure
# they work well with the python bridge properties.

WebmailSchema['title'].storage = atapi.AnnotationStorage()
#WebmailSchema['title'].widget.visible = 1

WebmailSchema['description'].storage = atapi.AnnotationStorage()
#WebmailSchema['description'].widget.visible = 1

from zope.component.hooks import getSite

schemata.finalizeATCTSchema(WebmailSchema, moveDiscussion=False)


class Webmail(folder.ATFolder):
    """A Plone4 webmail interface."""
    implements(IWebmail)
    security = ClassSecurityInfo()
    meta_type = "Webmail"
    Server = None
    schema = WebmailSchema
    
    title = atapi.ATFieldProperty('title')
    description = atapi.ATFieldProperty('description')

    # -*- Your ATSchema to Python Property Bridges Here ... -*-
    
    tmp_folder = atapi.ATFieldProperty('tmp_folder')
    #url_normalizer = atapi.ATFieldProperty('url_normalizer')
        
        
atapi.registerType(Webmail, PROJECTNAME)
