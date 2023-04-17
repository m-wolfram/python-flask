function copyToClipboard(TextElementID) {
    var copyText = document.getElementById(TextElementID);

    copyText.select();
    copyText.setSelectionRange(0, 99999); // For mobile devices

    try {
        navigator.clipboard.writeText(copyText.value);
    } catch (e) {
        console.log("Probably there's no SSL certificates.");
    }
}