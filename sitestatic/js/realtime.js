$(document).ready(function () {
    $("body").data("page-title", document.title);
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
                        var new_item = '<div class="entry"><a href="/explorer/'+data.id+'" class="title trigger-wrapper" data-link="'+data.link+
                        '" data-entry-id="'+data.id+'" data-feed-id="'+data.feed_id+'" data-title="FeedCraft | '+data.title+'">'+data.title+'</a></div>'
                        $(day).after(new_item);
                    }
                });
            }
        }

        if ($("#dashboard .timeline .new-entry-counter").length) {
            var detail_page = $(".feed-detail-header");
            if (detail_page.length != 0 && data.feed_id != detail_page.data("feed-id")) return;

            // Update dashboard for new entries
            var clickjacking_warn = '';
            if (data.available == 0) {
                var clickjacking_warn = '<div class="clickjacking-warn">'+
                    '<span>Unfortunately, viewing in an external site is disabled by publisher.</span>'+
                    '<a class="external-link" href="'+data.link+'" target="_blank">Open in a new tab.</a>'+
                    '</div>'
            }
            var entry = '<div style="display:none;" class="dashboard-entry" data-entry-id="'+data.id+'" data-feed-id="'+data.feed_id+'">'+
            '<ul class="entry-topbar">'+
            '<li><a href="'+data.link+'"'+'target="_blank"><i data-toggle="tooltip" title="Original Link" class="icon-share-alt"></i></li>'+
            '<li><a href="/explorer/'+data.id+'" target="_blank"><i data-toggle="tooltip" title="Open new tab" class="icon-share"></i></li>'+
            '</ul>'+
            '<div class="entry-content">'+
            '<a data-available="'+data.available+'" class="entry-title" href="/explorer/'+data.id+'">'+data.title+'</a>'+
            '<br/>'+
            '<a class="feed" href="/feed/'+data.feed_id+'">'+data.feed_title+'</a>'+
            '<div class="timeline-entry-interaction">'+
            '<span class="like">Like </span>'+
            '<span class="dislike">Dislike </span>'+
            '<span class="Comment">Comment </span>'+
            '</div></div>'+
            clickjacking_warn+
            '</div>';
            var item_count = $(".timeline .new-entry-counter").data("item-count");
            $(".timeline .new-entry-counter").data("item-count", item_count + 1);
            $(".timeline .new-entry-counter a").empty();
            if (item_count > 0) {
                var msg = item_count+1+" new entries";
            } else {
                var msg = "1 new entry";
            }
            $(".timeline .new-entry-counter a").text(msg);
            var title_item_count = item_count + 1;
            document.title = "("+title_item_count+") "+$("body").data("page-title");
            $(".timeline .new-entry-counter:hidden").css("display", "block");
            $("#dashboard .timeline .dashboard-entries").prepend(entry);
        }
    });

    announce.on('newfeed_rightbar', function(data) {
        $(".right-bar div.feed-items").append(data.dom);
    });
});