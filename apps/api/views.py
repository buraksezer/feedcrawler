import json
import time
import datetime
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from apps.storage.models import (Feed, Entry, EntryLike,
    Comment, ReadLater, List)
from apps.storage.tasks import SyncFeed
from userena.utils import get_profile_model, get_user_model
from django.contrib.auth.decorators import login_required
from utils import ajax_required, feedfinder
from django.db.models import Q
from django.db import IntegrityError

# For doing realtime stuff
from announce import AnnounceClient
announce_client = AnnounceClient()

# Utility functions
def get_user_profile(username):
    user = get_object_or_404(get_user_model(), username__iexact=username)
    profile_model = get_profile_model()
    try:
        profile = user.get_profile()
    except profile_model.DoesNotExist:
        profile = profile_model.objects.create(user=user)
    return profile


def get_user_timeline(user_id, feeds=[], offset=0, limit=15):
    feeds = feeds if feeds else Feed.objects.filter(users=user_id)
    return Entry.objects.filter(feed_id__in=feeds)[offset:limit]

def get_latest_comments(entry_id):
    offset = 0
    limit = 2
    results = []
    comments = Comment.objects.filter(entry_id=entry_id)[offset:limit]
    comment_count = Comment.objects.filter(entry_id=entry_id).count() - 2
    for comment in sorted(comments, key=lambda comment: comment.id):
        item = {
            "id": comment.id,
            "content": comment.content,
            "created_at": int(time.mktime(comment.created_at.timetuple())*1000),
            "author": comment.user.username
        }
        results.append(item)
    return {"results": results, "count": comment_count}

@ajax_required
@login_required
def user_profile(request):
    profile = get_user_profile(request.user.username)
    user = {
        "username": request.user.username,
        "subs_count": profile.user.feed_set.count(),
        "display_name": profile.user.get_full_name() if profile.user.get_full_name() else profile.user.username,
        "mugshot_url": profile.get_mugshot_url(),
        "rl_count": ReadLater.objects.filter(user=request.user).count(),
        "lists": [{"title": _list.title, "slug": _list.slug, "id": _list.id} for _list in List.objects.filter(user=request.user)]
    }
    return HttpResponse(json.dumps(user), content_type='application/json')


@login_required
def timeline(request, feeds=[]):
    offset = request.GET.get("offset", 0)
    limit = request.GET.get("limit", 15)
    entries = get_user_timeline(request.user.id, feeds=feeds, offset=offset, limit=limit)
    results = []
    for entry in entries:
        # FIXME: Move this blocks to model as a method
        try:
            EntryLike.objects.get(entry__id=entry.id, user=request.user)
            like_msg = "Unlike"
        except EntryLike.DoesNotExist:
            like_msg = "Like"

        try:
            like_count = EntryLike.objects.filter(entry__id=entry.id).count()
        except EntryLike.DoesNotExist:
            like_count = 0

        item = {
            'id': entry.id,
            'title': entry.title,
            'feed_id': entry.feed.id,
            'feed_title': entry.feed.title,
            'link': entry.link,
            'available': 1 if entry.available_in_frame is None else entry.available_in_frame,
            'like_msg': like_msg,
            'like_count': like_count,
            'created_at': int(time.mktime(entry.created_at.timetuple())*1000),
            'comments': get_latest_comments(entry.id),
            'inReadLater': True if ReadLater.objects.filter(user=request.user, entry__id=entry.id) else False
        }
        results.append(item)
    return HttpResponse(json.dumps(results), content_type='application/json')


@login_required
def _list(request, list_slug):
    feeds = [feed[0] for feed in List.objects.filter(slug=list_slug).values_list("feed__id")]
    return timeline(request, feeds=feeds)

@login_required
def list_title(request, list_slug):
    title = List.objects.filter(slug=list_slug).values("title")
    return HttpResponse(json.dumps(title[0]["title"]), content_type='application/json')


@ajax_required
@login_required
def single_entry(request, entry_id):
    try:
        entry = Entry.objects.get(id=entry_id)
    except Entry.DoesNotExist:
        return HttpResponse(json.dumps({'code': 0, 'msg': 'The entry could not be found.'}),
            content_type='application/json')

    # FIXME: Move this blocks to model as a method
    try:
        EntryLike.objects.get(entry__id=entry_id, user=request.user)
        like_msg = "Unlike"
    except EntryLike.DoesNotExist:
        like_msg = "Like"

    try:
        like_count = EntryLike.objects.filter(entry__id=entry_id).count()
    except EntryLike.DoesNotExist:
        like_count = 0

    item = {
        'id': entry.id,
        'title': entry.title,
        'feed_id': entry.feed.id,
        'feed_title': entry.feed.title,
        'link': entry.link,
        'available': 1 if entry.available_in_frame is None else entry.available_in_frame,
        'like_msg': like_msg,
        'like_count': like_count,
        'created_at': int(time.mktime(entry.created_at.timetuple())*1000),
        'comments': get_latest_comments(entry.id)
    }
    return HttpResponse(json.dumps(item), content_type='application/json')


