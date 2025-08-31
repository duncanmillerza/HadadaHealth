# Navigation

> Desktop and mobile navigation systems for HadadaHealth healthcare practice management interfaces.

## Desktop Navigation

### Top Navigation Bar
Primary navigation for desktop interfaces with brand prominence.

```html
<nav class="desktop-nav">
  <div class="nav-brand">
    <svg class="brand-logo" viewBox="0 0 2928 251">
      <path d="M203.2 0.225V251H169.25..." fill="#2D6356"/>
    </svg>
    <span class="brand-text">HadadaHealth</span>
  </div>
  
  <div class="nav-links">
    <a href="/dashboard" class="nav-link active">
      <i class="material-icons">dashboard</i>
      <span>Dashboard</span>
    </a>
    <a href="/patients" class="nav-link">
      <i class="material-icons">group</i>
      <span>Patients</span>
    </a>
    <a href="/appointments" class="nav-link">
      <i class="material-icons">event</i>
      <span>Appointments</span>
    </a>
    <a href="/reports" class="nav-link">
      <i class="material-icons">assessment</i>
      <span>Reports</span>
    </a>
  </div>
  
  <div class="nav-actions">
    <button id="theme-toggle" class="theme-toggle" aria-label="Toggle dark mode">
      <i class="material-icons theme-sun">light_mode</i>
      <i class="material-icons theme-moon">dark_mode</i>
    </button>
    <div class="user-menu">
      <button class="user-button">
        <i class="material-icons">account_circle</i>
        <span>Dr. Smith</span>
      </button>
    </div>
  </div>
</nav>
```

```css
.desktop-nav {
  background: var(--color-primary);
  color: var(--color-white);
  padding: var(--space-5) var(--space-6);
  display: flex;
  align-items: center;
  gap: var(--space-6);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-weight: 700;
  font-size: 1.1rem;
  letter-spacing: 0.2px;
  flex-shrink: 0;
}

.brand-logo {
  height: 32px;
  width: auto;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex: 1;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-white);
  text-decoration: none;
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  font-weight: 500;
  opacity: 0.9;
  transition: all 0.2s ease;
  border-bottom: 2px solid transparent;
}

.nav-link:hover {
  opacity: 1;
  background: rgba(255, 255, 255, 0.1);
}

.nav-link.active {
  opacity: 1;
  border-bottom-color: var(--color-white);
  background: rgba(255, 255, 255, 0.1);
}

.nav-link .material-icons {
  font-size: 20px;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  flex-shrink: 0;
}
```

### Theme Toggle Button
```css
.theme-toggle {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: var(--radius-md);
  color: var(--color-white);
  padding: var(--space-2);
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
}

.theme-toggle:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-1px);
}

/* Icon visibility based on theme */
.theme-sun { display: block; }
.theme-moon { display: none; }

[data-theme="dark"] .theme-sun { display: none; }
[data-theme="dark"] .theme-moon { display: block; }
```

## Mobile Navigation

### Bottom Navigation Bar
Mobile-first navigation with elevated central logo button.

```html
<nav class="mobile-nav">
  <a href="/patients" class="mobile-nav-link">
    <i class="material-icons">group</i>
    <span class="nav-label">Patients</span>
  </a>
  
  <a href="/appointments" class="mobile-nav-link">
    <i class="material-icons">event</i>
    <span class="nav-label">Schedule</span>
  </a>
  
  <a href="/dashboard" class="mobile-nav-link home-logo active">
    <!-- Light mode logo -->
    <svg viewBox="0 0 1000 1000" fill="none" class="logo-light">
      <circle cx="500" cy="500" r="500" fill="#96364C"/>
      <path d="M873 366.183C854.864 291.315..." stroke="white" stroke-width="30"/>
    </svg>
    <!-- Dark mode logo -->
    <svg viewBox="0 0 1000 1000" fill="none" class="logo-dark">
      <circle cx="500" cy="500" r="500" fill="#2D6356"/>
      <path d="M873 366.183C854.864 291.315..." stroke="white" stroke-width="30"/>
    </svg>
    <span class="nav-label">Home</span>
  </a>
  
  <a href="/reports" class="mobile-nav-link">
    <i class="material-icons">assessment</i>
    <span class="nav-label">Reports</span>
  </a>
  
  <a href="/profile" class="mobile-nav-link">
    <i class="material-icons">account_circle</i>
    <span class="nav-label">Profile</span>
  </a>
</nav>
```

