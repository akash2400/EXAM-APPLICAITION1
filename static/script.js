// Custom JavaScript for AI Exam System

// Global variables
let currentUser = null;
let examSession = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    setupAnimations();
});

// Initialize application
function initializeApp() {
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
    
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

// Setup event listeners
function setupEventListeners() {
    // Form validation
    setupFormValidation();
    
    // Auto-save functionality for exam answers
    setupAutoSave();
    
    // Keyboard shortcuts
    setupKeyboardShortcuts();
    
    // Print functionality
    setupPrintFunctionality();
}

// Setup form validation
function setupFormValidation() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
                
                // Show validation errors
                showValidationErrors(form);
            }
            form.classList.add('was-validated');
        });
    });
}

// Show validation errors
function showValidationErrors(form) {
    const invalidFields = form.querySelectorAll(':invalid');
    invalidFields.forEach(field => {
        field.classList.add('is-invalid');
        
        // Add error message if not exists
        if (!field.nextElementSibling || !field.nextElementSibling.classList.contains('invalid-feedback')) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            errorDiv.textContent = field.validationMessage || 'This field is required.';
            field.parentNode.appendChild(errorDiv);
        }
    });
}

// Setup auto-save for exam answers
function setupAutoSave() {
    const answerInputs = document.querySelectorAll('.answer-input');
    answerInputs.forEach(input => {
        input.addEventListener('input', debounce(function() {
            saveAnswerToLocalStorage(this);
        }, 1000));
        
        // Load saved answer on page load
        loadAnswerFromLocalStorage(input);
    });
}

// Save answer to localStorage
function saveAnswerToLocalStorage(input) {
    const examId = document.querySelector('input[name="exam_id"]')?.value;
    const questionId = input.id;
    const answer = input.value;
    
    if (examId && questionId && answer) {
        const key = `exam_${examId}_question_${questionId}`;
        localStorage.setItem(key, answer);
        
        // Show save indicator
        showSaveIndicator(input);
    }
}

// Load answer from localStorage
function loadAnswerFromLocalStorage(input) {
    const examId = document.querySelector('input[name="exam_id"]')?.value;
    const questionId = input.id;
    
    if (examId && questionId) {
        const key = `exam_${examId}_question_${questionId}`;
        const savedAnswer = localStorage.getItem(key);
        
        if (savedAnswer) {
            input.value = savedAnswer;
            input.dispatchEvent(new Event('input')); // Trigger input event to update progress
        }
    }
}

// Show save indicator
function showSaveIndicator(input) {
    // Remove existing indicator
    const existingIndicator = input.parentNode.querySelector('.save-indicator');
    if (existingIndicator) {
        existingIndicator.remove();
    }
    
    // Create new indicator
    const indicator = document.createElement('div');
    indicator.className = 'save-indicator text-success small mt-1';
    indicator.innerHTML = '<i class="fas fa-check me-1"></i>Saved';
    input.parentNode.appendChild(indicator);
    
    // Remove after 3 seconds
    setTimeout(() => {
        if (indicator.parentNode) {
            indicator.remove();
        }
    }, 3000);
}

// Setup keyboard shortcuts
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter to submit form
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            const submitBtn = document.querySelector('button[type="submit"]');
            if (submitBtn && submitBtn.offsetParent !== null) {
                submitBtn.click();
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            });
        }
    });
}

// Setup print functionality
function setupPrintFunctionality() {
    const printButtons = document.querySelectorAll('[onclick*="window.print"]');
    printButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            printPage();
        });
    });
}

// Print page
function printPage() {
    // Add print-specific styles
    const style = document.createElement('style');
    style.textContent = `
        @media print {
            .no-print { display: none !important; }
            .print-break { page-break-before: always; }
        }
    `;
    document.head.appendChild(style);
    
    // Print
    window.print();
    
    // Remove print styles
    document.head.removeChild(style);
}

// Setup animations
function setupAnimations() {
    // Intersection Observer for scroll animations
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                }
            });
        });
        
        const animatedElements = document.querySelectorAll('.card, .alert, .btn');
        animatedElements.forEach(el => observer.observe(el));
    }
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Show notification
function showNotification(message, type = 'info', duration = 5000) {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.custom-notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Create notification
    const notification = document.createElement('div');
    notification.className = `custom-notification alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
    `;
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after duration
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, duration);
}

// Confirm action
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Validate CSV file
function validateCSVFile(file) {
    const allowedTypes = ['text/csv', 'application/csv'];
    const maxSize = 5 * 1024 * 1024; // 5MB
    
    if (!allowedTypes.includes(file.type) && !file.name.endsWith('.csv')) {
        showNotification('Please select a valid CSV file.', 'error');
        return false;
    }
    
    if (file.size > maxSize) {
        showNotification('File size must be less than 5MB.', 'error');
        return false;
    }
    
    return true;
}

