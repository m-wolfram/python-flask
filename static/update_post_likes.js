$(document).ready(function() {
    $(document).on('click', '.btn-link.no-underline', function() {
        const post_id = $(this).attr('post_id');

        request = $.ajax({
            url: '/leave_message/posts/like',
            type: 'GET',
            data: {
                post_id: post_id
            }
        })
        .done(function(data) {
            $('#like_'+post_id).html(data);
        });
    });
});