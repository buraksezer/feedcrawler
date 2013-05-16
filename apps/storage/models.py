from django.db import models
from django.contrib.auth.models import User
from apps.utils import unique_slugify

class Feed(models.Model):
    feed_url = models.CharField(unique=True, max_length=512)
    hub = models.CharField(null=True, max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField('is active', default=True,
        help_text='If disabled, this feed will not be further updated.')

    tagline = models.TextField('tagline', blank=True)

    etag = models.CharField('etag', max_length=50, blank=True)

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

    class Meta:
        verbose_name = 'feed'
        verbose_name_plural = 'feeds'
        ordering = ('title', 'feed_url',)

    def __unicode__(self):
        return u'%s (%s)' % (self.title, self.feed_url)


    def save(self, *args, **kwargs):
        super(Feed, self).save(*args, **kwargs)



class FeedTag(models.Model):
    tag = models.CharField(unique=True, max_length=512)
    feed = models.ManyToManyField(Feed)
    users = models.ManyToManyField(User)

    def __unicode__(self):
        return self.tag

    def save(self, *args, **kwargs):
        super(FeedTag, self).save(*args, **kwargs)


class EntryTag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = 'tag'
        verbose_name_plural = 'tags'
        ordering = ('name',)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(EntryTag, self).save(*args, **kwargs)

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
    author_email = models.EmailField(blank=True)
    link = models.URLField(max_length=512)
    tags = models.ManyToManyField(EntryTag)

    # The date this entry was first published,
    # as a string in the same format as it was published in the original feed.
    published_at = models.DateField(null=True, blank=True)

    # The date this entry was last updated,
    # as a string in the same format as it was published in the original feed.
    #updated_at = models.DateField(null=True)

    date_modified = models.DateTimeField(null=True, blank=True)

    # A globally unique identifier for this entry.
    entry_id = models.URLField(unique=True, max_length=512)

    license = models.CharField(null=True, max_length=128)

    # Unique slug for every entry
    #slug = models.SlugField(blank=True)


    feed = models.ForeignKey(Feed)

    class Meta:
        ordering = ["-id"]

    def __unicode__(self):
        return self.title


    def save(self, *args, **kwargs):
        super(Entry, self).save(*args, **kwargs)


class Comment(models.Model):
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    entry = models.OneToOneField(Entry)
    user = models.OneToOneField(User)


class EntryLike(models.Model):
    entry = models.OneToOneField(Entry)
    user = models.ManyToManyField(User)


class EntryDislike(models.Model):
    entry = models.OneToOneField(Entry)
    user = models.ManyToManyField(User)
