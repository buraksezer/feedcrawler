import time
import datetime
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from apps.storage.models import (Feed, Entry, EntryLike,
    Comment, ReadLater, List)
from apps.storage.tasks import SyncFeed
from userena.utils import get_profile_model, get_user_model
from utils import feedfinder
from django.db.models import Q
from django.db import IntegrityError

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions

# For doing realtime stuff
from announce import AnnounceClient
announce_client = AnnounceClient()


def process_like(entry_id, user_id):
    try:
        EntryLike.objects.get(entry__id=entry_id, user=user_id)
        like_msg = "Unlike"
    except EntryLike.DoesNotExist:
        like_msg = "Like"

    try:
        like_count = EntryLike.objects.filter(entry__id=entry_id).count()
    except EntryLike.DoesNotExist:
        like_count = 0

    return like_msg, like_count


def get_user_profile(username):
    user = get_object_or_404(get_user_model(), username__iexact=username)
    profile_model = get_profile_model()
    try:
        profile = user.get_profile()
    except profile_model.DoesNotExist:
        profile = profile_model.objects.create(user=user)
    return profile


def get_user_timeline(user_id, feed_ids=[], offset=0, limit=15):
    if not feed_ids:
        feed_ids = [feed_id[0] for feed_id in Feed.objects.filter(users=user_id).values_list("id")]
    return Entry.objects.filter(feed_id__in=feed_ids).values("id", "title", "feed__slug", \
        "feed__title", "link", "available_in_frame", "created_at", "slug")[offset:limit]


def get_latest_comments(entry_id, offset=0, limit=2, whole=False):
    results = []
    if not whole:
        comments = Comment.objects.filter(entry_id=entry_id).values('id', \
            'content', 'created_at', 'user__username')[offset:limit]
        count = Comment.objects.filter(entry_id=entry_id).count()
    else:
        comments = Comment.objects.filter(entry_id=entry_id).values('id', \
            'content', 'created_at', 'user__username')
        count = 0

    for comment in sorted(comments, key=lambda comment: comment["id"]):
        item = {
            "id": comment["id"],
            "content": comment["content"],
            "created_at": int(time.mktime(comment["created_at"].timetuple())*1000),
            "author": comment['user__username']
        }
        results.append(item)
    return {"results": results, "count": count}


class AuthenticatedUser(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, pk=None):
        profile = get_user_profile(request.user.username)
        user = {
            "username": request.user.username,
            "subs_count": profile.user.feed_set.count(),
            "display_name": profile.user.get_full_name() if profile.user.get_full_name() else profile.user.username,
            "mugshot_url": profile.get_mugshot_url(),
            "rl_count": ReadLater.objects.filter(user=request.user).count(),
            "lists": [{"title": _list.title, "slug": _list.slug, "id": _list.id} for _list in List.objects.filter(user=request.user)]
        }
        return Response(user)


class Timeline(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, feed_ids=[], pk=None):
        offset = request.GET.get("offset", 0)
        limit = request.GET.get("limit", 15)
        entries = get_user_timeline(request.user.id, feed_ids=feed_ids, offset=offset, limit=limit)
        results = []
        for entry in entries:
            like_msg, like_count = process_like(entry["id"], request.user.id)
            item = {
                'id': entry["id"],
                'title': entry["title"],
                'feed_slug': entry["feed__slug"],
                'feed_title': entry["feed__title"],
                'link': entry["link"],
                'available': 1 if entry["available_in_frame"] is None else entry["available_in_frame"],
                'like_msg': like_msg,
                'like_count': like_count,
                'slug': entry["slug"],
                'created_at': int(time.mktime(entry["created_at"].timetuple())*1000),
                'comments': get_latest_comments(entry["id"]),
                'inReadLater': True if ReadLater.objects.filter(user=request.user, entry__id=entry["id"]) else False
            }
            results.append(item)
        return Response(results)


class ListTimeline(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, list_slug):
        feed_ids = [feed[0] for feed in List.objects.filter(slug=list_slug).values_list("feed__id")]
        timeline = Timeline()
        return timeline.get(request, feed_ids)


class PrepareList(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, list_slug):
        values = List.objects.filter(slug=list_slug).values_list("title", "feed__id")
        result = {}
        if values:
            feed_ids = []
            for title, feed_id in values:
                feed_ids.append(feed_id)
            result = {"title": title, "feed_ids": feed_ids}
        return Response(result)


