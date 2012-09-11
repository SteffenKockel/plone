from plone.formwidget.contenttree.widget import \
    Fetch, ContentTreeBase, MultiContentTreeWidget
    
from plone.formwidget.autocomplete.widget import \
    AutocompleteMultiSelectionWidget

from zope.app.pagetemplate.viewpagetemplatefile import \
    ViewPageTemplateFile

from zope.interface import implementsOnly, implementer

from z3c.form.interfaces import IFieldWidget
from z3c.form.widget import FieldWidget
from z3c.form import button
from zope.i18n import translate

from groovecubes.webmail import webmailMessageFactory as _

class UploadEnabledMultiContentTreeWidget(
        ContentTreeBase, AutocompleteMultiSelectionWidget):
    
    klass = u"contenttree-widget"
    multi_select = True
    display_template = ViewPageTemplateFile('tpl/display_multiple.pt')
    input_template = ViewPageTemplateFile('tpl/input.pt')
    
    def js_extra(self):
        form_url = self.request.getURL()
        url = "%s/++widget++%s/@@contenttree-fetch" % (form_url, self.name)

        return """\
                $.extend($.fn, { 
                    webmailAttachmentTreeConfig: {
                        script: '%(url)s',
                        folderEvent: '%(folderEvent)s',
                        selectEvent: '%(selectEvent)s',
                        expandSpeed: %(expandSpeed)d,
                        collapseSpeed: %(collapseSpeed)s,
                        multiFolder: %(multiFolder)s,
                        multiSelect: %(multiSelect)s,
                    } 
                });
                $('#%(id)s-widgets-query').each(function() {
                    if($(this).siblings('input.searchButton').length > 0) { return; }
                    $(document.createElement('input'))
                        .attr({
                            'type': 'button',
                            'value': '%(button_val)s'
                        })
                        .addClass('searchButton')
                        .click( function () {
                            var parent = $(this).parents("*[id$='-autocomplete']")
                            var window = parent.siblings("*[id$='-contenttree-window']")
                            window.showDialog();
                        }).insertAfter($(this));
                });
                $('#%(id)s-contenttree-window').find('.contentTreeAdd').unbind('click').click(function () {
                    $(this).contentTreeAdd();
                });
                $('#%(id)s-contenttree-window').find('.contentTreeCancel').unbind('click').click(function () {
                    $(this).contentTreeCancel();
                });
                $('#%(id)s-contenttree-window').find('.contentTreeUploadSend').unbind('click').click(function () {
                    $(this).contentTreeUploadFile();
                });
                $('#%(id)s-widgets-query').after(" ");
                $('#%(id)s-contenttree').contentTree(
                   $.fn.webmailAttachmentTreeConfig ,
                    function(event, selected, data, title) {
                        // alert(event + ', ' + selected + ', ' + data + ', ' + title);
                    }
                );
                
        """ % dict(url=url,
                   id=self.name.replace('.', '-'),
                   folderEvent=self.folderEvent,
                   selectEvent=self.selectEvent,
                   expandSpeed=self.expandSpeed,
                   collapseSpeed=self.collapseSpeed,
                   multiFolder=str(self.multiFolder).lower(),
                   multiSelect=str(self.multi_select).lower(),
                   name=self.name,
                   klass=self.klass,
                   title=self.title,
                   button_val=translate(
                       'label_contenttree_browse',
                       default=u'browse...',
                       domain='plone.formwidget.contenttree',
                       context=self.request))
    
    
@implementer(IFieldWidget)
def UploadEnabledMultiContentTreeFieldWidget(field, request):
    return FieldWidget(
        field, 
        UploadEnabledMultiContentTreeWidget(request)
        )