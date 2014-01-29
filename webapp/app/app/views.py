import urlparse
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
        form = authentication_form(data=request.POST, req=request)
        try:
            if form.is_valid():
                netloc = urlparse.urlparse(redirect_to)[1]

                if not redirect_to:
                    redirect_to = settings.LOGIN_REDIRECT_URL

                elif netloc and netloc != request.get_host():
                    redirect_to = settings.LOGIN_REDIRECT_URL

                # Okay, security checks complete. Log the user in.
                user = form.get_user()
                auth_login(request, user)
                token = form.cleaned_data['token']
                request.session[settings.AUTHENTICATION_TOKEN_KEY] = token

                if request.session.test_cookie_worked():
                    request.session.delete_test_cookie()

                msg = _("You have successfully logged in.")
                messages.success(request, msg, fail_silently=True)

                return redirect(redirect_to)
        except InvalidResponse:
            msg = _("Error. Please try again later")
            messages.error(request, msg, fail_silently=True)
        except:
            msg = _("Error. Please try again later")
            messages.error(request, msg, fail_silently=True)

    else:
        form = authentication_form(request)

    request.session.set_test_cookie()

    current_site = get_current_site(request)

    context = {
        'form': form,
        redirect_field_name: redirect_to,
        'site': current_site,
        'site_name': current_site.name,
    }
    if extra_context is not None:
        context.update(extra_context)
    return render(request, template_name, context, current_app=current_app)


def register(request):
    next = request.REQUEST.get('next', reverse('home'))
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
        except:
            msg = _("Error. Please try again later")
            messages.error(request, msg, fail_silently=True)
    else:
        form = RegistrationForm()

    context = {
        'form': form,
        'next': next,
    }

    return render(request, 'join.html', context)
