/**
 * In-App Notification System for AI Report Writing System
 * Handles real-time notifications, toast messages, and notification center
 */

// Notification system state
let notificationState = {
    notifications: [],
    unreadCount: 0,
    isVisible: false,
    settings: {
        soundEnabled: true,
        desktopEnabled: true,
        emailEnabled: false,
        reportRequests: true,
        reportUpdates: true,
        systemMessages: true,
        overduReminders: true
    },
    lastFetch: null,
    pollInterval: null
};

// Notification types and their configurations
const NOTIFICATION_TYPES = {
    REPORT_REQUEST: {
        icon: '📋',
        className: 'report-request',
        sound: 'notification',
        priority: 'normal'
    },
    REPORT_ASSIGNED: {
        icon: '👤',
        className: 'report-assigned', 
        sound: 'assign',
        priority: 'normal'
    },
    REPORT_COMPLETED: {
        icon: '✅',
        className: 'report-completed',
        sound: 'completion',
        priority: 'low'
    },
    REPORT_OVERDUE: {
        icon: '⚠️',
        className: 'report-overdue',
        sound: 'urgent',
        priority: 'high'
    },
    REPORT_REMINDER: {
        icon: '🔔',
        className: 'report-reminder',
        sound: 'reminder',
        priority: 'normal'
    },
    SYSTEM: {
        icon: '⚙️',
        className: 'system',
        sound: 'system',
        priority: 'low'
    }
};

// Initialize notification system
function initializeNotificationSystem() {
    createNotificationBell();
    createNotificationCenter();
    createToastContainer();
    loadNotificationSettings();
    setupEventListeners();
    startNotificationPolling();
    requestNotificationPermission();
    
    console.log('✅ Notification system initialized');
}

// Create notification bell in navigation
function createNotificationBell() {
    // Wait for navigation to load and try multiple strategies
    function addBellToNav() {
        // Strategy 1: Try to find an existing navigation
        const navBar = document.getElementById('top-nav');
        const navList = document.querySelector('nav ul') || document.querySelector('.nav-links');
        const headerRight = document.querySelector('.header-right') || document.querySelector('.nav-right');
        
        const bellHTML = `
            <div class="notification-bell" id="notification-bell" onclick="toggleNotificationCenter()" style="
                position: fixed;
                top: 15px;
                right: 20px;
                z-index: 1001;
                background: #2D6356;
                color: white;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                transition: background-color 0.2s;
            ">
                <span class="notification-bell-icon" style="font-size: 1.2rem;">🔔</span>
                <span class="notification-badge hidden" id="notification-badge" style="
                    position: absolute;
                    top: -4px;
                    right: -4px;
                    background: #f44336;
                    color: white;
                    font-size: 0.65rem;
                    font-weight: 700;
                    min-width: 18px;
                    height: 18px;
                    border-radius: 9px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border: 2px solid #2D6356;
                ">0</span>
            </div>
        `;
        
        // Check if bell already exists
        if (document.getElementById('notification-bell')) {
            return true;
        }
        
        // Try different placement strategies
        if (headerRight) {
            headerRight.insertAdjacentHTML('beforeend', bellHTML);
            return true;
        } else if (navList) {
            navList.insertAdjacentHTML('beforeend', `<li style="list-style: none; margin-left: auto;">${bellHTML}</li>`);
            return true;
        } else if (navBar && navBar.innerHTML.trim()) {
            // Add to existing nav content
            navBar.insertAdjacentHTML('beforeend', bellHTML);
            return true;
        } else {
            // Fallback: add as fixed position element
            document.body.insertAdjacentHTML('beforeend', bellHTML);
            return true;
        }
    }
    
    // Try immediately
    if (addBellToNav()) {
        return;
    }
    
    // If that fails, wait a bit for nav to load
    setTimeout(() => {
        if (!addBellToNav()) {
            console.warn('Could not find navigation element, adding notification bell as fixed element');
        }
    }, 1000);
}

