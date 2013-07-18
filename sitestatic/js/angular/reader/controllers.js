'use strict';

var ReaderMainCtrl = require("./controllers/ReaderMainCtrl.js");
var ReaderNavbarCtrl = require("./controllers/ReaderNavbarCtrl.js");

angular.module("Reader.controllers", [])
    .controller("ReaderMainCtrl", ["$scope", "$http", "$routeParams", ReaderMainCtrl])
    .controller("ReaderNavbarCtrl", ["$scope", "$http", "$location", "$rootScope", ReaderNavbarCtrl]);