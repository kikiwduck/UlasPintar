// ===== DATE UTILITIES =====
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('id-ID', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getTimeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'baru saja';
    if (diffMins < 60) return `${diffMins} menit yang lalu`;
    if (diffHours < 24) return `${diffHours} jam yang lalu`;
    if (diffDays < 7) return `${diffDays} hari yang lalu`;
    
    return formatDate(dateString);
}

// ===== DOWNLOAD UTILITIES =====
function downloadText(filename, text) {
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function downloadJSON(filename, data) {
    const jsonString = JSON.stringify(data, null, 2);
    downloadText(filename, jsonString);
}

// ===== STRING UTILITIES =====
function truncateText(text, maxLength = 150) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function sanitizeHTML(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===== COLOR UTILITIES =====
function getSentimentColor(sentiment) {
    const colors = {
        'positif': '#48bb78',
        'negatif': '#f56565',
        'netral': '#ed8936'
    };
    return colors[sentiment] || '#667eea';
}

function getSentimentEmoji(sentiment) {
    const emojis = {
        'positif': '😊',
        'negatif': '😞',
        'netral': '😐'
    };
    return emojis[sentiment] || '🤔';
}

// ===== VALIDATION =====
function isValidCSV(file) {
    if (!file) return false;
    if (!file.name.endsWith('.csv')) return false;
    if (file.size > 10 * 1024 * 1024) { // 10MB max
        showError('File terlalu besar. Maksimum 10MB');
        return false;
    }
    return true;
}

function validateFormData(formData) {
    const requiredFields = ['review'];
    const file = formData.get('file');
    
    if (!file) {
        showError('Silakan pilih file terlebih dahulu');
        return false;
    }
    
    if (!isValidCSV(file)) {
        return false;
    }
    
    return true;
}

// ===== STORAGE UTILITIES =====
function saveToLocalStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
        return true;
    } catch (e) {
        console.error('Error saving to localStorage:', e);
        return false;
    }
}

function getFromLocalStorage(key) {
    try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : null;
    } catch (e) {
        console.error('Error reading from localStorage:', e);
        return null;
    }
}

// ===== DEBOUNCE =====
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

// Export functions
window.Utils = {
    formatDate,
    getTimeAgo,
    downloadText,
    downloadJSON,
    truncateText,
    sanitizeHTML,
    getSentimentColor,
    getSentimentEmoji,
    isValidCSV,
    validateFormData,
    saveToLocalStorage,
    getFromLocalStorage,
    debounce
};