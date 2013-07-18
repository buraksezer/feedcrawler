(function () {
  'use strict';

    function InteractionsCtrl($scope, $http, $rootScope) {
        document.title = "Interactions"+" | "+CsFrontend.Globals.SiteTitle;
        // Reset interaction count in user space
        $("#new-interaction-count").trigger("reset_interaction_count");

        $scope.busy = false;
        var increment = 15;
        $scope.entries = [];
        $scope.offset = 0;
        $scope.limit = increment;
        $scope.interactions = {entries: []};

        $scope.loadInteractions = function() {
            if (typeof $scope.endOfData != 'undefined') return;
            if ($scope.busy) return;
            $scope.busy = true;
            $http.get("/api/interactions/"+"?&offset="+$scope.offset+"&limit="+$scope.limit).success(function(data) {
                if (!data.length) {
                    $scope.endOfData = true;
                    $scope.busy = false;
                } else {
                    for(var i = 0; i < data.length; i++) {
                        for(var j=0; j < data[i].comments.results.length; j++) {
                            // A bit confusing?
                            data[i].comments.results[j].content = nl2br(data[i].comments.results[j].content);
                        }
                        $scope.interactions.entries.push(data[i]);
                    }
                    $scope.offset += increment;
                    $scope.limit += increment;
                    $scope.busy = false;
                }
            });
        };

        $scope.showClickjackingWarn = function() {
            $scope.clickjacking = true;
        };
    }

  module.exports = InteractionsCtrl;
})();