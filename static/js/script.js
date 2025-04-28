document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Dynamic date pickers
    const dateInputs = document.querySelectorAll('.datepicker');
    dateInputs.forEach(input => {
        new Datepicker(input, {
            format: 'yyyy-mm-dd',
            autohide: true
        });
    });

    // Time pickers
    const timeInputs = document.querySelectorAll('.timepicker');
    timeInputs.forEach(input => {
        new Timepicker(input, {
            showMeridian: false,
            defaultTime: 'current'
        });
    });

    // Auto-dismiss flash messages after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => alert.remove(), 150);
        }, 5000);
    });
});

// AJAX functions
function fetchMemberDetails(memberId) {
    fetch(`/api/members/${memberId}`)
        .then(response => response.json())
        .then(data => {
            // Process member data
            console.log(data);
        });
}

function updateAttendance(attendanceId, attended) {
    fetch(`/api/attendance/${attendanceId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ attended: attended })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Attendance updated successfully', 'success');
        } else {
            showToast('Error updating attendance', 'danger');
        }
    });
}

// Toast notifications
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.style.position = 'fixed';
        container.style.top = '20px';
        container.style.right = '20px';
        container.style.zIndex = '1100';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0 show`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    document.getElementById('toastContainer').appendChild(toast);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 150);
    }, 3000);
}

// Password strength indicator
function checkPasswordStrength(password) {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (password.match(/[a-z]+/)) strength++;
    if (password.match(/[A-Z]+/)) strength++;
    if (password.match(/[0-9]+/)) strength++;
    if (password.match(/[!@#$%^&*(),.?":{}|<>]+/)) strength++;
    return strength;
}

// Update password strength indicator on registration page
const passwordInput = document.getElementById('password');
if (passwordInput) {
    const strengthIndicator = document.createElement('div');
    strengthIndicator.className = 'progress mt-2';
    strengthIndicator.innerHTML = '<div class="progress-bar" role="progressbar" style="width: 0%"></div>';
    passwordInput.parentNode.appendChild(strengthIndicator);

    passwordInput.addEventListener('input', function() {
        const strength = checkPasswordStrength(this.value);
        const progressBar = strengthIndicator.querySelector('.progress-bar');
        progressBar.style.width = `${strength * 20}%`;
        
        if (strength <= 2) {
            progressBar.className = 'progress-bar bg-danger';
        } else if (strength <= 3) {
            progressBar.className = 'progress-bar bg-warning';
        } else {
            progressBar.className = 'progress-bar bg-success';
        }
    });
}

// Date range validation for class scheduling
function validateDateRange() {
    const startDate = document.getElementById('start_date')?.value;
    const endDate = document.getElementById('end_date')?.value;
    
    if (startDate && endDate && startDate > endDate) {
        alert('End date must be after start date');
        return false;
    }
    return true;
}

// Phone number formatting
const phoneInputs = document.querySelectorAll('input[type="tel"]');
phoneInputs.forEach(input => {
    input.addEventListener('input', function(e) {
        let x = e.target.value.replace(/\D/g, '').match(/(\d{0,3})(\d{0,3})(\d{0,4})/);
        e.target.value = !x[2] ? x[1] : `(${x[1]}) ${x[2]}${x[3] ? `-${x[3]}` : ''}`;
    });
}

// Enable tooltips everywhere
const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
});