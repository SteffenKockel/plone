from zope import schema
from zope.interface import implements
from z3c.form.interfaces import HIDDEN_MODE
from zope.formlib import form
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
    
    imap_password = schema.Password(
        title=_(u'imap password'),
        description=_(u''),
        required= False
        )
