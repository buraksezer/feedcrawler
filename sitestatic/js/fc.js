(function(window,undefined){

    // Prepare
    var History = window.History; // Note: We are using a capital H instead of a lower h
    if ( !History.enabled ) {
         // History.js is disabled for this browser.
         // This is because we can optionally choose to support HTML4 browsers or not.
        return false;
    }

    // Bind to StateChange Event
    History.Adapter.bind(window, 'statechange', function(){ // Note: We are using statechange instead of popstate
        var State = History.getState(); // Note: We are using History.getState() instead of event.state
        History.log(State.data, State.title, State.url);
    });

})(window);

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        function getCookie(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie != '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = jQuery.trim(cookies[i]);
                    // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
        }
        if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
            // Only send the token to relative URLs i.e. locally.
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    }
});

$(document).ready(function() {
    function get_previous_next_items() {
        var entry_id = $("#iframe-container").data("entry-id");
        var feed_id = $("#iframe-container").data("feed-id");
        if (!$("#iframe-container").length) return;
        $.get("/get_previous_next/"+feed_id+"/"+entry_id, function(result) {
            if (!jQuery.isEmptyObject(result.next)) {
                $("#nav-next").removeAttr("disabled");
                $("#nav-next").data("feed-id", result.next.feed_id);
                $("#nav-next").data("title", "FeedCraft | "+result.next.title);
                $("#nav-next").data("entry-id", result.next.id);
                $("#nav-next").data("link", result.next.link);
                $("#nav-next").attr("href", "/explorer/"+result.next.id);
            } else {
                $("#nav-next").attr("disabled", "disabled");
            }

            if (!jQuery.isEmptyObject(result.previous)) {
                $("#nav-previous").removeAttr("disabled");
                $("#nav-previous").data("link", result.previous.link);
                $("#nav-previous").data("entry-id", result.previous.id);
                $("#nav-previous").data("title", "FeedCraft | "+result.previous.title);
                $("#nav-previous").data("feed-id", result.previous.feed_id);
                $("#nav-previous").attr("href", "/explorer/"+result.previous.id);
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
            $.post("/vote/", {action_type: action_type,
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

    function check_subscription() {
        if (!$(".check-subscription").length) return;
        $.each($(".check-subscription"), function(idx, value) {
            $.post("/check_subscribe/", {username: $(value).data("username")},
                function(result) {
                    if (result == 1) {
                        $(".subscribe-user-icon").css("display", "none");
                        $(".unsubscribe-button").css("display", "block");
                    }
                });
        });
    }

    function find_and_subscribe_feed() {
        $(".right-bar .ajax-spinner").css("display", "block");
        $.post("/subscribe/",  {feed_url: $("#id_feed_url").val()}, function(result) {
            $(".right-bar .ajax-spinner").css("display", "none");
            if ($(".subscribe-feed-dropdown").length == 0) {
                $(".right-bar-info-area").css("display", "block").delay(3000).fadeOut();
                $(".right-bar-info-area").empty().append(result.text);
                if (result.code == "1") {
                    $("#id_feed_url").val("");
                    $(".subscribe-feed-box").css("display", "none");
                }
            } else {
                var dropdown_content = $(".subscribe-feed-dropdown");
                dropdown_content.closest("li.dropdown").addClass("open");
                $(".subscribe-warning").css("display", "block").empty().append(result.text);
                if (result.code == "1") {
                    var delay = setTimeout(function() {
                        dropdown_content.closest("li.dropdown").removeClass("open");
                        $("#id_feed_url").val("");
                        $(".subscribe-warning").css("display", "none").empty();
                    }, 3000);
                }
            }
        });
    }

    // obtain a reference to the original handler
    var _clearMenus = $._data(document, "events").click.filter(function (el) {
        return el.namespace === 'data-api.dropdown' && el.selector === undefined
    })[0].handler;

    // disable the old listener
    $(document)
        .off('click.data-api.dropdown', _clearMenus)
        .on('click.data-api.dropdown', function (e) {
            // call the handler only when not right-click
            e.button === 2 || _clearMenus()
        });

    // Fix input element click problem at dropdown in navbar
    $('.navbar-inner .dropdown-menu').click(function(e) {
        e.stopPropagation();
    });

    $("div.feed").delegate("p", "click", function(evt) {
        var feed_item = $(this).closest(".feed").find("ul.entries")

        if (feed_item.css("display") === "none") {
            feed_item.css("display", "block");
        } else {
            feed_item.css("display", "none");
        }
    });

    $(document).on("click", "a.trigger-wrapper,#nav-previous,#nav-next", function(evt) {
        evt.preventDefault();
        var feed_id = $(this).data("feed-id");
        var entry_id = $(this).data("entry-id");
        var link = $(this).data("link");
        var title = $(this).data("title");
        var my_entry_item = $(this);
        History.pushState({id:entry_id}, title, "/explorer/"+entry_id);
        $("#frame").attr("src", link);
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
    });

    $(document).on('click', "#feed-source-list div.feed-item", function(evt) {
        evt.preventDefault();
        var feed_id = $(this).data("feed-id");
        var my_feed_item = $(this);
        var current_entry_id = $("#iframe-container").data("entry-id");
        $.post("/getfeedentries/", {current_entry_id: current_entry_id, feed_id: feed_id},
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
            $.post("/getuserfeeds/", {current_feed_id: feed_id},
                function(result) {
                    $(".main .box .row-fluid").prepend(result);
                    $("#iframe-container").removeClass("span12").addClass("span6");
                    $("iframe").css("width", "54.7%");
                    $("iframe").css("margin-left", "6px");
                    $('.row-fluid [class*="span"]').css("margin-left", "-0.436%", "important");
                    $.post("/getfeedentries/", {current_entry_id: entry_id, feed_id: feed_id},
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
                    $("#feed-source-list,#feed-entry-list").niceScroll({cursorcolor:"#555555", cursoropacitymax: "0.5"});
            });
        }
    });

    $(document).on('click', ".right-bar div.feed-items .feed-item", function(evt) {
        var my_feed_item = $(this).closest("div.feed-item");
        var feed_id = my_feed_item.data("feed-id");
        $(".right-bar .ajax-spinner").css("display", "block");
        $.post("/get_entries_by_feed_id/", {feed_id: feed_id},
            function(result) {
                $(".right-bar .ajax-spinner").css("display", "none");
                $("#dashboard .timeline").empty();
                $("#dashboard .timeline").append(result);
            }
        );
    });

    $(document).on('click', ".right-bar #live-stream", function(evt) {
        var my_feed_item = $(this);
        $(".right-bar .ajax-spinner").css("display", "block");
        $.post("/render_timeline_standalone/",
            function(result) {
                $(".right-bar .ajax-spinner").css("display", "none");
                $("#dashboard .timeline").empty();
                $("#dashboard .timeline").append(result);
            }
        );
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

    $(".unsubscribe-feed").click(function(evt) {
        evt.preventDefault();
        var feed_id = $(this).closest(".feed-item").data("feed-id");
        $.post("/unsubscribe/", {feed_id: feed_id},
            function(result) {
                if (result.code == "1") {
                    $(".right-bar-info-area").css("display", "block").delay(5000).fadeOut();
                    $(".right-bar-info-area").empty().append(result.text);
                    $(".feed-item[data-feed-id="+feed_id+"]").remove();
                } else {
                    $(".right-bar-info-area").append("An error occured, please try again later.");
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

    $(".subscribe-user-icon").click(function(evt) {
        evt.preventDefault();
        $.post("/subscribe_user/", {username: $(this).data("username")},
            function(result) {
                // FIXME: Processing gif is required.
                if (result == 1) {
                    $(".subscribe-user-icon").css("display", "none");
                    $(".unsubscribe-button").css("display", "block");
                } else {
                    // FIXME: Warning area is required.
                    console.log("hatalar oldu");
                }
            }
        );
    });

    $(".unsubscribe-button").click(function(evt) {
        evt.preventDefault();
        $.post("/unsubscribe_user/", {username: $(this).data("username")},
            // FIXME: Processing gif is required.
            function(result) {
                if (result == 1) {
                    $(".subscribe-user-icon").css("display", "block");
                    $(".unsubscribe-button").css("display", "none");
                }
            }
        );
    });

    $("#post-to-my-feed button").click(function(evt) {
        var feed_id = $("#iframe-container").data("feed-id");
        var entry_id = $("#iframe-container").data("entry-id");
        var note = $("#post-to-my-feed .make-textbox").html();
        $.post("/share_entry/", {note: note, entry_id: entry_id, feed_id: feed_id},
            function(result){
                console.log(result);
            }
        );
    });

    $(".fake-textbox").click(function(evt) {
        $(this).css("display", "none");
        $(".make-textbox").css("display", "block");
    });

    $(".right-bar div.feed-items").scroll(function(evt) {
        if ($(this).scrollTop() != 0) {
            $("#scrollable-sections-top-shadow").css("opacity", 1);
        } else {
            $("#scrollable-sections-top-shadow").css("opacity", 0);
        }
        if($(this).scrollTop() + $(this).innerHeight() >= $(this)[0].scrollHeight) {
            $("#scrollable-sections-bottom-shadow").css("opacity", 1);
        } else {
            $("#scrollable-sections-bottom-shadow").css("opacity", 0);
        }
    });

    $("#search-feed").click(function() {
        $(".subscribe-feed-box:visible").css("display", "none");
        $(".feed-search-box #id_feed_search").val('');
        if($(".feed-search-box:hidden").length) {
            $(".feed-search-box").css("display", "block")
        } else {
            $(".feed-search-box").css("display", "none");
        }
    });

    $("#subscribe-feed").click(function() {
        $(".feed-search-box:visible").css("display", "none");
        $(".subscribe-feed-box #id_feed_url").val('');
        if($(".subscribe-feed-box:hidden").length) {
            $(".subscribe-feed-box").css("display", "block")
        } else {
            $(".subscribe-feed-box").css("display", "none");
        }
    });

    var cache = {};
    $("#id_feed_search").autocomplete({
        minLength: 3,
        delay: 1000,
        source: function(request, response) {
            var term = request.term;
            if (term in cache) {
                response(cache[term]);
                return;
            }
            $(".right-bar .ajax-spinner").css("display", "block");
            $.getJSON("/get_user_subscriptions/", request, function(data, status, xhr) {
                $(".right-bar .ajax-spinner").css("display", "none");
                cache[term] = data;
                if (data.length == 0) {
                    $(".right-bar-info-area").css("display", "block").delay(3000).fadeOut();
                    $(".right-bar-info-area").empty().append("No result found for "+term);
                }
                response(data);
            });
        },
        select: function(event, ui) {
            $(".right-bar .ajax-spinner").css("display", "block");
            $.post("/get_entries_by_feed_id/", {feed_id: ui.item.id},
                function(result) {
                    $(".right-bar .ajax-spinner").css("display", "none");
                    $("#dashboard .timeline").empty();
                    $("#dashboard .timeline").append(result);
                    $(this).val('');
                    $(".feed-search-box").css("display", "none");
                }
            );
        }
    });

    $("#id_feed_url").keypress(function(evt) {
        if (evt.keyCode == 13) {
            $(this).closest("li.dropdown").removeClass("open");
            find_and_subscribe_feed();
        }
    });

    $(".subscribe-feed-box button,.subscribe-feed-dropdown button").click(function(evt) {
        find_and_subscribe_feed();
    });

    check_subscription();
    get_votes();
    get_previous_next_items();

    // Initialize tooltips
    $(".subscribe-user-icon").tooltip();
    $('#live-stream').tooltip();
    $('#search-feed').tooltip();
    $('#subscribe-feed').tooltip();

    // Initialize custom scrollbars
    $(".right-bar .feed-items").niceScroll({cursorcolor:"#555555", cursoropacitymax: "0.5"});

    $('.dropdown-toggle').dropdown();
});