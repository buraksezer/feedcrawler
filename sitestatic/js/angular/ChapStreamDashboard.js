var ChapStream = angular.module('ChapStream', ['infinite-scroll', 'ngSanitize'],
    function($routeProvider, $locationProvider) {
        $locationProvider.html5Mode(true);
        $routeProvider
        .when('/', { templateUrl: '/static/templates/timeline.html', controller: 'TimelineCtrl' })
        .when('/feed/:feedId', { templateUrl: '/static/templates/feed-detail.html', controller: 'FeedDetailCtrl' })
        .when('/subscriptions', { templateUrl: '/static/templates/subscriptions.html', controller: 'SubscriptionsCtrl' })
        .when('/interactions', { templateUrl: '/static/templates/interactions.html', controller: 'InteractionsCtrl' })
        .when('/readlater', { templateUrl: '/static/templates/readlater.html', controller: 'ReadLaterCtrl' })
        .when('/entry/:entryId', { templateUrl: '/static/templates/entry.html', controller: 'EntryCtrl' })
    }
);

ChapStream.factory('InitService', function() {
    return {
        realtime: function() {
            console.log("I am ready to fetch realtime data.");
            announce.init();
            announce.on('new_comment', function(data){
                $("#comments_"+data.entry_id).trigger("new_comment_event", {new_comment: data});
                $("#new-interaction").trigger("new_interaction_event",
                    {interaction_id: data.entry_id, owner: data.author}
                );
            });

            announce.on('new_entry', function(data){
                $("#new-entry").trigger("new_entry_event", {new_entry: data});
            });

        }
    }
});

ChapStream.run(function($rootScope, InitService) {
    $rootScope.username = CsFrontend.Globals.username;
    InitService.realtime();
    $rootScope.renderToReader = function(id) {
        document.location.href = "/reader/"+id;
    };

    $rootScope.safeApply = function(fn) {
        var phase = this.$root.$$phase;
        if(phase == '$apply' || phase == '$digest') {
            if(fn && (typeof(fn) === 'function')) {
                fn();
            }
        } else {
            this.$apply(fn);
        }
    };

    $rootScope.readlater_count = 0;
});

ChapStream.config(function($httpProvider) {
    $httpProvider.defaults.headers.post['X-CSRFToken'] = $('input[name=csrfmiddlewaretoken]').val();
});

