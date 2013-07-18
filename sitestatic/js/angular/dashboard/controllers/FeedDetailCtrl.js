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
            $http.post("/api/unsubscribe/"+id+"/").success(function(data) {
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