import json
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from apps.storage.models import Feed, Entry
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
        item = {
            'id': entry.id,
            'title': entry.title,
            'feed_id': entry.feed.id,
            'feed_title': entry.feed.title,
            'link': entry.link,
            'available': 1 if entry.available_in_frame is None else entry.available_in_frame
        }
        result.append(item)
    return HttpResponse(json.dumps(result), content_type='application/json')


def feed_detail(request, feed_id):
    offset = request.GET.get("offset", 0)
    limit = request.GET.get("limit", 15)
    entries = Entry.objects.filter(feed_id=feed_id)[offset:limit]
    feed = entries[0].feed if entries else Feed.objects.get(id=feed_id)
    result = {
        'feed': {
            'id': feed.id,
            'title': feed.title,
            'tagline': feed.tagline,
            'link': feed.link,
            'is_subscribed': True if feed.users.filter(username=request.user.username) else False,
            'subs_count': feed.users.count()
        }
    }
    items = []
    for entry in entries:
        item = {
            'id': entry.id,
            'title': entry.title,
            'link': entry.link,
            'available': 1 if entry.available_in_frame is None else entry.available_in_frame,
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
            "link": feed.link,
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

    feed_id = entry.feed.id
    result = {
        "title": entry.title,
        "link": entry.link,
        "id": entry.id,
        "feed_title": entry.feed.title,
        "available": 1 if entry.available_in_frame is None else entry.available_in_frame

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