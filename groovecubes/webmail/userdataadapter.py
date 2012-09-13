from plone.app.users.browser.personalpreferences import UserDataPanelAdapter
from plone.app.users.browser.personalpreferences import UserDataPanel
import z3c

class WebmailUserDataPanelAdapter(UserDataPanelAdapter):
    """
    """
    
    def get_imap_cache(self):
        return self.context.getProperty('imap_cache', '')
    def set_imap_cache(self, value):
        return self.context.setMemberProperties({'imap_cache': value})
    
    imap_cache = property(get_imap_cache, set_imap_cache)
    
    

class WebmailUserDataPanel(UserDataPanel):
    """ 
    Custom UserDataPanel for certain member attributes
    used by webmail. 
    """
    
    def __init__(self, context, request):
        
        super(WebmailUserDataPanel, self).__init__(context, request)
        self.form_fields = self.form_fields.omit('imap_cache')
        
        
         