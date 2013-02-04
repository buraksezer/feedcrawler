$(document).ready(function() {
    $("body").tooltip({
        selector: "a[rel=tooltip]",
        placement: "bottom"
    });

    $("a[rel=popover]").popover();

    $('ul.nav').delegate('#subscribe-nav', 'click', function(e) {
        // A hack to add csrf token to our dynamic form
        var csrf_token = $(this).closest(".nav li").find("input[name='csrfmiddlewaretoken']").closest("div[style='display:none']");
        $("#add-feed").append(csrf_token);
        $('.nav').on('click', '#subscribe-plus', function(evt){
            evt.preventDefault();
            var feed_url = $('input[name="feed_url"]').val();
            console.log(feed_url);
            // Disable the input area if feed_url is a valid URL
            var popover_title = $(this).closest(".popover-title");
            popover_title.empty();
            popover_title.append("Processing...<img id='processing-feed' src='/static/img/ajax-loader.gif'></img>");
            if (feed_url.length !== 0) {
                addFeed();
            } else {
            }
        });
    });
});

/*

TODO:
======

* Ajax functions must be collected at a class

/*

/* Post a feed url for adding to database */
function addFeed() {
    $.ajax({
        type: 'POST',
        url: '/reader/ajax/add_feed/',
        data: $("form#add-feed").serialize(),
        success: function(data) {
            $("a[rel=popover]").popover('hide');
            $('.container .span9').append('<div class="alert "'+data.alert_type+'>'+data.message+'</div>').delay(5000).fadeOut(2000);
        },
        error: function(data) {
        }
    });
}