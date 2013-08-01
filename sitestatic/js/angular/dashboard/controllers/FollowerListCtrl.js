(function () {
    'use strict';
    function FollowerListCtrl($scope, $http, $routeParams) {
        $scope.loadingFollowerList = true;
        $scope.busy = false;
        var increment = 15;
        $scope.entries = [];
        $scope.offset = 0;
        $scope.limit = increment;
        $scope.loadTimelineEntries = function() {
            $http.get("/api/user/"+$routeParams.userName+"/followers").success(function(data) {
                $scope.loadingFollowerList = false;
                document.title = "Followers | "+CsFrontend.Globals.SiteTitle;
                $scope.followerList = data;
            });
        }
    }
    module.exports = FollowerListCtrl;
})();
