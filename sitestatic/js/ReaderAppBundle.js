;(function(e,t,n){function i(n,s){if(!t[n]){if(!e[n]){var o=typeof require=="function"&&require;if(!s&&o)return o(n,!0);if(r)return r(n,!0);throw new Error("Cannot find module '"+n+"'")}var u=t[n]={exports:{}};e[n][0].call(u.exports,function(t){var r=e[n][1][t];return i(r?r:t)},u,u.exports)}return t[n].exports}var r=typeof require=="function"&&require;for(var s=0;s<n.length;s++)i(n[s]);return i})({1:[function(require,module,exports){
'use strict';

require("./controllers");
require("./directives");

var app = angular.module("Reader", ['Reader.controllers', 'Reader.directives', 'ngSanitize'])
    .config(["$routeProvider",
        function($routeProvider) {
            $routeProvider
            .when("/reader/:slug", {templateUrl: '/static/templates/iframe.html', controller: 'ReaderMainCtrl'})
    }])
    .config(["$locationProvider", function($locationProvider) {
        $locationProvider.html5Mode(true);
    }])
    .config(["$httpProvider", function($httpProvider) {
        $httpProvider.defaults.headers.post['X-CSRFToken'] = $('input[name=csrfmiddlewaretoken]').val();
    }]);

app.run(function($rootScope) {
    $rootScope.username = CsFrontend.Globals.username;
    $rootScope.isAuthenticated = CsFrontend.Globals.isAuthenticated;
    $rootScope.goToHome = function() {
        document.location.href = "/";
    }

    $rootScope.getEntry = function(data) {
        $rootScope.targetFeedId = data.feed_id;
        $rootScope.feedTitle = data.feed_title;
        $rootScope.entry = data;
    }

    $rootScope.empty = function(value) {
        return $.isEmptyObject(value);
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
});

},{"./controllers":2,"./directives":5}],2:[function(require,module,exports){
'use strict';

var ReaderMainCtrl = require("./controllers/ReaderMainCtrl.js");
var ReaderNavbarCtrl = require("./controllers/ReaderNavbarCtrl.js");

angular.module("Reader.controllers", [])
    .controller("ReaderMainCtrl", ["$scope", "$http", "$routeParams", ReaderMainCtrl])
    .controller("ReaderNavbarCtrl", ["$scope", "$http", "$location", "$rootScope", ReaderNavbarCtrl]);
},{"./controllers/ReaderMainCtrl.js":3,"./controllers/ReaderNavbarCtrl.js":4}],3:[function(require,module,exports){
(function () {
    'use strict';

    function ReaderMainCtrl($scope, $http, $routeParams) {
        // Remove old entry.link value to prevent reloading
        if (typeof $scope.entry != 'undefined') {
            $scope.entry.link = '';
        }

        $scope.showLoading = true;
        $http.get("/api/reader/"+$routeParams.slug).success(function(data) {
            $scope.showLoading = false;
            if (data.code == 1) {
                $scope.getEntry(data.result);
            } else {
                $scope.msg  = data.msg;
            }
            document.title = $scope.entry.title+" | "+CsFrontend.Globals.SiteTitle;
        });
    }

    module.exports = ReaderMainCtrl;
})();
},{}],4:[function(require,module,exports){
(function () {
    'use strict';

    function ReaderNavbarCtrl($scope, $http, $location, $rootScope) {
        var increment = 10;
        $scope.other_entries= [];
        $scope.offset = 0;
        $scope.limit = increment;

        $scope.loadEntries = function() {
            if ($(".entries-navigation-item a.active-entries-nav").attr("id") != "entries") return;
            $scope.showEntriesBlock = true;
            if (typeof $scope.endOfData != 'undefined') return;
            $scope.showLoading = true;
            $scope.busy = false;
            //if (typeof feed_id == 'undefined') return;
            $http.get("/api/entries_by_feed/"+$rootScope.targetFeedId+"/?&offset="+$scope.offset+"&limit="+$scope.limit).success(function(data) {
                $scope.showLoading = false;
                if ($scope.busy) return;
                $scope.busy = true;
                if (!data.length) {
                    $scope.endOfData = true;
                    $scope.busy = false;
                } else {
                    for(var i = 0; i < data.length; i++) {
                        $scope.other_entries.push(data[i]);
                    }
                    $scope.offset += increment;
                    $scope.limit += increment;
                    $scope.busy = false;
                }
                $(".entries").niceScroll({cursorcolor:"#555555", cursoropacitymax: "0.5"});
            })
        };
    }

    module.exports = ReaderNavbarCtrl;
})();
},{}],5:[function(require,module,exports){
'use strict';

/* Directives */

angular.module('Reader.directives', [])
    .directive('preventDefault', function() {
        return function(scope, element, attrs) {
            $(element).click(function(event) {
                event.preventDefault();
                event.stopPropagation();
            });
        }
    }).directive('entryLike', function($http) {
        return function (scope, element, attrs) {
            $(element).click(function(event) {
                $http.post("/api/like_entry/"+scope.entry.id+"/").success(function(data) {
                    if (data.code == 1) {
                        scope.entry.liked = true;
                    } else if (data.code == -1) {
                        scope.entry.liked = false;
                    } // error cases
                });
            });
        }
    }).directive('whenScrolled', function() {
        return function(scope, elm, attr) {
            var raw = elm[0];

            elm.bind('scroll', function() {
                if (raw.scrollTop + raw.offsetHeight >= raw.scrollHeight) {
                    scope.$apply(attr.whenScrolled);
                }
            });
        };
    }).directive('readLater', function($http) {
        return function(scope, element, attrs) {
            $(element).click(function(event) {
                $http.post("/api/readlater/"+scope.entry.id+"/").success(function(data) {
                    if (data.code == 1) {
                        scope.entry.inReadLater = true;
                    } else if (data.code == -1) {
                        scope.entry.inReadLater = false;
                    }
                });
            });
        }
    }).directive('entriesNavigation', function($http) {
        return function(scope, element, attrs) {
            $(element).click(function(event) {
                var element_id = event.target.getAttribute("id");
                $(element).find("a").removeClass("active-entries-nav");
                $(event.target).addClass("active-entries-nav");
                if (element_id == "subscriptions") {
                    scope.showEntriesBlock = false;
                    scope.showSubscriptionBlock = true;
                    scope.showNewSubscriotionBlock = false;
                } else if (element_id == "entries") {
                    scope.showEntriesBlock = true;
                    scope.showSubscriptionBlock = false;
                    scope.showNewSubscriotionBlock = false;
                } else if (element_id == "new-subscriotion") {
                    scope.showEntriesBlock = false;
                    scope.showSubscriptionBlock = false;
                    scope.showNewSubscriotionBlock = true;
                }
            });
        }
    }).directive('searchSubscriptions', function($http) {
        return function(scope, element, attrs) {
            $(element).keyup(throttle(function(event) {
                if (scope.subsKeyword.length == 0) {
                    scope.subscriptions = [];
                    scope.nothingFound = false;
                }
                $http.get("/api/subs-search/"+scope.subsKeyword+"?&typeahead=0").success(function(data) {
                    if (data.length == 0) {
                        scope.nothingFound = true;
                        scope.subscriptions = [];
                        return;
                    }
                    scope.nothingFound = false;
                    scope.subscriptions = data;
                    $(".subscriptions").niceScroll({cursorcolor:"#555555", cursoropacitymax: "0.5"});
                });
            }));
        }
    }).directive('getEntries', function($rootScope) {
        return function(scope, element, attrs) {
            $(element).click(function(event) {
                scope.$parent.showEntriesBlock = true;
                scope.$parent.showSubscriptionBlock = false;
                //scope.showNewSubscriotionBlock = false;
                $rootScope.targetFeedId = scope.subscription.id;
                $rootScope.feedTitle = scope.subscription.title;
                scope.$parent.other_entries = [];
                scope.$parent.offset = 0;
                scope.$parent.limit = 10;
                scope.$parent.endOfData = undefined;
                $(".entries-navigation-item a").removeClass("active-entries-nav");
                $("#entries").addClass("active-entries-nav");
                scope.$parent.loadEntries();
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

            $(element).closest(".comments-header").find("textarea").keypress(function(event) {
                if (event.shiftKey) {
                    scope.commentContent =+ "\n";
                } else {
                    if (event.keyCode != 13) return;
                    event.preventDefault();
                    post_comment();
                }
            });
        }
    }).directive('editComment', function() {
        return function(scope, element, attrs) {
            $(element).click(function() {
                var comment = scope.entry.comments.results[attrs.cIndex];
                var comment_content = $(element).closest(".comment .content");
                comment_edit = $(element).closest(".comment").find(".edit-comment-form");
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

            $(element).keypress(function(event) {
                if (event.shiftKey) {
                    scope.commentContent =+ "\n";
                } else {
                    if (event.keyCode != 13) return;
                    event.preventDefault();
                    post_comment();
                }
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
    }).directive('cancelComment', function() {
        return function(scope, element, attrs) {
            $(element).click(function(event) {
                // Edit related variables
                scope.showCommentEditBox = false;
                scope.commentEdit = false;
                // New comment related variables
                scope.postingComment = false;
                scope.commentContent = "";
            });
        }
    }).directive('prepareCommentBox', function () {
        return function(scope, element, attrs) {
            $(element).click(function(event) {
                var comment_box = $(".comments-header textarea.comment");
                comment_box.autosize();
                $(".comments").niceScroll({cursorcolor:"#555555", cursoropacitymax: "0.5"});
            });
        }
    });

},{}]},{},[1])
;