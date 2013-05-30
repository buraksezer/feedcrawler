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

from django.db import connection

announce_client = AnnounceClient()

class ProcessEntry(object):
    def __init__(self, feed, entries):
        self.feed = feed
        self.entries = entries
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

            if hasattr(entry, "published_parsed"):
                entry_item.published_at = datetime.fromtimestamp(mktime(entry.published_parsed))
            else:
                entry_item.published_at = datetime.utcnow()

            if hasattr(entry, "author") and entry.author is not None:
                entry_item.author = entry.author

            if hasattr(entry, "license") and entry.license is not None:
                entry_item.license = entry.license

            entry_item.link = entry.link
            entry_item.save()

            announce_client.broadcast_group(self.feed.id, 'new_entry', data={'id': entry_item.id,
                'feed_id': self.feed.id,
                'link': entry.link,
                'published_at': entry_item.published_at.strftime("%B %d, %y") if isinstance(entry_item.published_at, datetime) else entry_item.published_at,
                'feed_title': self.feed.title,
                'title':entry.title}
            )

class ProcessFeed(object):
    def __init__(self, feed):
        self.feed = feed
        self.user_agent = "FeedCraft RSS Reader User Agent"

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

        # TODO: UTC seems problematic
        self.feed.last_sync = datetime.utcnow()#.replace(tzinfo=utc)

        # Save this feed
        self.feed.save()

        self.entries = self.parsed.entries
        self.entries.reverse()


class DriveSync(object):
    def __init__(self, feed):
        sync_feed = ProcessFeed(feed)
        retval = sync_feed.process()
        if retval is None:
            # Process Entries
            ProcessEntry(feed, sync_feed.entries)
        feed.set_next_scheduled_update()
        connection.close()