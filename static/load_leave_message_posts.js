const cardContainer = document.getElementById("posts-container");
const loadMoreButton = document.getElementById("load-more");
const cardCountElem = document.getElementById("posts-count");
const cardTotalElem = document.getElementById("posts-total");


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
            cardCountElem.innerHTML = postsPerPage;
            cardTotalElem.innerHTML = postsCount;
        });

        loadMoreButton.addEventListener("click", () => {
            currentPage += 1;

            $.ajax({
                url: '/leave_message/posts',
                type: 'GET',
                data: {
                    page: currentPage
                }
            })
            .done(function(data) {
                cardContainer.innerHTML += data;
                if (currentPage === pagesCount) {
                    loadMoreButton.classList.replace("btn-primary", "btn-secondary");
                    loadMoreButton.classList.add("disabled");
                    loadMoreButton.setAttribute("disabled", true);
                    cardCountElem.innerHTML = (currentPage-1) * postsPerPage + postsCount - (currentPage-1) * postsPerPage;
                }
                else {
                    cardCountElem.innerHTML = postsPerPage * currentPage;
                };
            });
        });
    });
};