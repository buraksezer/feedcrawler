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