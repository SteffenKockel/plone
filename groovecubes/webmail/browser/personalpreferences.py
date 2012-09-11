from Acquisition import aq_inner

from zope.component import getUtility
from zope.component import adapts
from zope.interface import implements, Interface
from zope import schema
from zope.app.form.interfaces import WidgetInputError
from zope.app.form.browser import DropdownWidget
from zope.schema import ValidationError
from zope.schema import Choice
from zope.schema import Bool
from zope.formlib import form

from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.utils import getToolByName

from plone.app.users.browser.account import AccountPanelForm, AccountPanelSchemaAdapter
from plone.app.users.userdataschema import IUserDataSchemaProvider

from Products.CMFDefault.formlib.schema import SchemaAdapterBase
from Products.CMFDefault.formlib.widgets import FileUploadWidget
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.utils import set_own_login_name, safe_unicode
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from plone.app.users.browser.personalpreferences import UserDataPanel, IPasswordSchema, PasswordPanelAdapter, checkCurrentPassword


class PasswordAccountPanelWithIMAP(AccountPanelForm):

    """ Implementation of password reset form that uses formlib"""

    form_fields = form.FormFields(IPasswordSchema)

    label = _(u'listingheader_reset_password', default=u'Reset Password')
    description = _(u"Change Password")
    form_name = _(u'legend_password_details', default=u'Password Details')

    def validate_password(self, action, data):
        context = aq_inner(self.context)
        registration = getToolByName(context, 'portal_registration')
        membertool = getToolByName(context, 'portal_membership')

        errors = super(PasswordAccountPanelWithIMAP, self).validate(action, data)

        # check if password is correct
        current_password = data.get('current_password')
        if current_password:
            current_password = current_password.encode('ascii', 'ignore')

            if not membertool.testCurrentPassword(current_password):
                err_str = _(u"Incorrect value for current password")
                errors.append(WidgetInputError('current_password',
                                  u'label_current_password', err_str))
                self.widgets['current_password'].error = err_str


        # check if passwords are same and minimum length of 5 chars
        new_password = data.get('new_password')
        new_password_ctl = data.get('new_password_ctl')
        if new_password and new_password_ctl:
            failMessage = registration.testPasswordValidity(new_password,
                                                            new_password_ctl)
            if failMessage:
                errors.append(WidgetInputError('new_password',
                                  u'label_new_password', failMessage))
                errors.append(WidgetInputError('new_password_ctl',
                                  u'new_password_ctl', failMessage))
                self.widgets['new_password'].error = failMessage
                self.widgets['new_password_ctl'].error = failMessage

        return errors

    @form.action(_(u'label_change_password', 
                   default=u'Change Password') ,
                 validator='validate_password', 
                 name=u'reset_passwd')
    
    def action_reset_passwd(self, action, data):
        membertool = getToolByName(self.context, 'portal_membership')

        password = data['new_password']

        try:
            membertool.setPassword(password, None, REQUEST=self.request)
        except AttributeError:
            failMessage=_(u'While changing your password an AttributeError occurred. This is usually caused by your user being defined outside the portal.')

            IStatusMessage(self.request).addStatusMessage(_(failMessage),
                                                          type="error")
            return

        IStatusMessage(self.request).addStatusMessage(_("Password-- changed"),
                                                          type="info")
