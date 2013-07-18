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