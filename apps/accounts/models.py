from django.db import models

from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from userena.models import UserenaBaseProfile
from apps.storage.models import Feed


class UserProfile(UserenaBaseProfile):
    user = models.OneToOneField(User,unique=True,
        verbose_name=_('user'),related_name='user_profile')


class UserRelation(models.Model):
    user = models.ForeignKey(User)
    follower = models.ForeignKey(User, related_name="follower")


class FeedUserRelation(models.Model):
    user = models.ForeignKey(User)
    feed = models.ForeignKey(Feed)
    show_on_stream = models.BooleanField('Show on Stream', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.user.username+" subscribes "+self.feed.feed_url