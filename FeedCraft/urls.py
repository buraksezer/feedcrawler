from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'apps.reader.views.index', name='index'),
    url(r'^accounts/', include('userena.urls')),

    # URL definitions for Ajax API
    url(r'^reader/ajax/add_feed/', 'apps.reader.views.add_feed', name='add_feed'),

    # url(r'^FeedCraft/', include('FeedCraft.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