// Create notification center
function createNotificationCenter() {
    const centerHTML = `
        <div class="notification-center" id="notification-center">
            <div class="notification-header">
                <h4 class="notification-title">Notifications</h4>
                <span class="notification-count" id="notification-count">0</span>
                <div class="notification-actions">
                    <button class="notification-action-btn" onclick="markAllAsRead()">Mark All Read</button>
                    <button class="notification-action-btn" onclick="toggleNotificationSettings()">Settings</button>
                </div>
            </div>
            <div class="notification-list" id="notification-list">
                <div class="notification-loading">
                    <div class="notification-loading-spinner"></div>
                    Loading notifications...
                </div>
            </div>
            <div class="notification-settings" id="notification-settings" style="display: none;">
                <h5 class="notification-settings-title">Notification Settings</h5>
                <div class="notification-setting">
                    <span>Sound notifications</span>
                    <div class="notification-toggle" id="sound-toggle" onclick="toggleSetting('soundEnabled')"></div>
                </div>
                <div class="notification-setting">
                    <span>Desktop notifications</span>
                    <div class="notification-toggle" id="desktop-toggle" onclick="toggleSetting('desktopEnabled')"></div>
                </div>
                <div class="notification-setting">
                    <span>Report requests</span>
                    <div class="notification-toggle enabled" id="requests-toggle" onclick="toggleSetting('reportRequests')"></div>
                </div>
                <div class="notification-setting">
                    <span>Report updates</span>
                    <div class="notification-toggle enabled" id="updates-toggle" onclick="toggleSetting('reportUpdates')"></div>
                </div>
                <div class="notification-setting">
                    <span>Overdue reminders</span>
                    <div class="notification-toggle enabled" id="overdue-toggle" onclick="toggleSetting('overdueReminders')"></div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', centerHTML);
    
    // Close on outside click
    document.addEventListener('click', function(event) {
        const center = document.getElementById('notification-center');
        const bell = document.getElementById('notification-bell');
        
        if (!center.contains(event.target) && !bell.contains(event.target)) {
            hideNotificationCenter();
        }
    });
}

// Create toast container
function createToastContainer() {
    const containerHTML = `<div class="toast-container" id="toast-container"></div>`;
    document.body.insertAdjacentHTML('beforeend', containerHTML);
}

// Toggle notification center visibility
function toggleNotificationCenter() {
    const center = document.getElementById('notification-center');
    
    if (notificationState.isVisible) {
        hideNotificationCenter();
    } else {
        showNotificationCenter();
    }
}

// Show notification center
function showNotificationCenter() {
    const center = document.getElementById('notification-center');
    center.classList.add('visible', 'sliding-down');
    notificationState.isVisible = true;
    
    console.log('📨 Opening notification center - current notifications:', notificationState.notifications.length);
    
    // If we already have notifications (like test notifications), just show them
    if (notificationState.notifications.length > 0) {
        console.log('✅ Using existing notifications, updating UI...');
        updateNotificationUI();
    } else {
        console.log('🔄 No notifications found, loading from API...');
        loadNotifications();
    }
    
    setTimeout(() => {
        center.classList.remove('sliding-down');
    }, 300);
}

// Hide notification center
function hideNotificationCenter() {
    const center = document.getElementById('notification-center');
    center.classList.remove('visible');
    notificationState.isVisible = false;
    
    // Hide settings if open
    const settings = document.getElementById('notification-settings');
    settings.style.display = 'none';
}

// Load notifications from API
async function loadNotifications() {
    try {
        const response = await fetch('/api/notifications/user');
        if (!response.ok) {
            console.log('API request failed with status:', response.status);
            throw new Error(`Failed to load notifications: ${response.status}`);
        }
        
        const data = await response.json();
        notificationState.notifications = data.notifications || [];
        notificationState.unreadCount = data.unread_count || 0;
        
        updateNotificationUI();
        notificationState.lastFetch = new Date();
        
        console.log('✅ Loaded notifications from API:', notificationState.notifications.length);
        
    } catch (error) {
        console.log('❌ Error loading notifications from API:', error.message);
        console.log('🔄 Falling back to mock notifications for testing...');
        
        // Show mock notifications for testing
        loadMockNotifications();
    }
}

// Load mock notifications for testing
function loadMockNotifications() {
    console.log('📋 Loading mock notifications...');
    
    const mockNotifications = [
        {
            id: 1,
            type: 'REPORT_REQUEST',
            title: 'New Report Request',
            message: 'Dr. Smith has requested a discharge report for Patient John Doe',
            created_at: new Date(Date.now() - 5 * 60 * 1000).toISOString(), // 5 minutes ago
            is_read: false,
            priority: 'normal',
            source: 'Dr. Smith',
            report_id: 123
        },
        {
            id: 2,
            type: 'REPORT_OVERDUE',
            title: 'Report Overdue',
            message: 'Progress Report for Patient Jane Smith is 2 days overdue',
            created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
            is_read: false,
            priority: 'high',
            source: 'System',
            report_id: 124
        },
        {
            id: 3,
            type: 'REPORT_COMPLETED',
            title: 'Report Completed',
            message: 'Your insurance report for Patient Bob Johnson has been approved',
            created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
            is_read: true,
            priority: 'low',
            source: 'Insurance Dept',
            report_id: 125
        },
        {
            id: 4,
            type: 'REPORT_ASSIGNED',
            title: 'Report Assigned',
            message: 'You have been assigned to complete a multi-disciplinary assessment',
            created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(), // 3 days ago
            is_read: true,
            priority: 'normal',
            source: 'Team Lead',
            report_id: 126
        }
    ];
    
    notificationState.notifications = mockNotifications;
    notificationState.unreadCount = mockNotifications.filter(n => !n.is_read).length;
    
    console.log('✅ Mock notifications loaded:', mockNotifications.length, 'total,', notificationState.unreadCount, 'unread');
    
    updateNotificationUI();
    notificationState.lastFetch = new Date();
}

// Update notification UI elements
function updateNotificationUI() {
    console.log('🔄 Updating notification UI - notifications:', notificationState.notifications.length, 'unread:', notificationState.unreadCount);
    updateNotificationBadge();
    updateNotificationList();
    updateNotificationCount();
}

// Update notification badge
function updateNotificationBadge() {
    const badge = document.getElementById('notification-badge');
    const count = notificationState.unreadCount;
    
    if (count > 0) {
        badge.textContent = count > 99 ? '99+' : count;
        badge.classList.remove('hidden');
        badge.classList.add('bounce');
        
        setTimeout(() => badge.classList.remove('bounce'), 600);
    } else {
        badge.classList.add('hidden');
    }
}

// Update notification count in header
function updateNotificationCount() {
    const countElement = document.getElementById('notification-count');
    const count = notificationState.unreadCount;
    countElement.textContent = count;
}

// Update notification list
function updateNotificationList() {
    const listElement = document.getElementById('notification-list');
    const notifications = notificationState.notifications;
    
    if (notifications.length === 0) {
        listElement.innerHTML = `
            <div class="notification-empty">
                <div class="notification-empty-icon">🔔</div>
                <div class="notification-empty-message">No notifications yet</div>
            </div>
        `;
        return;
    }
    
    const notificationsHTML = notifications
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        .map(notification => createNotificationItem(notification))
        .join('');
    
    listElement.innerHTML = notificationsHTML;
}

// Create notification item HTML
function createNotificationItem(notification) {
    const config = NOTIFICATION_TYPES[notification.type] || NOTIFICATION_TYPES.SYSTEM;
    const timeAgo = formatTimeAgo(notification.created_at);
    const isUnread = !notification.is_read;
    const priorityClass = notification.priority === 'high' ? 'priority-high' : '';
    
    return `
        <div class="notification-item ${isUnread ? 'unread' : ''} ${priorityClass}" 
             onclick="handleNotificationClick(${notification.id})"
             data-notification-id="${notification.id}">
            <div class="notification-content">
                <div class="notification-icon ${config.className}">
                    ${config.icon}
                </div>
                <div class="notification-body">
                    <div class="notification-message ${notification.message.length > 100 ? 'truncated' : ''}">
                        <strong>${notification.title}</strong><br>
                        ${notification.message}
                    </div>
                    <div class="notification-meta">
                        <span class="notification-source">${notification.source}</span>
                        <span class="notification-time">${timeAgo}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Handle notification click
function handleNotificationClick(notificationId) {
    const notification = notificationState.notifications.find(n => n.id === notificationId);
    if (!notification) return;
    
    // Mark as read
    markNotificationAsRead(notificationId);
    
    // Handle different notification types
    switch (notification.type) {
        case 'REPORT_REQUEST':
        case 'REPORT_ASSIGNED':
            if (notification.report_id) {
                openReportWizard('therapist', notification.report_id);
            }
            break;
            
        case 'REPORT_OVERDUE':
            if (notification.report_id) {
                showToastNotification({
                    title: 'Opening Report',
                    message: 'Taking you to the overdue report...',
                    type: 'info'
                });
                openReportWizard('therapist', notification.report_id);
            }
            break;
            
        case 'REPORT_COMPLETED':
            showToastNotification({
                title: 'Report Completed',
                message: 'This report has been completed successfully.',
                type: 'success'
            });
            break;
            
        default:
            console.log('Notification clicked:', notification);
    }
    
    // Close notification center
    hideNotificationCenter();
}

// Mark notification as read
async function markNotificationAsRead(notificationId) {
    try {
        // Update local state immediately
        const notification = notificationState.notifications.find(n => n.id === notificationId);
        if (notification && !notification.is_read) {
            notification.is_read = true;
            notificationState.unreadCount--;
            updateNotificationUI();
        }
        
        // Send to API
        await fetch(`/api/notifications/${notificationId}/read`, {
            method: 'POST'
        });
        
    } catch (error) {
        console.error('Error marking notification as read:', error);
        // Revert local state on error
        const notification = notificationState.notifications.find(n => n.id === notificationId);
        if (notification) {
            notification.is_read = false;
            notificationState.unreadCount++;
            updateNotificationUI();
        }
    }
}

// Mark all notifications as read
async function markAllAsRead() {
    try {
        // Update local state immediately
        notificationState.notifications.forEach(n => n.is_read = true);
        notificationState.unreadCount = 0;
        updateNotificationUI();
        
        // Send to API
        await fetch('/api/notifications/mark-all-read', {
            method: 'POST'
        });
        
        showToastNotification({
            title: 'All Notifications Read',
            message: 'All notifications have been marked as read',
            type: 'success'
        });
        
    } catch (error) {
        console.error('Error marking all as read:', error);
        loadNotifications(); // Reload to get correct state
    }
}

// Show toast notification
function showToastNotification(options) {
    const {
        title = 'Notification',
        message = '',
        type = 'info',
        duration = 5000,
        actions = [],
        persistent = false
    } = options;
    
    const toastId = 'toast-' + Date.now();
    const typeConfig = {
        info: { icon: 'ℹ️', class: 'info' },
        success: { icon: '✅', class: 'success' },
        warning: { icon: '⚠️', class: 'warning' },
        error: { icon: '❌', class: 'error' }
    };
    
    const config = typeConfig[type] || typeConfig.info;
    
    const actionsHTML = actions.length > 0 ? `
        <div class="toast-actions">
            ${actions.map(action => `
                <button class="toast-action-btn ${action.primary ? 'primary' : ''}" 
                        onclick="${action.onclick}">
                    ${action.text}
                </button>
            `).join('')}
        </div>
    ` : '';
    
    const toastHTML = `
        <div class="toast-notification ${config.class}" id="${toastId}">
            <button class="toast-close" onclick="hideToastNotification('${toastId}')">&times;</button>
            <div class="toast-content">
                <div class="toast-icon">${config.icon}</div>
                <div class="toast-body">
                    <div class="toast-title">${title}</div>
                    <div class="toast-message">${message}</div>
                    ${actionsHTML}
                </div>
            </div>
        </div>
    `;
    
    const container = document.getElementById('toast-container');
    container.insertAdjacentHTML('afterbegin', toastHTML);
    
    const toastElement = document.getElementById(toastId);
    
    // Animate in
    setTimeout(() => {
        toastElement.classList.add('visible');
    }, 10);
    
    // Auto-hide after duration (unless persistent)
    if (!persistent && duration > 0) {
        setTimeout(() => {
            hideToastNotification(toastId);
        }, duration);
    }
    
    // Play sound if enabled
    if (notificationState.settings.soundEnabled) {
        playNotificationSound(type);
    }
    
    return toastId;
}

// Hide toast notification
function hideToastNotification(toastId) {
    const toastElement = document.getElementById(toastId);
    if (toastElement) {
        toastElement.classList.remove('visible');
        setTimeout(() => {
            toastElement.remove();
        }, 300);
    }
}

// Play notification sound
function playNotificationSound(type) {
    try {
        // Create audio context for sound generation
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        // Different sounds for different types
        const soundConfig = {
            info: { frequency: 800, duration: 200 },
            success: { frequency: 600, duration: 300 },
            warning: { frequency: 400, duration: 400 },
            error: { frequency: 300, duration: 500 }
        };
        
        const config = soundConfig[type] || soundConfig.info;
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.setValueAtTime(config.frequency, audioContext.currentTime);
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + config.duration / 1000);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + config.duration / 1000);
        
        // Show sound indicator
        showSoundIndicator();
        
    } catch (error) {
        console.log('Could not play notification sound:', error);
    }
}

