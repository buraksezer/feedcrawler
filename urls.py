from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'apps.frontend.views.home', name='home'),
    url(r'^accounts/', include('userena.urls')),
    url(r'^auth/', 'apps.frontend.views.auth', name='auth'),
    url(r'^explorer/(?P<feed_id>[^\.]+)/(?P<slug>[^\.]+)', 'apps.frontend.views.explorer', name='explorer'),
    url(r'^subscribe/', 'apps.frontend.views.subscribe', name='subscribe'),
    url(r'^vote/', 'apps.frontend.views.vote', name='vote'),
    url(r'^entrylist/', 'apps.frontend.views.entry_list', name='entrylist'),

    # Examples:
    # url(r'^$', 'FeedCraft.views.home', name='home'),
    # url(r'^FeedCraft/', include('FeedCraft.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
