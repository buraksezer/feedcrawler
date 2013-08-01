from apps.storage.models import (Feed, Entry, EntryTag, Comment, \
    FeedTag, EntryLike, ReadLater, List, RepostEntry)
from apps.accounts.models import UserRelation
from django.contrib import admin

admin.site.register(Feed)
admin.site.register(Entry)
admin.site.register(EntryTag)
admin.site.register(Comment)
admin.site.register(FeedTag)
admin.site.register(EntryLike)
admin.site.register(ReadLater)
admin.site.register(List)
admin.site.register(RepostEntry)
admin.site.register(UserRelation)
