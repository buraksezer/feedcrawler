(function () {
    'use strict';

    function UserSpaceCtrl($scope, $rootScope, $http) {
        $http.get("/api/authenticated_user/").success(function(data) {
            $rootScope.readlater_count = data.rl_count;
            $rootScope.lists = data.lists;
            $rootScope.subscriptionCount = data.subs_count;
            delete data.subs_count;
            $scope.profile = data;
        });
    }

    module.exports = UserSpaceCtrl;
})();