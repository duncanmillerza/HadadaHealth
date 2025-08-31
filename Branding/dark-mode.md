# Dark Mode

> Professional healthcare dark theme system designed for clinical environments and extended use.

## Theme Philosophy

HadadaHealth implements a comprehensive dark mode system designed specifically for healthcare environments where practitioners may work in various lighting conditions. The theme system maintains clinical professionalism while reducing eye strain during extended use periods.

## Color System

### Light Mode (Default)
The primary brand experience optimized for clinical documentation and daytime usage.

```css
:root {
  --color-primary: #2D6356;        /* Primary Hadada Green */
  --color-secondary: #32517A;      /* Secondary Deep Blue */
  --color-destructive: #96364C;    /* Destructive Deep Rose */
  
  --color-text: #1F2937;          /* Primary text (dark gray) */
  --color-muted: #6B7280;         /* Secondary text (medium gray) */
  --color-border: #E5E7EB;        /* Borders and dividers */
  --color-surface: #F9FAFB;       /* Card and section backgrounds */
  --color-white: #FFFFFF;         /* Pure white backgrounds */
  
  --color-success: #059669;       /* Success state */
  --color-warning: #F59E0B;       /* Warning state */
  --color-error: #DC3545;         /* Error state */
  --color-info: #0EA5E9;          /* Information state */
  
  /* Light mode shadows */
  --shadow-card: 0 4px 12px rgba(0,0,0,.08);
  --shadow-modal: 0 8px 24px rgba(0,0,0,.12);
}
```

### Dark Mode
Optimized for low-light environments and extended screen time, maintaining accessibility and clinical clarity.

```css
[data-theme="dark"] {
  --color-primary: #3B7F71;       /* Lighter primary for better contrast */
  --color-secondary: #4F6FBF;     /* Enhanced brighter blue for dark mode */
  --color-destructive: #B8556B;   /* Muted version of destructive color */
  
  --color-text: #F3F4F6;          /* Light text on dark backgrounds */
  --color-muted: #9CA3AF;         /* Muted text with sufficient contrast */
  --color-border: #374151;        /* Dark borders */
  --color-surface: #0F1419;       /* Very dark background surface */
  --color-white: #1F2937;         /* Dark card background */
  
  --color-success: #10B981;       /* Success state (brighter for dark) */
  --color-warning: #F59E0B;       /* Warning state (consistent across themes) */
  --color-error: #EF4444;         /* Error state (enhanced for dark) */
  --color-info: #3B82F6;          /* Info state (standard blue for dark) */
  
  /* Enhanced shadows for dark mode */
  --shadow-card: 0 4px 12px rgba(0,0,0,.3);
  --shadow-modal: 0 8px 24px rgba(0,0,0,.5);
}
```

## Theme Toggle Implementation

### HTML Structure
```html
<button id="theme-toggle" class="theme-toggle" aria-label="Toggle dark mode">
  <span class="theme-icon-container">
    <i class="material-icons theme-sun">light_mode</i>
    <i class="material-icons theme-moon">dark_mode</i>
  </span>
</button>
```

### CSS Styling
```css
.theme-toggle {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: var(--radius-md);
  color: var(--color-white);
  padding: 8px;
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

### JavaScript Implementation
```javascript
class ThemeManager {
  constructor() {
    this.theme = localStorage.getItem('theme') || this.getSystemPreference();
    this.init();
  }

  init() {
    document.documentElement.setAttribute('data-theme', this.theme);
    this.updateToggleButton();
    this.bindEvents();
  }

  getSystemPreference() {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  toggle() {
    this.theme = this.theme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', this.theme);
    localStorage.setItem('theme', this.theme);
    this.updateToggleButton();
  }

  updateToggleButton() {
    const toggleButton = document.getElementById('theme-toggle');
    if (toggleButton) {
      toggleButton.setAttribute('aria-label', 
        this.theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'
      );
    }
  }

  bindEvents() {
    document.getElementById('theme-toggle')?.addEventListener('click', () => this.toggle());
    
    // Listen for system preference changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (!localStorage.getItem('theme')) {
        this.theme = e.matches ? 'dark' : 'light';
        this.init();
      }
    });
  }
}

