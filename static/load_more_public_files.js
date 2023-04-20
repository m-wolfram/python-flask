const scriptTag = document.getElementById("load_more_public_files_script");
const publicFilesContainer = document.getElementById("public-files-container");
const loadMoreButton = document.getElementById("load-more");
const publicFilesCountElem = document.getElementById("public-files-count");
const publicFilesTotalElem = document.getElementById("public-files-total");


const isForUser = +scriptTag.getAttribute("for_user");
let currentPage = 1;
let publicFilesCount, publicFilesPerPage, pagesCount;


function switchLoadMoreButton() {
    loadMoreButton.classList.replace("btn-primary", "btn-secondary");
    loadMoreButton.classList.add("disabled");
    loadMoreButton.setAttribute("disabled", true);
};

window.onload = function() {
    $.ajax({
        url: '/public_files/parameters',
        type: 'GET',
        data: {
            for_user: isForUser
        }
    })
    .done(function(data) {
        // on first page load
        publicFilesCount = data["public_files_count"];
        publicFilesPerPage = data["public_files_per_page"];
        pagesCount = Math.ceil(publicFilesCount / publicFilesPerPage);

        $.ajax({
            url: '/public_files/load_files',
            type: 'GET',
            data: {
                page: currentPage,
                for_user: isForUser
            }
        })
        .done(function(data) {
            publicFilesContainer.innerHTML = data;
            publicFilesCountElem.innerHTML = publicFilesContainer.childElementCount;
            publicFilesTotalElem.innerHTML = publicFilesCount;
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
        url: '/public_files/load_files',
        type: 'GET',
        data: {
            page: currentPage,
            for_user: isForUser
        }
    })
    .done(function(data) {
        publicFilesContainer.innerHTML += data;
        publicFilesCountElem.innerHTML = publicFilesContainer.childElementCount;

        if (currentPage === pagesCount) {
            switchLoadMoreButton()
        };
    });
});