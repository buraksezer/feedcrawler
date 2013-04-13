$(document).ready(function() {
    function get_votes() {
        if (!$("#explorer").length) return;
        var action_types = ["dislike", "like"];
        $.each(action_types, function(idx, action_type) {
            $.get("/vote/", {action_type: action_type, entry_id: $("#feedcraft-container").data("entry-id")}, function(result) {
                    if (result == 1) {
                        $("#navigator .entry-"+action_type).addClass("like-voted");
                        $("#navigator .entry-"+action_type+" i").addClass("icon-white");
                        var disabled_action = (action_type == "dislike") ? "like" : "dislike";
                        $("#navigator .entry-"+disabled_action).attr("disabled", "disabled");
                    }
            });
        });
    }

    function common_vote(action_type) {
        if ($("#navigator .entry-"+action_type).attr("disabled") != "disabled") {
            $.post("/vote/", {action_type: action_type, csrfmiddlewaretoken: $("#fc-csrf input").val(),
                entry_id: $("#feedcraft-container").data("entry-id")}, function(result) {
                if (result == 1) {
                    var disabled_action = (action_type == "dislike") ? "like" : "dislike";
                    if ($("#navigator .entry-"+action_type).hasClass("like-voted")) {
                        $("#navigator .entry-"+disabled_action).removeAttr("disabled");
                        $("#navigator .entry-"+action_type).removeClass("like-voted");
                        $("#navigator .entry-"+action_type+" i").removeClass("icon-white");

                    } else {
                        $("#navigator .entry-"+disabled_action).attr("disabled", "disabled");
                        $("#navigator .entry-"+action_type).addClass("like-voted");
                        $("#navigator .entry-"+action_type+" i").addClass("icon-white");
                    }
                }
            });
        }
    }

    $("div.feed-item").delegate("p", "click", function(evt) {
        var feed_item = $(this).closest(".feed-item").find("ul.entry-list")

        if (feed_item.css("display") === "none") {
            feed_item.css("display", "block");
        } else {
            feed_item.css("display", "none");
        }
    });

    $(".entry-like").click(function(evt) {
        common_vote("like");
    });

    $(".entry-dislike").click(function(evt) {
        common_vote("dislike");
    });

    $('#nav-next').tooltip();
    $('#nav-previous').tooltip();
    get_votes();
});