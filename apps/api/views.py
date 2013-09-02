import time
import datetime
from django.forms.models import model_to_dict
from django.contrib.auth.models import User
from apps.storage.models import (Feed, Entry, EntryLike,
    Comment, ReadLater, List, RepostEntry, BaseEntry)
from apps.accounts.models import UserRelation, FeedUserRelation
from apps.storage.tasks import sync_feed
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


def get_user_timeline(user_id, feed_ids=[], offset=0, limit=15):
    if not feed_ids:
        feed_ids = [feed_id[0] for feed_id in \
                    FeedUserRelation.objects.filter(show_on_stream=True, \
                        user_id=user_id).values_list("feed_id")]

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


def get_display_name(user):
    display_name = user.get_full_name()
    if not display_name:
        display_name = user.username
    return display_name


class AuthenticatedUser(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, pk=None):
        user = {
            "username": request.user.username,
            "subs_count": request.user.feeduserrelation_set.count(),
            "display_name": get_display_name(request.user),
            "mugshot_url": request.user.user_profile.get_mugshot_url(),
            "rl_count": ReadLater.objects.filter(user=request.user).count(),
            "lists": [{"title": _list.title, "slug": _list.slug, "id": _list.id} for _list in List.objects.filter(user=request.user)]
        }

        return Response(user)


class Timeline(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def create_result(self, entries, request, repost=False, follower_ids=[]):
        results = []
        user_id = request.user.id
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
                'inReadLater': True if ReadLater.objects.filter(user=request.user, entry__id=entry["id"]) else False,
                'reposted': True if RepostEntry.objects.filter(entry_id=entry["id"], owner=request.user) else False
            }
            if repost:
                if entry["owner_id"] == user_id:
                    owner_display_name = "You"
                else:
                    owner_display_name = get_display_name(User.objects.get(id=entry["owner_id"]))
                item.update({
                    "isRepost": True,
                    "note": entry["note"],
                    "owner_display_name": owner_display_name,
                    "owner_username": entry["owner__username"],
                    "num_owner": RepostEntry.objects.filter(Q(origin_id=entry["origin_id"]) & Q(owner_id__in=follower_ids)).count()-1,
                })
            results.append(item)
        return results

    def get(self, request, feed_ids=[], pk=None):
        offset = request.GET.get("offset", 0)
        limit = request.GET.get("limit", 15)
        # Get entry items
        entries = get_user_timeline(request.user.id, feed_ids=feed_ids, offset=offset, limit=limit)
        results = self.create_result(entries, request)

        # If feed_ids list is not empty, this is a list request
        # So getting repost items are unnecessary.
        if not feed_ids:
            # Get repost items
            follower_ids = [follower[0] for follower in \
                    UserRelation.objects.filter(follower_id=request.user.id).values_list("user_id")]
            follower_ids.append(request.user.id)
            oldest_entry = entries[int(limit)-int(offset)-1]["created_at"]
            raw_reposted_items = RepostEntry.objects.filter(Q(created_at__gt=oldest_entry) \
                & Q(owner_id__in=follower_ids)).order_by("-created_at").values("id", \
                "title", "feed__slug", \
                "feed__title", "link", \
                "available_in_frame", \
                "created_at", "slug", \
                "note", \
                "owner_id", \
                "origin_id", \
                "owner__username", \
                "created_at")[offset:limit]

            reposted_items = []
            for item in raw_reposted_items:
                if not item["id"] in [r_item["id"] for r_item in reposted_items]:
                    reposted_items.append(item)
            results += self.create_result(reposted_items, request, repost=True, follower_ids=follower_ids)
        results.sort(key=lambda result: result["created_at"], reverse=True)
        return Response(results)