def feed_detail(request, feed_id):
    offset = request.GET.get("offset", 0)
    limit = request.GET.get("limit", 15)
    entries = Entry.objects.filter(feed_id=feed_id)[offset:limit]
    try:
        feed = entries[0].feed if entries else Feed.objects.get(id=feed_id)
    except Feed.DoesNotExist:
        return HttpResponse(json.dumps({}), content_type='application/json')
    # FIXME: Move this blocks to model as a method
    result = {
        'feed': {
            'id': feed.id,
            'title': feed.title,
            'tagline': feed.tagline,
            'link': feed.link,
            'is_subscribed': True if feed.users.filter(username=request.user.username) else False,
            'subs_count': feed.users.count(),
            'last_sync': int(time.mktime(feed.last_sync.timetuple())*1000),
        }
    }
    items = []
    for entry in entries:
        try:
            EntryLike.objects.get(entry__id=entry.id, user=request.user)
            like_msg = "Unlike"
        except EntryLike.DoesNotExist:
            like_msg = "Like"

        try:
            like_count = EntryLike.objects.filter(entry__id=entry.id).count()
        except EntryLike.DoesNotExist:
            like_count = 0

        item = {
            'id': entry.id,
            'title': entry.title,
            'link': entry.link,
            'available': 1 if entry.available_in_frame is None else entry.available_in_frame,
            'like_msg': like_msg,
            'like_count': like_count,
            'created_at': int(time.mktime(entry.created_at.timetuple())*1000),
            'comments': get_latest_comments(entry.id)
        }
        items.append(item)
    result.update({"entries": items})
    return HttpResponse(json.dumps(result), content_type='application/json')


def subs_search(request, keyword):
    feeds = Feed.objects.filter(title__icontains=keyword)
    results = []
    for feed in feeds:
        tokens = feed.title.split(" ")
        results.append({
            "id": feed.id,
            "value": feed.title,
            "tokens": tokens
            }
        )
    return HttpResponse(json.dumps(results), content_type='application/json')


@ajax_required
def reader(request, entry_id):
    next = {}
    previous = {}
    # Firstly, find feed id
    try:
        entry = Entry.objects.get(id=entry_id)
    except Entry.DoesNotExist:
        return HttpResponse(json.dumps({"code": 0, "msg": "Sorry, that page doesn't exist!"}),
            content_type='application/json')

    try:
        EntryLike.objects.get(entry__id=entry.id, user=request.user)
        liked = True
    except EntryLike.DoesNotExist:
        liked = False

    feed_id = entry.feed.id
    result = {
        "title": entry.title,
        "link": entry.link,
        "id": entry.id,
        "feed_title": entry.feed.title,
        "available": 1 if entry.available_in_frame is None else entry.available_in_frame,
        "liked": liked,
        "inReadLater": True if entry.readlater_set.only() else False
    }

    try:
        next_item = Entry.objects.filter(feed=feed_id, id__gt=entry_id).order_by("id")[0]
        #n_available = next_item.available_in_frame
        #if n_available is None:
        #    n_available = 1
        next = {
            "feed_id": feed_id,
            "link": next_item.link,
            "id": next_item.id,
            "title": next_item.title,
        #    "available": n_available
        }
    except IndexError:
        pass
    try:
        previous_item = Entry.objects.filter(feed=feed_id, id__lt=entry_id)[0]
        #p_available = previous_item.available_in_frame
        #if p_available is None:
        #    p_available = 1
        previous = {
            "feed_id": feed_id,
            "link": previous_item.link,
            "id": previous_item.id,
            "title": previous_item.title,
        #    "available": p_available
        }
    except IndexError:
        pass

    result.update({"next": next, "previous": previous, "feed_id": feed_id})
    return HttpResponse(json.dumps({"code": 1, "result": result}), content_type='application/json')

