// Main JavaScript for TradingView Access Management

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert:not(.alert-danger)');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const submitBtn = e.submitter;
            if (submitBtn) {
                // Add loading state
                submitBtn.classList.add('loading');
                submitBtn.disabled = true;
                
                // Re-enable after 3 seconds as fallback
                setTimeout(function() {
                    submitBtn.classList.remove('loading');
                    submitBtn.disabled = false;
                }, 3000);
            }
        });
    });

    // Pine ID validation
    const pineIdInput = document.getElementById('pine_ids');
    if (pineIdInput) {
        pineIdInput.addEventListener('blur', function() {
            validatePineIds(this.value);
        });
    }

    // Username input formatting
    const usernameInput = document.getElementById('username');
    if (usernameInput) {
        usernameInput.addEventListener('input', function() {
            // Remove spaces and convert to lowercase for consistency
            this.value = this.value.trim();
        });
    }
});

function validatePineIds(value) {
    const pineIdPattern = /^PUB;[a-f0-9]{32}$/;
    const ids = value.split(',').map(id => id.trim()).filter(id => id);
    
    let isValid = true;
    const invalidIds = [];
    
    ids.forEach(function(id) {
        if (!pineIdPattern.test(id)) {
            isValid = false;
            invalidIds.push(id);
        }
    });
    
    const pineIdInput = document.getElementById('pine_ids');
    if (!isValid && invalidIds.length > 0) {
        pineIdInput.classList.add('is-invalid');
        
        // Show validation message
        let feedback = pineIdInput.parentNode.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            pineIdInput.parentNode.appendChild(feedback);
        }
        feedback.textContent = 'Invalid Pine ID format: ' + invalidIds.join(', ');
    } else {
        pineIdInput.classList.remove('is-invalid');
        const feedback = pineIdInput.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.remove();
        }
    }
    
    return isValid;
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showToast('Copied to clipboard!', 'success');
    }).catch(function(err) {
        console.error('Could not copy text: ', err);
        showToast('Failed to copy to clipboard', 'error');
    });
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(function() {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 3000);
}

// Confirm dangerous operations
function confirmAction(message) {
    return confirm(message || 'Are you sure you want to perform this action?');
}

// Handle remove access with confirmation
document.addEventListener('click', function(e) {
    if (e.target.matches('button[name="action"][value="remove"]') || 
        e.target.closest('button[name="action"][value="remove"]')) {
        if (!confirmAction('Are you sure you want to remove access for this user? This action cannot be undone.')) {
            e.preventDefault();
        }
    }
});

// Auto-refresh functionality for dashboard
if (window.location.pathname === '/') {
    // Refresh recent activity every 30 seconds
    setInterval(function() {
        // Only refresh if page is visible
        if (!document.hidden) {
            // This would require an AJAX endpoint - simplified for now
            console.log('Auto-refresh would happen here');
        }
    }, 30000);
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + Enter to submit forms
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const activeForm = document.activeElement.closest('form');
        if (activeForm) {
            const submitBtn = activeForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.click();
            }
        }
    }
});
