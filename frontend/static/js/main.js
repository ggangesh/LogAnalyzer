// Main JavaScript file for LogSage AI Frontend

// Global configuration
const CONFIG = {
    API_BASE_URL: '/api',
    REFRESH_INTERVAL: 30000, // 30 seconds
    MAX_FILE_SIZE: 50 * 1024 * 1024, // 50MB
    ALLOWED_FILE_TYPES: ['.log', '.txt', '.json', '.csv', '.xml', '.yaml', '.yml']
};

// Utility functions
const utils = {
    // Format file size
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    // Format date
    formatDate: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    },

    // Show notification
    showNotification: function(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-md shadow-lg z-50 ${
            type === 'success' ? 'bg-green-50 border-l-4 border-green-400 text-green-700' :
            type === 'error' ? 'bg-red-50 border-l-4 border-red-400 text-red-700' :
            type === 'warning' ? 'bg-yellow-50 border-l-4 border-yellow-400 text-yellow-700' :
            'bg-blue-50 border-l-4 border-blue-400 text-blue-700'
        }`;
        
        notification.innerHTML = `
            <div class="flex">
                <div class="flex-shrink-0">
                    <i class="fas ${
                        type === 'success' ? 'fa-check-circle' :
                        type === 'error' ? 'fa-exclamation-circle' :
                        type === 'warning' ? 'fa-exclamation-triangle' :
                        'fa-info-circle'
                    }"></i>
                </div>
                <div class="ml-3">
                    <p class="text-sm">${message}</p>
                </div>
                <div class="ml-auto pl-3">
                    <button class="text-gray-400 hover:text-gray-600" onclick="this.parentElement.parentElement.parentElement.remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    },

    // Show loading state
    showLoading: function(element, text = 'Loading...') {
        element.innerHTML = `
            <div class="flex items-center justify-center py-4">
                <div class="loading-spinner mr-2"></div>
                <span>${text}</span>
            </div>
        `;
    },

    // Make API request
    apiRequest: async function(endpoint, options = {}) {
        try {
            const url = `${CONFIG.API_BASE_URL}${endpoint}`;
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
};

// System status management
const systemStatus = {
    checkStatus: async function() {
        try {
            const status = await utils.apiRequest('/status');
            this.updateStatusIndicators(true, status);
            return status;
        } catch (error) {
            this.updateStatusIndicators(false, { error: error.message });
            return null;
        }
    },

    updateStatusIndicators: function(isOnline, data) {
        const indicators = document.querySelectorAll('[id^="status-"]');
        const healthElements = document.querySelectorAll('[id^="health-"]');
        
        indicators.forEach(indicator => {
            if (indicator.id === 'status-indicator') {
                indicator.className = `w-3 h-3 rounded-full ${
                    isOnline ? 'bg-green-500' : 'bg-red-500'
                }`;
            } else if (indicator.id === 'status-text') {
                indicator.textContent = isOnline ? 'System Online' : 'System Offline';
            }
        });

        healthElements.forEach(element => {
            if (element.id === 'health-icon') {
                element.className = `fas ${
                    isOnline ? 'fa-heart text-success' : 'fa-exclamation-triangle text-danger'
                } text-2xl`;
            } else if (element.id === 'system-health') {
                element.textContent = isOnline ? 'Online' : 'Offline';
            }
        });
    }
};

// File upload management
const fileUpload = {
    initialize: function() {
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');
        
        if (!dropZone || !fileInput) return;

        // Drag and drop events
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drop-zone-active');
        });

        dropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drop-zone-active');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drop-zone-active');
            const files = Array.from(e.dataTransfer.files);
            this.handleFiles(files);
        });

        // File input change
        fileInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            this.handleFiles(files);
        });
    },

    handleFiles: function(files) {
        const validFiles = files.filter(file => this.validateFile(file));
        if (validFiles.length > 0) {
            this.displayFiles(validFiles);
        }
    },

    validateFile: function(file) {
        // Check file size
        if (file.size > CONFIG.MAX_FILE_SIZE) {
            utils.showNotification(`File ${file.name} is too large. Maximum size is ${utils.formatFileSize(CONFIG.MAX_FILE_SIZE)}.`, 'error');
            return false;
        }

        // Check file type (basic check)
        const extension = '.' + file.name.split('.').pop().toLowerCase();
        if (!CONFIG.ALLOWED_FILE_TYPES.includes(extension)) {
            utils.showNotification(`File type ${extension} is not supported.`, 'error');
            return false;
        }

        return true;
    },

    displayFiles: function(files) {
        const fileList = document.getElementById('file-list');
        const selectedFiles = document.getElementById('selected-files');
        
        if (!fileList || !selectedFiles) return;

        fileList.classList.remove('hidden');
        selectedFiles.innerHTML = '';

        files.forEach(file => {
            const fileItem = document.createElement('li');
            fileItem.className = 'flex items-center justify-between p-2 bg-gray-50 rounded';
            fileItem.innerHTML = `
                <div>
                    <span class="text-sm font-medium">${file.name}</span>
                    <span class="text-xs text-gray-500 ml-2">${utils.formatFileSize(file.size)}</span>
                </div>
                <button onclick="this.parentElement.remove()" class="text-red-500 hover:text-red-700">
                    <i class="fas fa-times"></i>
                </button>
            `;
            selectedFiles.appendChild(fileItem);
        });
    }
};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    console.log('LogSage AI Frontend initialized');
    
    // Initialize file upload if on upload page
    if (document.getElementById('drop-zone')) {
        fileUpload.initialize();
    }
    
    // Start system status monitoring
    systemStatus.checkStatus();
    setInterval(() => systemStatus.checkStatus(), CONFIG.REFRESH_INTERVAL);
    
    // Add smooth scrolling to anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
});

// Export for global access
window.LogSage = {
    utils,
    systemStatus,
    fileUpload,
    CONFIG
};