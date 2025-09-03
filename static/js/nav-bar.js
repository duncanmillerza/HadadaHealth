/**
 * Navigation Bar System for HadadaHealth
 * Handles responsive navigation, theme switching, and user interactions
 * Follows healthcare practice management design patterns with accessibility
 */

// Prevent script from loading multiple times
if (window.navigationManagerLoaded) {
  console.warn('NavigationManager script already loaded, skipping duplicate execution');
} else {
  window.navigationManagerLoaded = true;

class NavigationManager {
  constructor() {
    this.activeDropdown = null;
    this.theme = this.getStoredTheme() || 'light';
    this.init();
  }

  /**
   * Initialize navigation system on DOM content loaded
   */
  init() {
    this.loadNavigationFragments();
    this.setupEventListeners();
    this.initializeTheme();
    this.updateActiveNavigation();
  }

  /**
   * Load navigation fragments from server
   */
  async loadNavigationFragments() {
    try {
      const response = await fetch('/static/fragments/nav.html');
      if (!response.ok) {
        throw new Error(`Failed to fetch navigation: ${response.status}`);
      }
      
      const html = await response.text();
      const wrapper = document.createElement('div');
      wrapper.innerHTML = html;
      
      // Extract desktop and mobile navigation
      const desktopNav = wrapper.querySelector('.desktop-nav');
      const mobileNav = wrapper.querySelector('.mobile-nav');
      
      // Insert navigation components into containers
      const topContainer = document.getElementById('top-nav');
      const bottomContainer = document.getElementById('bottom-nav');
      
      if (topContainer && desktopNav) {
        topContainer.innerHTML = desktopNav.outerHTML;
      }
      
      if (bottomContainer && mobileNav) {
        bottomContainer.innerHTML = mobileNav.outerHTML;
      }
      
      // Re-initialize after DOM update
      this.setupEventListeners();
      this.updateActiveNavigation();
      
    } catch (error) {
      console.error('Navigation loading error:', error);
      this.showNavigationError();
    }
  }

  /**
   * Setup all event listeners for navigation functionality
   */
  setupEventListeners() {
    // Close dropdowns when clicking outside
    document.addEventListener('click', (event) => this.handleOutsideClick(event));
    
    // Handle escape key for dropdowns
    document.addEventListener('keydown', (event) => this.handleKeyPress(event));
    
    // Update active navigation on route changes
    window.addEventListener('popstate', () => this.updateActiveNavigation());
    
    // Handle theme preference changes
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)')
        .addEventListener('change', (e) => this.handleSystemThemeChange(e));
    }
  }

  /**
   * Initialize theme system and apply stored preferences
   */
  initializeTheme() {
    document.documentElement.setAttribute('data-theme', this.theme);
    this.updateThemeToggle();
  }

  /**
   * Get stored theme preference from localStorage
   */
  getStoredTheme() {
    try {
      return localStorage.getItem('hadadahealth-theme');
    } catch (error) {
      console.warn('Could not access localStorage for theme:', error);
      return null;
    }
  }

  /**
   * Store theme preference in localStorage
   */
  setStoredTheme(theme) {
    try {
      localStorage.setItem('hadadahealth-theme', theme);
    } catch (error) {
      console.warn('Could not store theme preference:', error);
    }
  }

  /**
   * Toggle between light and dark themes
   */
  toggleTheme() {
    this.theme = this.theme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', this.theme);
    this.setStoredTheme(this.theme);
    this.updateThemeToggle();
    
    // Announce theme change for screen readers
    this.announceThemeChange();
  }

  /**
   * Update theme toggle button state
   */
  updateThemeToggle() {
    const toggleBtn = document.getElementById('theme-toggle');
    if (toggleBtn) {
      toggleBtn.setAttribute('aria-label', 
        this.theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'
      );
      
      // Update button title for tooltip
      toggleBtn.setAttribute('title', 
        this.theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'
      );
    }
  }

  /**
   * Announce theme changes for accessibility
   */
  announceThemeChange() {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = `Switched to ${this.theme} mode`;
    
    document.body.appendChild(announcement);
    setTimeout(() => document.body.removeChild(announcement), 1000);
  }

  /**
   * Handle system theme preference changes
   */
  handleSystemThemeChange(event) {
    if (!this.getStoredTheme()) {
      this.theme = event.matches ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', this.theme);
      this.updateThemeToggle();
    }
  }

  /**
   * Toggle Reports dropdown menu
   */
  toggleReportsMenu() {
    const dropdown = document.getElementById('reports-dropdown');
    const button = document.querySelector('[onclick="toggleReportsMenu()"]');
    
    if (!dropdown || !button) return;
    
    const isOpen = dropdown.style.display === 'block';
    
    // Close all other dropdowns
    this.closeAllDropdowns();
    
    if (!isOpen) {
      dropdown.style.display = 'block';
      button.setAttribute('aria-expanded', 'true');
      this.activeDropdown = 'reports';
      
      // Focus first menu item for keyboard navigation
      const firstMenuItem = dropdown.querySelector('.dropdown-link');
      if (firstMenuItem) {
        setTimeout(() => firstMenuItem.focus(), 100);
      }
    } else {
      dropdown.style.display = 'none';
      button.setAttribute('aria-expanded', 'false');
      this.activeDropdown = null;
    }
  }

  /**
   * Toggle Admin dropdown menu
   */
  toggleAdminMenu() {
    const dropdown = document.getElementById('admin-dropdown');
    const button = document.querySelector('[onclick="toggleAdminMenu()"]');
    
    if (!dropdown || !button) return;
    
    const isOpen = dropdown.style.display === 'block';
    
    // Close all other dropdowns
    this.closeAllDropdowns();
    
    if (!isOpen) {
      dropdown.style.display = 'block';
      button.setAttribute('aria-expanded', 'true');
      this.activeDropdown = 'admin';
      
      // Focus first menu item for keyboard navigation
      const firstMenuItem = dropdown.querySelector('.dropdown-link');
      if (firstMenuItem) {
        setTimeout(() => firstMenuItem.focus(), 100);
      }
    } else {
      dropdown.style.display = 'none';
      button.setAttribute('aria-expanded', 'false');
      this.activeDropdown = null;
    }
  }

  /**
   * Toggle mobile admin dropdown menu
   */
  toggleBottomAdminMenu() {
    const dropdown = document.getElementById('bottom-admin-dropdown');
    const button = document.querySelector('[onclick="toggleBottomAdminMenu()"]');
    
    if (!dropdown || !button) return;
    
    const isOpen = dropdown.style.display === 'block';
    
    if (!isOpen) {
      dropdown.style.display = 'block';
      button.setAttribute('aria-expanded', 'true');
      this.activeDropdown = 'bottom-admin';
    } else {
      dropdown.style.display = 'none';
      button.setAttribute('aria-expanded', 'false');
      this.activeDropdown = null;
    }
  }

  /**
   * Close all dropdown menus
   */
  closeAllDropdowns() {
    const dropdowns = [
      { id: 'admin-dropdown', button: '[onclick="toggleAdminMenu()"]' },
      { id: 'reports-dropdown', button: '[onclick="toggleReportsMenu()"]' },
      { id: 'bottom-admin-dropdown', button: '[onclick="toggleBottomAdminMenu()"]' }
    ];

    dropdowns.forEach(({ id, button }) => {
      const dropdown = document.getElementById(id);
      const btn = document.querySelector(button);
      
      if (dropdown && dropdown.style.display === 'block') {
        dropdown.style.display = 'none';
      }
      
      if (btn) {
        btn.setAttribute('aria-expanded', 'false');
      }
    });
    
    this.activeDropdown = null;
  }

  /**
   * Handle clicks outside navigation elements
   */
  handleOutsideClick(event) {
    const isClickInsideNavigation = event.target.closest('.nav-link, .dropdown-trigger, .nav-dropdown, .mobile-dropdown');
    
    if (!isClickInsideNavigation && this.activeDropdown) {
      this.closeAllDropdowns();
    }
  }

  /**
   * Handle keyboard navigation for dropdowns
   */
  handleKeyPress(event) {
    if (event.key === 'Escape' && this.activeDropdown) {
      this.closeAllDropdowns();
      
      // Return focus to the button that opened the dropdown
      const activeButton = document.querySelector(`[aria-expanded="true"]`);
      if (activeButton) {
        activeButton.focus();
      }
    }
  }

  /**
   * Update active navigation state based on current URL
   */
  updateActiveNavigation() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link, .mobile-nav-link');
    
    navLinks.forEach(link => {
      if (link.tagName === 'A') {
        const href = link.getAttribute('href');
        link.classList.remove('active');
        
        // Add active class to current page link
        if (href === currentPath || (href !== '/' && currentPath.startsWith(href))) {
          link.classList.add('active');
          link.setAttribute('aria-current', 'page');
        } else {
          link.removeAttribute('aria-current');
        }
      }
    });
  }

  /**
   * Handle logout with proper session cleanup
   */
  async logout() {
    try {
      // Show loading state
      const logoutBtn = document.querySelector('.logout-btn');
      if (logoutBtn) {
        logoutBtn.style.opacity = '0.6';
        logoutBtn.style.pointerEvents = 'none';
      }
      
      const response = await fetch('/logout', { 
        credentials: 'include',
        method: 'GET'
      });
      
      if (response.ok) {
        // Clear any stored navigation state
        this.closeAllDropdowns();
        
        // Force cache bypass and redirect to login
        const timestamp = new Date().getTime();
        window.location.replace(`/?_logout=${timestamp}`);
      } else {
        console.error('Logout failed:', response.status);
        this.showLogoutError();
      }
    } catch (error) {
      console.error('Logout error:', error);
      this.showLogoutError();
    }
  }

  /**
   * Show navigation loading error message
   */
  showNavigationError() {
    const errorMessage = document.createElement('div');
    errorMessage.className = 'nav-error';
    errorMessage.textContent = 'Navigation could not be loaded. Please refresh the page.';
    errorMessage.style.cssText = `
      background: var(--color-error);
      color: var(--color-white);
      padding: var(--space-3) var(--space-4);
      border-radius: var(--radius-md);
      margin: var(--space-4);
      text-align: center;
    `;
    
    document.body.insertBefore(errorMessage, document.body.firstChild);
  }

  /**
   * Show logout error message
   */
  showLogoutError() {
    const errorMessage = document.createElement('div');
    errorMessage.className = 'logout-error';
    errorMessage.textContent = 'Logout failed. Please try again.';
    errorMessage.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: var(--color-error);
      color: var(--color-white);
      padding: var(--space-3) var(--space-4);
      border-radius: var(--radius-md);
      z-index: 1000;
    `;
    
    document.body.appendChild(errorMessage);
    setTimeout(() => {
      if (errorMessage.parentNode) {
        errorMessage.parentNode.removeChild(errorMessage);
      }
    }, 5000);
    
    // Reset logout button state
    const logoutBtn = document.querySelector('.logout-btn');
    if (logoutBtn) {
      logoutBtn.style.opacity = '';
      logoutBtn.style.pointerEvents = '';
    }
  }
}

// Global navigation manager instance
let navigationManager;

// Initialize navigation system when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  if (!navigationManager) {
    navigationManager = new NavigationManager();
  }
});

// Global functions for onclick handlers (maintaining backward compatibility)
function toggleReportsMenu() {
  if (navigationManager) {
    navigationManager.toggleReportsMenu();
  }
}

function toggleAdminMenu() {
  if (navigationManager) {
    navigationManager.toggleAdminMenu();
  }
}

function toggleBottomAdminMenu() {
  if (navigationManager) {
    navigationManager.toggleBottomAdminMenu();
  }
}

function toggleTheme() {
  if (navigationManager) {
    navigationManager.toggleTheme();
  }
}

function logout() {
  if (navigationManager) {
    navigationManager.logout();
  }
}

} // End navigationManagerLoaded check