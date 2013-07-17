$(document).ready(function() {
    function hide_scrollbar() {
        $(".subscriptions").getNiceScroll().hide();
        $(".entries").getNiceScroll().hide();
        $(".comments").getNiceScroll().hide();
    }

    $(".dropdown-menu").click(function() {
        var submenu = $(this).closest(".dropdown").find(".submenu");

        if($(this).attr('id') == 1) {
            hide_scrollbar();
            submenu.hide();
            $(this).attr('id', '0');
        } else {
            submenu.show();
            $(this).attr('id', '1');
            $(".subscriptions").getNiceScroll().show();
            $(".entries").getNiceScroll().show();
            $(".comments").getNiceScroll().show();
            /*
            $(".entries").niceScroll({cursorcolor:"#555555", cursoropacitymax: "0.5"});
            $(".subscriptions").niceScroll({cursorcolor:"#555555", cursoropacitymax: "0.5"});
            */
        }
    });

    //Mouse click on sub menu
    $(".submenu").mouseup(function() {
        return false
    });

    $(".dropdown-menu").mouseup(function() {
        return false
    });

    $(document).on('click', '.dropdown-entries .entry', function(event) {
        hide_scrollbar();
        $(".submenu").hide();
        $(".dropdown-menu").attr('id', '');
    });

    //Document Click
    $(document).mouseup(function() {
        hide_scrollbar();
        $(".submenu").hide();
        $(".dropdown-menu").attr('id', '');
    });
});