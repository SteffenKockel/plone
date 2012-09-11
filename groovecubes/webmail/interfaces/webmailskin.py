from zope.interface import Interface
from plone.theme.interfaces import IDefaultPloneLayer

class IWebmailSpecific(IDefaultPloneLayer):
    """Marker interface that defines a Zope 3 browser layer.
       If you need to register a viewlet only for the
       "groovecubes" theme, this interface must be its layer"""