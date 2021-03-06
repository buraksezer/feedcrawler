'use strict';

require("./services");
require("./controllers");
require("./directives");

var app = angular.module('Dashboard', ['Dashboard.services', 'Dashboard.controllers', 'Dashboard.directives', 'infinite-scroll', 'ngSanitize'])
    .config(["$routeProvider",
        function($routeProvider) {
            $routeProvider
            .when('/', { templateUrl: '/static/templates/timeline.html', controller: 'TimelineCtrl' })
            .when('/feed/:feedId', { templateUrl: '/static/templates/feed-detail.html', controller: 'FeedDetailCtrl' })
            .when('/subscriptions', { templateUrl: '/static/templates/subscriptions.html', controller: 'SubscriptionsCtrl' })
            .when('/interactions', { templateUrl: '/static/templates/interactions.html', controller: 'InteractionsCtrl' })
            .when('/readlater', { templateUrl: '/static/templates/readlater.html', controller: 'ReadLaterCtrl' })
            .when('/entry/:entryId', { templateUrl: '/static/templates/entry.html', controller: 'EntryCtrl' })
            .when('/repost/:repostId', { templateUrl: '/static/templates/repost.html', controller: 'RepostCtrl' })
            .when('/list/:listSlug', { templateUrl: '/static/templates/list.html', controller: 'ListCtrl' })
            .when('/user/:userName', { templateUrl: '/static/templates/user-profile.html', controller: 'UserProfileCtrl' })
            .when('/user/:userName/followers', { templateUrl: '/static/templates/follower-list.html', controller: 'UserProfileCtrl' })
            .when('/user/:userName/following', { templateUrl: '/static/templates/following-list.html', controller: 'UserProfileCtrl' });
            /*.when('/reader/:slug', { templateUrl: '/static/templates/reader.html', controller: 'ReaderCtrl'});*/
    }])
    .config(["$locationProvider", function($locationProvider) {
        $locationProvider.html5Mode(true);
    }])
    .config(["$httpProvider", function($httpProvider) {
        $httpProvider.defaults.headers.common['X-CSRFToken'] = $('input[name=csrfmiddlewaretoken]').val();
    }]);

app.run(function($rootScope, $location, $route, InitService) {
    $rootScope.username = CsFrontend.Globals.username;
    $rootScope.isAuthenticated = CsFrontend.Globals.isAuthenticated;
    $rootScope.viewMode = "dashboard";
    $rootScope.lastRoute = null;
    $rootScope.hiddenStream = false;
    InitService.realtime();

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

    /*$rootScope.$on('$locationChangeSuccess', function () {
        console.log($route.current.controller);
        console.log($rootScope.lastRoute.controller);
        if ($route.current.controller == "ReaderCtrl" || $route.current.controller == $rootScope.lastRoute.controller) {
            $route.current = $rootScope.lastRoute;
        }
        console.log('$locationChangeSuccess changed!', new Date());
    });*/


    $rootScope.readlater_count = 0;
});