class SingleEntry(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, entry_id):
        try:
            entry = Entry.objects.filter(id=entry_id).values("id", "title", "feed__slug", \
                "feed__title", "link", "available_in_frame", "created_at", "slug")[0]
        except (Entry.DoesNotExist, IndexError):
            return Response({'code': 0, 'msg': 'The entry could not be found.'})
        like_msg, like_count = process_like(entry["id"], request.user.id)
        item = {
            'id': entry["id"],
            'slug': entry["slug"],
            'title': entry["title"],
            'feed_slug': entry["feed__slug"],
            'feed_title': entry["feed__title"],
            'link': entry["link"],
            'available': 1 if entry["available_in_frame"] is None else entry["available_in_frame"],
            'like_msg': like_msg,
            'like_count': like_count,
            'created_at': int(time.mktime(entry["created_at"].timetuple())*1000),
            'comments': get_latest_comments(entry["id"], whole=True),
            'inReadLater': True if ReadLater.objects.filter(user=request.user, entry__id=entry["id"]) else False
        }
        return Response(item)

class FeedDetail(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, slug):
        offset = request.GET.get("offset", 0)
        limit = request.GET.get("limit", 15)

        try:
            feed_query = Feed.objects.get(slug=slug)
        except Feed.DoesNotExist:
            return Response({"code": 0, "msg": "Feed could not be found."})

        entries = Entry.objects.filter(feed__slug=slug).values("id", "title", \
            "link", "available_in_frame", "created_at", "slug")[offset:limit]

        feed = Feed.objects.filter(slug=slug).values("id", "title", \
                "tagline", "link", "last_sync")[0]
        result = {
            'feed': {
                'id': feed["id"],
                'title': feed["title"],
                'tagline': feed["tagline"],
                'link': feed["link"],
                'is_subscribed': True if feed_query.users.filter(username=request.user.username) else False,
                'subs_count': feed_query.users.count(),
                'last_sync': int(time.mktime(feed["last_sync"].timetuple())*1000),
            }
        }
        items = []
        for entry in entries:
            like_msg, like_count = process_like(entry["id"], request.user.id)

            item = {
                'id': entry["id"],
                'title': entry["title"],
                'slug': entry["slug"],
                'feed_id': feed["id"],
                'feed_title': feed["title"],
                'link': entry["link"],
                'available': 1 if entry["available_in_frame"] is None else entry["available_in_frame"],
                'like_msg': like_msg,
                'like_count': like_count,
                'created_at': int(time.mktime(entry["created_at"].timetuple())*1000),
                'comments': get_latest_comments(entry["id"]),
                'inReadLater': True if ReadLater.objects.filter(user=request.user, entry__id=entry["id"]) else False
            }
            items.append(item)
        result.update({"entries": items})
        return Response(result)


class SubsSearch(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, keyword):
        typeahead = request.GET.get("typeahead", 1)
        feeds = Feed.objects.filter(title__icontains=keyword).values("id", "slug", "title")
        results = []
        if typeahead == 1:
            for feed in feeds:
                tokens = feed["title"].split(" ")
                results.append({
                    "slug": feed["slug"],
                    "value": feed["title"],
                    "tokens": tokens
                    }
                )
        else:
            for feed in feeds:
                results.append({
                    "id": feed["id"],
                    "title": feed["title"],
                    }
                )
        return Response(results)

