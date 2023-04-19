$(document).on('click', '.btn-sm.btn-close.shadow-none', function() {
    let postCard = $(this).closest('.card.mb-3');
    let postID = postCard.attr('id').match(/post(\d+)/)[1]; // get post id

    $.ajax({
        url: '/leave_message/posts/delete/' + postID,
        type: 'DELETE'
    })
    .done(function() {
        postCard.remove();

        $.ajax({
            url: '/leave_message/posts/load_posts',
            type: 'GET',
            data: {
                page: currentPage,
                index: -1
            }
        })
        .done(function(data) {
            cardContainer.innerHTML += data;

            $("#posts-total").text(function(i, oldText) {
                return +oldText - 1
            });
            $("#posts-count").text(cardContainer.childElementCount);

            if (+$("#posts-total").text() === cardContainer.childElementCount) {
                switchLoadMoreButton();
            };
        });
    });
});