class ListTimeline(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, list_slug):
        feed_ids = [feed[0] for feed in List.objects.filter(slug=list_slug).values_list("feed__id")]
        if len(feed_ids) == 1 and feed_ids[0] is None:
            # This is an empty list
            return Response({})
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
                'is_subscribed': True if feed_query.feeduserrelation_set.filter(user=request.user) else False,
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
            next = {
                "feed_id": feed_id,
                "link": next_item["link"],
                "slug": next_item["slug"],
                "title": next_item["title"],
            }
        except IndexError:
            pass
        try:
            previous_item = Entry.objects.filter(feed=feed_id, \
                id__lt=entry["id"]).values("link", "slug", "title")[0]
            previous = {
                "feed_id": feed_id,
                "link": previous_item["link"],
                "slug": previous_item["slug"],
                "title": previous_item["title"],
            }
        except IndexError:
            pass

        result.update({"next": next, "previous": previous, \
            "feed_id": feed_id, "comments": get_latest_comments(entry["id"]) })
        return Response({"code": 1, "result": result})


class FeedUserRelationByFeedId(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)


    def post(self, request, feed_id):
        # FIXME: We should handle error cases.
        try:
            item = FeedUserRelation.objects.get(feed_id=feed_id, user=request.user)
            return Response({"code": 1, "msg": "You have already subscribed this feed."})
        except FeedUserRelation.DoesNotExist:
            item = FeedUserRelation(feed_id=feed_id, user=request.user)
            item.save()
            announce_client.register_group(request.user.id, feed_id)
            return Response({"code": 1, "msg": "New feed source has been added successfully."})


    def delete(self, request, feed_id):
        try:
            item = FeedUserRelation.objects.get(user=request.user, feed_id=feed_id)
        except FeedUserRelation.DoesNotExist:
            return Response({"code": 0, "msg": "This feed does not exist: %s" % feed_id})

        # Unsubcribe from the feed
        item.delete()
        # Unregister feed real time notification group
        try:
            announce_client.unregister_group(request.user.id, feed_id)
        except AttributeError:
            # This is an error case. We should return an error message about that case and log this.
            # Maybe we should send an email to admins
            pass
        # FIXME: Use msg instead of text
        return Response({"code": 1, "msg": "You have been unsubscribed successfully from %s." % feed_id})


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
        # TODO: URL validation needed!
        # Firstly, get or create the feed object
        feed = Feed.objects.get_or_create(feed_url=url)[0]
        # Now, check the subscription status and subscribe the feed if not
        try:
            FeedUserRelation.objects.get(user=request.user, feed=feed)
            return Response({"code": 0, "text": "You have already subscribed this feed."})
        except FeedUserRelation.DoesNotExist:
            item = FeedUserRelation(user=request.user, feed=feed)
            item.save()
            # Trigger first sync task
            sync_feed.apply_async((feed,))
        # Register the user to feed's broadcasting group to get real time updates
        announce_client.register_group(request.user.id, feed.id)
        return Response({"code": 1, "text": 'New feed source has been added successfully.'})


