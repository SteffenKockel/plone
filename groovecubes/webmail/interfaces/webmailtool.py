from zope.interface import Interface, Attribute

class IWebmailTool(Interface):
    id = Attribute('id', 'Must be set to "webmail_tool"')

    servers = Attribute('server_list', 'A dict with all servers')
