/**
 * Session Management Utility for HadadaHealth
 * Handles session timeout warnings and automatic logout
 */

class SessionManager {
    constructor(options = {}) {
        this.sessionTimeout = (options.sessionTimeout || 3600) * 1000; // Convert to milliseconds
        this.warningTime = options.warningTime || 5 * 60 * 1000; // 5 minutes before expiry
        this.checkInterval = options.checkInterval || 30 * 1000; // Check every 30 seconds
        
        this.lastActivity = Date.now();
        this.warningShown = false;
        this.timeoutId = null;
        this.intervalId = null;
        
        this.init();
    }
    
    init() {
        // Track user activity
        this.bindActivityEvents();
        
        // Start session monitoring
        this.startSessionMonitoring();
        
        // Reset activity on page load
        this.updateLastActivity();
    }
    
    bindActivityEvents() {
        const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
        
        events.forEach(event => {
            document.addEventListener(event, () => {
                this.updateLastActivity();
            }, { passive: true });
        });
    }
    
    updateLastActivity() {
        this.lastActivity = Date.now();
        this.warningShown = false;
        
        // Hide warning if shown
        this.hideWarning();
    }
    
    startSessionMonitoring() {
        this.intervalId = setInterval(() => {
            this.checkSession();
        }, this.checkInterval);
    }
    
    checkSession() {
        const now = Date.now();
        const timeSinceActivity = now - this.lastActivity;
        const timeUntilExpiry = this.sessionTimeout - timeSinceActivity;
        
        if (timeUntilExpiry <= 0) {
            // Session expired
            this.handleSessionExpiry();
        } else if (timeUntilExpiry <= this.warningTime && !this.warningShown) {
            // Show warning
            this.showSessionWarning(Math.ceil(timeUntilExpiry / 1000 / 60));
        }
    }
    
    showSessionWarning(minutesLeft) {
        this.warningShown = true;
        
        // Create warning modal
        const modal = document.createElement('div');
        modal.id = 'session-warning-modal';
        modal.className = 'session-warning-modal';
        modal.innerHTML = `
            <div class="session-warning-content">
                <h3>⏰ Session Expiring Soon</h3>
                <p>Your session will expire in <strong>${minutesLeft} minutes</strong> due to inactivity.</p>
                <p>Click "Stay Logged In" to continue your session.</p>
                <div class="session-warning-buttons">
                    <button onclick="sessionManager.extendSession()" class="btn-primary">Stay Logged In</button>
                    <button onclick="sessionManager.logout()" class="btn-secondary">Logout Now</button>
                </div>
            </div>
        `;
        
        // Add styles
        modal.innerHTML += `
            <style>
                .session-warning-modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.5);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 10000;
                }
                .session-warning-content {
                    background: white;
                    padding: 2rem;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                    max-width: 400px;
                    text-align: center;
                }
                .session-warning-content h3 {
                    color: #2D6356;
                    margin-bottom: 1rem;
                }
                .session-warning-buttons {
                    margin-top: 1.5rem;
                    display: flex;
                    gap: 1rem;
                    justify-content: center;
                }
                .session-warning-buttons button {
                    padding: 0.5rem 1rem;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: 500;
                }
                .btn-primary {
                    background: #2D6356;
                    color: white;
                }
                .btn-primary:hover {
                    background: #214c43;
                }
                .btn-secondary {
                    background: #f0f0f0;
                    color: #333;
                }
                .btn-secondary:hover {
                    background: #e0e0e0;
                }
            </style>
        `;
        
        document.body.appendChild(modal);
    }
    
    hideWarning() {
        const modal = document.getElementById('session-warning-modal');
        if (modal) {
            modal.remove();
        }
    }
    
    extendSession() {
        // Make request to server to refresh session
        fetch('/check-login', {
            method: 'GET',
            credentials: 'include'
        })
        .then(response => {
            if (response.ok) {
                this.updateLastActivity();
                console.log('Session extended successfully');
            } else {
                // Session invalid, redirect to login
                this.handleSessionExpiry();
            }
        })
        .catch(error => {
            console.error('Failed to extend session:', error);
            this.handleSessionExpiry();
        });
    }
    
    handleSessionExpiry() {
        // Clear monitoring
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
        
        // Show expiry message
        alert('Your session has expired due to inactivity. You will be redirected to the login page.');
        
        // Logout and redirect
        this.logout();
    }
    
    logout() {
        // Clear monitoring
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
        
        // Call logout endpoint
        fetch('/logout', {
            method: 'GET',
            credentials: 'include'
        })
        .then(() => {
            // Redirect to login page
            window.location.href = '/login-page';
        })
        .catch(error => {
            console.error('Logout failed:', error);
            // Force redirect anyway
            window.location.href = '/login-page';
        });
    }
    
    destroy() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
        this.hideWarning();
    }
}

// Initialize session manager when page loads
let sessionManager;
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize on pages that require authentication
    if (!window.location.pathname.includes('/login')) {
        sessionManager = new SessionManager({
            sessionTimeout: 3600, // 1 hour in seconds
            warningTime: 5 * 60 * 1000, // 5 minutes in milliseconds
            checkInterval: 30 * 1000 // Check every 30 seconds
        });
    }
});

// Clean up when page unloads
window.addEventListener('beforeunload', function() {
    if (sessionManager) {
        sessionManager.destroy();
    }
});