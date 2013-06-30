from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'apps.frontend.views.home', name='home'),
    url(r'^user/(?P<username>(?!signout|signup|signin)[\.\w-]+)/$', 'apps.userena.views.profile_detail', name='userena_profile_detail'),
    url(r'^user/signin/', 'apps.userena.views.signin', name='userena_signin'),
    url(r'^user/', include('userena.urls')),

    url(r'^feed/(?P<feed_id>[\w-]+)/$', 'apps.frontend.views.feed_detail', name='feed_detail'),
    url(r'^subscriptions/', 'apps.frontend.views.subscriptions', name='subscriptions'),
    url(r'^reader/(?P<entry_id>[\w-]+)/$', 'apps.frontend.views.reader', name='reader'),

    # API requests
    url(r'^api/reader/(?P<entry_id>[\w-]+)/$', 'apps.api.views.reader'),
    url(r'^api/subs-search/(?P<keyword>[\w-]+)/$', 'apps.api.views.subs_search'),
    url(r'^api/user_profile/', 'apps.api.views.user_profile'),
    url(r'^api/timeline/', 'apps.api.views.timeline'),
    url(r'^api/feed_detail/(?P<feed_id>[\w-]+)/$', 'apps.api.views.feed_detail'),
    url(r'^api/subscribe_by_id/(?P<feed_id>[\w-]+)/$', 'apps.api.views.subscribe_by_id', name='subscribe_by_id'),
    url(r'^api/unsubscribe/(?P<feed_id>[\w-]+)/$', 'apps.api.views.unsubscribe', name='unsubscribe'),
    url(r'^api/subscribe$', 'apps.api.views.subscribe'),
    url(r'^api/subscriptions/', 'apps.api.views.subscriptions'),
    url(r'^api/entries_by_feed/(?P<feed_id>[\w-]+)/$', 'apps.api.views.entries_by_feed'),
    url(r'^api/like/(?P<entry_id>[\w-]+)/$', 'apps.api.views.like'),
    url(r'^api/post_comment/', 'apps.api.views.post_comment'),
    url(r'^api/fetch_comments/(?P<entry_id>[\w-]+)/$', 'apps.api.views.fetch_comments'),
    url(r'^api/delete_comment/(?P<comment_id>[\w-]+)/$', 'apps.api.views.delete_comment'),

    #url(r'^subs$', 'apps.frontend.views.subs', name='subs'),


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