# -*- coding: utf-8 -*-
from time import mktime
from datetime import datetime
from feedparser import parse
from celery.task import Task
from apps.storage.models import Feed, Entry, EntryTag


class SyncFeed(Task):
    name = 'sync-feed'

    def run(self, **kwargs):
        feed_objects = Feed.objects.all()
        for feed_object in feed_objects:
            data_bundle = parse(feed_object.feed_url)

            if not hasattr(data_bundle.feed, "link"):
                # TODO: We must use a logging mech.
                print(">> "+feed_object.feed_url+": this doesn't seem a valid feed url!")
                continue

            print(">> Checking new feeds for "+feed_object.feed_url)

            #if not FeedMetadata.objects.filter(link=data_bundle.feed.link):
            #    feed_object = FeedMetadata(link=data_bundle.feed.link, feed=feed_object)
            #else:
            #    feed_object = FeedMetadata.objects.get(link=data_bundle.feed.link)

            if hasattr(data_bundle.feed, "language"):
                feed_object.language = data_bundle.feed.language
            if hasattr(data_bundle, "encoding"):
                feed_object.encoding = data_bundle.encoding
            if hasattr(data_bundle.feed, "subtitle"):
                feed_object.subtitle = data_bundle.feed.subtitle
            if hasattr(data_bundle.feed, "image") and hasattr(data_bundle.feed.image, "href"):
                feed_object.image = data_bundle.feed.image.href
            feed_object.title = data_bundle.feed.title
            feed_object.save()

            for entry in data_bundle.entries:
                if not Entry.objects.filter(entry_id=entry.id):
                    entry_item = Entry(title=entry.title, feed=feed_object)
                    entry_item.entry_id = entry.id
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
                    print("===> New entry %s" % entry.title)
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