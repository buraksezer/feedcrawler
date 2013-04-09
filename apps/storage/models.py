from django.db import models
from django.contrib.auth.models import User
from apps.utils import unique_slugify


class Feed(models.Model):
    feed_url = models.CharField(unique=True, max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)
    last_sync = models.DateTimeField(null=True)

    # The date the feed was last updated,
    # as a string in the same format as it was published in the original feed.
    updated_at = models.DateField(null=True)
    users = models.ManyToManyField(User)

    image = models.CharField(null=True, max_length=1024)
    language = models.CharField(null=True, max_length=128)
    title = models.CharField(null=True, max_length=512)
    # This is obsolete
    link = models.CharField(null=True, max_length=512)
    encoding = models.CharField(null=True, max_length=128)
    subtitle = models.CharField(null=True, max_length=512)

    def __unicode__(self):
        return self.feed_url


class FeedTag(models.Model):
    tag = models.CharField(unique=True, max_length=512)
    feed = models.ManyToManyField(Feed)
    users = models.ManyToManyField(User)

    def __unicode__(self):
        return self.tag


class Entry(models.Model):
    title = models.CharField(max_length=2048)
    content = models.TextField()
    # The content type of this piece of content.
    # Most likely values for type:
    #     text/plain
    #     text/html
    #     application/xhtml+xml
    content_type = models.CharField(max_length=64)

    # The language of this piece of content.
    language = models.CharField(null=True, max_length=128)
    author = models.CharField(null=True, max_length=256)
    link = models.URLField(max_length=512)

    # The date this entry was first published,
    # as a string in the same format as it was published in the original feed.
    published_at = models.DateField(null=True)

    # The date this entry was last updated,
    # as a string in the same format as it was published in the original feed.
    updated_at = models.DateField(null=True)

    # A globally unique identifier for this entry.
    entry_id = models.URLField(unique=True, max_length=512)

    license = models.CharField(null=True, max_length=128)

    # Unique slug for every entry
    slug = models.SlugField(blank=True)

    feed = models.ForeignKey(Feed)

    class Meta:
        ordering = ["-id"]

    def __unicode__(self):
        return self.title

    def save(self, **kwargs):
        if not self.id:
            unique_slugify(self, self.title)
        super(Entry, self).save()


class EntryTag(models.Model):
    tag = models.CharField(unique=True, max_length=512)
    entry = models.ManyToManyField(Entry)

    def __unicode__(self):
        return self.tag


class Comment(models.Model):
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    entry = models.OneToOneField(Entry)
    user = models.OneToOneField(User)