class FeedSubscriptions(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        offset = request.GET.get("offset", 0)
        limit = request.GET.get("limit", 10)
        subscriptions = FeedUserRelation.objects.filter(~Q(feed__last_sync=None), \
            user=request.user).order_by("-feed__entries_last_month").values("feed__id", \
            "feed__title", "feed__tagline", "feed__subtitle", "feed__link", "feed__slug")[offset:limit]
        results = []
        for subscription in subscriptions:
            item = {
                "slug": subscription["feed__slug"],
                "title": subscription["feed__title"],
                "summary": subscription["feed__tagline"] if subscription["feed__tagline"] \
                    is not None else subscription["feed__subtitle"],
                'link': subscription["feed__link"]
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
                entry = BaseEntry.objects.get(id=entry_id)
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
        entry = BaseEntry.objects.get(id=request.POST.get("entry_id"))
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
        #}) FIXME: deep copy?
        feed_id = Feed.objects.get(baseentry__id=request.POST.get("entry_id")).id
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
        entries = BaseEntry.objects.filter(Q(interaction__comment__user=user_id) | \
            Q(interaction__entrylike__user=user_id)).values(
            "id",
            "title",
            "feed__title",
            "feed__slug",
            "link",
            "repostentry__slug",
            "repostentry__owner_id",
            "repostentry__origin_id",
            "repostentry__owner__username",
            "repostentry__note",
            "entry__slug",
            "available_in_frame",
            "created_at",
            ).order_by("-last_interaction").distinct()[offset:limit]

        tmp = []
        results = []
        # FIXME: What is orm's behaviour about queries that in a loop?
        # How many times does it hit database?
        follower_ids = None
        for entry in entries:
            if entry["id"] in tmp:
                continue
            like_msg, like_count = process_like(entry["id"], request.user.id)
            item = {
                'id': entry["id"],
                'title': entry["title"],
                'feed_slug': entry["feed__slug"],
                'feed_title': entry["feed__title"],
                'slug': entry["entry__slug"] if entry["entry__slug"] is not None else entry["repostentry__slug"],
                'link': entry["link"],
                'available': 1 if entry["available_in_frame"] is None else entry["available_in_frame"],
                'like_msg': like_msg,
                'like_count': like_count,
                'created_at': int(time.mktime(entry["created_at"].timetuple())*1000),
                'comments': get_latest_comments(entry["id"])
            }
            if entry["repostentry__slug"]:
                if follower_ids is None:
                    follower_ids = [follower[0] for follower in \
                        UserRelation.objects.filter(follower_id=user_id).values_list("user_id")]
                if entry["repostentry__owner_id"] == user_id:
                    owner_display_name = "You"
                else:
                    owner_display_name = get_display_name(User.objects.get(id=entry["repostentry__owner_id"]))
                item.update({
                    "isRepost": True,
                    "note": entry["repostentry__note"],
                    "owner_display_name": owner_display_name,
                    "owner_username": entry["repostentry__owner__username"],
                    "num_owner": RepostEntry.objects.filter(Q(origin_id=entry["repostentry__origin_id"]) & Q(owner_id__in=follower_ids)).count()-1,
                })

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


class UserProfile(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, username):
        user = User.objects.get(username=username)
        follower_ids = [follower[0] for follower in \
            UserRelation.objects.filter(user_id=user.id).values_list("follower_id")]

        user = {
            "subs_count": user.feeduserrelation_set.count(),
            "display_name": user.get_full_name() \
                if user.get_full_name() else request.user.username,
            "mugshot_url": user.get_profile().get_mugshot_url(),
            "is_following": True if request.user.id in follower_ids else False,
            "following_count": UserRelation.objects.filter(follower__username=username).count(),
            "follower_count": len(follower_ids),
            "repost_count": RepostEntry.objects.filter(owner_id=user.id).count()
        }

        return Response(user)


class RepostList(APIView):
    """Lists RepostEntry items for current authenticated user"""
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, username):
        offset = request.GET.get("offset", 0)
        limit = request.GET.get("limit", 15)

        user = User.objects.get(username=username)
        follower_ids = [follower[0] for follower in \
            UserRelation.objects.filter(user_id=user.id).values_list("follower_id")]
        reposts = RepostEntry.objects.filter(owner=user).order_by("-created_at").values("id", \
                "title", "feed__slug", \
                "feed__title", "link", \
                "available_in_frame", \
                "created_at", "slug", \
                "note", \
                "origin_id", \
                "created_at")[offset:limit]

        repost_items = []
        # Process raw repost items for clients
        for repost in reposts:
            like_msg, like_count = process_like(repost["id"], user.id)
            item = {
                'id': repost["id"],
                'title': repost["title"],
                'feed_slug': repost["feed__slug"],
                'feed_title': repost["feed__title"],
                'link': repost["link"],
                'available': 1 if repost["available_in_frame"] is None else repost["available_in_frame"],
                'like_msg': like_msg,
                'like_count': like_count,
                'slug': repost["slug"],
                'created_at': int(time.mktime(repost["created_at"].timetuple())*1000),
                'comments': get_latest_comments(repost["id"]),
                'inReadLater': True if ReadLater.objects.filter(user=request.user, entry__id=repost["id"]) else False,
                "note": repost["note"],
                "owner_display_name": get_display_name(User.objects.get(id=user.id)),
                "owner_username": request.user.username,
                "num_owner": RepostEntry.objects.filter(Q(origin_id=repost["origin_id"]) \
                    & Q(owner_id__in=follower_ids)).count(),
            }
            repost_items.append(item)
        return Response(repost_items)


class RepostEntryItem(APIView):
    """Creates and saves repostentry instances from entry instances"""
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, entry_id):
        if RepostEntry.objects.filter(origin_id=entry_id, owner=request.user):
            return Response({'code': 1, 'msg': 'Already reposted'})

        # Create a new RepostEntry item now
        # Actually, this is a copy of a original entry item
        # We do this because every RepostEntry item is evaluated as an Entry item
        note = request.POST.get("note", None)
        entry = model_to_dict(BaseEntry.objects.get(id=entry_id))
        entry["feed_id"] = entry["feed"]
        entry["origin_id"] = entry["id"]
        for key in ('id', 'feed'):
            del entry[key]
        entry["owner"] = request.user
        entry["note"] = note
        repost = RepostEntry(**entry)
        repost.save()

        # Generate some values for real-time notification
        follower_ids = [follower[0] for follower in \
                        UserRelation.objects.filter(user=request.user).values_list("follower_id")]
        num_owner = RepostEntry.objects.filter(Q(origin_id=entry_id) \
            & Q(owner_id__in=follower_ids)).count()
        feed = Feed.objects.filter(id=entry["feed_id"]).values("title", "slug")[0]
        data = {
            'id': repost.id,
            'slug': repost.slug,
            'title': entry["title"],
            'feed_id': entry["feed_id"],
            'feed_title': feed["title"],
            'feed_slug': feed["slug"],
            'link': entry["link"],
            'available': 1 if entry["available_in_frame"] is None else entry["available_in_frame"],
            'created_at': int(time.mktime(repost.created_at.timetuple())*1000),
            'isRepost': True,
            'note': note,
            'owner_display_name': get_display_name(request.user),
            'owner_username': request.user.username,
            'num_owner': num_owner
        }
        # Broadcast reposted item to user's followers
        announce_client.broadcast_group(request.user.username+"_profile", \
                                        'new_repost', data=data)

        return Response({'code': 1, 'msg': 'Succesfully reposted.', \
                        'id': repost.id, \
                        'created_at': int(time.mktime(repost.created_at.timetuple())*1000), \
                        'num_owner': num_owner})

    def delete(self, request, entry_id):
        try:
            repost = RepostEntry.objects.get(origin_id=entry_id, owner=request.user)
            repost.delete()
            return Response({'code': -1, 'msg': 'Succesfully removed.'})
        except RepostEntry.DoesNotExist:
            return Response({'code': 0, 'msg': 'Repost could not be found for %s' % entry_id})


