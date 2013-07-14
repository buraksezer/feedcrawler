from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from utils import ajax_required

@login_required
def home(request):
    return render_to_response('frontend/home.html', context_instance=RequestContext(request))

@login_required
def feed_detail(request, slug):
    return render_to_response("frontend/home.html", context_instance=RequestContext(request))

def reader(request, slug):
    return render_to_response('frontend/reader.html', context_instance=RequestContext(request))

@login_required
def subscriptions(request):
    return render_to_response('frontend/home.html', context_instance=RequestContext(request))

@login_required
def interactions(request):
    return render_to_response('frontend/home.html', context_instance=RequestContext(request))

@login_required
def readlater(request):
    return render_to_response('frontend/home.html', context_instance=RequestContext(request))

@login_required
def entry(request, entry_id):
    return render_to_response('frontend/home.html', context_instance=RequestContext(request))

@login_required
def list(request, list_slug):
    return render_to_response('frontend/home.html', context_instance=RequestContext(request))