class Reader(APIView):
    authentication_classes = (authentication.SessionAuthentication,)

    def get(self, request, slug):
        next = {}
        previous = {}
        try:
            entry = Entry.objects.filter(slug=slug).values("id", "title", "link", "feed__title", \
                "available_in_frame", "feed__id")[0]
        except (Entry.DoesNotExist, IndexError):
            return Response({"code": 0, "msg": "Sorry, that page doesn't exist!"})

        feed_id = entry["feed__id"]

        if request.user.is_authenticated():
            try:
                EntryLike.objects.get(entry__id=entry["id"], user=request.user)
                liked = True
            except EntryLike.DoesNotExist:
                liked = False

            try:
                ReadLater.objects.get(entry__id=entry["id"], user=request.user)
                inReadLater = True
            except ReadLater.DoesNotExist:
                inReadLater = False

            result = {
                "title": entry["title"],
                "link": entry["link"],
                "id": entry["id"],
                "feed_title": entry["feed__title"],
                "available": 1 if entry["available_in_frame"] is None else entry["available_in_frame"],
                "liked": liked,
                "inReadLater": inReadLater
            }

        else:
            result = {
                "title": entry["title"],
                "link": entry["link"],
                "id": entry["id"],
                "feed_title": entry["feed__title"],
                "available": 1 if entry["available_in_frame"] is None else entry["available_in_frame"],
            }

        try:
            next_item = Entry.objects.filter(feed=feed_id, \
                id__gt=entry["id"]).order_by("id").values("link", "slug", "title")[0]
            #n_available = next_item.available_in_frame
            #if n_available is None:
            #    n_available = 1
            next = {
                "feed_id": feed_id,
                "link": next_item["link"],
                "slug": next_item["slug"],
                "title": next_item["title"],
            #    "available": n_available
            }
        except IndexError:
            pass
        try:
            previous_item = Entry.objects.filter(feed=feed_id, \
                id__lt=entry["id"]).values("link", "slug", "title")[0]
            #p_available = previous_item.available_in_frame
            #if p_available is None:
            #    p_available = 1
            previous = {
                "feed_id": feed_id,
                "link": previous_item["link"],
                "slug": previous_item["slug"],
                "title": previous_item["title"],
            #    "available": p_available
            }
        except IndexError:
            pass

        result.update({"next": next, "previous": previous, \
            "feed_id": feed_id, "comments": get_latest_comments(entry["id"]) })
        return Response({"code": 1, "result": result})


class UnsubscribeByFeedId(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, feed_id):
        try:
            feed = Feed.objects.get(id=feed_id)
        except Feed.DoesNotExist:
            # FIXME: Use msg instead of text
            return Response({"code": 0, "text": "This feed does not exist: %s" % feed_id})

        # Unsubcribe from the feed
        feed.users.remove(User.objects.get(id=request.user.id))
        # Unregister feed real time notification group
        try:
            announce_client.unregister_group(request.user.id, feed.id)
        except AttributeError:
            # This is an error case. We should return an error message about that case and log this.
            # Maybe we should send an email to admins
            pass
        # FIXME: Use msg instead of text
        return Response({"code": 1, "text": "You have been unsubscribed successfully from %s." % feed.title})


class SubscribeByFeedId(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, feed_id):
        # FIXME: We should handle error cases.
        feed_obj = Feed.objects.get(id=feed_id)
        user = User.objects.get(username=request.user.username)
        if not feed_obj.users.filter(username__contains=request.user.username):
            feed_obj.users.add(user)
            announce_client.register_group(request.user.id, feed_obj.id)
            return Response({"code": 1, "text":"New feed source has been added successfully."})
        return Response({"code": 1, "text": "You have already subscribed this feed."})