class SingleRepost(APIView):
    """Retrieves a repost entry item with id"""
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, repost_id):
        try:
            repost = RepostEntry.objects.filter(id=repost_id).values("id",
                "title", "feed__slug", "feed__title", "link", \
                "available_in_frame", "created_at", "slug", \
                "note", "created_at", "owner_id", "origin_id")[0]
        except (RepostEntry.DoesNotExist, IndexError):
            return Response({'code': 0, 'msg': 'Repost item could not be found.'})

        like_msg, like_count = process_like(repost["id"], request.user.id)
        user_id = request.user.id
        owner_ids = [follower[0] for follower in \
                        UserRelation.objects.filter(follower_id=user_id).values_list("user_id")]
        if repost["owner_id"] == user_id:
            owner_display_name = "You"
        else:
            owner_display_name = get_display_name(User.objects.get(id=repost["owner_id"]))
        item = {
            'id': repost["id"],
            'slug': repost["slug"],
            'title': repost["title"],
            'feed_slug': repost["feed__slug"],
            'feed_title': repost["feed__title"],
            'link': repost["link"],
            'available': 1 if repost["available_in_frame"] is \
                                None else repost["available_in_frame"],
            'like_msg': like_msg,
            'like_count': like_count,
            'created_at': int(time.mktime(repost["created_at"].timetuple())*1000),
            'comments': get_latest_comments(repost["id"], whole=True),
            'inReadLater': True if ReadLater.objects.filter(user=request.user, \
                                    entry__id=repost["id"]) else False,
            "note": repost["note"],
            "owner_display_name": owner_display_name,
            "num_owner":  RepostEntry.objects.filter(Q(origin_id=repost["origin_id"]) \
                & Q(owner_id__in=owner_ids)).count(),
        }
        return Response(item)


