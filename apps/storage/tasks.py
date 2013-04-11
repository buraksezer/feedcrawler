# -*- coding: utf-8 -*-
import os
import logging
from time import mktime
from datetime import datetime
from feedparser import parse
from celery.task import Task
from apps.storage.models import Feed, Entry, EntryTag

logfile = "feedcraft-sync.log"


def initialize_logging():
    # Early form of logging facility

    # Create logfile if it does not exist
    # FIXME-1: Can I use with statement in bellow case?
    # FIXME-2: We must use a more proper way to serve constant values
    if not os.access(logfile, os.F_OK):
        f = open(logfile, 'w')
        f.close()

    # initialize
    if os.access(logfile, os.W_OK):
        logger = logging.getLogger("feedcraft-sync")
        hdlr = logging.FileHandler(logfile)
        formatter = logging.Formatter('%(created)f %(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)
        logger.setLevel(logging.INFO)
        return logger
    else:
        print("ERROR: I could not open {feedcraft-sync.log} file with write permissions. Please check this!")
        raise SystemExit(0)


def run_sync(feed_objects):
    for feed_object in feed_objects:
        data_bundle = parse(feed_object.feed_url)

        if not hasattr(data_bundle.feed, "link"):
            # TODO: We must use a logging mech.
            print(">> "+feed_object.feed_url+": this doesn't seem a valid feed url!")
            continue

        log.info(">> Checking new feeds for "+feed_object.feed_url)

        if hasattr(data_bundle.feed, "language"):
            feed_object.language = data_bundle.feed.language
        if hasattr(data_bundle, "encoding"):
            feed_object.encoding = data_bundle.encoding
        if hasattr(data_bundle.feed, "subtitle"):
            feed_object.subtitle = data_bundle.feed.subtitle
        if hasattr(data_bundle.feed, "image") and hasattr(data_bundle.feed.image, "href"):
            feed_object.image = data_bundle.feed.image.href
        feed_object.title = data_bundle.feed.title
        # TODO: UTC seems problematic
        feed_object.last_sync = datetime.now()
        feed_object.save()

        for entry in data_bundle.entries:
            entry_id = entry.id if hasattr(entry, "id") else entry.link
            if not Entry.objects.filter(entry_id=entry_id):
                entry_item = Entry(title=entry.title, feed=feed_object)
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
                if hasattr(entry, "updated_parsed"):
                    entry_item.updated_at = datetime.fromtimestamp(mktime(entry.updated_parsed))
                if hasattr(entry, "published_parsed"):
                    entry_item.published_at = datetime.fromtimestamp(mktime(entry.published_parsed))
                if hasattr(entry, "author") and entry.author is not None:
                    entry_item.author = entry.author
                if hasattr(entry, "license") and entry.license is not None:
                    entry_item.license = entry.license
                entry_item.link = entry.link
                # TODO: Logging needed
                log.info("===> New entry %s" % entry.title)
                entry_item.save()

                if hasattr(entry, "tags"):
                    for tag in entry.tags:
                        if not EntryTag.objects.filter(tag=tag.term):
                            entry_tag_item = EntryTag(tag=tag.term)
                            entry_tag_item.save()
                        else:
                            entry_tag_item = EntryTag.objects.get(tag=tag.term)
                        entry_tag_item.entry.add(entry_item)
                        entry_tag_item.save()


class SyncFeed(Task):
    name = 'sync-feed'

    def run(self, **kwargs):
        feed_objects = kwargs.get("feed_objects", Feed.objects.all())
        run_sync(feed_objects)


class FirstSync(Task):
    name = 'first-sync'

    def run(self, **kwargs):
        feed_objects = Feed.objects.filter(last_sync=None)
        if feed_objects:
            log.info("Running first-sync for some items")
            run_sync(feed_objects)

# Start logging
log = initialize_logging()
