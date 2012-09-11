from zope.interface import Interface, Attribute
# -*- Additional Imports Here -*-
from zope import schema

from groovecubes.webmail import webmailMessageFactory as _



class IIMAPServer(Interface):
    """A Plone4 webmail interface."""

    # -*- schema definition goes here -*-
