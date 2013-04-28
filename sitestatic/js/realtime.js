$(document).ready(function () {
    // .init() will authenticate against the announce.js server, and open the WebSocket connection.
    announce.init();

    // use .on() to add a listener. you can add as many listeners as you want.
    announce.on('new_entry', function(data){
        if($("#feed-source-list").length) {
            // Update entry list for current feed
            var active_feed = $("#feed-source-list").find(".active");
            var active_feed_id = active_feed.data("feed-id");
            if (data.feed_id == active_feed_id) {
                $.each($("#feed-entry-list .entries").find(".day"), function(idx, day) {
                    if (data.published_at == null || data.published_at == $(day).text()) {
                        var new_item = '<div class="entry"><a href="#" class="title trigger-wrapper" data-link="'+data.link+
                        '" data-entry-id="'+data.id+'" data-feed-id="'+data.feed_id+'" data-title="FeedCraft | '+data.title+'">'+data.title+'</a></div>'
                        $(day).after(new_item);
                    }
                });
            }
        }

        if ($("#dashboard .timeline").length) {
            console.log("burda");
            // Update dashboard for new entries
            var entry = '<div style="display:none;" class="dashboard-entry" data-entry-id="'+data.id+'" data-feed-id="'+data.feed_id+'">'+
            '<a class="entry-title" href="#">'+data.title+'</a> on '+
            '<a class="feed" href="#">'+data.feed_title+'</a>'+
            '<div class="timeline-entry-interaction">'+
            '<span class="like">Like </span>'+
            '<span class="dislike">Dislike </span>'+
            '<span class="Comment">Comment </span>'+
            '</div></div>';

            var item_count = $(".timeline .new-entry-counter").data("item-count");
            $(".timeline .new-entry-counter").data("item-count", item_count + 1);
            $(".timeline .new-entry-counter a").empty();
            if (item_count > 0) {
                var msg = item_count+1+" new entries";
            } else {
                var msg = "1 new entry";
            }
            $(".timeline .new-entry-counter a").text(msg);
            $(".timeline .new-entry-counter:hidden").css("display", "block");
            $("#dashboard .timeline .dashboard-entries").prepend(entry);
        }
    });

});