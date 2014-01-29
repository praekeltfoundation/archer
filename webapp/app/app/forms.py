from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import authenticate
from app.api import register, InvalidResponse


class LoginForm(forms.Form):
    username = forms.EmailField(label=_("Email"))
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)

    error_messages = {
        'invalid_login': _("Please enter a correct email and password."),
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
    def __init__(self, req=None, *args, **kwargs):
        self.request = req
        self.user_cache = None
        super(RegistrationForm, self).__init__(*args, **kwargs)

    error_messages = {
        'duplicate_username': _("A user with that username already exists."),
        'password_mismatch': _("The two password fields didn't match."),
    }

    first_name = forms.CharField(label=_('Firstname'), max_length=100)
    last_name = forms.CharField(label=_('Surname'), max_length=100)
    username = forms.EmailField(label=_('Email'))
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
        first_name = self.cleaned_data.get('first_name')
        last_name = self.cleaned_data.get('last_name')

        if username and password and password2:
            user = {
                'username': username,
                'password': password,
                'first_name': first_name,
                'last_name': last_name,
            }
            try:
                register(user)
            except InvalidResponse:
                raise forms.ValidationError(
                    self.error_messages['duplicate_username'])
        return self.cleaned_data

    def get_user(self):
        return self.user_cache
