(function () {
    'use strict';

    function ListCtrl($scope, $routeParams, $http) {
        $http.get("/api/prepare_list/"+$routeParams.listSlug+"/").success(function(data) {
            $scope.listTitle = data.title;
            $scope.listFeedIds = data.feed_ids;
            document.title = $scope.listTitle +" | "+CsFrontend.Globals.SiteTitle;
        });
    }
    module.exports = ListCtrl;
})();