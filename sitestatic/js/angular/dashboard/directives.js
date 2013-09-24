'use strict';

/* Directives */

angular.module('Dashboard.directives', []).
    directive('catchNewEntry', function() {
        return function (scope, element, attrs) {
            scope.newEntryCount = 0;
            scope.originalTitle = document.title;
            $(element).bind("new_entry_event", function(event, data) {
                if (data.new_entry.isRepost == true &&
                        scope.username == data.new_entry.owner_username) {
                    return;
                }
                if ($(".list-header").length !== 0) {
                    if (jQuery.inArray(data.new_entry.feed_id, scope.listFeedIds) == -1) {
                        return;
                    }
                }
                scope.$apply(function() {
                    // Dont show this entry until user clicks notifier
                    data.new_entry.instantEntry = true;
                    // Add some fields that not included by default
                    data.new_entry.like_msg = "Like",
                    data.new_entry.like_count = 0,
                    data.new_entry.comments = {"results": [], "count": 0}
                    if (typeof scope.feed_detail == 'undefined') {
                        // This is timeline
                        scope.entries.unshift(data.new_entry);
                        scope.hiddenEntry = true;
                        scope.newEntryCount++;
                        document.title = "("+scope.newEntryCount+") "+scope.originalTitle;
                    } else {
                        // This is feed detail
                        if (scope.feed_detail.feed.id == data.new_entry.feed_id) {
                            scope.feed_detail.entries.unshift(data.new_entry);
                            scope.hiddenEntry = true;
                            scope.newEntryCount++;
                            document.title = "("+scope.newEntryCount+") "+scope.originalTitle;
                        }
                    }
                });
            });
        }
    }).directive('showHiddenEntry', function() {
        return function (scope, element, attrs) {
            $(element).click(function() {
                scope.$apply(function() {
                    scope.hiddenEntry = false;
                    scope.newEntryCount = 0;
                    document.title = scope.originalTitle;

                    if (typeof scope.feed_detail == 'undefined') {
                        var dataset = scope.entries;
                    } else {
                        var dataset = scope.feed_detail.entries;
                    }

                    for (var i=0; i<dataset.length; i++ ) {
                        if (dataset[i].instantEntry == true) {
                            dataset[i].instantEntry = false;
                        } else {
                            break;
                        }
                    }
                    $(".dashboard-entry").slideDown('fast');
                });
            });
        }
    }).directive('signOut', function() {
        return function (scope, element, attrs) {
            $(element).click(function() {
                document.location.href = "/user/signout/";
            });
        }
    }).directive('preventDefault', function() {
        return function(scope, element, attrs) {
            $(element).click(function(event) {
                event.preventDefault();
                event.stopPropagation();
            });
        };
    }).directive('clickjackingWarn', function () {
        return function (scope, element, attrs) {
            $(element).click(function(event) {
                var myElement = $(this).closest(".dashboard-entry").find(".clickjacking-warn");
                myElement.css("display", "block").delay(3000).fadeOut();
            });
        };
    }).directive('entryLike', function($http) {
        return function (scope, element, attrs) {
            $(element).click(function(event) {
                $http.post("/api/like_entry/"+scope.entry.id+"/").success(function(data) {
                    if (data.code == 1) {
                        scope.entry.like_count += 1;
                        $(element).text(data.msg)
                    } else if (data.code == -1) {
                        scope.entry.like_count -= 1;
                        $(element).text(data.msg);
                    } // error cases
                });
            });
        }
    }).directive('commentBox', function($http) {
        return function (scope, element, attrs) {
            $(element).click(function(event) {
                var target = $(element).closest(".dashboard-entry").find(".comment-form textarea.comment");
                target.autosize();
                $(element).closest(".dashboard-entry").find(".comment-form").slideToggle("fast");
            });
        }
    }).directive('postComment', function($http) {
        return function (scope, element, attrs) {
            function post_comment() {
                if (!scope.commentContent.trim().length) return;
                scope.postingComment = true;
                $http({
                    url: '/api/post_comment/',
                    method: "POST",
                    data:  $.param({content: scope.commentContent, entry_id: scope.entry.id}),
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'}
                }).success(function (data, status, headers, config) {
                    scope.postingComment = false;
                    scope.showCommentBox = false;
                    data.content = nl2br(scope.commentContent);
                    if (scope.entry.comments.last_comment_id != data.id) {
                        scope.entry.comments.results.push(data);
                        scope.entry.comments.last_comment_id = data.id;
                    }
                    scope.commentContent = undefined;
                }).error(function (data, status, headers, config) {
                    // Error case
                });
            }

            $(element).closest(".comments-area").find("textarea").keypress(function(event) {
                if (event.shiftKey) {
                    scope.commentContent += "\n";
                } else {
                    if (event.keyCode != 13) return;
                    event.preventDefault();
                    post_comment();
                }
            });

            $(element).click(function(event) {
                post_comment();
            });
        }
    }).directive('editComment', function() {
        return function(scope, element, attrs) {
            $(element).click(function() {
                var comment = scope.entry.comments.results[attrs.cIndex];
                var comment_content = $(element).closest(".comment .content");
                var comment_edit = $(element).closest(".comment").find(".edit-comment-form");
                scope.commentContent = scope.entry.comments.results[attrs.cIndex].content;
                comment_edit.find("textarea").autosize();
                scope.commentEdit = true;
                scope.showCommentEditBox = true;
            });
        }
    }).directive('doneEditComment', function($http) {
        return function(scope, element, attrs) {
            function post_comment() {
                if (!scope.commentContent.trim().length) return;
                scope.postingComment = true;
                $http({
                    url: '/api/update_comment/',
                    method: "POST",
                    data:  $.param({content: scope.commentContent, id: attrs.cId}),
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'}
                }).success(function (data, status, headers, config) {
                    scope.postingComment = false;
                    scope.showCommentEditBox = false;
                    scope.commentEdit = false;
                    scope.entry.comments.results[attrs.cIndex].content = nl2br(scope.commentContent);
                    scope.commentContent = undefined;
                }).error(function (data, status, headers, config) {
                    // Error case
                });
            }

            $(element).closest(".edit-comment-form").find("textarea").keypress(function(event) {
                if (event.shiftKey) {
                    scope.commentContent += "\n";
                } else {
                    if (event.keyCode != 13) return;
                    event.preventDefault();
                    post_comment();
                }
            });

            $(element).click(function(event) {
                post_comment();
            });
        }
    }).directive('catchNewInteraction', function($http) {
        return function(scope, element, attrs) {
            scope.interaction_count = 0;
            scope.newEntryCount = 0;
            scope.originalTitle = document.title;
            $(element).bind("new_interaction_event", function(event, data) {
                var single_entry = false;
                scope.hiddenEntry = false;
                for (var i=0; i<scope.interactions.entries.length; i++) {
                    if (scope.interactions.entries[i].id == data.interaction_id) {
                        single_entry = true;
                        if (i == 0) break;
                        scope.safeApply(function() {
                            scope.interactions.entries.unshift(scope.interactions.entries[i]);
                            scope.interactions.entries.splice(i+1, 1);
                            $("#entry-"+data.interaction_id).hide().fadeIn();
                        });
                        break;
                    }
                }
                if (!single_entry) {
                    $http.get("/api/single_entry/"+data.interaction_id+"/").success(function(data) {
                        scope.hiddenEntry = true;
                        scope.safeApply(function() {
                            scope.newEntryCount++;
                            data.instantEntry = true;
                            scope.interactions.entries.unshift(data);
                        });
                    });
                }

            });
        }
    }).directive('catchNewComment', function() {
        return function(scope, element, attrs) {
            $(element).bind("new_comment_event", function(event, data) {
                scope.$apply(function () {
                    if (scope.entry.comments.last_comment_id != data.new_comment.id) {
                        data.new_comment.content = nl2br(data.new_comment.content);
                        data.new_comment.instantComment = true;
                        scope.entry.comments.results.push(data.new_comment);
                        scope.entry.comments.last_comment_id = data.new_comment.id;
                    }
                });
                $(".comment").slideDown();
            });
        }
    }).directive('deleteComment',function($http) {
        return function (scope, element, attrs) {
            $(element).click(function(event) {
                scope.commentDelSure = true;
            });
        }
    }).directive('cancelDeleteComment',function($http) {
        return function (scope, element, attrs) {
            $(element).click(function(event) {
                scope.commentDelSure = false;
            });
        }
    }).directive('sureDeleteComment', function($http) {
        return function (scope, element, attrs) {
            $(element).click(function(event) {
                scope.commentLoading = true;
                $http.post("/api/delete_comment/"+attrs.cId+"/").success(function(data) {
                    scope.commentLoading = false;
                    scope.entry.comments.results.splice(attrs.cIndex, 1);
                });
            });
        }
    }).directive('cancelComment', function() {
        return function(scope, element, attrs) {
            $(element).click(function(event) {
                // Edit related variables
                scope.showCommentEditBox = false;
                scope.commentEdit = false;
                // New comment related variables
                scope.postingComment = false;
                scope.commentContent = "";
                $(element).closest(".dashboard-entry").find(".comment-form").slideUp('fast');
            });
        }
    }).directive('loadComments', function($http) {
        return function(scope, element, attrs) {
            $(element).click(function(event) {
                $http.get("/api/fetch_comments/"+scope.entry.id+"/").success(function(data) {
                    for(var i=0; i < data.results.length; i++) {
                        data.results[i].content = nl2br(data.results[i].content);
                    }
                    scope.entry.comments = data;
                });
            })
        }
    }).directive('countChar', function($http) {
        return function(scope, element, attrs) {
            scope.maxCharCount = 2000;
            $(element).bind("keypress keyup keydown paste", function(event) {
                if (typeof scope.commentContent == 'undefined') return;
                if (scope.restCharCount <= 0) {
                    event.preventDefault();
                } else {
                    scope.restCharCount = scope.maxCharCount - scope.commentContent.length;
                }
            });
        };
    }).directive('calcFromNow', function($timeout) {
        return function(scope, element, attrs) {
            attrs.$observe('ts', function(ts) {
                function calcTime(timestamp) {
                    scope.safeApply(function() {
                        scope.created_at = moment(parseInt(ts, 10)).format('MMMM Do YYYY, h:mm:ss a');
                        scope.calcTime = moment(parseInt(ts, 10)).fromNow();
                    });
                }
                calcTime(ts);
                $timeout(function calcTimeInterval(){
                    calcTime(ts);
                    $timeout(calcTimeInterval, 60000);
                },60000);

            });
        };
    }).directive('readLater', function($rootScope, $http) {
        return function(scope, element, attrs) {
            $(element).click(function(event) {
                $http.post("/api/readlater/"+scope.entry.id+"/").success(function(data) {
                    if (data.code == 1) {
                        $rootScope.readlater_count++;
                        scope.entry.inReadLater = true;
                    } else if (data.code == -1) {
                        $rootScope.readlater_count--;
                        scope.entry.inReadLater = false;
                        if($(".readlater-header").length) {
                            $(element).closest(".dashboard-entry").fadeOut(function() {
                                scope.entries.splice(jQuery.inArray(scope.entry, scope.entries), 1);
                                // This trick does not work. Why?
                                /*if ($rootScope.readlater_count == 0) {
                                    scope.safeApply(function() {
                                        scope.noData = true;
                                    });
                                }*/
                            });
                        }
                    }
                });
            });
        }
    }).directive('shareBox',  function() {
        return function(scope, element, attrs) {
            $(element).click(function(event) {
                var box = $(element).closest(".dashboard-entry").find(".share-box");
                var entry_type = null;
                if (scope.entry.isRepost == true) {
                    entry_type = "repost";
                } else {
                    entry_type = "entry"
                }
                box.find("input").val(document.location.origin+"/"+entry_type+"/"+scope.entry.id);
                box.slideToggle('fast');
            });
        }
    }).directive('listControlModal', function() {
        return {
            templateUrl: '/static/templates/list-modal.html'
        }
    }).directive('runListControlModal', function($http, $rootScope) {
        return function(scope, element, attrs) {
            $(element).click(function(event) {
                $http.get("/api/lists/").success(function(data) {
                    scope.safeApply(function() {
                        $rootScope.lists = data;
                        if (typeof scope.feed_detail != 'undefined') {
                            $rootScope.feedItem = scope.feed_detail.feed.title;
                            $rootScope.feedId = scope.feed_detail.feed.id;
                        }
                    });
                })
            });
        }
    }).directive('listToggle', function($http) {
        return function(scope, element, attrs) {
            $(element).click(function(event) {
                $(element).closest(".list").find(".items").slideToggle();
            });
        }
    }).directive('appendToList', function($http, $rootScope) {
        return function(scope, element, attrs) {
            $(element).click(function(event) {
                scope.listBusy = true;
                $http.post("/api/append_to_list/"+attrs.listId+"/"+attrs.feedId+"/").success(function(data) {
                    scope.listBusy = false;
                    $(element).closest(".list").find(".items").slideDown();
                    if (data.code == 1) {
                        scope.safeApply(function() {
                            $rootScope.lists[attrs.listId].items.push({id: attrs.feedId, title: scope.feedItem});
                        });
                    }
                })
            });
        }
    }).directive('deleteFromList', function($http, $rootScope) {
        return function(scope, element, attrs) {
            $(element).click(function(event) {
                scope.listBusy = true;
                $http.post("/api/delete_from_list/"+attrs.listId+"/"+attrs.feedId+"/").success(function(data) {
                    scope.listBusy = false;
                    if (data.code == 1) {
                         scope.safeApply(function() {
                            $rootScope.lists[attrs.listId].items.splice(attrs.itemIndex, 1);
                        });
                     }
                 });
            });
        }
    }).directive('sureDeleteList', function($http, $rootScope) {
        return function(scope, element, attrs) {
            $(element).click(function(event) {
                scope.listBusy = true;
                $http.post("/api/delete_list/"+attrs.listId+"/").success(function(data) {
                scope.listBusy = false;
                    if (data.code == 1) {
                         scope.safeApply(function() {
                            delete $rootScope.lists[attrs.listId];
                        });
                     }
                 });
            });
        }
    }).directive('createList', function($http, $rootScope) {
        return function(scope, element, attrs) {
            function create_list() {
                scope.listBusy = true;
                $http({
                    url: '/api/create_list/',
                    method: "POST",
                    data:  $.param({title: scope.newListName}),
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'}
                }).success(function (data, status, headers, config) {
                    scope.listBusy = false;
                    if (data.code == 1) {
                        scope.safeApply(function() {
                            $rootScope.lists[data.id] = {id: data.id, title: scope.newListName, items:[], slug: data.slug};
                            scope.showCreateList = '';
                            scope.newListName = undefined;
                        });
                    }
                });
            }

            $(element).closest(".create-list").find("input[name=list-name]").keypress(function(event) {
                if (event.keyCode != 13) return;
                create_list();
            });

            $(element).click(function(event) {
                create_list();
            });
        }
    }).directive('showLists', function($http) {
        return function(scope, element, attrs) {
            $(element).click(function(event) {
                if (!$(event.target).hasClass("list-manage")) {
                    $("#lists").slideToggle('fast');
                }
            });
        }
    }).directive('repostEntryModal', function() {
        return {
            templateUrl: '/static/templates/repost-entry-modal.html'
        }
    }).directive('runRepostEntryModal', function($rootScope) {
        return function(scope, element, attrs) {
            $(element).click(function(event) {
                $("#repost-notebox_"+scope.entry.id).autosize();
                scope.repostComment = undefined;
            });
        }
    }).directive("repostEntry", function($http) {
        return function(scope, element, attr) {
            function repost_entry() {
                $http({
                    url: '/api/repost_entry/'+scope.entry.id+'/',
                    method: "POST",
                    data:  $.param({note: scope.repostNote}),
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'}
                }).success(function (data, status, headers, config) {
                    $('#repostModal_'+scope.entry.id).modal('hide')
                    scope.entry.reposted = true;
                    var new_item = jQuery.extend(true, {}, scope.entry);
                    // Overwrite some values of existed entry.
                    new_item.id = data.id;
                    new_item.owner_display_name = "You";
                    new_item.owner_username = scope.username;
                    new_item.num_owner = data.num_owner;
                    new_item.created_at = data.created_at;
                    new_item.isRepost = true;
                    new_item.note = scope.repostNote;
                    // Add the new repost item to top of entries array
                    scope.safeApply(function() {
                        scope.entries.unshift(new_item);
                    });
                });
            }

            $(element).keypress(function(event) {
                if (event.shiftKey) {
                    scope.repostNote += "\n";
                } else {
                    if (event.keyCode != 13) return;
                    event.preventDefault();
                    repost_entry();
                }
            });

            $(element).closest(".modal").find("button.repost-button").click(function(event) {
                repost_entry();
            });
        }
    }).directive("undoRepost", function($http) {
        return function(scope, element, attr) {
            $(element).click(function(event) {
                $http({
                    url: '/api/repost_entry/'+scope.entry.id+'/',
                    method: "DELETE",
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'}
                }).success(function (data, status, headers, config) {
                    scope.entry.reposted = false;
                    if (scope.entry.isRepost) {
                        var repost_index = jQuery.inArray(scope.entry, scope.entries);
                        scope.entries.splice(repost_index, 1);
                        // Find original entry item if it is ready in current scope
                        // and change its reposted status
                        for (var i=0; i<scope.entries.length; i++) {
                            if (scope.entries[i].id == scope.entry.id) {
                                scope.entries[i].reposted = false;
                            }
                        }
                    }
                });
            });
        }
    }).directive("unfollow", function($http) {
        return function(scope, element, attr) {
            $(element).click(function(event) {
                if (typeof attr.username == "undefined") {
                    var username = scope.userProfile.current_username;
                } else {
                    var username = attr.username;
                }
                $http({
                    url: "/api/user_fellowship/"+username+"/",
                    method: "DELETE",
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'}
                }).success(function (data, status, headers, config) {
                    if (data.code == 1) {
                        if (typeof attr.username == "undefined") {
                            // An authenticated user views another profile
                            scope.userProfile.is_following = false;
                            scope.userProfile.follower_count -= 1;
                        } else {
                            // An authenticated user views an follower/following list of someone else
                            if (typeof scope.followingUser == "undefined") {
                                scope.followerUser.following = false;
                            } else {
                                scope.followingUser.following = false;
                            }
                            if (scope.username == scope.userProfile.current_username) {
                                scope.userProfile.following_count -= 1;
                            }
                        }
                    }
                });
            });
        }
    }).directive("follow", function($http) {
        return function(scope, element, attr) {
            $(element).click(function(event) {
                if (typeof attr.username == "undefined") {
                    var username = scope.userProfile.current_username;
                } else {
                    var username = attr.username;
                }
                $http({
                    url: "/api/user_fellowship/"+username+"/",
                    method: "POST",
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'}
                }).success(function (data, status, headers, config) {
                    if (data.code == 1) {
                        scope.safeApply(function() {
                            if (typeof attr.username == "undefined") {
                                // An authenticated user views another profile
                                scope.userProfile.is_following = true;
                                scope.userProfile.follower_count += 1;
                            } else {
                                // An authenticated user views an follower/following list of someone else
                                if (typeof scope.followerUser == "undefined") {
                                    scope.followingUser.following = true;
                                } else {
                                    scope.followerUser.following = true;
                                }
                                if (scope.username == scope.userProfile.current_username) {
                                    scope.userProfile.following_count += 1;
                                }
                            }
                        })
                    }
                });
            });
        }
    }).directive("readThis", function($http) {
        return function(scope, element, attr) {
            $(element).click(function(event) {
                if (typeof scope.entry.content == "undefined") {
                    $http.get("/api/get_baseentry_content/"+scope.entry.id+"/").success(function(data) {
                        scope.safeApply(function() {
                            scope.entry.content = data[0];
                        });
                    });
                } else {
                    scope.safeApply(function() {
                        scope.entry.content = undefined;
                    });
                }
                /*
                if (scope.viewMode == "reader") {
                    $("#dashboard").hide();
                    $("#navbar").hide();
                    $("#reader-container").show();
                    $("body").css("overflow-y", "hidden");
                    $("iframe").attr("src", scope.entry.link);
                } else {
                    $("#reader-container").hide();
                    $("#dashboard").show();
                    $("#navbar").show();
                    $("body").css("overflow-y", "");
                    $("iframe").attr("src", "");
                }*/
            });
        }
    });