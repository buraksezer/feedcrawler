'use strict';

/* Dashboard Services */

angular.module('Dashboard.services', []).factory('InitService', function() {
    return {
        realtime: function() {
            console.log("I am ready to fetch realtime data.");
            announce.init();
            announce.on('new_comment', function(data){
                $("#comments_"+data.entry_id).trigger("new_comment_event", {new_comment: data});
                $("#new-interaction").trigger("new_interaction_event",
                    {interaction_id: data.entry_id, owner: data.author}
                );
            });

            announce.on('new_entry', function(data){
                $("#new-entry").trigger("new_entry_event", {new_entry: data});
            });

            announce.on('new_repost', function(data){
                console.log(data);
                $("#new-entry").trigger("new_entry_event", {new_entry: data});
            });
        }
    }
});