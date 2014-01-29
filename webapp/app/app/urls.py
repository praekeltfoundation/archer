from django.conf.urls import patterns, include, url
from app import forms

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', 'app.views.home', name='home'),

    url(
        r'^login/$',
        'app.views.login',
        {'authentication_form': forms.LoginForm},
        name='login',
    ),
    url(
        r'^logout/$',
        'app.views.logout',
        name='logout'),
    url(
        r'^join/$',
        'app.views.register',
        name='join'),

    url(r'^admin/', include(admin.site.urls)),
)
