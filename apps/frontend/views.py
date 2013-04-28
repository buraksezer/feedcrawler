import json
from collections import OrderedDict
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.models import User
from apps.frontend.forms import SubscribeForm
from apps.storage.models import Feed, FeedTag, Entry, EntryLike, EntryDislike

# For doing realtime stuff
from announce import AnnounceClient
announce_client = AnnounceClient()


def home(request):
    entries = []
    # FIXME: This method may have caused performance issues.
    if request.user.is_authenticated():
        for entry in Entry.objects.all():
            if entry.feed.users.filter(id=request.user.id):
                entries.append(entry)
                if len(entries) == 15:
                    break
    return render_to_response('frontend/home.html', {"entries": entries}, context_instance=RequestContext(request))


def wrapper(request):
    if request.method != "POST":
        return HttpResponse("You must send a POST request.")
    if not request.user.is_authenticated():
        return HttpResponse("You must be login for using this.")

    request.session["feed_id"] = request.POST["feed_id"]
    request.session["entry_id"] = request.POST["entry_id"]
    return HttpResponse(1)


def get_user_feeds(request):
    if not request.user.is_authenticated():
        return HttpResponse("You must be login for using this.")
    return render_to_response('frontend/get_user_feeds.html', {"current_feed_id": int(request.POST["current_feed_id"]),
        "feeds": Feed.objects.filter(users=request.user.id).order_by("id")},
        context_instance=RequestContext(request))


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


def get_previous_and_next_items(request):
    # Why do we use get_next/previous_by_foo methods for doing this?
    # Those methods are broken for our case?
    feed_id = request.session["feed_id"]
    entry_id = request.session["entry_id"]
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


def explorer(request):
    if not request.user.is_authenticated():
        return HttpResponse("You must be login for using this.")
    if request.method != "GET":
        return HttpResponse("You must send a GET request.")

    entry_id = request.session["entry_id"]
    return render_to_response('frontend/explorer.html', {
        'entry': get_object_or_404(Entry, id=entry_id),
    }, context_instance=RequestContext(request))


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
