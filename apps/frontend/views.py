import uuid
import json
from collections import OrderedDict
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.models import User
from apps.frontend.forms import SubscribeForm
from apps.storage.models import Feed, FeedTag, Entry, EntryLike, EntryDislike
from userena.utils import signin_redirect, get_profile_model, get_user_model

# For doing realtime stuff
from announce import AnnounceClient
announce_client = AnnounceClient()

# Cassandra related functions
import cass

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


def render_timeline_standalone(request):
    if not request.user.is_authenticated():
        return HttpResponse("You must be sign in to do this.")
    return render_to_response('frontend/partials/dashboard_timeline.html', {"timeline": True,
        'entries': get_user_timeline(request.user.id)}, context_instance=RequestContext(request))


def home(request):
    profile = None
    entries = []
    # FIXME: This method may have caused performance issues.
    if request.user.is_authenticated():
        # This function must be called from Sign Up function
        # This is a temporary stuation
        cass.save_user(request.user.username)
        entries = get_user_timeline(request.user.id)
        profile = get_user_profile(request.user.username)
    return render_to_response('frontend/home.html', {"timeline": True, "entries": entries,
        "feeds": Feed.objects.filter(users=request.user.id).order_by("id"),
        "profile": profile}, context_instance=RequestContext(request))


def explorer(request, entry_id):
    return render_to_response('frontend/explorer.html', {
        'entry': get_object_or_404(Entry, id=entry_id),
    }, context_instance=RequestContext(request))


def get_user_feeds(request):
    if not request.user.is_authenticated():
        return HttpResponse("You must be login for using this.")
    return render_to_response('frontend/get_user_feeds.html', {"current_feed_id": int(request.POST["current_feed_id"]),
        "feeds": Feed.objects.filter(users=request.user.id).order_by("id")},
        context_instance=RequestContext(request))


def get_entries_by_feed_id(request):
    if request.method != "POST":
        return HttpResponse("You must send a POST request.")
    if not request.user.is_authenticated():
        return HttpResponse("You must be login for using this.")
    depth = 1 if request.POST.get("depth") is None else int(request.POST.get("depth"))
    entries = Entry.objects.filter(feed=request.POST["feed_id"])[:depth*10]
    feed_title = Feed.objects.get(id=request.POST["feed_id"]).title
    return render_to_response('frontend/partials/dashboard_timeline.html', {"feed_title": feed_title,
        'depth': depth+1,
        "entries": entries}, context_instance=RequestContext(request))


def get_feed_entries(request):
    if request.method != "POST":
        return HttpResponse("You must send a POST request.")
    if not request.user.is_authenticated():
        return HttpResponse("You must be login for using this.")
    data = OrderedDict()
    for entry in Entry.objects.filter(feed=request.POST["feed_id"]):
        if not entry.published_at in data:
            data[entry.published_at] = [entry]
        else:
            data[entry.published_at].append(entry)
    return render_to_response('frontend/get_feed_entries.html', {"current_entry_id": int(request.POST["current_entry_id"]),
        "feed_id":request.POST["feed_id"],
        "data": data}, context_instance=RequestContext(request))


def get_previous_and_next_items(request, feed_id, entry_id):
    # Why do we use get_next/previous_by_foo methods for doing this?
    # Those methods are broken for our case?
    # The next entry
    next_items = Entry.objects.filter(feed=feed_id, id__gt=entry_id)
    next = {}
    if next_items and len(next_items)-1 >= 0:
        next = {"feed_id": feed_id, "link": next_items[len(next_items)-1].link,
        "id": next_items[len(next_items)-1].id, "title": next_items[len(next_items)-1].title}
    # The previous item
    previous_items = Entry.objects.filter(feed=feed_id, id__lt=entry_id)
    previous = {} if not previous_items else {"feed_id": feed_id, "link": previous_items[0].link, "id": previous_items[0].id,
        "title": previous_items[0].title}
    return HttpResponse(json.dumps({"next": next, "previous": previous}), content_type='application/json')


def subscribe(request):
    def add_tags():
        for tag in tags:
            try:
                item = FeedTag.objects.get(tag=tag)
            except FeedTag.DoesNotExist:
                item = FeedTag(tag=tag)
                item.save()
                item = FeedTag.objects.get(tag=tag)
            item.feed.add(feed_obj)
            item.users.add(user)
            item.save()

    if request.method == "POST":
        form = SubscribeForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data["feed_url"]
            tags= [tag.strip() for tag in form.cleaned_data["tags"].split(",") if tag.strip()]
            user = User.objects.get(username=request.user.username)
            try:
                feed_obj = Feed.objects.get(feed_url=url)
                if not feed_obj.users.filter(username__contains=request.user.username):
                    feed_obj.users.add(user)
                    if tags:
                        add_tags()
                else:
                    return HttpResponse(json.dumps({"code": 1, "text": "You have already subscribed this feed."}), content_type='application/json')
            except Feed.DoesNotExist:
                new_feed = Feed(feed_url=url)
                new_feed.save()
                feed_obj = Feed.objects.get(feed_url=url)
                feed_obj.users.add(user)
                feed_obj.save()
                if tags:
                    add_tags()
            announce_client.register_group(request.user.id, feed_obj.id)
            return HttpResponse(json.dumps({"code": 1, "text": 'New feed source has been added successfully.'}), content_type='application/json')
        else:
            return HttpResponse(json.dumps({"code": 0, "text": "Broken form"}), content_type='application/json')
    else:
        form = SubscribeForm()
        return render_to_response('frontend/subscribe.html', {"form": form}, context_instance=RequestContext(request))


def vote(request):
    '''Sets or removes user votes on entries.'''
    # FIXME: We must evaluate error cases
    if request.user.is_authenticated():
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
    else:
        return HttpResponse("You must be logged in for using this.")


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