// Initialize theme manager
document.addEventListener('DOMContentLoaded', () => {
  new ThemeManager();
});
```

## Component Adaptations for Dark Mode

### Button States
```css
/* Light mode button (default) */
.btn-primary {
  background: var(--color-primary);
  color: var(--color-white);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Enhanced disabled state for dark mode */
[data-theme="dark"] .btn:disabled {
  opacity: 0.3;
  background: var(--color-border) !important;
  color: rgba(255, 255, 255, 0.3) !important;
  border-color: transparent !important;
  box-shadow: none !important;
}
```

### Mobile Navigation
```css
/* Light mode - gradient background */
.mobile-nav {
  background: linear-gradient(to right, #2D6356, #32517A);
  color: white;
}

.mobile-nav-link {
  color: rgba(255, 255, 255, 0.8);
}

.mobile-nav-link:hover,
.mobile-nav-link.active {
  color: white;
  background: rgba(255, 255, 255, 0.15);
}

/* Dark mode - solid dark background */
[data-theme="dark"] .mobile-nav {
  background: var(--color-white);
  color: var(--color-text);
  border-top-color: var(--color-border);
}

[data-theme="dark"] .mobile-nav-link {
  color: var(--color-muted);
}

[data-theme="dark"] .mobile-nav-link:hover,
[data-theme="dark"] .mobile-nav-link.active {
  color: var(--color-primary);
  background: rgba(59, 127, 113, 0.15);
}
```

### Clinical Components
```css
/* Patient cards in dark mode */
[data-theme="dark"] .patient-card:hover {
  background: rgba(59, 127, 113, 0.1);
}

/* Discipline tags in dark mode */
[data-theme="dark"] .discipline-tag {
  background: rgba(59, 127, 113, 0.15);
  color: var(--color-primary);
  border-color: rgba(59, 127, 113, 0.3);
}

/* Progress indicators in dark mode */
[data-theme="dark"] .dot.active {
  background: var(--color-secondary);
  color: white;
  border: 2px solid var(--color-secondary);
}
```

## Accessibility in Dark Mode

### Contrast Requirements
- **Text contrast:** Minimum 4.5:1 ratio maintained in both themes
- **Interactive elements:** Clear focus states with sufficient contrast
- **Color independence:** Never rely solely on color to convey information

### WCAG 2.1 AA Compliance
- All color combinations tested for accessibility compliance
- Focus indicators remain visible in both light and dark modes
- Text remains readable across all theme states

### Testing Implementation
```css
/* Focus states that work in both themes */
.btn:focus-visible,
.input:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  [data-theme="dark"] .text-muted {
    color: var(--color-text);
  }
}
```

## Healthcare-Specific Dark Mode Considerations

### Clinical Environment Usage
- **Reduced eye strain:** Lower brightness for extended documentation sessions
- **Low-light compatibility:** Optimal for dimmed clinical rooms
- **Screen sharing:** Maintains professionalism during telemedicine
- **Equipment compatibility:** Works well alongside medical device displays

### Patient Privacy
- **Reduced screen glow:** Less conspicuous during patient interactions
- **Professional appearance:** Maintains clinical credibility
- **Focused attention:** Dark backgrounds reduce distractions

## Theme Persistence

### Storage Strategy
```javascript
// Check for saved theme preference or default to system preference
const savedTheme = localStorage.getItem('theme');
const systemPreference = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
const currentTheme = savedTheme || systemPreference;

// Apply theme immediately to prevent flash
document.documentElement.setAttribute('data-theme', currentTheme);
```

### Implementation Best Practices
- **localStorage:** User preference stored locally
- **System preference:** Respects OS dark mode setting when no preference set
- **Session continuity:** Theme maintained across browser sessions
- **No FOUC:** Theme applied before page render to prevent flash of unstyled content

## Performance Considerations

### CSS Organization
```css
/* Base styles (mobile-first, light theme default) */
.component { 
  background: var(--color-white);
  color: var(--color-text);
}

/* Dark theme overrides grouped together */
[data-theme="dark"] .component { 
  background: var(--color-surface);
  color: var(--color-text);
}

/* Responsive overrides after theme styles */
@media (min-width: 769px) {
  .component { 
    padding: var(--space-8); 
  }
  [data-theme="dark"] .component { 
    border: 1px solid var(--color-border);
  }
}
```

### Loading Performance
- **Critical CSS:** Theme styles included in critical path
- **No FOUC:** Theme applied before page render
- **Efficient selectors:** Grouped theme overrides for better performance

## Logo Integration

### Theme-Specific Logo Usage
```css
/* Logo visibility based on theme */
.logo-light { display: block; }
.logo-dark { display: none; }

[data-theme="dark"] .logo-light { display: none; }
[data-theme="dark"] .logo-dark { display: block; }
```

### Mobile Navigation Logo Colors
- **Light Mode:** Deep Rose (#96364C) for brand accent
- **Dark Mode:** Primary Green (#2D6356) for consistency
- **Purpose:** Prominent central home button in mobile bottom navigation

## Testing Guidelines

### Visual Testing
- **Component states:** All interactive states tested in both themes
- **Contrast verification:** Automated and manual contrast testing
- **Brand consistency:** Logo and branding appropriate for each theme

### Functional Testing
- **Toggle behavior:** Smooth transitions between themes
- **Persistence:** Theme setting maintained across sessions  
- **System integration:** Respects OS preferences appropriately
- **Performance:** No layout shifts or rendering delays during theme changes

### Healthcare Context Testing
- **Clinical lighting:** Test in various healthcare environment lighting conditions
- **Extended use:** Verify reduced eye strain during long documentation sessions
- **Device compatibility:** Test on tablets and mobile devices used in clinical settings
- **Professional appearance:** Ensure clinical credibility maintained in dark mode

---

**Related Files:**
- [Color System](color-system.md) - Complete color palette specifications
- [CSS Variables](implementation/css-variables.md) - Technical implementation details
- [Mobile Navigation](components/navigation.md) - Theme-aware navigation implementation

*This dark mode system provides a professional healthcare-appropriate dark theme that reduces eye strain while maintaining clinical credibility and accessibility standards.*