import redis
import celery
from datetime import datetime
from utils import log as logging
from utils.feed_fetcher import DriveSync
from django.conf import settings
from apps.storage.models import Feed
from django.db.models import Q


@celery.task(name="update-feed")
def update_feed(feed, **kwargs):
    r = redis.Redis(connection_pool=settings.REDIS_FEED_POOL)
    logging.info("%s:%s updating" % (feed.id, feed.title))
    r.zrem("scheduled_updates", feed.id)
    DriveSync(feed)


@celery.task(name='task-feed')
def task_feed(**kwargs):
    r = redis.Redis(connection_pool=settings.REDIS_FEED_POOL)
    now = datetime.utcnow()
    feed_ids = r.zrangebyscore("scheduled_updates", 0, now.strftime("%s"))
    print feed_ids
    for feed_id in feed_ids:
        try:
            feed = Feed.objects.get(id=feed_id)
            update_feed.apply_async((feed,))
        except Feed.DoesNotExist:
            r.zrem("scheduled_updates", feed_id)


@celery.task(name='sync-feed')
def sync_feed(feed, **kwargs):
    DriveSync(feed)


@celery.task(name="unattended-feeds-sync")
def unattended_feeds_sync(**kwargs):
    r = redis.Redis(connection_pool=settings.REDIS_FEED_POOL)
    scheduled_feed_ids = r.zrange("scheduled_updates", 0, -1)
    feeds = Feed.objects.filter(~Q(id__in=scheduled_feed_ids), is_active=True)
    for feed in feeds:
        sync_feed.apply_async((feed,))
