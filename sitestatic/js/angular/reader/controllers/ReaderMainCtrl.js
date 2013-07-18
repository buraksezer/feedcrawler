(function () {
    'use strict';

    function ReaderMainCtrl($scope, $http, $routeParams) {
        // Remove old entry.link value to prevent reloading
        if (typeof $scope.entry != 'undefined') {
            $scope.entry.link = '';
        }

        $scope.showLoading = true;
        $http.get("/api/reader/"+$routeParams.slug).success(function(data) {
            $scope.showLoading = false;
            if (data.code == 1) {
                $scope.getEntry(data.result);
            } else {
                $scope.msg  = data.msg;
            }
            document.title = $scope.entry.title+" | "+CsFrontend.Globals.SiteTitle;
        });
    }

    module.exports = ReaderMainCtrl;
})();