const leaveMessageForm = document.getElementById("send_message_form");
const clearButton = document.getElementById("clear_send_message_form");

clearButton.addEventListener("click", () => {
    leaveMessageForm.reset();
});
