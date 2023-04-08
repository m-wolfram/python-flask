$(function() {
    let script_tag = document.getElementById('scroll_to_element');
    let element_id = script_tag.getAttribute("element_id")
    let delay = script_tag.getAttribute("delay")
    $("html, body").animate({ scrollTop: $("#" + element_id).offset().top }, +delay);
});