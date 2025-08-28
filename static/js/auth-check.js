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
        // Check authentication before page fully loads
        fetch('/check-login', {
            method: 'GET',
            credentials: 'include',
            cache: 'no-cache'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Auth check failed');
            }
            return response.json();
        })
        .then(data => {
            if (!data.logged_in) {
                console.log('🔐 Not authenticated, redirecting to login');
                // Redirect to login if not authenticated
                window.location.replace('/login-page');
            }
            // If authenticated, page will continue loading normally
        })
        .catch(error => {
            console.error('Authentication check failed:', error);
            // On error, redirect to login as a safety measure
            window.location.replace('/login-page');
        });
    }
})();