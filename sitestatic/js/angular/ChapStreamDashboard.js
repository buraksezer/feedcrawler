var ChapStream = angular.module('ChapStream', ['infinite-scroll'],
    function($routeProvider, $locationProvider) {
        $locationProvider.html5Mode(true);
        $routeProvider
        .when('/', { templateUrl: '/static/templates/timeline.html', controller: 'TimelineCtrl' })
        .when('/feed/:feedId', { templateUrl: '/static/templates/feed-detail.html', controller: 'FeedDetailCtrl' })
        .when('/subscriptions', { templateUrl: '/static/templates/subscriptions.html', controller: 'SubscriptionsCtrl' })
    }
);

ChapStream.config(function($httpProvider) {
    $httpProvider.defaults.headers.post['X-CSRFToken'] = $('input[name=csrfmiddlewaretoken]').val();
});

ChapStream.directive('preventDefault', function() {
    return function(scope, element, attrs) {
        $(element).click(function(event) {
            event.preventDefault();
            event.stopPropagation();
        });
    }
});

ChapStream.run(function($rootScope) {
    $rootScope.renderToReader = function(id) {
        document.location.href = "/reader/"+id;
    }
});

function SubscriptionsCtrl($scope, $http, $routeParams) {
    document.title = "Your subscriptions"+" | "+SiteTitle;
    var increment = 10;
    $scope.busy = false;
    $scope.subscriptions= []
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
    }
}

function FeedDetailCtrl($scope, $http, $routeParams) {
    $scope.busy = false;
    var increment = 15;
    $scope.feed_detail = {feed: {}, entries: []}
    $scope.offset = 0;
    $scope.limit = increment;
    $scope.loading = true;

    $scope.loadFeedDetail = function() {
        if (typeof $scope.endOfData != 'undefined') return;
        if ($scope.busy) return;
        $scope.busy = true;
        console.log($scope.feed_detail.entries)
        $http.get("/api/feed_detail/"+$routeParams.feedId+"/?&offset="+$scope.offset+"&limit="+$scope.limit).success(function(data) {
            if (!data.entries.length) {
                $scope.endOfData = true;
                $scope.busy = false;
            } else {
                if (!$scope.feed_detail.feed.length) {
                    $scope.feed_detail.feed = data.feed;
                }

                for(var i = 0; i < data.entries.length; i++) {
                    $scope.feed_detail.entries.push(data.entries[i]);
                }

                $scope.loading = false;
                $scope.offset += increment;
                $scope.limit += increment;
                $scope.busy = false;
                document.title = data.feed.title+" | "+SiteTitle;
            }
        });
    }

    $scope.unsubscribeFeed = function(id) {
        $http.post("/api/unsubscribe/"+id+"/").success(function(data) {
            if (data.code == 1){
                $scope.feed_detail.feed.is_subscribed = false;
                $scope.feed_detail.feed.subs_count -= 1;
            }
        })
    }

    $scope.subscribeFeed = function(id) {
        $http.post("/api/subscribe_by_id/"+id+"/").success(function(data) {
            if (data.code == 1) {
                $scope.feed_detail.feed.is_subscribed = true;
                $scope.feed_detail.feed.subs_count += 1;
            }
        });
    }
}

function TimelineCtrl($scope, $http) {
    document.title = SiteTitle;
    $scope.busy = false;
    var increment = 15;
    $scope.entries = []
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
                    $scope.entries.push(data[i]);
                }
                $scope.offset += increment;
                $scope.limit += increment;
                $scope.busy = false;
            }
        });
    }
}

function ReaderCtrl($scope, $http) {
}

function SubscribeController($scope, $http, $timeout) {
    var defaultForm = {
        feed_url : ""
    }
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
                $("form.subscribe-feed-dropdown").closest("li.dropdown").removeClass("open")
                $scope.subscribe_warning = "";
                $scope.form = angular.copy(defaultForm);
            }, 1500);
        });
    }
}

function UserspaceCtrl($scope, $http, $timeout) {
    $http.get("/api/user_profile/").success(function(data) {
        $scope.profile = data;
    });
}