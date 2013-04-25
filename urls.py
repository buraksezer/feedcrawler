from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'apps.frontend.views.home', name='home'),
    url(r'^accounts/', include('userena.urls')),
    url(r'^explorer/', 'apps.frontend.views.explorer', name='explorer'),
    url(r'^subscribe/', 'apps.frontend.views.subscribe', name='subscribe'),
    url(r'^vote/', 'apps.frontend.views.vote', name='vote'),
    url(r'^getuserfeeds/', 'apps.frontend.views.get_user_feeds', name='getuserfeeds'),
    url(r'^getfeedentries/', 'apps.frontend.views.get_feed_entries', name='getfeed'),
    url(r'^wrapper/', 'apps.frontend.views.wrapper', name='wrapper'),
    url(r'^get_previous_next/', 'apps.frontend.views.get_previous_and_next_items', name='get_previous_next'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
