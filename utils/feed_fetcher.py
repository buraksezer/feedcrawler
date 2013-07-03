import time
import redis
import feedparser
import django
from time import mktime
from datetime import datetime
from announce import AnnounceClient
from apps.storage.models import Feed, Entry, EntryTag
from django.utils.timezone import utc
from utils import log as logging
from django.conf import settings
from urlparse import urlparse

from django.db import connection

announce_client = AnnounceClient()

class ProcessEntry(object):
    def __init__(self, feed, entries, available=1):
        self.feed = feed
        self.entries = entries
        self.available = available
        for entry in self.entries:
            self.process(entry)
        self.feed.calculate_last_entry_date()
        self.feed.save_feed_entries_last_month()


    def process(self, entry):
        entry_id = entry.id if hasattr(entry, "id") else entry.link
        if not Entry.objects.filter(entry_id=entry_id):
            entry_item = Entry(title=entry.title, feed=self.feed)
            # FIXME: What if entry object has not link variable?
            entry_item.entry_id = entry.id if hasattr(entry, "id") else entry.link
            if hasattr(entry, "content"):
                entry_item.content = entry.content[0].value
                if hasattr(entry.content[0], "language") and entry.content[0].language is not None:
                    entry_item.language = entry.content[0]["language"]
                if hasattr(entry.content[0], "type"):
                    entry_item.content_type = entry.content[0].type
            else:
                entry_item.content = entry.summary
                entry_item.content_type = entry.summary_detail.type
                if hasattr(entry.summary_detail, "language") and entry.summary_detail.language is not None:
                    entry_item.language = entry.summary_detail.language

            if hasattr(entry, "published_parsed") and entry.published_parsed is not None:
                entry_item.published_at = datetime.fromtimestamp(mktime(entry.published_parsed))
            else:
                entry_item.published_at = datetime.utcnow()

            if hasattr(entry, "author") and entry.author is not None:
                entry_item.author = entry.author

            if hasattr(entry, "license") and entry.license is not None:
                entry_item.license = entry.license

            if hasattr(entry, "feedburner_origlink"):
                entry_item.link = entry.feedburner_origlink
            else:
                entry_item.link = entry.link

            feed_hostname = urlparse(self.feed.link).hostname
            if urlparse(entry_item.link).hostname == urlparse(self.feed.link).hostname:
                entry_item.available_in_frame = self.available
            else:
                entry_item.available_in_frame = 1

            entry_item.save()

            announce_client.broadcast_group(self.feed.id, 'new_entry',
                data = {
                    'id': entry_item.id,
                    'title': entry_item.title,
                    'feed_id': entry_item.feed.id,
                    'feed_title': self.feed.title,
                    'link': entry_item.link,
                    'available': 1 if entry_item.available_in_frame is None else entry_item.available_in_frame,
                    'created_at': int(time.mktime(entry_item.published_at.timetuple())*1000),
                }
            )
            # created_at field seems problematic.

class ProcessFeed(object):
    def __init__(self, feed):
        self.feed = feed
        self.user_agent = "ChapStream RSS Reader User Agent"

    def process(self):
        self.parsed = feedparser.parse(self.feed.feed_url, agent=self.user_agent, \
            etag=self.feed.etag)

        if hasattr(self.parsed, 'status'):
            # TODO: Other status codes, 200, 301 and etc...
            if self.parsed.status == 304:
                return True
            elif self.parsed.status >= 400:
                logging.error("HTTP ERROR %s: id:%s url:%s" % (self.parsed.status, \
                    self.feed.id, self.feed.feed_url))
                return False
            if hasattr(self.parsed, 'bozo') and self.parsed.bozo:
                logging.warn("!BOZO! Feed is not well formed: id:%s url:%s" % \
                    (self.feed.id, self.feed.feed_url))

        if 'links' in self.parsed.feed:
            for link in self.parsed.feed.links:
                if link.rel == 'hub':
                    # Hub detected!
                    self.feed.hub = link.href

        self.feed.etag = self.parsed.get('etag', '')
        # some times this is None (it never should) *sigh*
        if self.feed.etag is None:
            self.feed.etag = ''

        self.feed.tagline = self.parsed.feed.get('tagline', '')

        if hasattr(self.parsed.feed, "language"):
            self.feed.language = self.parsed.feed.language

        if hasattr(self.parsed.feed, "encoding"):
            self.feed.encoding = self.parsed.feed.encoding

        if hasattr(self.parsed.feed, "subtitle"):
            self.feed.subtitle = self.parsed.feed.subtitle

        if hasattr(self.parsed.feed, "image") and hasattr(self.parsed.feed.image, "href"):
            self.feed.image = self.parsed.feed.image.href

        if hasattr(self.parsed.feed, 'title'):
            self.feed.title = self.parsed.feed.title

        if hasattr(self.parsed.feed, 'link'):
            self.feed.link = self.parsed.feed.link

        # TODO: UTC seems problematic
        self.feed.last_sync = datetime.utcnow()#.replace(tzinfo=utc)

        # Save this feed
        self.feed.save()

        self.entries = self.parsed.entries
        self.entries.reverse()

        self.available = 0 if self.parsed.headers.has_key("x-frame-options") else 1


class DriveSync(object):
    def __init__(self, feed):
        sync_feed = ProcessFeed(feed)
        retval = sync_feed.process()
        if retval is None:
            # Process Entries
            ProcessEntry(feed, sync_feed.entries, available=sync_feed.available)
        feed.set_next_scheduled_update()
        connection.close()