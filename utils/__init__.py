import datetime
from django.http import HttpResponseForbidden

def seconds_timesince(value):
    if not value:
        return 0
    now = datetime.datetime.utcnow()
    delta = now - value

    return delta.days * 24 * 60 * 60 + delta.seconds

def ajax_required(function=None):
    def _dec(view_func):
        def _view(request, *args, **kwargs):
            if not request.is_ajax():
                return HttpResponseForbidden()
            else:
                return view_func(request, *args, **kwargs)

        _view.__name__ = view_func.__name__
        _view.__dict__ = view_func.__dict__
        _view.__doc__ = view_func.__doc__

        return _view

    if function is None:
        return _dec
    else:
        return _dec(function)