from django.conf.urls import include, url, patterns
from django.contrib import admin
from django.conf import settings
from registration.backends.simple.views import RegistrationView

# create a new class that redirects the user to the index page if
# successful at logging. this is sort of a classic example
# of subclassing with the sole purpose of overriding a single 
# class method. 
class MyRegistrationView(RegistrationView):
    
    def get_success_url(self, request, user):
        return '/rango/'


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'tango_with_django_project.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^rango/', include('rango.urls')),
    url(r'^admin/', include(admin.site.urls)),
    #add this url patter to override the default pattern in accounts
    url(r'^accounts/register/$', MyRegistrationView.as_view(), name='registration_register'),

    (r'^accounts/', include('registration.backends.simple.urls')),
    (r'^accounts/', include('registration.backends.default.urls')),
)

if settings.DEBUG:
    urlpatterns += patterns(
        'django.views.static',
        (r'^media/(?P<path>.*)',
        'serve',
        {'document_root': settings.MEDIA_ROOT}), )
