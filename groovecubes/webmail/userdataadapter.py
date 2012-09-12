from plone.app.users.browser.personalpreferences import UserDataPanelAdapter
from plone.app.users.browser.personalpreferences import UserDataPanel
import z3c

class WebmailUserDataPanelAdapter(UserDataPanelAdapter):
    """
    """
    
    def get_imap_password(self):
        return self.context.getProperty('imap_password', '')
    def set_imap_password(self, value):
        return self.context.setMemberProperties({'imap_password': value})
    
    imap_password = property(get_imap_password, set_imap_password)
    
    

class WebmailUserDataPanel(UserDataPanel):
    """ 
    Custom UserDataPanel for certain member attributes
    used by webmail. 
    """
    def __init__(self, context, request):
        
        super(WebmailUserDataPanel, self).__init__(context, request)
        self.form_fields = self.form_fields.omit('imap_password')
        
        
         