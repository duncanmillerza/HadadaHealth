/**
 * Authentication Check Utility
 * Ensures session is valid before page loads
 */

(function() {
    'use strict';
    
    // Skip auth check on login page
    if (window.location.pathname.includes('login')) {
        return;
    }
    
    // Check if this page requires authentication
    const protectedPages = [
        '/week-calendar-page',
        '/patients-page',
        '/therapists-page',
        '/settings-page',
        '/manage-users-page',
        '/billing-page',
        '/medical-aid-page'
    ];
    
    const currentPath = window.location.pathname;
    const needsAuth = protectedPages.includes(currentPath) || currentPath === '/';
    
    if (needsAuth) {
        // Add small delay to allow session cookies to propagate after login
        const authCheckDelay = window.location.search.includes('_login=') ? 200 : 50;
        
        setTimeout(() => {
            checkAuthenticationWithRetry();
        }, authCheckDelay);
    }
    
    function checkAuthenticationWithRetry(attempt = 1, maxAttempts = 3) {
        console.log(`🔐 Auth check attempt ${attempt}/${maxAttempts}`);
        
        fetch('/check-login', {
            method: 'GET',
            credentials: 'include',
            cache: 'no-cache'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Auth check failed: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (!data.logged_in) {
                if (attempt < maxAttempts) {
                    // Retry after a short delay if we still have attempts left
                    console.log(`🔄 Auth check failed, retrying in 100ms (attempt ${attempt + 1}/${maxAttempts})`);
                    setTimeout(() => {
                        checkAuthenticationWithRetry(attempt + 1, maxAttempts);
                    }, 100);
                } else {
                    console.log('🔐 Not authenticated after retries, redirecting to login');
                    window.location.replace('/login-page');
                }
            } else {
                console.log('✅ Authentication verified, page can continue loading');
            }
        })
        .catch(error => {
            console.error(`Authentication check failed (attempt ${attempt}):`, error);
            
            if (attempt < maxAttempts) {
                // Retry on network errors too
                console.log(`🔄 Retrying auth check in 150ms (attempt ${attempt + 1}/${maxAttempts})`);
                setTimeout(() => {
                    checkAuthenticationWithRetry(attempt + 1, maxAttempts);
                }, 150);
            } else {
                console.error('🚨 Final auth check failed, redirecting to login as safety measure');
                window.location.replace('/login-page');
            }
        });
    }
})();