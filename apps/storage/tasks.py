import redis
from datetime import datetime
from celery.task import Task
from utils import log as logging
from utils.feed_fetcher import DriveSync
from django.conf import settings
from apps.storage.models import Feed

class UpdateFeed(Task):
    name = "update-feed"

    def run(self, feed, **kwargs):
        r = redis.Redis(connection_pool=settings.REDIS_FEED_POOL)
        logging.info("%s:%s updating" %(feed.id, feed.title))
        r.zrem("scheduled_updates", feed.id)
        DriveSync(feed)


class TaskFeed(Task):
    name = 'task-feed'

    def run(self, **kwargs):
        r = redis.Redis(connection_pool=settings.REDIS_FEED_POOL)
        now = datetime.utcnow()
        feed_ids = r.zrangebyscore("scheduled_updates", 0, now.strftime("%s"))
        print feed_ids
        for feed_id in feed_ids:
            try:
                feed = Feed.objects.get(id=feed_id)
                UpdateFeed.apply_async((feed,))
            except Feed.DoesNotExist:
                r.zrem("scheduled_updates", feed_id)

class SyncFeed(Task):
    name = 'sync-feed'

    def run(self, feed, **kwargs):
        DriveSync(feed)

class FirstSync(Task):
    name = 'first-sync'

    def run(self, **kwargs):
        for feed in Feed.objects.filter(is_active=True, last_sync=None):
            SyncFeed.apply_async((feed,))

