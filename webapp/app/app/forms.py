from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import authenticate
from app.api import register, InvalidResponse

def as_div(form):
    """This formatter arranges label, widget, help text and error messages by
    using divs.  Apply to custom form classes, or use to monkey patch form
    classes not under our direct control."""
    # Yes, evil but the easiest way to set this property for all forms.
    form.required_css_class = 'required'

    return form._html_output(
        normal_row=u'<div class="form-group"><div %(html_class_attr)s>%(label)s %(errors)s <div class="helptext">%(help_text)s</div> %(field)s</div></div>',
        error_row=u'%s',
        row_ender='</div>',
        help_text_html=u'%s',
        errors_on_separate_row=False
    )



class LoginForm(forms.Form):
    as_div = as_div
    username = forms.CharField(label=_('Username'), max_length=100)
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)

    error_messages = {
        'invalid_login': _("Please enter a correct username and password."),
        'no_cookies': _("Your Web browser doesn't appear to have cookies "
                        "enabled. Cookies are required for logging in."),
        'inactive': _("This account is inactive."),
    }

    def __init__(self, req=None, *args, **kwargs):
        self.request = req
        self.user_cache = None
        super(LoginForm, self).__init__(*args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(request=self.request,
                                           username=username,
                                           password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'])
            elif not self.user_cache.is_active:
                raise forms.ValidationError(self.error_messages['inactive'])
            self.cleaned_data['token'] = self.user_cache.token
        self.check_for_test_cookie()
        return self.cleaned_data

    def check_for_test_cookie(self):
        if self.request and not self.request.session.test_cookie_worked():
            raise forms.ValidationError(self.error_messages['no_cookies'])

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache


class RegistrationForm(forms.Form):
    as_div = as_div

    def __init__(self, req=None, *args, **kwargs):
        self.request = req
        self.user_cache = None
        super(RegistrationForm, self).__init__(*args, **kwargs)

    error_messages = {
        'duplicate_username': _("A user with that username already exists."),
        'password_mismatch': _("The two password fields didn't match."),
    }

    username = forms.CharField(label=_('Username'), max_length=100)
    mobile_number = forms.CharField(label=_('Mobile number'), max_length=100)
    email = forms.EmailField(label=_('Email'))
    password1 = forms.CharField(label=_("Password"),
                                widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"),
                                widget=forms.PasswordInput,
                                help_text=_("Enter the same password as above,"
                                            " for verification."))

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'])
        return password2

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        email = self.cleaned_data.get('email')
        mobile_number = self.cleaned_data.get('mobile_number')

        if username and password and password2:
            user = {
                'username': username,
                'password': password,
                'email': email,
                'msisdn': mobile_number,
            }
            try:
                register(user)
                self.user_cache = authenticate(request=self.request,
                                               username=username,
                                               password=password)
            except InvalidResponse:
                raise forms.ValidationError(
                    self.error_messages['duplicate_username'])
        return self.cleaned_data

    def get_user(self):
        return self.user_cache
