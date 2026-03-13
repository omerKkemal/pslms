// action.js - Enhanced version

// DOM elements
const loading = document.getElementById("loading");
const content1 = document.getElementById("content1");
const content2 = document.getElementById("content2");
const note = document.getElementById("note");
const noteTitle = document.getElementById("title");
const noteSubject = document.getElementById("subject");

// Hide loading spinner and show content on page load
window.addEventListener('load', () => {
    if (loading) loading.style.display = "none";
    if (content1) content1.style.display = "initial";
    if (content2) content2.style.display = "initial";
});

/**
 * Show loading spinner and hide main content
 */
function loading_animation() {
    if (loading) loading.style.display = "flex";
    if (content1) content1.style.display = "none";
    if (content2) content2.style.display = "none";
}

/**
 * Navigate back to previous page
 */
function goBack() {
    if (document.referrer) {
        window.location.href = document.referrer;
    } else {
        window.history.back(); // fallback
    }
}

/**
 * Show loading spinner and go back
 */
function loading_back() {
    loading_animation();
    // Use setTimeout to ensure spinner is shown before navigation
    setTimeout(goBack, 50);
}

/**
 * Show notification popup
 * @param {string} message - The message to display
 * @param {string} type - 'success', 'error', 'info' (default 'info')
 * @param {number} duration - milliseconds to show (default 3000)
 */
function showNotification(message, type = 'info', duration = 3000) {
    if (!note || !noteTitle || !noteSubject) return;

    // Set colors based on type
    const colors = {
        success: { bg: 'bg-green-500', border: 'border-green-700' },
        error: { bg: 'bg-red-500', border: 'border-red-700' },
        info: { bg: 'bg-blue-500', border: 'border-blue-700' }
    };
    const color = colors[type] || colors.info;

    // Apply classes (if using Tailwind)
    note.className = `fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 ${color.bg} text-white rounded-lg p-4 shadow-lg z-50 w-11/12 max-w-sm ${color.border} border-l-4`;
    
    noteTitle.textContent = type.charAt(0).toUpperCase() + type.slice(1);
    noteSubject.textContent = message;
    note.style.display = 'block';

    // Auto-hide after duration
    setTimeout(() => {
        note.style.display = 'none';
    }, duration);
}

// Legacy notification function (kept for backward compatibility)
function notifcation(subject, stute) {
    showNotification(subject, stute === 'error' ? 'error' : 'success');
}

/**
 * Toggle dropdown menu
 * Assumes dropdown element with id 'drop'
 */
function dropdown() {
    const dropdown = document.getElementById('drop');
    if (dropdown) {
        dropdown.classList.toggle('show');
    }
}

// Close dropdown when clicking outside
window.addEventListener('click', function(event) {
    const dropdown = document.getElementById('drop');
    if (!dropdown) return;
    
    if (!event.target.matches('.btn') && !dropdown.contains(event.target)) {
        dropdown.classList.remove('show');
    }
});

// Optional: Add a utility function for AJAX delete operations (if used)
function _delete(id, type) {
    if (confirm('Are you sure you want to delete this item?')) {
        // Implement your delete logic here
        console.log('Delete', id, type);
        // Example: fetch(`/delete/${type}/${id}`, { method: 'POST' })
        //     .then(response => response.json())
        //     .then(data => {
        //         if (data.success) showNotification('Deleted successfully', 'success');
        //         else showNotification('Delete failed', 'error');
        //     });
    }
}

// For flaskApi_Delete (used in view_resources.html)
function flaskApi_Delete(id, type) {
    _delete(id, type);
}