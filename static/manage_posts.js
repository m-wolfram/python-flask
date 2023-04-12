const cardContainer = document.getElementById("posts-container");
const loadMoreButton = document.getElementById("load-more");
const cardCountElem = document.getElementById("posts-count");
const cardTotalElem = document.getElementById("posts-total");


let currentPage = 1;

function switchLoadMoreButton() {
    loadMoreButton.classList.replace("btn-primary", "btn-secondary");
    loadMoreButton.classList.add("disabled");
    loadMoreButton.setAttribute("disabled", true);
};

window.onload = function() {
    $.ajax({
        url: '/leave_message/posts/parameters',
        type: 'GET'
    })
    .done(function(data) {
        // on first page load
        const postsCount = data["posts_count"];
        const postsPerPage = data["posts_per_page"];
        const pagesCount = Math.ceil(postsCount / postsPerPage);

        $.ajax({
            url: '/leave_message/posts/load_posts',
            type: 'GET',
            data: {
                page: currentPage
            }
        })
        .done(function(data) {
            cardContainer.innerHTML = data;
            cardCountElem.innerHTML = cardContainer.childElementCount;
            cardTotalElem.innerHTML = postsCount;
        });

        // load more
        if (pagesCount <= 1) {
            switchLoadMoreButton()
        };

        loadMoreButton.addEventListener("click", () => {
            currentPage += 1;

            $.ajax({
                url: '/leave_message/posts/load_posts',
                type: 'GET',
                data: {
                    page: currentPage
                }
            })
            .done(function(data) {
                cardContainer.innerHTML += data;
                cardCountElem.innerHTML = cardContainer.childElementCount;
                if (currentPage === pagesCount) {
                    switchLoadMoreButton()
                };
            });
        });

        // delete post button
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
    });
};