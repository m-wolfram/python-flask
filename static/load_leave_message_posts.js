const cardContainer = document.getElementById("posts-container");
const loadMoreButton = document.getElementById("load-more");

let currentPage = 1;

window.onload = function() {
    $.ajax({
        url: '/leave_message/posts_parameters',
        type: 'GET'
    })
    .done(function(data) {
        const postsCount = data["posts_count"];
        const postsPerPage = data["posts_per_page"];
        const pagesCount = Math.ceil(postsCount / postsPerPage);

        $.ajax({
            url: '/leave_message/posts',
            type: 'GET',
            data: {
                page: currentPage
            }
        })
        .done(function(data) {
            cardContainer.innerHTML = data;
        });

        loadMoreButton.addEventListener("click", () => {
            currentPage += 1;

            if (currentPage === pagesCount) {
                loadMoreButton.classList.replace("btn-primary", "btn-secondary");
                loadMoreButton.classList.add("disabled");
                loadMoreButton.setAttribute("disabled", true);
            };

            $.ajax({
                url: '/leave_message/posts',
                type: 'GET',
                data: {
                    page: currentPage
                }
            })
            .done(function(data) {
                cardContainer.innerHTML += data;
            });
        });
    });
};