ChapStream.directive('catchNewEntry', function() {
    return function (scope, element, attrs) {
        scope.newEntryCount = 0;
        scope.originalTitle = document.title;
        $(element).bind("new_entry_event", function(event, data) {
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
});

ChapStream.directive('showHiddenEntry', function() {
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
});


ChapStream.directive('signOut', function() {
    return function (scope, element, attrs) {
        $(element).click(function() {
            document.location.href = "/user/signout";
        });
    }
});

ChapStream.directive('preventDefault', function() {
    return function(scope, element, attrs) {
        $(element).click(function(event) {
            event.preventDefault();
            event.stopPropagation();
        });
    };
});

ChapStream.directive('clickjackingWarn', function () {
    return function (scope, element, attrs) {
        $(element).click(function(event) {
            var myElement = $(this).closest(".dashboard-entry").find(".clickjacking-warn");
            myElement.css("display", "block").delay(3000).fadeOut();
        });
    };
});

ChapStream.directive('entryLike', function($http) {
    return function (scope, element, attrs) {
        $(element).click(function(event) {
            $http.post("/api/like/"+scope.entry.id+"/").success(function(data) {
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
});

ChapStream.directive('commentBox', function($http) {
    return function (scope, element, attrs) {
        $(element).click(function(event) {
            var target = $(element).closest(".dashboard-entry").find(".comments-area textarea.comment")
            target.autosize();
            scope.$apply(function() {
                scope.showCommentBox = true;
            })
            target.focus();

        });
    }
});

ChapStream.directive('postComment', function($http) {
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
                scope.commentContent =+ "\n";
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
});

ChapStream.directive('editComment', function() {
    return function(scope, element, attrs) {
        $(element).click(function() {
            var comment = scope.entry.comments.results[attrs.cIndex];
            var comment_content = $(element).closest(".comment .content");
            var comment_edit = $(element).closest(".comment").find(".edit-comment-form");
            comment_edit.find("textarea").autosize();
            scope.commentContent = scope.entry.comments.results[attrs.cIndex].content;
            scope.commentEdit = true;
            scope.showCommentEditBox = true;
        });
    }
});

ChapStream.directive('doneEditComment', function($http) {
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
                scope.commentContent =+ "\n";
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
});

/*
ChapStream.directive('countNewInteractions', function() {
    return function(scope, element, attrs) {
        if (!$("#new-interaction").length) {
            scope.interaction_count = 0;
        }
        $(element).bind("reset_interaction_count", function(event) {
            scope.safeApply(function() {
                scope.interaction_count = 0;
            });
        });

        $(element).bind("new_interaction_event", function(event, data) {
            if (!$("#new-interaction").length && scope.username != data.owner) {
                scope.safeApply(function() {
                    scope.interaction_count++;
                });
            }
        });
    }
}); */


ChapStream.directive('catchNewInteraction', function($http) {
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
});


ChapStream.directive('catchNewComment', function() {
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
});

ChapStream.directive('deleteComment',function($http) {
    return function (scope, element, attrs) {
        $(element).click(function(event) {
            scope.commentDelSure = true;
        });
    }
});

ChapStream.directive('cancelDeleteComment',function($http) {
    return function (scope, element, attrs) {
        $(element).click(function(event) {
            scope.commentDelSure = false;
        });
    }
});

ChapStream.directive('sureDeleteComment', function($http) {
    return function (scope, element, attrs) {
        $(element).click(function(event) {
            scope.commentLoading = true;
            $http.post("/api/delete_comment/"+attrs.cId+"/").success(function(data) {
                scope.commentLoading = false;
                scope.entry.comments.results.splice(attrs.cIndex, 1);
            });
        });
    }
})

ChapStream.directive('cancelComment', function() {
    return function(scope, element, attrs) {
        $(element).click(function(event) {
            // Edit related variables
            scope.showCommentEditBox = false;
            scope.commentEdit = false;
            // New comment related variables
            scope.showCommentBox = false;
            scope.postingComment = false;

            scope.commentContent = "";
        });
    }
});

ChapStream.directive('loadComments', function($http) {
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
});

ChapStream.directive('countChar', function($http) {
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
    }
});

ChapStream.directive('calcFromNow', function() {
    return function(scope, element, attrs) {
        attrs.$observe('ts', function(ts) {
            scope.created_at = moment(parseInt(ts, 10)).format('MMMM Do YYYY, h:mm:ss a');
            scope.calcTime = moment(parseInt(ts, 10)).fromNow();
        });
    }
});

ChapStream.directive('readLater', function($rootScope, $http) {
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
});

ChapStream.directive('shareBox',  function() {
    return function(scope, element, attrs) {
        $(element).click(function(event) {
            var box = $(element).closest(".dashboard-entry").find(".share-box");
            box.find("input").val(document.location.origin+"/entry/"+scope.entry.id);
            box.slideToggle('fast');
        });
    }
});

function InteractionsCtrl($scope, $http, $rootScope) {
    document.title = "Interactions"+" | "+CsFrontend.Globals.SiteTitle;
    // Reset interaction count in user space
    $("#new-interaction-count").trigger("reset_interaction_count");

    $scope.busy = false;
    var increment = 15;
    $scope.entries = [];
    $scope.offset = 0;
    $scope.limit = increment;
    $scope.interactions = {entries: []};
    $scope.loadInteractions = function() {
        if (typeof $scope.endOfData != 'undefined') return;
        if ($scope.busy) return;
        $scope.busy = true;
        $http.get("/api/interactions/"+"?&offset="+$scope.offset+"&limit="+$scope.limit).success(function(data) {
            if (!data.length) {
                $scope.endOfData = true;
                $scope.busy = false;
            } else {
                for(var i = 0; i < data.length; i++) {
                    for(var j=0; j < data[i].comments.results.length; j++) {
                        // A bit confusing?
                        data[i].comments.results[j].content = nl2br(data[i].comments.results[j].content);
                    }
                    $scope.interactions.entries.push(data[i]);
                }
                $scope.offset += increment;
                $scope.limit += increment;
                $scope.busy = false;
            }
        });
    };

    $scope.showClickjackingWarn = function() {
        $scope.clickjacking = true;
    };
}

function SubscriptionsCtrl($scope, $http) {
    document.title = "Your subscriptions"+" | "+CsFrontend.Globals.SiteTitle;
    var increment = 10;
    $scope.busy = false;
    $scope.subscriptions= [];
    $scope.offset = 0;
    $scope.limit = increment;

    $scope.loadSubscriptions = function () {
        if (typeof $scope.endOfData != 'undefined') return;
        if ($scope.busy) return;
        $scope.busy = true;
        $http.get("/api/subscriptions/"+"?&offset="+$scope.offset+"&limit="+$scope.limit).success(function(data) {
            if (!data.length) {
                $scope.endOfData = true;
                $scope.busy = false;
            } else {
                for(var i = 0; i < data.length; i++) {
                    $scope.subscriptions.push(data[i]);
                }
                $scope.offset += increment;
                $scope.limit += increment;
                $scope.busy = false;
            }
        });
    };
}

function FeedDetailCtrl($scope, $http, $routeParams) {
    $scope.busy = false;
    var increment = 15;
    $scope.feed_detail = {feed: {}, entries: []};
    $scope.offset = 0;
    $scope.limit = increment;
    $scope.loading = true;

    $scope.loadFeedDetail = function() {
        if (typeof $scope.endOfData != 'undefined') return;
        if ($scope.busy) return;
        $scope.busy = true;
        $http.get("/api/feed_detail/"+$routeParams.feedId+"/?&offset="+$scope.offset+"&limit="+$scope.limit).success(function(data) {
            if (jQuery.isEmptyObject(data)) {
                $scope.endOfData = true;
                $scope.feed404 = true;
                $scope.busy = false;
                return;
            }
            if (!data.entries.length) {
                $scope.endOfData = true;
                $scope.busy = false;
            } else {
                if (!$scope.feed_detail.feed.length) {
                    $scope.feed_detail.feed = data.feed;
                }

                data.feed.last_sync = moment(parseInt(data.feed.last_sync, 10)).fromNow();

                for(var i = 0; i < data.entries.length; i++) {
                    for(var j=0; j < data.entries[i].comments.results.length; j++) {
                        // A bit confusing?
                        data.entries[i].comments.results[j].content = nl2br(data.entries[i].comments.results[j].content);
                    }
                    $scope.feed_detail.entries.push(data.entries[i]);
                }

                $scope.loading = false;
                $scope.offset += increment;
                $scope.limit += increment;
                $scope.busy = false;
                document.title = data.feed.title+" | "+CsFrontend.Globals.SiteTitle;
            }
        });
    };

    $scope.unsubscribeFeed = function(id) {
        $http.post("/api/unsubscribe/"+id+"/").success(function(data) {
            if (data.code == 1){
                $scope.feed_detail.feed.is_subscribed = false;
                $scope.feed_detail.feed.subs_count -= 1;
            }
        });
    };

    $scope.subscribeFeed = function(id) {
        $http.post("/api/subscribe_by_id/"+id+"/").success(function(data) {
            if (data.code == 1) {
                $scope.feed_detail.feed.is_subscribed = true;
                $scope.feed_detail.feed.subs_count += 1;
            }
        });
    };
}

function TimelineCtrl($scope, $http) {
    document.title = CsFrontend.Globals.SiteTitle;

    $scope.busy = false;
    var increment = 15;
    $scope.entries = [];
    $scope.offset = 0;
    $scope.limit = increment;
    $scope.loadTimelineEntries = function() {
        if (typeof $scope.endOfData != 'undefined') return;
        if ($scope.busy) return;
        $scope.busy = true;
        $http.get("/api/timeline/"+"?&offset="+$scope.offset+"&limit="+$scope.limit).success(function(data) {
            if (!data.length) {
                $scope.endOfData = true;
                $scope.busy = false;
            } else {
                for(var i = 0; i < data.length; i++) {
                    for(var j=0; j < data[i].comments.results.length; j++) {
                        // A bit confusing?
                        data[i].comments.results[j].content = nl2br(data[i].comments.results[j].content);
                    }
                    $scope.entries.push(data[i]);
                }
                $scope.offset += increment;
                $scope.limit += increment;
                $scope.busy = false;
            }
        });
    };

    $scope.showClickjackingWarn = function() {
        $scope.clickjacking = true;
    };
}

function ReadLaterCtrl($scope, $http) {
    document.title = "Read Later List | "+CsFrontend.Globals.SiteTitle;

    $scope.busy = false;
    var increment = 15;
    $scope.entries = [];
    $scope.offset = 0;
    $scope.limit = increment;
    $scope.loadReadLaterList = function() {
        if (typeof $scope.endOfData != 'undefined') return;
        if ($scope.busy || $scope.noData) return;
        $scope.busy = true;
        $http.get("/api/readlater_list/"+"?&offset="+$scope.offset+"&limit="+$scope.limit).success(function(data) {
            if (!data.length) {
                if ($scope.offset > 0) {
                    $scope.endOfData = true;
                } else {
                    $scope.noData = true;
                }
                $scope.busy = false;
            } else {
                for(var i = 0; i < data.length; i++) {
                    for(var j=0; j < data[i].comments.results.length; j++) {
                        // A bit confusing?
                        data[i].comments.results[j].content = nl2br(data[i].comments.results[j].content);
                    }
                    $scope.entries.push(data[i]);
                }
                $scope.offset += increment;
                $scope.limit += increment;
                $scope.busy = false;
            }
        });
    };
}

function SubscribeController($scope, $http, $timeout) {
    var defaultForm = {
        feed_url : ""
    };
    $scope.form = angular.copy(defaultForm);

    $scope.findSource = function() {
        $scope.warning = '';
        $scope.results = [];
        if (typeof $scope.form.feed_url != "string" || $scope.form.feed_url.length < 3) {
            $scope.warning = "Please give a valid URL.";
            return;
        }
        $scope.showWait = true;
        $http.get("/api/find_source?url="+$scope.form.feed_url).success(function(data) {
            $scope.showWait = false;
            if (!data.length) {
                $scope.warning = "No result found.";
                var delay = $timeout(function() {
                    $scope.warning = '';
                }, 2000);
                return;
            }
            $scope.results = data;
        });
    }

    $scope.subsFeed = function(url) {
        $scope.showWait = true;
        $http.get("/api/subscribe?url="+url).success(function(data) {
            $scope.warning = data.text;
            $scope.showWait = false;
            var delay = $timeout(function() {
                $scope.warning = '';
            }, 2000);
        });
    };

    $scope.cleanSubsModal = function() {
        $scope.form = angular.copy(defaultForm);
        $scope.results = undefined;
    }
}

function EntryCtrl($scope, $http, $routeParams) {
    $scope.loadingEntry = true;
    $http.get("/api/single_entry/"+$routeParams.entryId+"/").success(function(data) {
        $scope.loadingEntry = false;
        if (data.code == 0) {
            $scope.notFound = true;
        } else {
            document.title = data.title+" | "+CsFrontend.Globals.SiteTitle;
            $scope.entry = data;
            $scope.showCommentBox = true;
            $(".comments-area form.comment-form textarea").autosize();
        }
    });
}

function UserspaceCtrl($scope, $rootScope, $http) {
    $http.get("/api/user_profile/").success(function(data) {
        $rootScope.readlater_count = data.rl_count;
        $scope.profile = data;
    });
}