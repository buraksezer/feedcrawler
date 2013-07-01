import json
import time
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from apps.storage.models import Feed, Entry, EntryLike, Comment
from userena.utils import get_profile_model, get_user_model
from django.contrib.auth.decorators import login_required
from utils import ajax_required
from django.db.models import Q

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


def get_user_timeline(user_id, offset=0, limit=15):
    feeds = Feed.objects.filter(users=user_id)
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
    }
    return HttpResponse(json.dumps(user), content_type='application/json')


@login_required
def timeline(request):
    offset = request.GET.get("offset", 0)
    limit = request.GET.get("limit", 15)
    entries = get_user_timeline(request.user.id, offset=offset, limit=limit)
    result = []
    for entry in entries:
        # FIXME: Move this blocks to model as a method
        try:
            EntryLike.objects.get(entry__id=entry.id, user=request.user)
            like_msg = "Unlike"
        except EntryLike.DoesNotExist:
            like_msg = "Like"

        try:
            like_count = EntryLike.objects.get(entry__id=entry.id).user.count()
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
            'created_at': int(time.mktime(entry.published_at.timetuple())*1000),
            'comments': get_latest_comments(entry.id)
        }
        result.append(item)
    return HttpResponse(json.dumps(result), content_type='application/json')


def feed_detail(request, feed_id):
    offset = request.GET.get("offset", 0)
    limit = request.GET.get("limit", 15)
    entries = Entry.objects.filter(feed_id=feed_id)[offset:limit]
    feed = entries[0].feed if entries else Feed.objects.get(id=feed_id)
    # FIXME: Move this blocks to model as a method
    result = {
        'feed': {
            'id': feed.id,
            'title': feed.title,
            'tagline': feed.tagline,
            'link': feed.link,
            'is_subscribed': True if feed.users.filter(username=request.user.username) else False,
            'subs_count': feed.users.count(),
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
            like_count = EntryLike.objects.get(entry__id=entry.id).user.count()
        except EntryLike.DoesNotExist:
            like_count = 0

        item = {
            'id': entry.id,
            'title': entry.title,
            'link': entry.link,
            'available': 1 if entry.available_in_frame is None else entry.available_in_frame,
            'like_msg': like_msg,
            'like_count': like_count,
            'created_at': int(time.mktime(entry.published_at.timetuple())*1000),
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
        entry = Entry.objects.get(id=entry_id)
        try:
            item = EntryLike.objects.get(entry=entry)
            if not item.user.filter(username__contains=request.user.username):
                item.user.add(request.user)
                item.save()
            else:
                item.user.remove(request.user)
                return HttpResponse(json.dumps({"code": -1, "msg": "Like"}), content_type="application/json")
        except EntryLike.DoesNotExist:
            item = EntryLike(entry=entry)
            item.save()
            my_item = EntryLike.objects.get(id=item.id)
            my_item.user.add(request.user)
            my_item.save()
        # TODO:Error cases
        return HttpResponse(json.dumps({"code": 1, "msg": "Unlike"}), content_type="application/json")


# Comment related functions

@ajax_required
@login_required
def post_comment(request):
    comment = Comment()
    comment.entry_id = request.POST.get("entry_id")
    comment.user_id = request.user.id
    comment.content = request.POST.get("content").strip()
    comment.save()

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