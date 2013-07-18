from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from apps.api import views
from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns

# Regular and Dummy URLs
urlpatterns = patterns('',
    url(r'^$', 'apps.frontend.views.home', name='home'),
    url(r'^user/(?P<username>(?!signout|signup|signin)[\.\w-]+)/$', 'apps.userena.views.profile_detail', name='userena_profile_detail'),
    url(r'^user/signin/', 'apps.userena.views.signin', name='userena_signin'),
    url(r'^user/', include('userena.urls')),

    # Dummy URLs
    url(r'^feed/(?P<slug>[-A-Za-z0-9_]+)/$', 'apps.frontend.views.feed_detail', name='feed_detail'),
    url(r'^subscriptions/', 'apps.frontend.views.subscriptions', name='subscriptions'),
    url(r'^interactions/', 'apps.frontend.views.interactions', name='interactions'),
    url(r'^readlater/', 'apps.frontend.views.readlater', name='readlater'),
    url(r'^reader/(?P<slug>[-A-Za-z0-9_]+)/$', 'apps.frontend.views.reader', name='reader'),
    url(r'^entry/(?P<entry_id>[\w-]+)/$', 'apps.frontend.views.entry', name='entry'),
    url(r'^list/(?P<list_slug>[-A-Za-z0-9_]+)/$', 'apps.frontend.views.list', name='list'),

    # Admin
    url(r'^admin/', include(admin.site.urls)),
)

# RESTful JSON API
router = routers.DefaultRouter()
apipatterns = patterns('',
    url(r'^api/authenticated_user/$', views.AuthenticatedUser.as_view()),
    url(r'^api/timeline/', views.Timeline.as_view()),
    url(r'^api/list/(?P<list_slug>[-A-Za-z0-9_]+)/$', views.ListTimeline.as_view()),
    url(r'^api/prepare_list/(?P<list_slug>[-A-Za-z0-9_]+)/$', views.PrepareList.as_view()),
    url(r'^api/single_entry/(?P<entry_id>[\w-]+)/$', views.SingleEntry.as_view()),
    url(r'^api/feed_detail/(?P<slug>[-A-Za-z0-9_]+)/$', views.FeedDetail.as_view()),
    url(r'^api/subs-search/(?P<keyword>[\w-]+)/$', views.SubsSearch.as_view()),
    url(r'^api/reader/(?P<slug>[-A-Za-z0-9_]+)/$', views.Reader.as_view()),
    url(r'^api/unsubscribe/(?P<feed_id>[\w-]+)/$', views.UnsubscribeByFeedId.as_view()),
    url(r'^api/subscribe_by_id/(?P<feed_id>[\w-]+)/$', views.SubscribeByFeedId.as_view()),
    url(r'^api/find_source$', views.FindFeedWithURL.as_view()),
    url(r'^api/subscribe$', views.SubscribeFeed.as_view()),
    url(r'^api/subscriptions/', views.FeedSubscriptions.as_view()),
    url(r'^api/entries_by_feed/(?P<feed_id>[\w-]+)/$', views.EntriesByFeed.as_view()),
    url(r'^api/like_entry/(?P<entry_id>[\w-]+)/$', views.LikeEntry.as_view()),
    url(r'^api/post_comment/', views.PostComment.as_view()),
    url(r'^api/update_comment/', views.UpdateComment.as_view()),
    url(r'^api/delete_comment/(?P<comment_id>[\w-]+)/$', views.DeleteComment.as_view()),
    url(r'^api/fetch_comments/(?P<entry_id>[\w-]+)/$', views.FetchComments.as_view()),
    url(r'^api/interactions/', views.Interactions.as_view()),
    url(r'^api/readlater/(?P<entry_id>[\w-]+)/$', views.ManageReadLater.as_view()),
    url(r'^api/readlater_list/', views.ReadLaterList.as_view()),
    url(r'^api/lists/', views.RetrieveLists.as_view()),
    url(r'^api/append_to_list/(?P<list_id>[\w-]+)/(?P<feed_id>[\w-]+)/$', views.AppendToList.as_view()),
    url(r'^api/delete_from_list/(?P<list_id>[\w-]+)/(?P<feed_id>[\w-]+)/$', views.DeleteFromList.as_view()),
    url(r'^api/delete_list/(?P<list_id>[\w-]+)/$', views.DeleteList.as_view()),
    url(r'^api/create_list/', views.CreateList.as_view()),
)
urlpatterns += format_suffix_patterns(apipatterns)
