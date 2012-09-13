from zope import schema
from zope.interface import implements
from BTrees.OOBTree import OOBTree

from plone.app.users.userdataschema import IUserDataSchemaProvider
from plone.app.users.userdataschema import IUserDataSchema

from groovecubes.webmail import webmailMessageFactory as _



class UserDataSchemaProvider(object):
    implements(IUserDataSchemaProvider)
    
    def getSchema(self):
        """ Standard schema accessor. """
        return IWebmailUserDataSchema
    

class IWebmailUserDataSchema(IUserDataSchema):
    """
    Enhance the user form. 
    """
    
    imap_cache = schema.Container(
        title=_(u'imap cache'),
        description=_(u''),
        default = OOBTree(),
        required= False
        )