```css
/* Mobile navigation - Light mode (gradient background) */
.mobile-nav {
  background: linear-gradient(to right, #2D6356, #32517A);
  color: white;
  padding: 12px 0;
  padding-bottom: calc(12px + env(safe-area-inset-bottom));
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  z-index: 1000;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.mobile-nav-link {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 48px;
  padding: 8px 12px;
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  transition: all 0.2s ease;
  border-radius: var(--radius-md);
  position: relative;
}

.mobile-nav-link:hover,
.mobile-nav-link.active:not(.home-logo) {
  color: white;
  background: rgba(255, 255, 255, 0.15);
  transform: translateY(-1px);
}

.mobile-nav-link .material-icons {
  font-size: 24px;
  margin-bottom: 4px;
}

.nav-label {
  font-size: 11px;
  font-weight: 500;
  text-align: center;
}

/* Central elevated logo button */
.mobile-nav-link.home-logo {
  position: relative;
  margin-top: -32px; /* Creates overlap above nav bar */
  opacity: 1 !important; /* Always full opacity */
}

.mobile-nav-link.home-logo svg {
  width: 68px;
  height: 68px;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.15));
  transition: transform 0.2s ease;
}

.mobile-nav-link.home-logo:hover svg {
  transform: scale(1.05);
  filter: drop-shadow(0 6px 12px rgba(0, 0, 0, 0.2));
}

.mobile-nav-link.home-logo .nav-label {
  margin-top: 4px;
}

/* Logo visibility based on theme */
.logo-light { display: block; }
.logo-dark { display: none; }

[data-theme="dark"] .logo-light { display: none; }
[data-theme="dark"] .logo-dark { display: block; }

/* Dark mode overrides */
[data-theme="dark"] .mobile-nav {
  background: var(--color-white);
  color: var(--color-text);
  border-top: 1px solid var(--color-border);
}

[data-theme="dark"] .mobile-nav-link {
  color: var(--color-muted);
}

[data-theme="dark"] .mobile-nav-link:hover,
[data-theme="dark"] .mobile-nav-link.active:not(.home-logo) {
  color: var(--color-primary);
  background: rgba(59, 127, 113, 0.15);
}
```

## Navigation States

### Active State Management
```javascript
// Active state management for navigation
function updateActiveNavigation() {
  const currentPath = window.location.pathname;
  const navLinks = document.querySelectorAll('.nav-link, .mobile-nav-link');
  
  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    
    // Remove active class from all links
    link.classList.remove('active');
    
    // Add active class to current page link
    if (href === currentPath || (href !== '/' && currentPath.startsWith(href))) {
      link.classList.add('active');
    }
  });
}

// Update navigation on page load and navigation
document.addEventListener('DOMContentLoaded', updateActiveNavigation);
window.addEventListener('popstate', updateActiveNavigation);
```

### Loading States
```css
.nav-link.loading {
  position: relative;
  opacity: 0.6;
  pointer-events: none;
}

.nav-link.loading::after {
  content: "";
  position: absolute;
  top: 50%;
  left: 50%;
  width: 16px;
  height: 16px;
  margin: -8px 0 0 -8px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid rgba(255, 255, 255, 0.8);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
```

## Responsive Navigation

### Navigation Switching
```css
/* Hide mobile nav on desktop */
@media (min-width: 769px) {
  .mobile-nav { display: none; }
  body { padding-bottom: 0; }
}

/* Hide desktop nav on mobile */
@media (max-width: 768px) {
  .desktop-nav { display: none; }
  body { padding-bottom: 80px; }
}
```

### Tablet Navigation
```css
@media (min-width: 769px) and (max-width: 1024px) {
  .nav-links {
    gap: var(--space-1);
  }
  
  .nav-link {
    padding: var(--space-2) var(--space-3);
    font-size: 14px;
  }
  
  .nav-link .material-icons {
    font-size: 18px;
  }
}
```

## Healthcare-Specific Navigation

### Clinical Workflow Navigation
```html
<nav class="workflow-nav">
  <div class="workflow-steps">
    <a href="/assessment" class="workflow-step completed">
      <i class="material-icons">assessment</i>
      <span>Assessment</span>
      <div class="step-indicator"></div>
    </a>
    
    <a href="/treatment" class="workflow-step active">
      <i class="material-icons">healing</i>
      <span>Treatment</span>
      <div class="step-indicator"></div>
    </a>
    
    <a href="/review" class="workflow-step">
      <i class="material-icons">rate_review</i>
      <span>Review</span>
      <div class="step-indicator"></div>
    </a>
  </div>
</nav>
```

