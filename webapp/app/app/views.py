from django.shortcuts import render, redirect
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.sites.models import get_current_site
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login
from django.contrib.auth.views import logout as auth_logout
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.template.response import TemplateResponse
from django.utils.http import is_safe_url
from django.shortcuts import resolve_url

from app.api import InvalidResponse
from app.forms import RegistrationForm


def home(request):
    return render(request, 'home.html')


def logout(request):
    if settings.AUTHENTICATION_TOKEN_KEY in request.session:
        del request.session[settings.AUTHENTICATION_TOKEN_KEY]
    return auth_logout(request, next_page=reverse('home'))


@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(request, template_name='login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm,
          current_app=None, extra_context=None):
    """
    Displays the login form and handles the login action.
    """
    redirect_to = request.REQUEST.get(redirect_field_name, '')

    if request.method == "POST":
        form = authentication_form(request, data=request.POST)
        if form.is_valid():

            # Ensure the user-originating redirection url is safe.
            if not is_safe_url(url=redirect_to, host=request.get_host()):
                redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)

            # Okay, security check complete. Log the user in.
            auth_login(request, form.get_user())

            token = form.cleaned_data['token']
            request.session[settings.AUTHENTICATION_TOKEN_KEY] = token
            msg = _("You have successfully logged in.")
            messages.success(request, msg, fail_silently=True)

            return redirect(redirect_to)
    else:
        form = authentication_form(request)

    current_site = get_current_site(request)

    context = {
        'form': form,
        redirect_field_name: redirect_to,
        'site': current_site,
        'site_name': current_site.name,
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, template_name, context,
                            current_app=current_app)


def register(request):
    next = request.REQUEST.get('next') or reverse('home')
    if request.method == 'POST':
        form = RegistrationForm(data=request.POST, req=request)
        try:
            if form.is_valid():
                auth_login(request, form.get_user())
                msg = _("You have successfully signed up to the site.")
                messages.success(request, msg, fail_silently=True)
                return redirect(next)
        except InvalidResponse:
            msg = _("Error. Please try again later")
            messages.error(request, msg, fail_silently=True)
#        except:
#            msg = _("Error. Please try again later")
#            messages.error(request, msg, fail_silently=True)
    else:
        form = RegistrationForm()

    context = {
        'form': form,
        'next': next,
    }

    return render(request, 'join.html', context)
