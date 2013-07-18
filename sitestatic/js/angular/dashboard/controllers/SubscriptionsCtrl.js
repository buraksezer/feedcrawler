(function () {
  'use strict';

    function SubscriptionsCtrl($scope, $http) {
        document.title = "Your subscriptions"+" | "+CsFrontend.Globals.SiteTitle;
        var increment = 10;
        $scope.busy = false;
        $scope.subscriptions= [];
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
        };
    }

  module.exports = SubscriptionsCtrl;
})();