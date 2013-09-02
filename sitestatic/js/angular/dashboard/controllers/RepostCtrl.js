(function () {
    'use strict';
    function RepostCtrl($scope, $http, $routeParams) {
        $scope.loadingEntry = true;
        $http.get("/api/single_repost/"+$routeParams.repostId+"/").success(function(data) {
            $scope.loadingEntry = false;
            if (data.code == 0) {
                $scope.notFound = true;
            } else {
                document.title = data.title+" | "+CsFrontend.Globals.SiteTitle;
                data.note = nl2br(data.note);
                $scope.entry = data;
                $scope.singleRepost = true;
                $(document).ready(function() {
                    $(".comments-area form.comment-form textarea").autosize();
                    $(".comments-area form.comment-form").css("display", "block");
                });

            }
        });
    }
    module.exports = RepostCtrl;
})();