// Update file name display
function updateFileName(examId, input) {
    const fileInfo = document.getElementById(`fileInfo${examId}`);
    const fileName = document.getElementById(`fileName${examId}`);
    
    if (input.files && input.files[0]) {
        const file = input.files[0];
        fileName.textContent = file.name;
        fileInfo.style.display = 'block';
        
        // Validate file
        if (!validateCSVFile(file)) {
            fileInfo.style.display = 'none';
            input.value = '';
        }
    } else {
        fileInfo.style.display = 'none';
    }
}

// Open upload modal with proper handling
function openUploadModal(examId) {
    console.log('Opening upload modal for exam:', examId);
    
    const modalId = `uploadModal${examId}`;
    const modal = document.getElementById(modalId);
    
    if (!modal) {
        console.error('Modal not found:', modalId);
        showNotification('Error: Modal not found', 'error');
        return;
    }
    
    // Remove any existing modal instances and backdrops
    const existingModal = bootstrap.Modal.getInstance(modal);
    if (existingModal) {
        existingModal.dispose();
    }
    
    // Remove any existing backdrops
    const existingBackdrops = document.querySelectorAll('.modal-backdrop');
    existingBackdrops.forEach(backdrop => backdrop.remove());
    
    // Create new modal instance WITHOUT backdrop
    const newModal = new bootstrap.Modal(modal, {
        backdrop: false,  // NO backdrop to prevent shadowing
        keyboard: true,
        focus: true
    });
    
    // Show modal
    newModal.show();
    
    // Ensure modal is visible and properly positioned
    setTimeout(() => {
        modal.style.display = 'block';
        modal.classList.add('show');
        modal.style.zIndex = '9999';
        
        // Remove modal-open class to prevent body scrolling issues
        document.body.classList.remove('modal-open');
        
        console.log('Modal opened without backdrop - should be fully interactive');
        
        // Add click outside to close functionality
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeUploadModal(examId);
            }
        });
    }, 100);
}

// Close upload modal
function closeUploadModal(examId) {
    const modalId = `uploadModal${examId}`;
    const modal = document.getElementById(modalId);
    
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
        
        // Remove any remaining backdrops
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => backdrop.remove());
        
        console.log('Modal closed');
    }
}

// Ensure modal opens properly
function ensureModalOpen(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        // Remove any existing modal instances
        const existingModal = bootstrap.Modal.getInstance(modal);
        if (existingModal) {
            existingModal.dispose();
        }
        
        // Create new modal instance
        const newModal = new bootstrap.Modal(modal, {
            backdrop: true,
            keyboard: true,
            focus: true
        });
        
        // Show modal
        newModal.show();
        
        // Ensure modal is visible
        modal.style.display = 'block';
        modal.classList.add('show');
        
        // Add backdrop if not present
        if (!document.querySelector('.modal-backdrop')) {
            const backdrop = document.createElement('div');
            backdrop.className = 'modal-backdrop fade show';
            backdrop.style.zIndex = '1054';
            document.body.appendChild(backdrop);
        }
    }
}

// CSV Upload functionality
function uploadCSV(examId) {
    console.log('uploadCSV called with examId:', examId);
    
    const formData = new FormData();
    const fileInput = document.getElementById(`csvFile${examId}`);
    
    if (!fileInput) {
        console.error('File input not found for examId:', examId);
        showNotification('Error: File input not found', 'error');
        return;
    }
    
    if (!fileInput.files[0]) {
        showNotification('Please select a CSV file', 'error');
        return;
    }
    
    const file = fileInput.files[0];
    console.log('Selected file:', file.name, 'Size:', file.size, 'Type:', file.type);
    
    // Validate file
    if (!validateCSVFile(file)) {
        return;
    }
    
    formData.append('csv_file', file);
    
    // Show loading state
    const uploadBtn = document.querySelector(`#uploadModal${examId} .btn-primary`);
    if (!uploadBtn) {
        console.error('Upload button not found');
        showNotification('Error: Upload button not found', 'error');
        return;
    }
    
    const originalText = uploadBtn.innerHTML;
    uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Uploading...';
    uploadBtn.disabled = true;
    
    console.log('Starting upload to:', `/admin/upload_csv/${examId}`);
    
    fetch(`/admin/upload_csv/${examId}`, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        console.log('Response status:', response.status);
        console.log('Response headers:', response.headers);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        if (data.error) {
            showNotification('Error: ' + data.error, 'error');
        } else {
            showNotification('Success: ' + data.message, 'success');
            // Close modal and reload
            const modal = bootstrap.Modal.getInstance(document.getElementById(`uploadModal${examId}`));
            if (modal) {
                modal.hide();
            }
            setTimeout(() => location.reload(), 1000);
        }
    })
    .catch(error => {
        console.error('Upload error:', error);
        showNotification('An error occurred while uploading the file: ' + error.message, 'error');
    })
    .finally(() => {
        // Reset button state
        if (uploadBtn) {
            uploadBtn.innerHTML = originalText;
            uploadBtn.disabled = false;
        }
    });
}

// Export functions to global scope for use in templates
window.AIExamSystem = {
    showNotification,
    confirmAction,
    formatDate,
    formatFileSize,
    validateCSVFile,
    debounce,
    uploadCSV,
    updateFileName,
    ensureModalOpen,
    openUploadModal,
    closeUploadModal
};
