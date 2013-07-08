$(document).ready(function() {
    $(".dropdown-menu").click(function() {
        var submenu = $(this).closest(".dropdown").find(".submenu");

        if($(this).attr('id') == 1) {
            submenu.hide();
            $(this).attr('id', '0');
        } else {
            submenu.show();
            $(this).attr('id', '1');
        }
    });

    //Mouse click on sub menu
    /*$(".submenu").mouseup(function() {
        console.log("submenu mouse up");
        return false
    });

    $(".dropdown-menu").mouseup(function() {
        console.log("dropdown-menu mouse up");
        return false
    });*/

    $(document).on('.dropdown-entries .entry', 'click', function(event) {
        $(".submenu").hide();
        $(".dropdown-menu").attr('id', '');
    });

    //Document Click
    $(document).mouseup(function() {
        $(".submenu").hide();
        $(".dropdown-menu").attr('id', '');
    });
});