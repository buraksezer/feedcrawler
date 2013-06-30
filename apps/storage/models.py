import datetime
import random
import redis
from django.db import models
from django.contrib.auth.models import User
from utils import seconds_timesince
from django.conf import settings


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
    entries_last_month = models.IntegerField(default=0)
    last_entry_date = models.DateTimeField(null=True, blank=True)
    min_to_decay = models.IntegerField(default=0)
    next_scheduled_update = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'feed'
        verbose_name_plural = 'feeds'
        ordering = ('title', 'feed_url',)

    def save_feed_entries_last_month(self):
        month_ago = datetime.datetime.utcnow() - datetime.timedelta(days=30)
        self.entries_last_month = Entry.objects.filter(feed_id=self.id, published_at__gte=month_ago).count()
        self.save()

    def get_next_scheduled_update(self):
        upd  = self.entries_last_month / 30.0
        # TODO: Active users?
        subs =  User.objects.filter(feed=self.id).count()

        # UPD = 1  Subs > 1:  t = 5         # 11625  * 1440/5 =       3348000
        # UPD = 1  Subs = 1:  t = 60        # 17231  * 1440/60 =      413544
        # UPD < 1  Subs > 1:  t = 60        # 37904  * 1440/60 =      909696
        # UPD < 1  Subs = 1:  t = 60 * 12   # 143012 * 1440/(60*12) = 286024
        # UPD = 0  Subs > 1:  t = 60 * 3    # 28351  * 1440/(60*3) =  226808
        # UPD = 0  Subs = 1:  t = 60 * 24   # 807690 * 1440/(60*24) = 807690
        if upd >= 1:
            if subs > 1:
                total = 1
            else:
                total = 5
        elif upd > 0:
            if subs > 1:
                total = 60 - (upd * 60)
            else:
                total = 60*12 - (upd * 60*12)
        elif upd == 0:
            if subs > 1:
                total = 60 * 6
            else:
                total = 60 * 24
            #last_entry_date = datetime.datetime.utcnow() if self.last_entry_date is None else self.last_entry_date
            months_since_last_story = seconds_timesince(datetime.datetime.combine(self.last_entry_date, datetime.time())) * 60*60*24*30
            total *= max(1, months_since_last_story)

        #if self.is_push:
        #    total = total * 12

        # 1 day max
        if total > 60*24:
            total = 60*24

        return total


    def set_next_scheduled_update(self, skip_scheduling=False):
        if not self.is_active:
            return

        r = redis.Redis(connection_pool=settings.REDIS_FEED_POOL)
        total = self.get_next_scheduled_update()
        # TODO: Error count must be stored
        #error_count = self.error_count

        #if error_count:
        #    total = total * error_count

        random_factor = random.randint(0, total) / 4
        self.next_scheduled_update = datetime.datetime.utcnow() + datetime.timedelta(minutes = total + random_factor)

        self.min_to_decay = total

        #delta = self.next_scheduled_update - datetime.datetime.now()
        #minutes_to_next_fetch = delta.total_seconds() / 60
        #if minutes_to_next_fetch > self.min_to_decay or not skip_scheduling:
        #self.next_scheduled_update = next_scheduled_update

        # If this could not set a new value, remove the previous value and retry
        r.zadd("scheduled_updates", self.id, self.next_scheduled_update.strftime('%s'))
        self.save()

    def calculate_last_entry_date(self):
        last_entry_date = None

        try:
            latest_entry = Entry.objects.filter(feed_id=self.id).latest("published_at")
            if latest_entry:
                last_entry_date = latest_entry.published_at
        except Entry.DoesNotExist:
            pass

        if not last_entry_date or seconds_timesince(datetime.datetime.combine(last_entry_date, datetime.time())) < 0:
            last_entry_date = datetime.datetime.now()

        self.last_entry_date = last_entry_date
        self.save()

    def __unicode__(self):
        return u'%s (%s)' % (self.title, self.feed_url)

    def save(self, *args, **kwargs):
        if not self.next_scheduled_update:
            self.next_scheduled_update = datetime.datetime.utcnow()
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
    published_at = models.DateTimeField()

    # The date this entry was last updated,
    # as a string in the same format as it was published in the original feed.
    #updated_at = models.DateField(null=True)

    date_modified = models.DateTimeField(null=True, blank=True)

    # A globally unique identifier for this entry.
    entry_id = models.URLField(unique=True, max_length=512)

    license = models.CharField(null=True, max_length=128)

    # Unique slug for every entry
    #slug = models.SlugField(blank=True)

    available_in_frame = models.IntegerField(null=True, blank=True)


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
    entry = models.ForeignKey(Entry)
    user = models.ForeignKey(User)

    class Meta:
        ordering = ["-id"]

    def __unicode__(self):
        return str(self.id)

class EntryLike(models.Model):
    entry = models.OneToOneField(Entry)
    user = models.ManyToManyField(User)