@ajax_required
@login_required
def unsubscribe(request, feed_id):
    try:
        feed = Feed.objects.get(id=feed_id)
    except Feed.DoesNotExist:
        return HttpResponse(json.dumps({"code": 0, "text": "This feed does not exist: %s" % feed_id}), \
            content_type='application/json')
    # Unsubcribe from the feed
    feed.users.remove(User.objects.get(id=request.user.id))
    # Unregister feed real time notification group
    try:
        announce_client.unregister_group(request.user.id, feed.id)
    except AttributeError:
        # This is an error case. We should return an error message about that case and log this.
        # Maybe we should send an email to admins
        pass
    return HttpResponse(json.dumps({"code": 1, \
        "text": "You have been unsubscribed successfully from %s." % feed.title }), \
        content_type='application/json')

@ajax_required
@login_required
def subscribe_by_id(request, feed_id):
    # FIXME: We should handle error cases.
    feed_obj = Feed.objects.get(id=feed_id)
    user = User.objects.get(username=request.user.username)
    if not feed_obj.users.filter(username__contains=request.user.username):
        feed_obj.users.add(user)
        announce_client.register_group(request.user.id, feed_obj.id)
        return HttpResponse(json.dumps({"code": 1, "text":
            "New feed source has been added successfully."}), content_type='application/json')
    else:
        return HttpResponse(json.dumps({"code": 1,
            "text": "You have already subscribed this feed."}), content_type='application/json')


@ajax_required
@login_required
def find_source(request):
    url = request.GET.get("url", None)
    return HttpResponse(json.dumps(feedfinder.feeds(url)), content_type='application/json')


@ajax_required
@login_required
def subscribe(request):
    url = request.GET.get("url", None)
    # TODO: URL validation needed!
    #if url is None:
    #    return HttpResponse(json.dumps({"code":0,
    #        "text": "A valid feed could not be found for given URL."}), content_type='application/json')
    user = User.objects.get(username=request.user.username)
    try:
        feed_obj = Feed.objects.get(feed_url=url)
        if not feed_obj.users.filter(username__contains=request.user.username):
            feed_obj.users.add(user)
        else:
            return HttpResponse(json.dumps({"code": 1, "text": "You have already subscribed this feed."}), \
                content_type='application/json')
    except Feed.DoesNotExist:
        new_feed = Feed(feed_url=url)
        new_feed.save()
        feed_obj = Feed.objects.get(feed_url=url)
        feed_obj.users.add(user)
        feed_obj.save()
        SyncFeed.apply_async((feed_obj,))
    announce_client.register_group(request.user.id, feed_obj.id)
    return HttpResponse(json.dumps({"code": 1, "text": 'New feed source has been added successfully.'}), \
        content_type='application/json')


@login_required
def subscriptions(request):
    offset = request.GET.get("offset", 0)
    limit = request.GET.get("limit", 10)
    subscriptions = Feed.objects.filter(~Q(last_sync=None), users=request.user).order_by("-entries_last_month")[offset:limit]
    results = []
    for subscription in subscriptions:
        item = {
            "id": subscription.id,
            "title": subscription.title,
            "summary": subscription.tagline if subscription.tagline is not None else subscription.subtitle,
            'link': subscription.link
        }
        results.append(item)
    return HttpResponse(json.dumps(results), content_type="application/json")

@login_required
def entries_by_feed(request, feed_id):
    offset = request.GET.get("offset", 0)
    limit = request.GET.get("limit", 10)
    results = []
    entries = Entry.objects.filter(feed=feed_id)[offset:limit]
    for entry in entries:
        item = {
            "id": entry.id,
            "title": entry.title,
        }
        results.append(item)
    return HttpResponse(json.dumps(results), content_type="application/json")

@ajax_required
@login_required
def like(request, entry_id):
    '''Sets or removes user votes on entries.'''
    if request.method == "POST":
        item = EntryLike.objects.filter(user__id=request.user.id, entry__id=entry_id)
        if item:
            item.delete()
            return HttpResponse(json.dumps({"code": -1, "msg": "Like"}), content_type="application/json")
        else:
            try:
                new_item = EntryLike()
                new_item.entry_id = entry_id
                new_item.user_id = request.user.id
                new_item.save()

                # Set last_interaction field
                entry = Entry.objects.get(id=entry_id)
                entry.last_interaction = datetime.datetime.utcnow()
                entry.save()

                return HttpResponse(json.dumps({"code": 1, "msg": "Unlike"}), content_type="application/json")
            except IntegrityError:
                return HttpResponse(json.dumps({"code": 0, "msg": "Entry could not be found: %s" % entry_id}),
                    content_type="application/json")


# Comment related functions

