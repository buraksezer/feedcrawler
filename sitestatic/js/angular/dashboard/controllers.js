// Dashboard spesific controllers here.

'use strict';

var InteractionsCtrl = require("./controllers/InteractionsCtrl.js");
var SubscriptionsCtrl = require("./controllers/SubscriptionsCtrl.js");
var FeedDetailCtrl = require("./controllers/FeedDetailCtrl.js");
var TimelineCtrl = require("./controllers/TimelineCtrl.js");
var ReadLaterCtrl = require("./controllers/ReadLaterCtrl.js");
var SubscribeCtrl = require("./controllers/SubscribeCtrl.js");
var EntryCtrl = require("./controllers/EntryCtrl.js");
var ListCtrl = require("./controllers/ListCtrl.js");
var UserSpaceCtrl = require("./controllers/UserSpaceCtrl.js");
var UserProfileCtrl = require("./controllers/UserProfileCtrl.js");
var RepostCtrl = require("./controllers/RepostCtrl.js");
var ReaderCtrl = require("./controllers/ReaderCtrl.js");

angular.module("Dashboard.controllers", [])
    .controller("UserSpaceCtrl", ["$scope", "$rootScope", "$http", UserSpaceCtrl])
    .controller("InteractionsCtrl", ["$scope", "$http", "$rootScope", "$route", InteractionsCtrl])
    .controller("SubscriptionsCtrl", ["$scope", "$http", SubscriptionsCtrl])
    .controller("FeedDetailCtrl", ["$scope", "$http", "$routeParams", "$rootScope", FeedDetailCtrl])
    .controller("TimelineCtrl", ["$scope", "$routeParams", "$http", '$route', "$rootScope", TimelineCtrl])
    .controller("ReadLaterCtrl", ["$scope", "$http", "$rootScope", "$route", ReadLaterCtrl])
    .controller("SubscribeCtrl", ["$scope", "$http", "$timeout", "$rootScope", SubscribeCtrl])
    .controller("EntryCtrl", ["$scope", "$http", "$routeParams", EntryCtrl])
    .controller("ListCtrl", ["$scope", "$http", "$routeParams", ListCtrl])
    .controller("UserProfileCtrl", ["$scope", "$http", "$routeParams", UserProfileCtrl])
    .controller("RepostCtrl", ["$scope", "$http", "$routeParams", RepostCtrl])
    .controller("ReaderCtrl", ["$scope", "$http", "$routeParams", "$route", "$rootScope", ReaderCtrl]);