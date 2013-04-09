$(document).ready(function() {
    $("div.feed-item").delegate("p", "click", function(evt) {
        var feed_item = $(this).closest(".feed-item").find("ul.entry-list")

        if (feed_item.css("display") === "none") {
            feed_item.css("display", "block");
        } else {
            feed_item.css("display", "none");
        }
    });
    $('#nav-next').tooltip();
    $('#nav-previous').tooltip();
});