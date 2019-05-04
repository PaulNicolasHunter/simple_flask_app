function remove_or_wish_it(ele, rem, tab){

    if (rem === 1) {
       var url = '/remove_it'; // from recent and wish list
    }
    else {
       var url = '/add_wishlist'; // from recent and wish list
    }
    var id = $(ele).attr('id');

    $.ajax({
        type: "POST",
        dataType: "json",
        url: url,
        data: {"id": id, "table": tab},
    });
    if (rem === 1) {
        location.reload();
    }
}

