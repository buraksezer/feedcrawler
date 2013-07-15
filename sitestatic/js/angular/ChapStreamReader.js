var ChapStreamReader = angular.module("ChapStreamReader", [],
    function($routeProvider, $locationProvider) {
        $locationProvider.html5Mode(true);
        $routeProvider
        .when("/reader/:entryId", {templateUrl: '/static/templates/iframe.html', controller: 'ReaderMainCtrl'})
    }
);

ChapStreamReader.config(function($httpProvider) {
    $httpProvider.defaults.headers.post['X-CSRFToken'] = $('input[name=csrfmiddlewaretoken]').val();
});

ChapStreamReader.directive('preventDefault', function() {
    return function(scope, element, attrs) {
        $(element).click(function(event) {
            event.preventDefault();
            event.stopPropagation();
        });
    }
});

ChapStreamReader.run(function($rootScope) {
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
});

ChapStreamReader.directive('entryLike', function($http) {
    return function (scope, element, attrs) {
        $(element).click(function(event) {
            $http.post("/api/like/"+scope.entry.id+"/").success(function(data) {
                if (data.code == 1) {
                    scope.entry.liked = true;
                } else if (data.code == -1) {
                    scope.entry.liked = false;
                } // error cases
            });
        });
    }
});

ChapStreamReader.directive('whenScrolled', function() {
    return function(scope, elm, attr) {
        var raw = elm[0];

        elm.bind('scroll', function() {
            if (raw.scrollTop + raw.offsetHeight >= raw.scrollHeight) {
                scope.$apply(attr.whenScrolled);
            }
        });
    };
});

ChapStreamReader.directive('readLater', function($http) {
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
});

ChapStreamReader.directive('entriesNavigation', function($http) {
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
});

ChapStreamReader.directive('searchSubscriptions', function($http) {
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
});

ChapStreamReader.directive('getEntries', function($rootScope) {
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
});

function ReaderMainCtrl($scope, $http, $routeParams) {
    // Remove old entry.link value to prevent reloading
    if (typeof $scope.entry != 'undefined') {
        $scope.entry.link = '';
    }

    $scope.showLoading = true;
    $http.get("/api/reader/"+$routeParams.entryId).success(function(data) {
        $scope.showLoading = false;
        if (data.code == 1) {
            $scope.getEntry(data.result);
        } else {
            $scope.msg  = data.msg;
        }
        document.title = $scope.entry.title+" | "+CsFrontend.Globals.SiteTitle;
    });
}

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