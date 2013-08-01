(function () {
    'use strict';

    function UserProfileCtrl($scope, $http, $routeParams) {
        $scope.entries = [];
        $scope.followerUsers = [];
        $scope.followingUsers = [];

        $http.get("/api/user_profile/"+$routeParams.userName+"/").success(function(data) {
            $scope.userProfile = data;
            document.title = $scope.userProfile.display_name+" on "+CsFrontend.Globals.SiteTitle;
            $scope.userProfile.current_username = $routeParams.userName;
        });

        $scope.busy = false;
        var increment = 15;

        var listOffset = 0;
        var listLimit = increment
        $scope.loadRepostList = function() {
            $http.get("/api/repost_list/"+$routeParams.userName+"/"+"?&offset="+listOffset+"&limit="+listLimit).success(function(data) {
                if (!data.length) {
                    $scope.endOfData = true;
                    $scope.busy = false;
                } else {
                    $scope.entries = $scope.entries.concat(data);
                    listOffset += increment;
                    listLimit += increment;
                    $scope.busy = false;
                }
            });
        }

        var followerOffset = 0;
        var followerLimit = increment;
        $scope.loadFollowerList = function() {
            if (typeof $scope.endOfData != 'undefined') return;
            if ($scope.busy) return;
            $scope.busy = true;
            $http.get("/api/user/"+$routeParams.userName+"/followers/"+"?&offset="+followerOffset+"&limit="+followerLimit).success(function(data) {
                if (!data.length) {
                    $scope.endOfData = true;
                    $scope.busy = false;
                } else {
                    $scope.followerUsers = $scope.followerUsers.concat(data);
                    followerOffset += increment;
                    followerLimit += increment;
                    $scope.busy = false;
                }
            });
        }

        var followingOffset = 0;
        var followingLimit = increment;
        $scope.loadFollowingList = function() {
            if (typeof $scope.endOfData != 'undefined') return;
            if ($scope.busy) return;
            $scope.busy = true;
            $http.get("/api/user/"+$routeParams.userName+"/following/"+"?&offset="+followingOffset+"&limit="+followingLimit).success(function(data) {
                if (!data.length) {
                    $scope.endOfData = true;
                    $scope.busy = false;
                } else {
                    $scope.followingUsers = $scope.followingUsers.concat(data);
                    followingOffset += increment;
                    followingLimit += increment;
                    $scope.busy = false;
                }
            });
        }
    }

    module.exports = UserProfileCtrl;
})();