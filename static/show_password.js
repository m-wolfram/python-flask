$(document).ready(function() {
    $(".toggle_hide_password").on('click', function(e) {
        e.preventDefault()
        let input_group = $(this).closest('.input-group')
        let input = input_group.find('input.form-control')
        let icon = input_group.find('i')
        input.attr('type', input.attr("type") === "text" ? 'password' : 'text')
        icon.toggleClass('bi-eye-slash-fill bi-eye-fill')
    })
})