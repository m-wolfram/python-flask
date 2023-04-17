function copyToClipboard(TextElementID) {
    var copyText = document.getElementById(TextElementID);

    copyText.select();
    copyText.setSelectionRange(0, 99999); // For mobile devices

    document.execCommand("copy");
}