'use strict';

require("./controllers");
require("./directives");

var app = angular.module("Reader", ['Reader.controllers', 'Reader.directives', 'ngSanitize'])
    .config(["$routeProvider",
        function($routeProvider) {
            $routeProvider
            .when("/reader/:slug", {templateUrl: '/static/templates/iframe.html', controller: 'ReaderMainCtrl'})
    }])
    .config(["$locationProvider", function($locationProvider) {
        $locationProvider.html5Mode(true);
    }])
    .config(["$httpProvider", function($httpProvider) {
        $httpProvider.defaults.headers.post['X-CSRFToken'] = $('input[name=csrfmiddlewaretoken]').val();
    }]);

app.run(function($rootScope) {
    $rootScope.username = CsFrontend.Globals.username;
    $rootScope.isAuthenticated = CsFrontend.Globals.isAuthenticated;
    $rootScope.goToHome = function() {
        document.location.href = "/";
    }

    $rootScope.getEntry = function(data) {
        $rootScope.targetFeedId = data.feed_id;
        $rootScope.feedTitle = data.feed_title;
        $rootScope.entry = data;
    }

    $rootScope.empty = function(value) {
        return $.isEmptyObject(value);
    };

    $rootScope.safeApply = function(fn) {
        var phase = this.$root.$$phase;
        if(phase == '$apply' || phase == '$digest') {
            if(fn && (typeof(fn) === 'function')) {
                fn();
            }
        } else {
            this.$apply(fn);
        }
    };
});