class FindFeedWithURL(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        url = request.GET.get("url", None)
        return Response(feedfinder.feeds(url))


class SubscribeFeed(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        url = request.GET.get("url", None)
        # FIXME: URL validation needed!
        #if url is None:
        #    return HttpResponse(json.dumps({"code":0,
        #        "text": "A valid feed could not be found for given URL."}), content_type='application/json')
        user = User.objects.get(username=request.user.username)
        try:
            feed_obj = Feed.objects.get(feed_url=url)
            if not feed_obj.users.filter(username__contains=request.user.username):
                feed_obj.users.add(user)
            else:
                return Response({"code": 0, "text": "You have already subscribed this feed."})
        except Feed.DoesNotExist:
            new_feed = Feed(feed_url=url)
            new_feed.save()
            feed_obj = Feed.objects.get(feed_url=url)
            feed_obj.users.add(user)
            feed_obj.save()
            SyncFeed.apply_async((feed_obj,))
        announce_client.register_group(request.user.id, feed_obj.id)
        return Response({"code": 1, "text": 'New feed source has been added successfully.'})


class FeedSubscriptions(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        offset = request.GET.get("offset", 0)
        limit = request.GET.get("limit", 10)
        subscriptions = Feed.objects.filter(~Q(last_sync=None), \
            users=request.user).order_by("-entries_last_month").values("id", \
            "title", "tagline", "subtitle", "link", "slug")[offset:limit]
        results = []
        for subscription in subscriptions:
            item = {
                "slug": subscription["slug"],
                "title": subscription["title"],
                "summary": subscription["tagline"] if subscription["tagline"] \
                    is not None else subscription["subtitle"],
                'link': subscription["link"]
            }
            results.append(item)
        return Response(results)


class EntriesByFeed(APIView):
    authentication_classes = (authentication.SessionAuthentication,)

    def get(self, request, feed_id):
        offset = request.GET.get("offset", 0)
        limit = request.GET.get("limit", 10)
        results = []
        entries = Entry.objects.filter(feed=feed_id).values("slug", "title")[offset:limit]
        for entry in entries:
            item = {
                "slug": entry["slug"],
                "title": entry["title"],
            }
            results.append(item)
        return Response(results)


class LikeEntry(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, entry_id):
        '''Sets or removes user votes on entries.'''
        item = EntryLike.objects.filter(user__id=request.user.id, entry__id=entry_id)
        if item:
            item.delete()
            return Response({"code": -1, "msg": "Like"})
        else:
            try:
                new_item = EntryLike()
                new_item.entry_id = entry_id
                new_item.user_id = request.user.id
                new_item.save()
                # Set last_interaction field
                entry = Entry.objects.get(id=entry_id)
                entry.last_interaction = datetime.datetime.utcnow()
                entry.save()
                return Response({"code": 1, "msg": "Unlike"})
            except IntegrityError:
                return Response({"code": 0, "msg": "Entry could not be found: %s" % entry_id})


class PostComment(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        comment = Comment()
        comment.entry_id = request.POST.get("entry_id")
        comment.user_id = request.user.id
        comment.content = request.POST.get("content").strip()
        comment.save()

        # Set last_interaction field
        entry = Entry.objects.get(id=request.POST.get("entry_id"))
        entry.last_interaction = datetime.datetime.utcnow()
        entry.save()

        # Result a json for presenting the new comment
        result = {
            "created_at": int(time.mktime(comment.created_at.timetuple())*1000),
            "author": request.user.username,
            "id": comment.id,
            "content": request.POST.get("content").strip(),
            "entry_id": request.POST.get("entry_id")
        }

        #realtime_result = result
        #realtime_result.update({
        #    "content": request.POST.get("content").strip(),
        #    "entry_id": request.POST.get("entry_id")
        #}) deep copy?
        feed_id = Feed.objects.get(entry__id=request.POST.get("entry_id")).id
        announce_client.broadcast_group(feed_id, 'new_comment', data=result)
        return Response(result)


class UpdateComment(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            comment = Comment.objects.get(id=request.POST.get("id"), user__id=request.user.id)
            comment.content = request.POST.get("content").strip()
            comment.save()
        except Comment.DoesNotExist:
            return Response({"code": 0, "msg": "Invalid comment id."})
        return Response({"code": 1, "msg": "The comment updated successfully."})


class DeleteComment(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, comment_id):
        try:
            comment = Comment.objects.get(id=comment_id, user=request.user)
            comment.delete()
        except Comment.DoesNotExist:
            return Response({"code": 0, "msg": "Invalid comment id."})
        return Response({"code": 1, "msg": "Comment has been deleted successfully."})


class FetchComments(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, entry_id):
        comments = Comment.objects.filter(entry_id=entry_id)
        results = []
        for comment in sorted(comments, key=lambda comment: comment.id):
            item = {
                "content": comment.content,
                "created_at": int(time.mktime(comment.created_at.timetuple())*1000),
                "author": comment.user.username,
                "id": comment.id
            }
            results.append(item)
        return Response({"results": results, "count": 0})


class Interactions(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        offset = request.GET.get("offset", 0)
        limit = request.GET.get("limit", 15)
        user_id = request.user.id
        entries = Entry.objects.filter(Q(interaction__comment__user=user_id) | \
            Q(interaction__entrylike__user=user_id)).values(
            "id",
            "title",
            "feed__title",
            "feed__slug",
            "link",
            "slug",
            "available_in_frame",
            "created_at",
            ).order_by("-last_interaction").distinct()[offset:limit]

        tmp = []
        results = []
        for entry in entries:
            if entry["id"] in tmp:
                continue
            like_msg, like_count = process_like(entry["id"], request.user.id)
            item = {
                'id': entry["id"],
                'title': entry["title"],
                'feed_slug': entry["feed__slug"],
                'feed_title': entry["feed__title"],
                'slug': entry["slug"],
                'link': entry["link"],
                'available': 1 if entry["available_in_frame"] is None else entry["available_in_frame"],
                'like_msg': like_msg,
                'like_count': like_count,
                'created_at': int(time.mktime(entry["created_at"].timetuple())*1000),
                'comments': get_latest_comments(entry["id"])
            }

            # FIXME: We should use a better method to handle duplicate items.
            # Django's distinct() method does not work for this case.
            if not entry["id"] in tmp:
                results.append(item)
                tmp.append(entry["id"])
        return Response(results)


class ManageReadLater(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, entry_id):
        readlater = ReadLater.objects.filter(user=request.user, entry__id=entry_id)
        if readlater:
            readlater.delete()
            return Response({'code': -1, 'msg': 'Succesfully removed.'})
        else:
            try:
                readlater = ReadLater()
                readlater.entry_id = entry_id
                readlater.user_id = request.user.id
                readlater.save()
                return Response({'code': 1, 'msg': 'Succesfully added.'})
            except IntegrityError:
                return Response({'code': 0, 'msg': 'Invalid user or entry.'})


class ReadLaterList(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        offset = request.GET.get("offset", 0)
        limit = request.GET.get("limit", 15)
        results = []
        entries = ReadLater.objects.filter(user=request.user).values(
            "entry__title",
            "entry__link",
            "entry__id",
            "entry__available_in_frame",
            "entry__created_at",
            "entry__feed__slug",
            "entry__feed__title",
            "entry__slug"
        )[offset:limit]

        for entry in entries:
            like_msg, like_count = process_like(entry["entry__id"], request.user.id)
            item = {
                'id': entry["entry__id"],
                'slug': entry["entry__slug"],
                'title': entry["entry__title"],
                'feed_slug': entry["entry__feed__slug"],
                'feed_title': entry["entry__feed__title"],
                'link': entry["entry__link"],
                'available': 1 if entry["entry__available_in_frame"] is None else entry["entry__available_in_frame"],
                'like_msg': like_msg,
                'like_count': like_count,
                'created_at': int(time.mktime(entry["entry__created_at"].timetuple())*1000),
                'comments': get_latest_comments(entry["entry__id"])
            }
            results.append(item)
        return Response(results)


class RetrieveLists(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        lists = List.objects.filter(user=request.user)
        if not lists:
            return Response({"code": 0, "msg": "No list found."})
        results = {}
        for _list in lists:
            _list_id = _list.id
            results[_list_id] = {'id': _list_id, 'slug': _list.slug, 'title': _list.title, 'items': []}
            items = List.objects.filter(id=_list_id).values("feed__title", "feed")
            for item in items:
                result = {
                    'id': item["feed"],
                    'title': item["feed__title"]
                }
                results[_list_id]['items'].append(result)
        return Response(results)


class AppendToList(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, list_id, feed_id):
        try:
            feed_item = Feed.objects.get(id=feed_id)
        except Feed.DoesNotExist:
            return Response({"code": 0, "msg": "Feed item could not be found."})
        try:
            list_item = List.objects.get(id=list_id)
            try:
                list_item.feed.get(id=feed_id)
                return Response({"code": 0, "msg": "The list already includes the feed."})
            except Feed.DoesNotExist:
                pass
        except List.DoesNotExist:
            return Response({"code": 0, "msg": "List item could not be found."})
        list_item.feed.add(feed_item)
        return Response({"code": 1, "msg": "Successfully added."})


class DeleteFromList(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, list_id, feed_id):
        try:
            feed_item = Feed.objects.get(id=feed_id)
        except Feed.DoesNotExist:
            return Response({"code": 0, "msg": "Feed item could not be found."})
        try:
            list_item = List.objects.get(id=list_id)
            try:
                list_item.feed.get(id=feed_id)
            except Feed.DoesNotExist:
                return Response({"code": 0, "msg": "The list does not include the feed."})
        except List.DoesNotExist:
            return Response({"code": 0, "msg": "The list could not be found."})
        list_item.feed.remove(feed_item)
        return Response({"code": 1, "msg": "Successfully removed."})


class DeleteList(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, list_id):
        try:
            list_item = List.objects.get(id=list_id)
        except List.DoesNotExist:
            return Response({"code": 0, "msg": "The list could not be found."})
        list_item.delete()
        return Response({"code": 1, "msg": "Successfully deleted."})


class CreateList(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            List.objects.get(user=request.user, title=request.POST.get("title"))
            return Response({"code": 0, "msg": "You have a list with that name."})
        except List.DoesNotExist:
            item = List(title=request.POST.get("title"), user=request.user)
            item.save()
            return Response({"code": 1, "msg": "Successfully created.", "id": item.id, "slug": item.slug})
