// INEC Underage Eradicator - Main JS

document.addEventListener('DOMContentLoaded', () => {
    // Dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });

    // File input preview helpers
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name;
            const helpText = this.nextElementSibling;
            if (fileName && helpText && helpText.classList.contains('form-text')) {
                helpText.textContent = `Selected: ${fileName}`;
                helpText.style.color = 'var(--primary)';
            }
        });
    });

    // Biometric capture helper (simulating interactions)
    const videoElements = document.querySelectorAll('.biometric-preview');
    if (videoElements.length > 0 && navigator.mediaDevices) {
        // Just an aesthetic addition to show "live feed" or placeholder in a real app
    }
});
