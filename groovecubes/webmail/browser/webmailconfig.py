from Products.Archetypes.Widget import TextAreaWidget
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from Products.CMFDefault.formlib.schema import SchemaAdapterBase
from Products.CMFCore.utils import getToolByName
from zope import interface, schema,component
from zope.formlib import form

from plone.app.controlpanel.form import ControlPanelForm

from groovecubes.webmail import webmailMessageFactory as _

class IWebmailSchema(interface.Interface):
    # -*- extra stuff goes here -*-

    server_list = schema.TextLine(
        title=_(u'Server list'),
        description=_(u''),
        required=False,
        readonly=False,
        
        )
    pass

class WebmailControlPanelAdapter(SchemaAdapterBase):
    component.adapts(IPloneSiteRoot)
    interface.implements(IWebmailSchema)

    def __init__(self, context):
        super(WebmailControlPanelAdapter, self).__init__(context)
        self.context = getToolByName(context,'webmail_tool')

        self.server_list = self.context.getList()

    def set_server_list(self, val):
#        if safe_hasattr(self.context, 'server_list'):
        pass

    def get_server_list(self):
        self.server_list = getattr(self.context, 'getList()')
        return self.server_list

    use_login = property(get_server_list, set_server_list)


class WebmailControlPanel(ControlPanelForm):
    form_fields = form.FormFields(IWebmailSchema)
    # @TODO: make this a multiline or dict widget
    # form.widget(server_list='Products.Archetypes.Widget.LinesWidget')
    label = _(u'Webmail configuration')
    description = _(u'')
    form_name = _('Webmail settings')

    



