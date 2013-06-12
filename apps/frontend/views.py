import json
from collections import OrderedDict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.models import User
from apps.frontend.forms import SubscribeForm, FeedSearchForm
from apps.storage.models import Feed, FeedTag, Entry, EntryLike, EntryDislike
from userena.utils import get_profile_model, get_user_model
from django.contrib.auth.decorators import login_required
from utils import ajax_required, feedfinder

# For doing realtime stuff
from announce import AnnounceClient
announce_client = AnnounceClient()

# Cassandra related functions
#import cass

# Utility functions
def get_user_profile(username):
    user = get_object_or_404(get_user_model(), username__iexact=username)
    profile_model = get_profile_model()
    try:
        profile = user.get_profile()
    except profile_model.DoesNotExist:
        profile = profile_model.objects.create(user=user)
    return profile


def get_user_timeline(user_id):
    entries = []
    for entry in Entry.objects.all():
        if entry.feed.users.filter(id=user_id):
            entries.append(entry)
            if len(entries) == 15:
                break
    return entries

@ajax_required
@login_required
def render_timeline_standalone(request):
    return render_to_response('frontend/partials/dashboard_timeline.html', {"timeline": True,
        'entries': get_user_timeline(request.user.id)}, context_instance=RequestContext(request))


@login_required
def home(request):
    profile = None
    entries = []
    # FIXME: This method may have caused performance issues.
    # This function must be called from Sign Up function
    # This is a temporary stuation
    #cass.save_user(request.user.username)
    entries = get_user_timeline(request.user.id)
    profile = get_user_profile(request.user.username)
    return render_to_response('frontend/home.html', {"timeline": True, "entries": entries,
        "feeds": Feed.objects.filter(users=request.user.id).order_by("id"),
        "profile": profile,
        "feed_search_form": FeedSearchForm(),
        "subscribe_feed_form": SubscribeForm(),
        }, context_instance=RequestContext(request))


def explorer(request, entry_id):
    return render_to_response('frontend/explorer.html', {
        'entry': get_object_or_404(Entry, id=entry_id),
        'subscribe_feed_form': SubscribeForm(),
    }, context_instance=RequestContext(request))


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
def get_entries_by_feed_id(request):
    if request.method != "POST":
        return HttpResponse("You must send a POST request.")
    depth = 1 if request.POST.get("depth") is None else int(request.POST.get("depth"))
    entries = Entry.objects.filter(feed=request.POST["feed_id"])[:depth*10]
    feed_title = Feed.objects.get(id=request.POST["feed_id"]).title
    return render_to_response('frontend/partials/dashboard_timeline.html', {"feed_title": feed_title,
        'depth': depth+1,
        "entries": entries}, context_instance=RequestContext(request))


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
        pass
    return HttpResponse(json.dumps({"code": 1, "text": "You have been unsubscribed successfully from %s." % feed.title }), \
        content_type='application/json')


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
            return HttpResponse(json.dumps({"code": 1, "text": "You have already subscribed this feed."}), content_type='application/json')
    except Feed.DoesNotExist:
        new_feed = Feed(feed_url=url)
        new_feed.save()
        feed_obj = Feed.objects.get(feed_url=url)
        feed_obj.users.add(user)
        feed_obj.save()
    announce_client.register_group(request.user.id, feed_obj.id)
    return HttpResponse(json.dumps({"code": 1, "text": 'New feed source has been added successfully.'}), content_type='application/json')


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

"""
def subscribe_user(request):
    if not request.user.is_authenticated():
        return HttpResponse("You must be logged in for doing this.")
    subscriber = request.POST["username"]
    if cass.subscribe_user(request.user.username, subscriber):
        return HttpResponse(1)
    return HttpResponse(0)


def unsubscribe_user(request):
    if not request.user.is_authenticated():
        return HttpResponse("You must be logged in for doing this.")
    subscriber = request.POST["username"]
    if cass.unsubscribe_user(request.user.username, subscriber):
        return HttpResponse(1)
    return HttpResponse(0)


def check_subscribe(request):
    if not request.user.is_authenticated():
        return HttpResponse("You must be logged in for doing this.")
    if cass.check_subscription(request.POST["username"], request.user.username):
        return HttpResponse(1)
    return HttpResponse(0)

def share_entry(request):
    if not request.user.is_authenticated():
        return HttpResponse("You must be logged in for doing this.")

    if request.method == "POST":
        peed = {"note": request.POST["note"],
                "entry_id": request.POST["entry_id"],
                "feed_id": request.POST["feed_id"],
                "username": request.user.username
                }
        peed_id = uuid.uuid1()
        print request.POST["note"]
        cass.save_peed(peed_id, request.user.username, peed)
        return HttpResponse(1)
    return HttpResponse(0)
"""