import json
from collections import OrderedDict
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.models import User
from apps.frontend.forms import SubscribeForm #, FeedSearchForm
from apps.storage.models import Feed, Entry, EntryLike, EntryDislike
from userena.utils import get_profile_model, get_user_model
from django.contrib.auth.decorators import login_required
from utils import ajax_required, feedfinder
from django.conf import settings

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
def timeline(request):
    offset = request.GET.get("offset", 0)
    limit = request.GET.get("limit", 15)
    by_id = request.GET.get("by_id", None)
    template = "frontend/partials/dashboard_timeline.html"
    if by_id is None:
        entries = get_user_timeline(request.user.id, offset=offset, limit=limit)
        timeline = True
    else:
        entries = Entry.objects.filter(feed_id=by_id)[offset:limit]
        timeline = False
    if offset != 0:
        template = "frontend/partials/dashboard_entries.html"
        timeline = False
    data = {"timeline": timeline, "entries": entries}
    return render_to_response(template, data, context_instance=RequestContext(request))


@login_required
def home(request):
    profile = None
    entries = []
    entries = get_user_timeline(request.user.id)
    profile = get_user_profile(request.user.username)
    data = {
        "timeline": True,
        "entries": entries,
        "profile": profile,
        "site_title": settings.DEFAULT_SITE_TITLE,
        "subscribe_feed_form": SubscribeForm()
    }
    return render_to_response('frontend/home.html', data, context_instance=RequestContext(request))


@login_required
def feed_detail(request, feed_id):
    offset = request.GET.get("offset", 0)
    limit = request.GET.get("limit", 15)
    profile = get_user_profile(request.user.username)
    entries = Entry.objects.filter(feed=feed_id)[offset:limit]
    feed = entries[0].feed if entries else Feed.objects.get(id=feed_id)
    data =  {
            "entries": entries,
            "profile": profile,
            "subscribe_feed_form": SubscribeForm(),
            "feed": feed,
            "site_title": settings.DEFAULT_SITE_TITLE+" | "+ feed.title,
            "is_subscribed": True if feed.users.filter(username=request.user.username) else False
    }
    return render_to_response("frontend/home.html", data, context_instance=RequestContext(request))


def explorer(request, entry_id):
    data = {
        'entry': get_object_or_404(Entry, id=entry_id),
        'subscribe_feed_form': SubscribeForm()
    }
    return render_to_response('frontend/explorer.html', data, context_instance=RequestContext(request))


@ajax_required
@login_required
def available_feeds(request):
    feeds = Feed.objects.all().order_by("-entries_last_month")
    return render_to_response('frontend/available_feeds.html',
        {"feeds": feeds}, context_instance=RequestContext(request))


@ajax_required
@login_required
def get_user_feeds(request):
    return render_to_response('frontend/get_user_feeds.html', {"current_feed_id": int(request.POST["current_feed_id"]),
        "feeds": Feed.objects.filter(users=request.user.id).order_by("id")},
        context_instance=RequestContext(request))

@ajax_required
@login_required
def get_feed_entries(request):
    if request.method != "POST":
        return HttpResponse("You must send a POST request.")
    data = OrderedDict()
    for entry in Entry.objects.filter(feed=request.POST["feed_id"]):
        if not entry.published_at in data:
            data[entry.published_at] = [entry]
        else:
            data[entry.published_at].append(entry)
    return render_to_response('frontend/get_feed_entries.html', {"current_entry_id": int(request.POST["current_entry_id"]),
        "feed_id":request.POST["feed_id"],
        "data": data}, context_instance=RequestContext(request))


@ajax_required
def get_previous_and_next_items(request, feed_id, entry_id):
    # Why do we use get_next/previous_by_foo methods for doing this?
    # Those methods are broken for our case?
    # The next entry
    next_items = Entry.objects.filter(feed=feed_id, id__gt=entry_id)
    next = {}
    if next_items and len(next_items)-1 >= 0:
        n_available = next_items[len(next_items)-1].available_in_frame
        if n_available is None:
            n_available = 1
        next = {"feed_id": feed_id, "link": next_items[len(next_items)-1].link,
        "id": next_items[len(next_items)-1].id, "title": next_items[len(next_items)-1].title,
        "available": n_available}
    # The previous item
    previous_items = Entry.objects.filter(feed=feed_id, id__lt=entry_id)
    p_available = previous_items[0].available_in_frame
    if p_available is None:
        p_available = 1
    previous = {} if not previous_items else {"feed_id": feed_id, "link": previous_items[0].link, "id": previous_items[0].id,
        "title": previous_items[0].title, "available": p_available}
    return HttpResponse(json.dumps({"next": next, "previous": previous}), content_type='application/json')


@ajax_required
@login_required
def unsubscribe(request):
    if request.method != "POST":
        return HttpResponse("You must send a POST request")
    feed_id = request.POST.get("feed_id", None)
    if feed_id is None:
        return HttpResponse("You must send a feed_id as a parameter.")

    try:
        feed = Feed.objects.get(id=feed_id)
    except Feed.DoesNotExist:
        return HttpResponse("This feed does not exist: %s" % feed_id)
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
def subscribe_by_id(request):
    # FIXME: We should handle error cases.
    feed_obj = Feed.objects.get(id=request.POST.get("feed_id"))
    user = User.objects.get(username=request.user.username)
    if not feed_obj.users.filter(username__contains=request.user.username):
        feed_obj.users.add(user)
        return HttpResponse(json.dumps({"code": 1, "text":
            "New feed source has been added successfully."}), content_type='application/json')
    else:
        return HttpResponse(json.dumps({"code": 1,
            "text": "You have already subscribed this feed."}), content_type='application/json')

@ajax_required
@login_required
def subscribe(request):
    url = feedfinder.feed(request.POST.get("feed_url"))
    if url is None:
        return HttpResponse(json.dumps({"code":0,
            "text": "A valid feed could not be found for given URL."}), content_type='application/json')
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
def subs(request):
    return HttpResponse(render_to_response("frontend/subscribe.html", {"url": request.GET.get("url")}))


@ajax_required
@login_required
def vote(request):
    '''Sets or removes user votes on entries.'''
    # FIXME: We must evaluate error cases
    if request.method == "POST":
        db_object = EntryLike if request.POST["action_type"] == "like" else EntryDislike
        entry = Entry.objects.get(id=request.POST["entry_id"])
        try:
            item = db_object.objects.get(entry=entry)
            if not item.user.filter(username__contains=request.user.username):
                item.user.add(request.user)
                item.save()
            else:
                item.user.remove(request.user)
        except db_object.DoesNotExist:
            item = db_object(entry=entry)
            item.save()
            my_item = db_object.objects.get(id=item.id)
            my_item.user.add(request.user)
            my_item.save()
        return HttpResponse(1)
    else:
        db_object = EntryLike if request.GET["action_type"] == "like" else EntryDislike
        entry = Entry.objects.get(id=request.GET["entry_id"])
        if db_object.objects.filter(entry=entry, user=request.user):
            return HttpResponse(1)
        return HttpResponse(0)


@ajax_required
@login_required
def get_user_subscriptions(request):
    result = []
    # What if title does not exist?
    for feed in Feed.objects.filter(users=request.user, title__icontains=request.GET.get("term")):
        item = feed.title[:32] if len(feed.title) >= 32 else feed.title
        result.append({"id": feed.id, "label": item})
    return HttpResponse(json.dumps(result), content_type='application/json')
