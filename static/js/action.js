// action.js - Enhanced version with full functionality

// DOM elements
const pageLoader = document.getElementById("page-loader");
const note = document.getElementById("note");
const noteTitle = document.getElementById("title");
const noteSubject = document.getElementById("subject");

function showPageLoader() {
    if (!pageLoader) return;
    pageLoader.hidden = false;
    pageLoader.setAttribute('aria-hidden', 'false');
    document.body.setAttribute('aria-busy', 'true');
}

function hidePageLoader() {
    if (!pageLoader) return;
    pageLoader.hidden = true;
    pageLoader.setAttribute('aria-hidden', 'true');
    document.body.removeAttribute('aria-busy');
}

window.addEventListener('pageshow', hidePageLoader);

function loading_animation() {
    showPageLoader();
}

/**
 * Navigate back to previous page
 */
function goBack() {
    if (document.referrer) {
        window.location.href = document.referrer;
    } else if (window.history.length > 1) {
        window.history.back();
    } else {
        hidePageLoader();
        window.location.href = '/';
    }
}

/**
 * Show the page loader and go back
 */
function loading_back() {
    showPageLoader();
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

/**
 * Legacy notification function (shows alert and redirects)
 * Used by message.html
 */
function info(message) {
    alert(message);
    loading_animation();
    // Use goBack() logic to return to previous page
    if (document.referrer) {
        window.location.href = document.referrer;
    } else {
        window.history.back();
    }
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

// _delete and flaskApi_Delete are defined in api.js — do not redefine here.