@ajax_required
@login_required
def post_comment(request):
    comment = Comment()
    comment.entry_id = request.POST.get("entry_id")
    comment.user_id = request.user.id
    comment.content = request.POST.get("content").strip()
    comment.save()

    # Set last_interaction field
    entry = Entry.objects.get(id=request.POST.get("entry_id"))
    entry.last_interaction = datetime.datetime.utcnow()
    entry.save()

    # Result a json for presenting the new comment
    result = {
        "epoch": int(time.mktime(comment.created_at.timetuple())*1000),
        "author": request.user.username,
        "id": comment.id,
        "content": request.POST.get("content").strip(),
        "entry_id": request.POST.get("entry_id")
    }

    #realtime_result = result
    #realtime_result.update({
    #    "content": request.POST.get("content").strip(),
    #    "entry_id": request.POST.get("entry_id")
    #}) deep copy?
    feed_id = Feed.objects.get(entry__id=request.POST.get("entry_id")).id
    announce_client.broadcast_group(feed_id, 'new_comment', data=result)

    return HttpResponse(json.dumps(result), content_type="application/json")

@ajax_required
@login_required
def update_comment(request):
    comment = Comment.objects.get(id=request.POST.get("id"), user__id=request.user.id)
    #comment.user_id = request.user.id
    comment.content = request.POST.get("content").strip()
    comment.save()
    return HttpResponse(json.dumps({"code": 1}), content_type="application/json")


@ajax_required
@login_required
def delete_comment(request, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id, user=request.user)
        comment.delete()
    except Comment.DoesNotExist:
        return HttpResponse(json.dumps({"code": 0, "msg": "Invalid comment id."}), content_type="application/json")

    return HttpResponse(json.dumps({"code": 1, "msg": "Comment has been deleted successfully."}), content_type="application/json")


@ajax_required
@login_required
def fetch_comments(request, entry_id):
    comments = Comment.objects.filter(entry_id=entry_id)
    results = []
    for comment in sorted(comments, key=lambda comment: comment.id):
        item = {
            "content": comment.content,
            "created_at": int(time.mktime(comment.created_at.timetuple())*1000),
            "author": comment.user.username,
            "id": comment.id
        }
        results.append(item)
    return HttpResponse(json.dumps({"results": results, "count": 0}), content_type="application/json")

@ajax_required
@login_required
def interactions(request):
    offset = request.GET.get("offset", 0)
    limit = request.GET.get("limit", 15)
    user_id = request.user.id
    entries = Entry.objects.filter(Q(interaction__comment__user=user_id) | \
        Q(interaction__entrylike__user=user_id)).values(
        "id",
        "title",
        "feed__id",
        "feed__title",
        "link",
        "available_in_frame",
        "created_at",
        ).order_by("-last_interaction").distinct()[offset:limit]

    tmp = []
    results = []
    for entry in entries:
        if entry["id"] in tmp:
            continue
        try:
            EntryLike.objects.get(entry__id=entry["id"], user=request.user)
            like_msg = "Unlike"
        except EntryLike.DoesNotExist:
            like_msg = "Like"

        try:
            like_count = EntryLike.objects.filter(entry__id=entry["id"]).count()
        except EntryLike.DoesNotExist:
            like_count = 0

        item = {
            'id': entry["id"],
            'title': entry["title"],
            'feed_id': entry["feed__id"],
            'feed_title': entry["feed__title"],
            'link': entry["link"],
            'available': 1 if entry["available_in_frame"] is None else entry["available_in_frame"],
            'like_msg': like_msg,
            'like_count': like_count,
            'created_at': int(time.mktime(entry["created_at"].timetuple())*1000),
            'comments': get_latest_comments(entry["id"])
        }

        # FIXME: We should use a better method to handle duplicate items.
        # Django's distinct() method does not work for this case.
        if not entry["id"] in tmp:
            results.append(item)
            tmp.append(entry["id"])
    return HttpResponse(json.dumps(results), content_type="application/json")


@ajax_required
@login_required
def readlater(request, entry_id):
    readlater = ReadLater.objects.filter(user=request.user, entry__id=entry_id)
    if readlater:
        readlater.delete()
        return HttpResponse(json.dumps({'code': -1, 'msg': 'Succesfully removed.'}),
            content_type="application/json")
    else:
        try:
            readlater = ReadLater()
            readlater.entry_id = entry_id
            readlater.user_id = request.user.id
            readlater.save()
            return HttpResponse(json.dumps({'code': 1, 'msg': 'Succesfully added.'}),
                content_type="application/json")
        except IntegrityError:
            return HttpResponse(json.dumps({'code': 0, 'msg': 'Invalid user or entry.'}),
                content_type="application/json")

