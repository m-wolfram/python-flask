const registrationForm = document.getElementById("registration_form");
const registrationFormResetButton = document.getElementById("reset_registration_form");

registrationFormResetButton.addEventListener("click", () => {
    registrationForm.reset();
});
