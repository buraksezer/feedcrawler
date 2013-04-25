$(document).ready(function () {
    // .init() will authenticate against the announce.js server, and open the WebSocket connection.
    announce.init();

    // use .on() to add a listener. you can add as many listeners as you want.
    announce.on('notifications', function(data){
        console.log(data.msg);
    });

});