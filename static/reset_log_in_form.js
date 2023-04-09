const form = document.getElementById("log_in_form");
const formResetButton = document.getElementById("reset_log_in_form");

formResetButton.addEventListener("click", () => {
    form.reset();
});
