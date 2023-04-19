const cardContainer = document.getElementById("posts-container");
const loadMoreButton = document.getElementById("load-more");
const cardCountElem = document.getElementById("posts-count");
const cardTotalElem = document.getElementById("posts-total");


let currentPage = 1;
let postsCount, postsPerPage, pagesCount;


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
        postsCount = data["posts_count"];
        postsPerPage = data["posts_per_page"];
        pagesCount = Math.ceil(postsCount / postsPerPage);

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
    });
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