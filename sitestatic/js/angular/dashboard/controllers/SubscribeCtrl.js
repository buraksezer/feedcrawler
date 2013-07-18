(function () {
  'use strict';
    function SubscribeCtrl($scope, $http, $timeout, $rootScope) {
        var defaultForm = {
            feed_url : ""
        };
        $scope.form = angular.copy(defaultForm);

        $scope.findSource = function() {
            $scope.warning = '';
            $scope.results = [];
            if (typeof $scope.form.feed_url != "string" || $scope.form.feed_url.length < 3) {
                $scope.warning = "Please give a valid URL.";
                return;
            }
            $scope.showWait = true;
            $http.get("/api/find_source?url="+$scope.form.feed_url).success(function(data) {
                $scope.showWait = false;
                if (!data.length) {
                    $scope.warning = "No result found.";
                    var delay = $timeout(function() {
                        $scope.warning = '';
                    }, 2000);
                    return;
                }
                $scope.results = data;
            });
        }

        $scope.subsFeed = function(url) {
            $scope.showWait = true;
            $http.get("/api/subscribe?url="+url).success(function(data) {
                if (data.code == 1) {
                    $rootScope.subscriptionCount += 1;
                }
                $scope.warning = data.text;
                $scope.showWait = false;
                var delay = $timeout(function() {
                    $scope.warning = '';
                }, 2000);
            });
        };

        $scope.cleanSubsModal = function() {
            $scope.form = angular.copy(defaultForm);
            $scope.results = undefined;
        }
    }

    module.exports = SubscribeCtrl;
})();