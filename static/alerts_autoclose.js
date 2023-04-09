const alerts = document.querySelectorAll('#alert')

alerts.forEach(function(alert) {
        new bootstrap.Alert(alert);

        setTimeout(() => {
            bootstrap.Alert.getInstance(alert).close();
        }, 3000);
});