```css
.workflow-nav {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  padding: var(--space-4) var(--space-6);
  margin-bottom: var(--space-6);
}

.workflow-steps {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-8);
  max-width: 600px;
  margin: 0 auto;
  position: relative;
}

.workflow-steps::before {
  content: "";
  position: absolute;
  top: 24px;
  left: 60px;
  right: 60px;
  height: 2px;
  background: var(--color-border);
  z-index: 1;
}

.workflow-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  text-decoration: none;
  color: var(--color-muted);
  transition: all 0.2s ease;
  position: relative;
  z-index: 2;
}

.workflow-step.completed {
  color: var(--color-primary);
}

.workflow-step.active {
  color: var(--color-secondary);
}

.workflow-step .material-icons {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-white);
  border: 2px solid var(--color-border);
  font-size: 24px;
}

.workflow-step.completed .material-icons {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.workflow-step.active .material-icons {
  background: var(--color-secondary);
  border-color: var(--color-secondary);
  color: white;
}
```

### Specialty Navigation
```html
<nav class="specialty-nav">
  <div class="specialty-tabs">
    <button class="specialty-tab active" data-specialty="physiotherapy">
      <i class="material-icons">directions_run</i>
      <span>Physiotherapy</span>
    </button>
    
    <button class="specialty-tab" data-specialty="occupational">
      <i class="material-icons">accessible</i>
      <span>Occupational</span>
    </button>
    
    <button class="specialty-tab" data-specialty="speech">
      <i class="material-icons">record_voice_over</i>
      <span>Speech</span>
    </button>
    
    <button class="specialty-tab" data-specialty="psychology">
      <i class="material-icons">psychology</i>
      <span>Psychology</span>
    </button>
  </div>
</nav>
```

```css
.specialty-nav {
  background: var(--color-white);
  border-bottom: 1px solid var(--color-border);
  padding: 0 var(--space-6);
}

.specialty-tabs {
  display: flex;
  gap: var(--space-2);
  overflow-x: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.specialty-tabs::-webkit-scrollbar {
  display: none;
}

.specialty-tab {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-5);
  background: transparent;
  border: none;
  color: var(--color-muted);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 3px solid transparent;
  white-space: nowrap;
}

.specialty-tab:hover {
  color: var(--color-text);
  background: var(--color-surface);
}

.specialty-tab.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

.specialty-tab .material-icons {
  font-size: 20px;
}
```

## Accessibility Guidelines

### Navigation Accessibility
```html
<!-- Proper ARIA labels and roles -->
<nav role="navigation" aria-label="Main navigation">
  <ul role="menubar">
    <li role="none">
      <a href="/dashboard" role="menuitem" aria-current="page">Dashboard</a>
    </li>
    <li role="none">
      <a href="/patients" role="menuitem">Patients</a>
    </li>
  </ul>
</nav>

<!-- Skip links for keyboard users -->
<a href="#main-content" class="skip-link">Skip to main content</a>

<!-- Mobile navigation with proper labeling -->
<nav role="navigation" aria-label="Mobile navigation">
  <a href="/dashboard" aria-label="Dashboard (current page)" aria-current="page">
    <i class="material-icons" aria-hidden="true">dashboard</i>
    <span>Dashboard</span>
  </a>
</nav>
```

### Keyboard Navigation
```css
/* Focus states */
.nav-link:focus-visible,
.mobile-nav-link:focus-visible {
  outline: 2px solid rgba(255, 255, 255, 0.8);
  outline-offset: 2px;
}

.workflow-step:focus-visible,
.specialty-tab:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-offset);
}

/* Skip link */
.skip-link {
  position: absolute;
  top: -40px;
  left: 6px;
  background: var(--color-primary);
  color: white;
  padding: 8px;
  text-decoration: none;
  border-radius: var(--radius-md);
  z-index: 1000;
  opacity: 0;
  transition: all 0.2s ease;
}

.skip-link:focus {
  top: 6px;
  opacity: 1;
}
```

## Healthcare-Specific Considerations

### Clinical Context Awareness
- Navigation should indicate current patient context when applicable
- Support for emergency navigation patterns
- Quick access to critical functions (patient alerts, urgent appointments)
- Integration with clinical workflow states

### Multi-Disciplinary Support
- Consistent navigation across healthcare specialties
- Specialty-specific quick actions without compromising general usability
- Support for cross-disciplinary patient handoffs
- Universal healthcare terminology in navigation labels

### POPIA Compliance
- Clear indication of data access levels in navigation
- Support for audit trail requirements in navigation logging
- Privacy-aware navigation states (e.g., patient names only when appropriate)
- Secure logout and session management integration

---

**Related Files:**
- [Logo System](../logo-system.md) - Navigation logo implementations
- [Dark Mode](../dark-mode.md) - Theme-aware navigation styling
- [Buttons](buttons.md) - Navigation button components
- [Mobile Design](../implementation/responsive-design.md) - Mobile navigation patterns

*This navigation system ensures consistent, accessible, and professional navigation across all HadadaHealth healthcare practice management interfaces while supporting clinical workflows and multi-device usage.*