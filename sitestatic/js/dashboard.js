$(document).ready(function(){
    $('.search-query').typeahead(
        [{
            remote: '/api/subs-search/%QUERY',
            template: '<p class="search-result">{{value}}</p>',
            engine: Hogan
        }]
    ).on('typeahead:selected', function($e, data) {
        window.location.href = "/feed/"+data.id;
        // FIXME: Prevent sending a request again to subs-search
    });

    /*
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
    $(document).on('click', '.dropdown-menu', function(e) {
        e.preventDefault();
        e.stopPropagation();
    }); */

    // Initialize bootstrap tooltips
    $("#header .link-signout i.signout-button").tooltip();
});

