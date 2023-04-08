$(document).ready(function() {
    $(document).on('click', '.btn-link', function() {
        var page = $(this).attr('page');
        var post_id = $(this).attr('post_id');

        request = $.ajax({
            url: '/leave_message/like',
            type: 'POST',
            data: {page: page, post_id: post_id}
        })
        .done(function(data) {
            $('#like_'+post_id).html(data);
        });
    });
});