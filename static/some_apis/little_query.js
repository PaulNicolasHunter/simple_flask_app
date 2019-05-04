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
    } else {
        alert('Item has been added to your wishlist :)');
    }
}

$("#e_mail").keydown(function(){
    mail_me();
});

function mail_me(){

    $.ajax({
        type: "POST",
        dataType: "json",
        url: '/mail_me',
        data: {"mail": $('#e_mail').val()},
    });

    alert('Please check your mail :)');
}


