(function () {
  'use strict';

    function ReadLaterCtrl($scope, $http, $rootScope, $route) {
        $rootScope.lastRoute = $route.current;
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