// Show sound indicator
function showSoundIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'notification-sound-indicator';
    indicator.textContent = '🔊 Notification';
    document.body.appendChild(indicator);
    
    setTimeout(() => indicator.classList.add('visible'), 10);
    
    setTimeout(() => {
        indicator.classList.remove('visible');
        setTimeout(() => indicator.remove(), 300);
    }, 1000);
}

// Toggle notification settings
function toggleNotificationSettings() {
    const settings = document.getElementById('notification-settings');
    const isVisible = settings.style.display !== 'none';
    settings.style.display = isVisible ? 'none' : 'block';
    
    // Update toggle states
    updateSettingsToggles();
}

// Update settings toggle states
function updateSettingsToggles() {
    const settings = notificationState.settings;
    
    document.getElementById('sound-toggle').classList.toggle('enabled', settings.soundEnabled);
    document.getElementById('desktop-toggle').classList.toggle('enabled', settings.desktopEnabled);
    document.getElementById('requests-toggle').classList.toggle('enabled', settings.reportRequests);
    document.getElementById('updates-toggle').classList.toggle('enabled', settings.reportUpdates);
    document.getElementById('overdue-toggle').classList.toggle('enabled', settings.overdueReminders);
}

// Toggle setting
function toggleSetting(settingName) {
    notificationState.settings[settingName] = !notificationState.settings[settingName];
    updateSettingsToggles();
    saveNotificationSettings();
    
    showToastNotification({
        title: 'Settings Updated',
        message: `${settingName.replace(/([A-Z])/g, ' $1').toLowerCase()} ${notificationState.settings[settingName] ? 'enabled' : 'disabled'}`,
        type: 'success',
        duration: 2000
    });
}