class UserFellowship(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, username):
        if username == request.user.username:
            return Response({"code": 0, "msg": "You cannot follow yourself."})
        try:
            UserRelation.objects.get(user__username=username, follower=request.user)
            return Response({"code": 0, "msg": "%s already follows %s" % \
                            (request.user.username, username)})
        except UserRelation.DoesNotExist:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response({"code": 0, "msg": "Username '%s' could not be found." % username})
            relation = UserRelation(user=user, follower=request.user)
            relation.save()
            # Register user's announce channel to get instant notifications
            announce_client.register_group(request.user.id, username+"_profile")
            return Response({"code": 1})

    def delete(self, request, username):
        try:
            relation = UserRelation.objects.get(user__username=username, follower=request.user)
        except UserRelation.DoesNotExist:
            return Response({"code": 0, "msg": "%s does not follow %s" % \
                            (request.user.username, username)})

        relation.delete()
        announce_client.unregister_group(request.user.id, username+"_profile")
        return Response({"code": 1})


class FollowerList(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, username):
        offset = request.GET.get("offset", 0)
        limit = request.GET.get("limit", 15)

        followers = []
        follower_items = UserRelation.objects.select_related().filter(user__username=username)[offset:limit]
        for follower_item in follower_items:
            follower_username = follower_item.follower.get_profile().user.username
            following = True if UserRelation.objects.filter(user__username=follower_username, \
                follower__username=username) else False

            follower = {
                "username": follower_username,
                "display_name": follower_item.follower.get_profile().get_full_name_or_username(),
                "mugshot_url": follower_item.follower.get_profile().get_mugshot_url(),
                "following": following
            }
            followers.append(follower)
        return Response(followers)


class FollowingList(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, username):
        offset = request.GET.get("offset", 0)
        limit = request.GET.get("limit", 15)

        following_users = []
        following_items = UserRelation.objects.select_related().filter(follower__username=username)[offset:limit]
        for following_item in following_items:
            following_username = following_item.user.get_profile().user.username
            following = True if UserRelation.objects.filter(user__username=following_username, \
                follower__username=username) else False

            following_user = {
                "username": following_username,
                "display_name": following_item.user.get_profile().get_full_name_or_username(),
                "mugshot_url": following_item.user.get_profile().get_mugshot_url(),
                "following": following
            }
            following_users.append(following_user)
        return Response(following_users)


class ShowOnStream(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, feed_id):
        try:
            item = FeedUserRelation.objects.get(user=request.user, feed_id=feed_id)
            item.show_on_stream = True
            item.save()
            return Response({"code": 1, "msg": "The feed will be shown on Stream"})
        except FeedUserRelation.DoesNotExist:
            return Response({"code": 0, "msg": "You don't subscribe this feed"})

    def delete(self, request, feed_id):
        try:
            item = FeedUserRelation.objects.get(user=request.user, feed_id=feed_id)
            item.show_on_stream = False
            item.save()
            return Response({"code": 1, "msg": "The feed is removed from Stream"})
        except FeedUserRelation.DoesNotExist:
            return Response({"code": 0, "msg": "You don't subscribe this feed"})
