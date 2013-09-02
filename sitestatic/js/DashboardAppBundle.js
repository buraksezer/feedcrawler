;(function(e,t,n){function i(n,s){if(!t[n]){if(!e[n]){var o=typeof require=="function"&&require;if(!s&&o)return o(n,!0);if(r)return r(n,!0);throw new Error("Cannot find module '"+n+"'")}var u=t[n]={exports:{}};e[n][0].call(u.exports,function(t){var r=e[n][1][t];return i(r?r:t)},u,u.exports)}return t[n].exports}var r=typeof require=="function"&&require;for(var s=0;s<n.length;s++)i(n[s]);return i})({1:[function(require,module,exports){
'use strict';

require("./services");
require("./controllers");
require("./directives");

var app = angular.module('Dashboard', ['Dashboard.services', 'Dashboard.controllers', 'Dashboard.directives', 'infinite-scroll', 'ngSanitize'])
    .config(["$routeProvider",
        function($routeProvider) {
            $routeProvider
            .when('/', { templateUrl: '/static/templates/timeline.html', controller: 'TimelineCtrl' })
            .when('/feed/:feedId', { templateUrl: '/static/templates/feed-detail.html', controller: 'FeedDetailCtrl' })
            .when('/subscriptions', { templateUrl: '/static/templates/subscriptions.html', controller: 'SubscriptionsCtrl' })
            .when('/interactions', { templateUrl: '/static/templates/interactions.html', controller: 'InteractionsCtrl' })
            .when('/readlater', { templateUrl: '/static/templates/readlater.html', controller: 'ReadLaterCtrl' })
            .when('/entry/:entryId', { templateUrl: '/static/templates/entry.html', controller: 'EntryCtrl' })
            .when('/repost/:repostId', { templateUrl: '/static/templates/repost.html', controller: 'RepostCtrl' })
            .when('/list/:listSlug', { templateUrl: '/static/templates/list.html', controller: 'ListCtrl' })
            .when('/user/:userName', { templateUrl: '/static/templates/user-profile.html', controller: 'UserProfileCtrl' })
            .when('/user/:userName/followers', { templateUrl: '/static/templates/follower-list.html', controller: 'UserProfileCtrl' })
            .when('/user/:userName/following', { templateUrl: '/static/templates/following-list.html', controller: 'UserProfileCtrl' });
    }])
    .config(["$locationProvider", function($locationProvider) {
        $locationProvider.html5Mode(true);
    }])
    .config(["$httpProvider", function($httpProvider) {
        $httpProvider.defaults.headers.common['X-CSRFToken'] = $('input[name=csrfmiddlewaretoken]').val();
    }]);

app.run(function($rootScope, InitService) {
    $rootScope.username = CsFrontend.Globals.username;
    $rootScope.isAuthenticated = CsFrontend.Globals.isAuthenticated;
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

},{"./controllers":2,"./directives":14,"./services":15}],2:[function(require,module,exports){
// Dashboard spesific controllers here.

'use strict';

var InteractionsCtrl = require("./controllers/InteractionsCtrl.js");
var SubscriptionsCtrl = require("./controllers/SubscriptionsCtrl.js");
var FeedDetailCtrl = require("./controllers/FeedDetailCtrl.js");
var TimelineCtrl = require("./controllers/TimelineCtrl.js");
var ReadLaterCtrl = require("./controllers/ReadLaterCtrl.js");
var SubscribeCtrl = require("./controllers/SubscribeCtrl.js");
var EntryCtrl = require("./controllers/EntryCtrl.js");
var ListCtrl = require("./controllers/ListCtrl.js");
var UserSpaceCtrl = require("./controllers/UserSpaceCtrl.js");
var UserProfileCtrl = require("./controllers/UserProfileCtrl.js");
var RepostCtrl = require("./controllers/RepostCtrl.js");

angular.module("Dashboard.controllers", [])
    .controller("UserSpaceCtrl", ["$scope", "$rootScope", "$http", UserSpaceCtrl])
    .controller("InteractionsCtrl", ["$scope", "$http", "$rootScope", InteractionsCtrl])
    .controller("SubscriptionsCtrl", ["$scope", "$http", SubscriptionsCtrl])
    .controller("FeedDetailCtrl", ["$scope", "$http", "$routeParams", "$rootScope", FeedDetailCtrl])
    .controller("TimelineCtrl", ["$scope", "$routeParams", "$http", TimelineCtrl])
    .controller("ReadLaterCtrl", ["$scope", "$http", ReadLaterCtrl])
    .controller("SubscribeCtrl", ["$scope", "$http", "$timeout", "$rootScope", SubscribeCtrl])
    .controller("EntryCtrl", ["$scope", "$http", "$routeParams", EntryCtrl])
    .controller("ListCtrl", ["$scope", "$http", "$routeParams", ListCtrl])
    .controller("UserProfileCtrl", ["$scope", "$http", "$routeParams", UserProfileCtrl])
    .controller("RepostCtrl", ["$scope", "$http", "$routeParams", RepostCtrl]);
},{"./controllers/EntryCtrl.js":3,"./controllers/FeedDetailCtrl.js":4,"./controllers/InteractionsCtrl.js":5,"./controllers/ListCtrl.js":6,"./controllers/ReadLaterCtrl.js":7,"./controllers/RepostCtrl.js":8,"./controllers/SubscribeCtrl.js":9,"./controllers/SubscriptionsCtrl.js":10,"./controllers/TimelineCtrl.js":11,"./controllers/UserProfileCtrl.js":12,"./controllers/UserSpaceCtrl.js":13}],3:[function(require,module,exports){
(function () {
    'use strict';
    function EntryCtrl($scope, $http, $routeParams) {
        $scope.loadingEntry = true;
        $http.get("/api/single_entry/"+$routeParams.entryId+"/").success(function(data) {
            $scope.loadingEntry = false;
            if (data.code == 0) {
                $scope.notFound = true;
            } else {
                document.title = data.title+" | "+CsFrontend.Globals.SiteTitle;
                $scope.entry = data;
                $scope.singleEntry = true;
                $(".comments-area form.comment-form textarea").autosize();
                $(".comments-area form.comment-form").css("display", "block");
            }
        });
    }
    module.exports = EntryCtrl;
})();

},{}],4:[function(require,module,exports){
(function () {
  'use strict';

    function FeedDetailCtrl($scope, $http, $routeParams, $rootScope) {
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
            $http({
                url: "/api/unsubscribe/"+id+"/",
                method: "DELETE",
                headers: {'Content-Type': 'application/x-www-form-urlencoded'}
            }).success(function (data, status, headers, config) {
                if (data.code == 1){
                    $scope.feed_detail.feed.is_subscribed = false;
                    $scope.feed_detail.feed.subs_count -= 1;
                    $rootScope.subscriptionCount -= 1;
                }
            });
        };

        $scope.subscribeFeed = function(id) {
            $http.post("/api/subscribe_by_id/"+id+"/").success(function(data) {
                if (data.code == 1) {
                    $scope.feed_detail.feed.is_subscribed = true;
                    $scope.feed_detail.feed.subs_count += 1;
                    $rootScope.subscriptionCount += 1;
                }
            });
        };
    }

  module.exports = FeedDetailCtrl;
})();
},{}],5:[function(require,module,exports){
(function () {
  'use strict';

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

  module.exports = InteractionsCtrl;
})();
},{}],6:[function(require,module,exports){
(function () {
    'use strict';

    function ListCtrl($scope, $http, $routeParams) {
        $http.get("/api/prepare_list/"+$routeParams.listSlug+"/").success(function(data) {
            $scope.listTitle = data.title;
            $scope.listFeedIds = data.feed_ids;
            document.title = $scope.listTitle +" | "+CsFrontend.Globals.SiteTitle;
        });
    }
    module.exports = ListCtrl;
})();
},{}],7:[function(require,module,exports){
(function () {
  'use strict';

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
    module.exports = ReadLaterCtrl;
})();
},{}],8:[function(require,module,exports){
(function () {
    'use strict';
    function RepostCtrl($scope, $http, $routeParams) {
        $scope.loadingEntry = true;
        $http.get("/api/single_repost/"+$routeParams.repostId+"/").success(function(data) {
            $scope.loadingEntry = false;
            if (data.code == 0) {
                $scope.notFound = true;
            } else {
                document.title = data.title+" | "+CsFrontend.Globals.SiteTitle;
                data.note = nl2br(data.note);
                $scope.entry = data;
                $scope.singleRepost = true;
                $(document).ready(function() {
                    $(".comments-area form.comment-form textarea").autosize();
                    $(".comments-area form.comment-form").css("display", "block");
                });

            }
        });
    }
    module.exports = RepostCtrl;
})();

},{}],9:[function(require,module,exports){
(function () {
  'use strict';
    function SubscribeCtrl($scope, $http, $timeout, $rootScope) {
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
                if (data.code == 1) {
                    $rootScope.subscriptionCount += 1;
                }
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

    module.exports = SubscribeCtrl;
})();
},{}],10:[function(require,module,exports){
(function () {
  'use strict';

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

  module.exports = SubscriptionsCtrl;
})();
},{}],11:[function(require,module,exports){
(function () {
  'use strict';

    function TimelineCtrl($scope, $routeParams, $http) {
        // If this is a list, a custom timeline, use a different URL.
        var urlBody = "timeline";
        if ($(".list-header").length !== 0) {
            urlBody = "list/"+$routeParams.listSlug;
        }

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
            $http.get("/api/"+urlBody+"?&offset="+$scope.offset+"&limit="+$scope.limit).success(function(data) {
                if (!data.length) {
                    $scope.endOfData = true;
                    $scope.busy = false;
                } else {
                    for(var i = 0; i < data.length; i++) {
                        if (typeof data[i].repost != 'undefined') {
                            data[i].repost.note = nl2br(data[i].repost.note);
                            data[i].isRepost = true;
                        }
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

  module.exports = TimelineCtrl;
})();
},{}],12:[function(require,module,exports){
(function () {
    'use strict';

    function UserProfileCtrl($scope, $http, $routeParams) {
        $scope.entries = [];
        $scope.followerUsers = [];
        $scope.followingUsers = [];

        $http.get("/api/user_profile/"+$routeParams.userName+"/").success(function(data) {
            $scope.userProfile = data;
            document.title = $scope.userProfile.display_name+" on "+CsFrontend.Globals.SiteTitle;
            $scope.userProfile.current_username = $routeParams.userName;
        });

        $scope.busy = false;
        var increment = 15;

        var listOffset = 0;
        var listLimit = increment
        $scope.loadRepostList = function() {
            $http.get("/api/repost_list/"+$routeParams.userName+"/"+"?&offset="+listOffset+"&limit="+listLimit).success(function(data) {
                if (!data.length) {
                    $scope.endOfData = true;
                    $scope.busy = false;
                } else {
                    $scope.entries = $scope.entries.concat(data);
                    listOffset += increment;
                    listLimit += increment;
                    $scope.busy = false;
                }
            });
        }

        var followerOffset = 0;
        var followerLimit = increment;
        $scope.loadFollowerList = function() {
            if (typeof $scope.endOfData != 'undefined') return;
            if ($scope.busy) return;
            $scope.busy = true;
            $http.get("/api/user/"+$routeParams.userName+"/followers/"+"?&offset="+followerOffset+"&limit="+followerLimit).success(function(data) {
                if (!data.length) {
                    $scope.endOfData = true;
                    $scope.busy = false;
                } else {
                    $scope.followerUsers = $scope.followerUsers.concat(data);
                    followerOffset += increment;
                    followerLimit += increment;
                    $scope.busy = false;
                }
            });
        }

        var followingOffset = 0;
        var followingLimit = increment;
        $scope.loadFollowingList = function() {
            if (typeof $scope.endOfData != 'undefined') return;
            if ($scope.busy) return;
            $scope.busy = true;
            $http.get("/api/user/"+$routeParams.userName+"/following/"+"?&offset="+followingOffset+"&limit="+followingLimit).success(function(data) {
                if (!data.length) {
                    $scope.endOfData = true;
                    $scope.busy = false;
                } else {
                    $scope.followingUsers = $scope.followingUsers.concat(data);
                    followingOffset += increment;
                    followingLimit += increment;
                    $scope.busy = false;
                }
            });
        }
    }

    module.exports = UserProfileCtrl;
})();
},{}],13:[function(require,module,exports){
(function () {
    'use strict';

    function UserSpaceCtrl($scope, $rootScope, $http) {
        $http.get("/api/authenticated_user/").success(function(data) {
            $rootScope.readlater_count = data.rl_count;
            $rootScope.lists = data.lists;
            $rootScope.subscriptionCount = data.subs_count;
            delete data.subs_count;
            $scope.profile = data;
        });
    }

    module.exports = UserSpaceCtrl;
})();
},{}],14:[function(require,module,exports){
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
                document.location.href = "/user/signout";
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
    })
},{}],15:[function(require,module,exports){
'use strict';

/* Dashboard Services */

angular.module('Dashboard.services', []).factory('InitService', function() {
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

            announce.on('new_repost', function(data){
                $("#new-entry").trigger("new_entry_event", {new_entry: data});
            });
        }
    }
});
},{}]},{},[1])
;