// Save notification settings
function saveNotificationSettings() {
    try {
        localStorage.setItem('notificationSettings', JSON.stringify(notificationState.settings));
    } catch (error) {
        console.error('Error saving notification settings:', error);
    }
}

// Load notification settings
function loadNotificationSettings() {
    try {
        const saved = localStorage.getItem('notificationSettings');
        if (saved) {
            notificationState.settings = { ...notificationState.settings, ...JSON.parse(saved) };
        }
    } catch (error) {
        console.error('Error loading notification settings:', error);
    }
}

// Request desktop notification permission
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                notificationState.settings.desktopEnabled = true;
                saveNotificationSettings();
            }
        });
    }
}

// Show desktop notification
function showDesktopNotification(options) {
    if (!notificationState.settings.desktopEnabled || Notification.permission !== 'granted') {
        return;
    }
    
    const notification = new Notification(options.title, {
        body: options.message,
        icon: '/static/favicon.ico',
        badge: '/static/hadada_health_logo.svg',
        tag: 'hadada-health-report'
    });
    
    notification.onclick = function() {
        window.focus();
        if (options.onclick) {
            options.onclick();
        }
        notification.close();
    };
    
    // Auto-close after 5 seconds
    setTimeout(() => notification.close(), 5000);
}

// Start notification polling
function startNotificationPolling() {
    // Poll every 30 seconds
    notificationState.pollInterval = setInterval(loadNotifications, 30000);
    
    // Initial load
    loadNotifications();
}

