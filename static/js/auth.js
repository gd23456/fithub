// Password functionality
document.addEventListener('DOMContentLoaded', function() {
    // Function to toggle password visibility
    function setupPasswordToggle(buttonId, inputId) {
        const toggleButton = document.getElementById(buttonId);
        if (toggleButton) {
            toggleButton.addEventListener('click', function() {
                const input = document.getElementById(inputId);
                const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
                input.setAttribute('type', type);
                
                // Toggle the eye icon
                const icon = this.querySelector('i');
                icon.classList.toggle('bi-eye');
                icon.classList.toggle('bi-eye-slash');
            });
        }
    }

    // Setup toggle for both password fields
    setupPasswordToggle('togglePassword', 'password');
    setupPasswordToggle('toggleConfirmPassword', 'confirm_password');

    // Password validation
    const password = document.getElementById('password');
    if (password) {
        password.addEventListener('input', function() {
            const value = this.value;
            
            // Update requirement checks
            document.getElementById('length').innerHTML = 
                `<i class="bi bi-${value.length >= 8 ? 'check-circle text-success' : 'x-circle text-danger'}"></i> At least 8 characters`;
            
            document.getElementById('uppercase').innerHTML = 
                `<i class="bi bi-${/[A-Z]/.test(value) ? 'check-circle text-success' : 'x-circle text-danger'}"></i> One uppercase letter`;
            
            document.getElementById('lowercase').innerHTML = 
                `<i class="bi bi-${/[a-z]/.test(value) ? 'check-circle text-success' : 'x-circle text-danger'}"></i> One lowercase letter`;
            
            document.getElementById('number').innerHTML = 
                `<i class="bi bi-${/[0-9]/.test(value) ? 'check-circle text-success' : 'x-circle text-danger'}"></i> One number`;
            
            document.getElementById('special').innerHTML = 
                `<i class="bi bi-${/[@$!%*?&]/.test(value) ? 'check-circle text-success' : 'x-circle text-danger'}"></i> One special character`;
        });
    }

    // Password confirmation validation
    const confirmPassword = document.getElementById('confirm_password');
    if (confirmPassword) {
        confirmPassword.addEventListener('input', function() {
            const passwordMatch = document.getElementById('passwordMatch');
            if (this.value === password.value) {
                passwordMatch.innerHTML = '<span class="text-success"><i class="bi bi-check-circle"></i> Passwords match</span>';
                this.setCustomValidity('');
            } else {
                passwordMatch.innerHTML = '<span class="text-danger"><i class="bi bi-x-circle"></i> Passwords do not match</span>';
                this.setCustomValidity('Passwords do not match');
            }
        });
    }
});
