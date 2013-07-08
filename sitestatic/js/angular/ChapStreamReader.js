var ChapStreamReader = angular.module("ChapStreamReader", [],
    function($routeProvider, $locationProvider) {
        $locationProvider.html5Mode(true);
        $routeProvider
        .when("/reader/:entryId", {templateUrl: '/static/templates/iframe.html', controller: 'ReaderMainCtrl'})
    }
);

ChapStreamReader.config(function($httpProvider) {
    $httpProvider.defaults.headers.post['X-CSRFToken'] = $('input[name=csrfmiddlewaretoken]').val();
});

ChapStreamReader.directive('preventDefault', function() {
    return function(scope, element, attrs) {
        $(element).click(function(event) {
            event.preventDefault();
            event.stopPropagation();
        });
    }
});

ChapStreamReader.run(function($rootScope) {
    $rootScope.goToHome = function() {
        document.location.href = "/";
    }

    $rootScope.getEntry = function(data) {
        $rootScope.entry = data;
    }

    $rootScope.empty = function(value) {
        return $.isEmptyObject(value);
    };
});

ChapStreamReader.directive('entryLike', function($http) {
    return function (scope, element, attrs) {
        $(element).click(function(event) {
            $http.post("/api/like/"+scope.entry.id+"/").success(function(data) {
                if (data.code == 1) {
                    scope.entry.liked = true;
                } else if (data.code == -1) {
                    scope.entry.liked = false;
                } // error cases
            });
        });
    }
});

ChapStreamReader.directive('whenScrolled', function() {
    return function(scope, elm, attr) {
        var raw = elm[0];

        elm.bind('scroll', function() {
            if (raw.scrollTop + raw.offsetHeight >= raw.scrollHeight) {
                scope.$apply(attr.whenScrolled);
            }
        });
    };
});

function ReaderMainCtrl($scope, $http, $routeParams) {
    // Remove old entry.link value to prevent reloading
    if (typeof $scope.entry != 'undefined') {
        $scope.entry.link = '';
    }

    $scope.showLoading = true;
    $http.get("/api/reader/"+$routeParams.entryId).success(function(data) {
        $scope.showLoading = false;
        if (data.code == 1) {
            $scope.getEntry(data.result);
        } else {
            $scope.msg  = data.msg;
        }
        document.title = $scope.entry.title+" | "+CsFrontend.Globals.SiteTitle;
    });
}

function ReaderNavbarCtrl($scope, $http, $location) {
    $scope.sections = [
        {name: 'Entries'},
        {name: 'Sites'},
        {name: 'Add content'}
    ];

    var increment = 10;
    $scope.other_entries= [];
    $scope.offset = 0;
    $scope.limit = increment;

    $scope.loadEntries = function(feed_id) {
        $scope.showLoading = true;
        $scope.busy = false;
        if (typeof feed_id == 'undefined') return;
        $http.get("/api/entries_by_feed/"+feed_id+"/?&offset="+$scope.offset+"&limit="+$scope.limit).success(function(data) {
            $scope.showLoading = false;
            if (typeof $scope.endOfData != 'undefined') return;
            if ($scope.busy) return;
            $scope.busy = true;
            if (!data.length) {
                $scope.endOfData = true;
                $scope.busy = false;
            } else {
                for(var i = 0; i < data.length; i++) {
                    $scope.other_entries.push(data[i]);
                }
                $scope.offset += increment;
                $scope.limit += increment;
                $scope.busy = false;
            }
            $(".entries").niceScroll({cursorcolor:"#555555", cursoropacitymax: "0.5"});
        })
    };

    $scope.isCurrentEntry = function(entry_id) {
        $scope.entry.id === entry_id;
    }

    $scope.setMaster = function(section) {
        $scope.selected = section;
    };

    $scope.isSelected = function(section) {
        return $scope.selected === section;
    };
}