// Stop notification polling
function stopNotificationPolling() {
    if (notificationState.pollInterval) {
        clearInterval(notificationState.pollInterval);
        notificationState.pollInterval = null;
    }
}

// Setup event listeners
function setupEventListeners() {
    // Listen for report events to trigger notifications
    document.addEventListener('reportCreated', function(event) {
        showToastNotification({
            title: 'Report Created',
            message: `Report "${event.detail.title}" has been created successfully`,
            type: 'success'
        });
    });
    
    document.addEventListener('reportUpdated', function(event) {
        showToastNotification({
            title: 'Report Updated',
            message: `Report "${event.detail.title}" has been updated`,
            type: 'info'
        });
    });
    
    // Visibility change handling
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            // Refresh notifications when tab becomes visible
            loadNotifications();
        }
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        // Ctrl/Cmd + Shift + N to toggle notification center
        if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'N') {
            event.preventDefault();
            toggleNotificationCenter();
        }
    });
}

// Utility function to format time ago
function formatTimeAgo(dateString) {
    const now = new Date();
    const date = new Date(dateString);
    const diffInMs = now - date;
    const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
    const diffInHours = Math.floor(diffInMinutes / 60);
    const diffInDays = Math.floor(diffInHours / 24);
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInHours < 24) return `${diffInHours}h ago`;
    if (diffInDays < 7) return `${diffInDays}d ago`;
    
    return date.toLocaleDateString();
}

