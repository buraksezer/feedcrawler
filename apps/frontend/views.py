# Create your views here.

from django.contrib import messages
from django.http import HttpResponse #, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib.auth import authenticate, login
from django.template import RequestContext
from django.contrib.auth.models import User


from apps.frontend.forms import AuthenticationForm, SubscribeForm

from apps.storage.models import Feed, FeedTag, Entry


def home(request):
    data = {}
    for item in Feed.objects.filter(users=request.user.id):
        data[item] = Entry.objects.filter(feed=item.id)
    return render_to_response('frontend/home.html', {"data": data}, context_instance=RequestContext(request))


def explorer(request, feed_id, slug):
    if not request.user.is_authenticated():
        return HttpResponse("You must be login for using this.")
    entry = Entry.objects.filter(feed=feed_id, slug=slug)[0]
    # The next entry
    next_items = Entry.objects.filter(feed=feed_id, id__gt=entry.id)
    next = {} if not next_items else {"link": "/explorer/"+feed_id+"/"+next_items[len(next_items)-1].slug, \
        "title": next_items[len(next_items)-1].title}

    # The previous item
    previous_items = Entry.objects.filter(feed=feed_id, id__lt=entry.id)
    previous = {} if len(previous_items) == 0 else {"link": "/explorer/"+feed_id+"/"+previous_items[0].slug, \
        "title": previous_items[0].title}

    return render_to_response('frontend/explorer.html', {
        'entry': get_object_or_404(Entry, slug=slug),
        'previous': previous,
        'next': next
    }, context_instance=RequestContext(request))



def auth(request):
    if request.method == "POST":
        form = AuthenticationForm(request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data["username"], password=form.cleaned_data["password"])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    # Redirect to a success page.
                    return redirect("home")
                else:
                    return HttpResponse("disabled account")
                # Return a 'disabled account' error message
            else:
                return HttpResponse("invalid login")
            # Return an 'invalid login' error message.
    else:
        form = AuthenticationForm()
        return render_to_response('frontend/auth.html', {"form": form}, context_instance=RequestContext(request))

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
                    messages.add_message(request, messages.INFO, 'You have already subscribed this feed.')
                return redirect("home")
            except Feed.DoesNotExist:
                new_feed = Feed(feed_url=url)
                new_feed.save()
                feed_obj = Feed.objects.get(feed_url=url)
                feed_obj.users.add(user)
                feed_obj.save()
                if tags:
                    add_tags()
                messages.add_message(request, messages.INFO, 'New feed source has been added successfully.')
                return redirect("home")
            return HttpResponse(tags)
        else:
            return HttpResponse("corrupted form")
    else:
        form = SubscribeForm()
        return render_to_response('frontend/subscribe.html', {"form": form}, context_instance=RequestContext(request))