@ajax_required
@login_required
def readlater_list(request):
    offset = request.GET.get("offset", 0)
    limit = request.GET.get("limit", 15)
    results = []
    entries = ReadLater.objects.filter(user=request.user).values(
        "entry__title",
        "entry__link",
        "entry__id",
        "entry__available_in_frame",
        "entry__created_at",
        "entry__feed__id",
        "entry__feed__title",
    )[offset:limit]

    for entry in entries:
        try:
            EntryLike.objects.get(entry__id=entry["entry__id"], user=request.user)
            like_msg = "Unlike"
        except EntryLike.DoesNotExist:
            like_msg = "Like"

        try:
            like_count = EntryLike.objects.filter(entry__id=entry["entry__id"]).count()
        except EntryLike.DoesNotExist:
            like_count = 0

        item = {
            'id': entry["entry__id"],
            'title': entry["entry__title"],
            'feed_id': entry["entry__feed__id"],
            'feed_title': entry["entry__feed__title"],
            'link': entry["entry__link"],
            'available': 1 if entry["entry__available_in_frame"] is None else entry["entry__available_in_frame"],
            'like_msg': like_msg,
            'like_count': like_count,
            'created_at': int(time.mktime(entry["entry__created_at"].timetuple())*1000),
            'comments': get_latest_comments(entry["entry__id"])
        }
        results.append(item)

    return HttpResponse(json.dumps(results), content_type="application/json")


@ajax_required
@login_required
def lists(request):
    lists = List.objects.filter(user=request.user)
    if not lists:
        return HttpResponse(json.dumps({}), content_type="application/json")

    results = {}
    for _list in lists:
        _list_id = _list.id
        results[_list_id] = {'id': _list_id, 'slug': _list.slug, 'title': _list.title, 'items': []}
        items = List.objects.filter(id=_list_id).values("feed__title", "feed")
        for item in items:
            result = {
                'id': item["feed"],
                'title': item["feed__title"]
            }
            results[_list_id]['items'].append(result)

    return HttpResponse(json.dumps(results), content_type="application/json")

@ajax_required
@login_required
def append_to_list(request, list_id, feed_id):
    try:
        feed_item = Feed.objects.get(id=feed_id)
    except Feed.DoesNotExist:
        return HttpResponse(json.dumps({"code": 0, "msg": "Feed item could not be found."}),
            content_type="application/json")

    try:
        list_item = List.objects.get(id=list_id)
        try:
            list_item.feed.get(id=feed_id)
            return HttpResponse(json.dumps({"code": 0, "msg": "The list already includes the feed."}),
                content_type="application/json")
        except Feed.DoesNotExist:
            pass
    except List.DoesNotExist:
        return HttpResponse(json.dumps({"code": 0, "msg": "List item could not be found."}),
            content_type="application/json")

    list_item.feed.add(feed_item)
    return HttpResponse(json.dumps({"code": 1, "msg": "Successfully added."}),
            content_type="application/json")

@ajax_required
@login_required
def delete_from_list(request, list_id, feed_id):
    try:
        feed_item = Feed.objects.get(id=feed_id)
    except Feed.DoesNotExist:
        return HttpResponse(json.dumps({"code": 0, "msg": "Feed item could not be found."}),
            content_type="application/json")

    try:
        list_item = List.objects.get(id=list_id)
        try:
            list_item.feed.get(id=feed_id)
        except Feed.DoesNotExist:
            return HttpResponse(json.dumps({"code": 0, "msg": "The list does not include the feed."}),
                content_type="application/json")
    except List.DoesNotExist:
        return HttpResponse(json.dumps({"code": 0, "msg": "The list could not be found."}),
            content_type="application/json")

    list_item.feed.remove(feed_item)
    return HttpResponse(json.dumps({"code": 1, "msg": "Successfully deleted."}),
            content_type="application/json")


@ajax_required
@login_required
def delete_list(request, list_id):
    try:
        list_item = List.objects.get(id=list_id)
    except List.DoesNotExist:
        return HttpResponse(json.dumps({"code": 0, "msg": "The list could not be found."}),
            content_type="application/json")

    list_item.delete()
    return HttpResponse(json.dumps({"code": 1, "msg": "Successfully deleted."}),
            content_type="application/json")

@ajax_required
@login_required
def create_list(request):
    try:
        List.objects.get(user=request.user, title=request.POST.get("title"))
        return HttpResponse(json.dumps({"code": 0, "msg": "You have a list with that name."}),
            content_type="application/json")
    except List.DoesNotExist:
        item = List(title=request.POST.get("title"), user=request.user)
        item.save()
        return HttpResponse(json.dumps({"code": 1, "msg": "Successfully created.", "id": item.id, "slug": item.slug}),
            content_type="application/json")