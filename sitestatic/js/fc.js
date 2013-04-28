$(document).ready(function() {
    function get_previous_next_items() {
        if (!$("#iframe-container").length) return;
        $.get("/get_previous_next/", function(result) {
            if (!jQuery.isEmptyObject(result.next)) {
                $("#nav-next").removeAttr("disabled");
                $("#nav-next").data("feed-id", result.next.feed_id);
                $("#nav-next").data("title", "FeedCraft | "+result.next.title);
                $("#nav-next").data("entry-id", result.next.id);
                $("#nav-next").data("link", result.next.link);
            } else {
                $("#nav-next").attr("disabled", "disabled");
            }

            if (!jQuery.isEmptyObject(result.previous)) {
                $("#nav-previous").removeAttr("disabled");
                $("#nav-previous").data("link", result.previous.link);
                $("#nav-previous").data("entry-id", result.previous.id);
                $("#nav-previous").data("title", "FeedCraft | "+result.previous.title);
                $("#nav-previous").data("feed-id", result.previous.feed_id);
            } else {
                $("#nav-previous").attr("disabled", "disabled");
            }
        });
    }

    function get_votes() {
        if (!$("#iframe-container").length) return;
        var action_types = ["dislike", "like"];
        $.each(action_types, function(idx, action_type) {
            $.get("/vote/", {action_type: action_type, entry_id: $("#iframe-container").data("entry-id")}, function(result) {
                $("#navigator .entry-"+action_type).removeClass("like-voted");
                $("#navigator .entry-"+action_type+" i").removeClass("icon-white");
                var disabled_action = (action_type == "dislike") ? "like" : "dislike";
                $("#navigator .entry-"+disabled_action).removeAttr("disabled");
                if (result == 1) {
                    $("#navigator .entry-"+action_type).addClass("like-voted");
                    $("#navigator .entry-"+action_type+" i").addClass("icon-white");
                    $("#navigator .entry-"+disabled_action).attr("disabled", "disabled");
                }
            });
        });
    }

    function common_vote(action_type) {
        if ($("#navigator .entry-"+action_type).attr("disabled") != "disabled") {
            $.post("/vote/", {action_type: action_type, csrfmiddlewaretoken: $("#fc-csrf input").val(),
                entry_id: $("#iframe-container").data("entry-id")}, function(result) {
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

    $("div.feed").delegate("p", "click", function(evt) {
        var feed_item = $(this).closest(".feed").find("ul.entries")

        if (feed_item.css("display") === "none") {
            feed_item.css("display", "block");
        } else {
            feed_item.css("display", "none");
        }
    });

    $(document).on("click", "a.trigger-wrapper,#nav-previous,#nav-next", function(evt) {
        var feed_id = $(this).data("feed-id");
        var entry_id = $(this).data("entry-id");
        var csrf = $("#fc-csrf input").val();
        var link = $(this).data("link");
        var title = $(this).data("title");
        var my_entry_item = $(this);
        $.post("/wrapper/", {feed_id: feed_id, entry_id: entry_id, csrfmiddlewaretoken: csrf}, function(result) {
            if (result == "1") {
                $("#frame").attr("src", link);
                document.title = title;
                $("#iframe-container").data("feed-id", feed_id);
                $("#iframe-container").data("entry-id", entry_id);
                $("#iframe-container").data("link", link);
                $.each($("#feed-entry-list .trigger-wrapper"), function(idx, item) {
                    if ($(item).hasClass("current-entry")) {
                        $(item).removeClass("current-entry");
                    }
                    if ($(item).data("entry-id") == entry_id) {
                        $(item).addClass("current-entry");
                    }
                });
                $(my_entry_item).addClass("current-entry");
                get_votes();
                get_previous_next_items();
            }
            /* catch error cases */
        });
    });

    $(document).on('click', ".dashboard-entry .entry-title", function(evt) {
        var feed_id = $(this).closest(".dashboard-entry").data("feed-id");
        var entry_id = $(this).closest(".dashboard-entry").data("entry-id");
        var csrf = $("#fc-csrf input").val();
        $.post("/wrapper/", {feed_id: feed_id, entry_id: entry_id, csrfmiddlewaretoken: csrf}, function(result) {
            if (result == "1") {
                window.location.href = "/explorer/";
            }
            /* catch error cases */
        });
    });

    $(document).on('click', "div.feed-item", function(evt) {
        var feed_id = $(this).data("feed-id");
        var my_feed_item = $(this);
        var current_entry_id = $("#iframe-container").data("entry-id");
        $.post("/getfeedentries/", {current_entry_id: current_entry_id, feed_id: feed_id, csrfmiddlewaretoken: $("#fc-csrf input").val()},
            function(result) {
                $.each($("#feed-source-list div.feed-item"), function(idx, item) {
                    if ($(item).hasClass("active")) {
                        $(item).removeClass("active");
                    }
                });
                $(my_feed_item).addClass("active");
                $("#feed-entry-list .entry-padding").empty();
                $("#feed-entry-list .entry-padding").append(result);
            }
        );
    });

    $("#feed-navigation").click(function(evt) {
        evt.preventDefault();
        var feed_id = $("#iframe-container").data("feed-id");
        var entry_id = $("#iframe-container").data("entry-id");
        if($("#feed-source-list:visible").length !==  0) {
            $("#feed-source-list").css("display", "none");
            $("#feed-entry-list").css("display", "none");
            $("#iframe-container").removeClass("span6").addClass("span12");
            $("iframe").css("width", "100%");
            $("iframe").css("margin-left", "");
            $('.row-fluid [class*="span"]').css("margin-left", "0", "important");
            return;
        } else if($("#feed-source-list:hidden").length !== 0) {
            $("#feed-source-list").css("display", "");
            $("#feed-entry-list").css("display", "");
            $("#iframe-container").removeClass("span12").addClass("span6");
            $("iframe").css("width", "54.7%");
            $("iframe").css("margin-left", "6px");
            $('.row-fluid [class*="span"]').css("margin-left", "-0.436%", "important");
            return;
        }

        if ($("#feed-source-list").length == 0) {
            $.post("/getuserfeeds/", {current_feed_id: feed_id,
                csrfmiddlewaretoken: $("#fc-csrf input").val()}, function(result) {
                    $(".main .box .row-fluid").prepend(result);
                    $("#iframe-container").removeClass("span12").addClass("span6");
                    $("iframe").css("width", "54.7%");
                    $("iframe").css("margin-left", "6px");
                    $('.row-fluid [class*="span"]').css("margin-left", "-0.436%", "important");
                    $.post("/getfeedentries/", {current_entry_id: entry_id, feed_id: feed_id, csrfmiddlewaretoken: $("#fc-csrf input").val()},
                        function(result) {
                            $.each($("#feed-entry-list .trigger-wrapper"), function(idx, item) {
                                if ($(item).data("entry-id") == entry_id) {
                                    $(item).addClass("current-entry")
                                } else {
                                    if ($(item).hasClass("current-entry")) {
                                        $(item).removeClass("current-entry");
                                    }
                                }
                            });
                            $("#feed-entry-list .entry-padding").empty();
                            $("#feed-entry-list .entry-padding").append(result);
                            $("#feed-source-list").removeClass("auto-detect");
                        }
                    );
            });
        }
    });

    $("a[href=#share-modal]").click(function(evt) {
        var link = $("#iframe-container").data("link");
        $("#share-modal div.modal-body input.link").val(link);
        $("#share-modal div.modal-body small.open-new-tab a").attr("href", link);
    });

    $(".entry-like").click(function(evt) {
        common_vote("like");
    });

    $(".entry-dislike").click(function(evt) {
        common_vote("dislike");
    });

    $("#share-modal input.link").click(function(evt) {
        $(this).select();
    });

    $("a[href=#subscribe-modal]").click(function(evt) {
        evt.preventDefault();
        if (!$("#subscribe-modal").length) {
            $.get("/subscribe/", function(result) {
                $(".container").prepend(result);
                $('#subscribe-modal').modal();
            });
        }
    });

    $(document).on("click", "#subscribe-modal button[type=submit]", function(evt) {
        evt.preventDefault();
        var subs_form = $("#subscribe-modal form.form-subscribe").serialize();
        $("#subscribe-modal .loading-gif").css("display", "block");
        $.post("/subscribe/", subs_form, function(result) {
            if (result.code == "1") {
                $("#subscribe-modal span.warning").empty();
                $("#subscribe-modal span.warning").text(result.text)
                $("#subscribe-modal .loading-gif").css("display", "none");
            }
        });
    });

    $(document).on("click", ".new-entry-counter", function(evt) {
        $(".timeline .new-entry-counter").data("item-count", 0);
        $("p.empty-timeline").remove();
        $(".dashboard-entry:hidden").css("display", "block");
        $(".timeline .new-entry-counter").css("display", "none");
        document.title = $("body").data("page-title");
    });

    get_votes();
    get_previous_next_items();
});