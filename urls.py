from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'apps.frontend.views.home', name='home'),
    url(r'^user/(?P<username>(?!signout|signup|signin)[\.\w-]+)/$', 'apps.userena.views.profile_detail', name='userena_profile_detail'),
    url(r'^user/signin/', 'apps.userena.views.signin', name='userena_signin'),
    url(r'^user/', include('userena.urls')),
    url(r'^explorer/(?P<entry_id>[\w-]+)/$', 'apps.frontend.views.explorer', name='explorer'),
    url(r'^subscribe/', 'apps.frontend.views.subscribe', name='subscribe'),
    url(r'^subs$', 'apps.frontend.views.subs', name='subs'),
    url(r'^unsubscribe/', 'apps.frontend.views.unsubscribe', name='unsubscribe'),
    url(r'^vote/', 'apps.frontend.views.vote', name='vote'),
    url(r'^getuserfeeds/', 'apps.frontend.views.get_user_feeds', name='getuserfeeds'),
    url(r'^getfeedentries/', 'apps.frontend.views.get_feed_entries', name='getfeed'),
    url(r'^get_previous_next/(?P<feed_id>[\w-]+)/(?P<entry_id>[\w-]+)/$', 'apps.frontend.views.get_previous_and_next_items', name='get_previous_next'),
    url(r'^get_entries_by_feed_id/', 'apps.frontend.views.get_entries_by_feed_id', name='get_entries_by_feed_id'),
    url(r'^render_timeline_standalone/', 'apps.frontend.views.render_timeline_standalone', name='render_timeline_standalone'),
    url(r'^feedfinder/', 'apps.frontend.views.available_feeds', name='available_feeds'),
    url(r'^get_user_subscriptions/', 'apps.frontend.views.get_user_subscriptions', name='get_user_subscriptions'),

    # This is required for pubsubhubbub
    #url(r'^subscriber/', include('django_push.subscriber.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)


"""
    url(r'^subscribe_user/', 'apps.frontend.views.subscribe_user', name='subscribe_user'),
    url(r'^unsubscribe_user/', 'apps.frontend.views.unsubscribe_user', name='unsubscribe_user'),
    url(r'^check_subscribe/', 'apps.frontend.views.check_subscribe', name='check_subscribe'),
    url(r'^share_entry/', 'apps.frontend.views.share_entry', name='share_entry'),
"""