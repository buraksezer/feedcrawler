from apps.storage.models import (Feed, Entry, Comment, EntryLike, ReadLater, List, RepostEntry)
from django.contrib import admin

admin.site.register(Feed)
admin.site.register(Entry)
admin.site.register(Comment)
admin.site.register(EntryLike)
admin.site.register(ReadLater)
admin.site.register(List)
admin.site.register(RepostEntry)
