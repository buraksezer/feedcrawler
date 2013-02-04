from django.utils import simplejson
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth import authenticate, login
from django.template import RequestContext

from django.contrib.auth.models import User
from apps.reader.models import Feed


def index(request):
    return render_to_response("reader/index.html", \
        context_instance=RequestContext(request))

# Functions for AJAX requests


def add_feed(request):
    if not request.user.is_authenticated():
        response_data = {
            "message": "You must be sign in for doing this.",
            "alert_type": "alert-error"
        }
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
    if request.method == "POST":
        url = request.POST.get("feed_url")
        user = User.objects.get(username=request.user.username)
        try:
            feed_obj = Feed.objects.get(feed_url=url)
            if not feed_obj.users.filter(username__contains=request.user.username):
                feed_obj.users.add(user)
            else:
                response_data = {"message":
                    "You have already subscribed this feed.",
                    "alert_type": "alert-block"
                }
                return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
        except Feed.DoesNotExist:
            new_feed = Feed(feed_url=url)
            new_feed.save()
            feed_obj = Feed.objects.get(feed_url=url)
            feed_obj.users.add(user)
            feed_obj.save()
            response_data = {
                "message": "New feed source has been added successfully.",
                "alert_type": "alert-success"
            }
            return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
    return HttpResponse("I am only accepting POST methods. Sorry... :'(")