// Public API for creating notifications
function createNotification(options) {
    const notification = {
        id: Date.now() + Math.random(), // Ensure unique ID
        type: options.type || 'SYSTEM',
        title: options.title,
        message: options.message,
        created_at: new Date().toISOString(),
        is_read: false,
        priority: options.priority || 'normal',
        source: options.source || 'System',
        report_id: options.report_id || null
    };
    
    console.log('➕ Creating notification:', notification.title, 'ID:', notification.id);
    
    // Add to notifications array
    notificationState.notifications.unshift(notification);
    notificationState.unreadCount++;
    
    console.log('📊 Notification state updated - Total:', notificationState.notifications.length, 'Unread:', notificationState.unreadCount);
    
    // Update UI
    updateNotificationUI();
    
    // Show toast if requested
    if (options.showToast !== false) {
        showToastNotification({
            title: notification.title,
            message: notification.message,
            type: notification.priority === 'high' ? 'warning' : 'info'
        });
    }
    
    // Show desktop notification if enabled
    if (notificationState.settings.desktopEnabled) {
        showDesktopNotification({
            title: notification.title,
            message: notification.message,
            onclick: () => handleNotificationClick(notification.id)
        });
    }
    
    return notification.id;
}

// Cleanup function
function cleanupNotificationSystem() {
    stopNotificationPolling();
}

// Export functions for global use
window.initializeNotificationSystem = initializeNotificationSystem;
window.toggleNotificationCenter = toggleNotificationCenter;
window.showToastNotification = showToastNotification;
window.hideToastNotification = hideToastNotification;
window.createNotification = createNotification;
window.markAllAsRead = markAllAsRead;
window.toggleNotificationSettings = toggleNotificationSettings;
window.toggleSetting = toggleSetting;
window.cleanupNotificationSystem = cleanupNotificationSystem;
window.createTestNotifications = createTestNotifications;

// Test function to create sample notifications (for development/testing)
function createTestNotifications() {
    console.log('Creating test notifications...');
    
    // Create various test notifications
    createNotification({
        type: 'REPORT_REQUEST',
        title: 'New Report Request',
        message: 'Dr. Smith has requested a discharge report for Patient John Doe',
        priority: 'normal',
        source: 'Dr. Smith',
        report_id: 123
    });
    
    setTimeout(() => {
        createNotification({
            type: 'REPORT_OVERDUE',
            title: 'Report Overdue',
            message: 'Progress Report for Patient Jane Smith is 2 days overdue',
            priority: 'high',
            source: 'System',
            report_id: 124
        });
    }, 2000);
    
    setTimeout(() => {
        createNotification({
            type: 'REPORT_COMPLETED',
            title: 'Report Completed',
            message: 'Your insurance report for Patient Bob Johnson has been approved',
            priority: 'low',
            source: 'Insurance Dept',
            report_id: 125
        });
    }, 4000);
}

// Export test function
window.createTestNotifications = createTestNotifications;

// Note: Auto-initialization removed - now controlled by main template
// This allows proper coordination with other dashboard components