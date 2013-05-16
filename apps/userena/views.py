import cass
from userena.views import *
from apps.storage.models import Entry

from datetime import datetime

def profile_detail(request, username,
    template_name=userena_settings.USERENA_PROFILE_DETAIL_TEMPLATE,
    extra_context=None, **kwargs):
    """
    Detailed view of an user.

    :param username:
        String of the username of which the profile should be viewed.

    :param template_name:
        String representing the template name that should be used to display
        the profile.

    :param extra_context:
        Dictionary of variables which should be supplied to the template. The
        ``profile`` key is always the current profile.

    **Context**

    ``profile``
        Instance of the currently viewed ``Profile``.

    """
    def get_user_profile(user_name):
        user = get_object_or_404(get_user_model(),
                                 username__iexact=user_name)
        profile_model = get_profile_model()
        try:
            profile = user.get_profile()
        except profile_model.DoesNotExist:
            profile = profile_model.objects.create(user=user)
        return profile

    profile = get_user_profile(username)
    if not profile.can_view_profile(request.user):
        return HttpResponseForbidden(_("You don't have permission to view this profile."))
    if not extra_context:
        extra_context = dict()
    extra_context['profile'] = profile
    extra_context['hide_email'] = userena_settings.USERENA_HIDE_EMAIL

    if request.user.username == username:
        timeline_items = cass.get_timeline(username)[0]
    else:
        timeline_items = cass.get_userline(username)[0]
    shared_items = []
    for timeline_item in timeline_items:
        participant_name = request.user.username if request.user.username == timeline_item["username"] \
            else timeline_item["username"]
        shared_items.append({"entry": Entry.objects.filter(id=timeline_item["entry_id"]).get(),
         "participant": get_user_profile(participant_name),
         "note": timeline_item["note"] if timeline_item["note"].strip() else None,
         "timestamp": datetime.fromtimestamp(timeline_item["timestamp"] / 1e6)
         })
    extra_context["shared_items"] = shared_items
    return ExtraContextTemplateView.as_view(template_name=template_name,
                                            extra_context=extra_context)(request)
