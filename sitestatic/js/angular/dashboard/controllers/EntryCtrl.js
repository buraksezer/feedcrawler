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
