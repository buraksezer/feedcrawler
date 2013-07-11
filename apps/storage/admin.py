from apps.storage.models import (Feed, Entry, EntryTag, Comment,
    FeedTag, EntryLike, ReadLater, List)
from django.contrib import admin

admin.site.register(Feed)
admin.site.register(Entry)
admin.site.register(EntryTag)
admin.site.register(Comment)
admin.site.register(FeedTag)
admin.site.register(EntryLike)
admin.site.register(ReadLater)
admin.site.register(List)
