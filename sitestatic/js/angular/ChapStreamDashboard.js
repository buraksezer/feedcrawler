var ChapStream = angular.module('ChapStream', ['infinite-scroll', 'ngSanitize'],
    function($routeProvider, $locationProvider) {
        $locationProvider.html5Mode(true);
        $routeProvider
        .when('/', { templateUrl: '/static/templates/timeline.html', controller: 'TimelineCtrl' })
        .when('/feed/:feedId', { templateUrl: '/static/templates/feed-detail.html', controller: 'FeedDetailCtrl' })
        .when('/subscriptions', { templateUrl: '/static/templates/subscriptions.html', controller: 'SubscriptionsCtrl' })
    }
);

ChapStream.factory('InitService', function() {
    return {
        realtime: function() {
            console.log("I am ready to fetch realtime data.");
            announce.init();
            announce.on('new_comment', function(data){
                $("#comments_"+data.entry_id).trigger("new_comment_event", {new_comment: data});
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

function SubscriptionsCtrl($scope, $http, $routeParams) {
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

function ReaderCtrl($scope, $http) {
}

function SubscribeController($scope, $http, $timeout) {
    var defaultForm = {
        feed_url : ""
    };
    $scope.form = angular.copy(defaultForm);
    $scope.subs_feed = function() {
        if (typeof $scope.form.feed_url != "string" || $scope.form.feed_url.length < 3) {
            $scope.subscribe_warning = "Please give a valid URL.";
            return;
        }
        $scope.showLoading = true;
        $http.get("/api/subscribe?url="+$scope.form.feed_url).success(function(data) {
            $scope.showLoading = false;
            $scope.subscribe_warning = data.text;
            var delay = $timeout(function() {
                $("form.subscribe-feed-dropdown").closest("li.dropdown").removeClass("open");
                $scope.subscribe_warning = "";
                $scope.form = angular.copy(defaultForm);
            }, 1500);
        });
    };
}

function UserspaceCtrl($scope, $http, $timeout) {
    $http.get("/api/user_profile/").success(function(data) {
        $scope.profile = data;
    });
}