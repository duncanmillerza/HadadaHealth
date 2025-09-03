# CSS Variables

> Complete custom properties system for dual-theme support in HadadaHealth healthcare practice management interfaces.

## CSS Variable Philosophy

HadadaHealth uses a comprehensive CSS custom properties system that provides consistent design tokens across all interface elements while supporting seamless light/dark theme switching. This system ensures maintainability, consistency, and performance in healthcare applications.

## Complete Variable System

### Brand Colors (Theme Independent)
Core brand colors that remain consistent across all themes.

```css
:root {
  /* Brand Colors - Same across themes */
  --color-primary: #2D6356;     /* Hadada Green - sole brand anchor */
  --color-secondary: #32517A;   /* Deep Blue - links, secondary CTAs */
  --color-destructive: #96364C; /* Destructive secondary - delete/cancel actions */
}
```

### Theme-Specific Color Variables
Comprehensive color system supporting light and dark modes.

```css
:root {
  /* Light mode colors */
  --color-text-light: #1F2937;        /* Main text */
  --color-muted-light: #6B7280;       /* Muted text */
  --color-border-light: #E5E7EB;      /* Borders */
  --color-surface-light: #F9FAFB;     /* Background surfaces */
  --color-white-light: #FFFFFF;       /* Pure white */
  
  /* Dark mode colors - Professional healthcare dark theme */
  --color-primary-dark: #3B7F71;       /* Slightly brighter version of original green */
  --color-secondary-dark: #4F6FBF;     /* Brighter blue for dark mode */
  --color-destructive-dark: #B8556B;   /* Muted version of destructive color */
  --color-text-dark: #F3F4F6;          /* Light text on dark */
  --color-muted-dark: #9CA3AF;         /* Muted text for dark */
  --color-border-dark: #374151;        /* Dark borders */
  --color-surface-dark: #0F1419;       /* Very dark background */
  --color-white-dark: #1F2937;         /* Dark card background */
  
  /* Status colors for light mode */
  --color-success-light: #059669;
  --color-info-light: #0EA5E9;
  --color-warning-light: #F59E0B;
  --color-error-light: #DC3545;
  
  /* Status colors for dark mode - more subdued */
  --color-success-dark: #10B981;
  --color-info-dark: #3B82F6;
  --color-warning-dark: #F59E0B;
  --color-error-dark: #EF4444;
}
```

### Active Theme Variables
Variables that automatically switch based on the active theme.

```css
:root {
  /* Default to light mode */
  --color-text: var(--color-text-light);
  --color-muted: var(--color-muted-light);
  --color-border: var(--color-border-light);
  --color-surface: var(--color-surface-light);
  --color-white: var(--color-white-light);
  --color-success: var(--color-success-light);
  --color-info: var(--color-info-light);
  --color-warning: var(--color-warning-light);
  --color-error: var(--color-error-light);
}

/* Dark mode activation */
[data-theme="dark"] {
  --color-primary: var(--color-primary-dark);
  --color-secondary: var(--color-secondary-dark);
  --color-destructive: var(--color-destructive-dark);
  --color-text: var(--color-text-dark);
  --color-muted: var(--color-muted-dark);
  --color-border: var(--color-border-dark);
  --color-surface: var(--color-surface-dark);
  --color-white: var(--color-white-dark);
  --color-success: var(--color-success-dark);
  --color-info: var(--color-info-dark);
  --color-warning: var(--color-warning-dark);
  --color-error: var(--color-error-dark);
}
```

## Layout Design Tokens

### Spacing System
Consistent 4px-based spacing grid for all interface elements.

```css
:root {
  /* Spacing - 4px grid system */
  --space-0: 0px;
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-7: 28px;
  --space-8: 32px;
  --space-9: 36px;
  --space-10: 40px;
  --space-12: 48px;
  --space-14: 56px;
  --space-16: 64px;
  --space-20: 80px;
  --space-24: 96px;
  --space-32: 128px;
}
```

### Border Radius System
Consistent border radius values across all components.

```css
:root {
  /* Border radius - Single radius across all components */
  --radius-none: 0px;
  --radius-sm: 4px;
  --radius-md: 8px;          /* Primary radius for all components */
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;     /* Circular elements */
  
  /* Component-specific radius (all use md for consistency) */
  --radius-button: var(--radius-md);
  --radius-card: var(--radius-md);
  --radius-input: var(--radius-md);
  --radius-modal: var(--radius-md);
}
```

### Shadow System
Comprehensive shadow system with theme-aware variations.

```css
:root {
  /* Light mode shadows */
  --shadow-card: 0 4px 12px rgba(0, 0, 0, 0.08);
  --shadow-modal: 0 8px 24px rgba(0, 0, 0, 0.12);
  --shadow-dropdown: 0 4px 16px rgba(0, 0, 0, 0.1);
  --shadow-button: 0 2px 4px rgba(45, 99, 86, 0.2);
  --shadow-focus: 0 0 0 3px rgba(45, 99, 86, 0.1);
  
  /* Dark mode shadows - more pronounced */
  --shadow-card-dark: 0 4px 12px rgba(0, 0, 0, 0.3);
  --shadow-modal-dark: 0 8px 24px rgba(0, 0, 0, 0.5);
  --shadow-dropdown-dark: 0 4px 16px rgba(0, 0, 0, 0.4);
  --shadow-button-dark: 0 2px 4px rgba(59, 127, 113, 0.3);
  --shadow-focus-dark: 0 0 0 3px rgba(59, 127, 113, 0.2);
}

[data-theme="dark"] {
  --shadow-card: var(--shadow-card-dark);
  --shadow-modal: var(--shadow-modal-dark);
  --shadow-dropdown: var(--shadow-dropdown-dark);
  --shadow-button: var(--shadow-button-dark);
  --shadow-focus: var(--shadow-focus-dark);
}
```

## Typography Variables

### Font Families
Healthcare-appropriate font stacks for digital and print contexts.

```css
:root {
  /* Typography - System fonts only for digital, serif for print */
  --font-ui: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --font-serif: Georgia, "Times New Roman", Times, serif; /* PDF/print only */
  --font-mono: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
}
```

### Font Sizes
Comprehensive typography scale with responsive considerations.

```css
:root {
  /* Font sizes - rem-based scale */
  --text-xs: 0.75rem;        /* 12px */
  --text-sm: 0.875rem;       /* 14px */
  --text-base: 1rem;         /* 16px */
  --text-lg: 1.125rem;       /* 18px */
  --text-xl: 1.25rem;        /* 20px */
  --text-2xl: 1.5rem;        /* 24px */
  --text-3xl: 1.875rem;      /* 30px */
  --text-4xl: 2.25rem;       /* 36px */
  --text-5xl: 3rem;          /* 48px */
  
  /* Heading sizes */
  --text-h1: var(--text-5xl);   /* 48px / 3rem */
  --text-h2: var(--text-3xl);   /* 30px / 1.875rem */
  --text-h3: var(--text-xl);    /* 20px / 1.25rem */
  --text-h4: var(--text-lg);    /* 18px / 1.125rem */
  --text-h5: var(--text-base);  /* 16px / 1rem */
  --text-h6: var(--text-sm);    /* 14px / 0.875rem */
  
  /* UI component sizes */
  --text-button: 0.9375rem;     /* 15px */
  --text-input: var(--text-base);
  --text-label: var(--text-sm);
  --text-caption: var(--text-xs);
}
```

### Font Weights
Consistent font weight scale for interface hierarchy.

```css
:root {
  /* Font weights */
  --font-thin: 100;
  --font-extralight: 200;
  --font-light: 300;
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;
  --font-extrabold: 800;
  --font-black: 900;
  
  /* Component-specific font weights */
  --weight-body: var(--font-normal);
  --weight-heading: var(--font-semibold);
  --weight-button: var(--font-medium);
  --weight-label: var(--font-medium);
  --weight-nav: var(--font-medium);
}
```

### Line Heights
Optimized line heights for healthcare content readability.

```css
:root {
  /* Line heights */
  --leading-none: 1;
  --leading-tight: 1.25;
  --leading-snug: 1.375;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;
  --leading-loose: 2;
  
  /* Context-specific line heights */
  --leading-body: var(--leading-relaxed);    /* 1.625 for readability */
  --leading-heading: var(--leading-tight);   /* 1.25 for headings */
  --leading-ui: var(--leading-normal);       /* 1.5 for UI elements */
}
```

## Interactive States

### Focus System
Comprehensive focus state variables for accessibility compliance.

```css
:root {
  /* Focus states - WCAG 2.1 AA compliant */
  --focus-outline: 2px solid rgba(45, 99, 86, 0.6);
  --focus-outline-dark: 2px solid rgba(59, 127, 113, 0.8);
  --focus-offset: 2px;
  --focus-radius: var(--radius-md);
  
  /* Focus ring colors by context */
  --focus-primary: rgba(45, 99, 86, 0.6);
  --focus-secondary: rgba(50, 81, 122, 0.6);
  --focus-destructive: rgba(150, 54, 76, 0.6);
  --focus-success: rgba(5, 150, 105, 0.6);
  --focus-warning: rgba(245, 158, 11, 0.6);
  --focus-error: rgba(220, 53, 69, 0.6);
}

[data-theme="dark"] {
  --focus-outline: var(--focus-outline-dark);
  --focus-primary: rgba(59, 127, 113, 0.8);
  --focus-secondary: rgba(79, 111, 191, 0.8);
  --focus-destructive: rgba(184, 85, 107, 0.8);
}
```

### Animation Variables
Consistent timing and easing functions for all animations.

```css
:root {
  /* Animation timing */
  --duration-fast: 0.15s;
  --duration-normal: 0.2s;
  --duration-slow: 0.3s;
  --duration-slower: 0.5s;
  
  /* Easing functions */
  --ease-linear: linear;
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-bounce: cubic-bezier(0.175, 0.885, 0.32, 1.275);
  --ease-back: cubic-bezier(0.68, -0.55, 0.265, 1.55);
  
  /* Component-specific animations */
  --transition-button: all var(--duration-normal) var(--ease-out);
  --transition-card: all var(--duration-slow) var(--ease-in-out);
  --transition-modal: all var(--duration-normal) var(--ease-out);
  --transition-dropdown: all var(--duration-fast) var(--ease-out);
}
```

## Breakpoint System

### Responsive Breakpoints
Mobile-first responsive design breakpoints.

```css
:root {
  /* Breakpoints - Mobile-first approach */
  --bp-xs: 0px;           /* Extra small devices */
  --bp-sm: 480px;         /* Small phones */
  --bp-md: 768px;         /* Tablets */
  --bp-lg: 1024px;        /* Small laptops */
  --bp-xl: 1280px;        /* Desktops */
  --bp-2xl: 1536px;       /* Large desktops */
  
  /* Container max-widths */
  --container-sm: 640px;
  --container-md: 768px;
  --container-lg: 1024px;
  --container-xl: 1280px;
  --container-2xl: 1536px;
}
```

### Component Sizing
Responsive component dimensions based on breakpoints.

```css
:root {
  /* Component heights */
  --height-input: 48px;
  --height-input-sm: 40px;
  --height-input-lg: 56px;
  --height-button: 44px;
  --height-button-sm: 36px;
  --height-button-lg: 52px;
  --height-nav: 64px;
  --height-nav-mobile: 80px;
  
  /* Component widths */
  --width-sidebar: 280px;
  --width-sidebar-collapsed: 80px;
  --width-modal-sm: 400px;
  --width-modal-md: 600px;
  --width-modal-lg: 800px;
  --width-modal-xl: 1200px;
}

/* Mobile adjustments */
@media (max-width: 768px) {
  :root {
    --height-input: 44px;
    --height-button: 44px;
    --height-nav: 56px;
  }
}
```

## Healthcare-Specific Variables

### Clinical Interface Variables
Variables specific to healthcare practice management interfaces.

```css
:root {
  /* Patient card dimensions */
  --patient-card-width: 320px;
  --patient-avatar-size: 56px;
  --patient-avatar-size-sm: 40px;
  
  /* Appointment timeline */
  --timeline-width: 4px;
  --timeline-dot-size: 12px;
  --timeline-gap: 24px;
  
  /* Progress indicators */
  --progress-height: 8px;
  --progress-height-sm: 4px;
  --progress-height-lg: 12px;
  
  /* Status indicators */
  --status-badge-height: 24px;
  --discipline-tag-height: 28px;
  
  /* Assessment forms */
  --section-gap: 32px;
  --field-gap: 16px;
  --form-max-width: 800px;
}
```

### POPIA Compliance Variables
Variables supporting privacy and compliance features.

```css
:root {
  /* Privacy indicator colors */
  --color-privacy-secure: var(--color-success);
  --color-privacy-warning: var(--color-warning);
  --color-privacy-restricted: var(--color-error);
  
  /* Audit trail styling */
  --color-audit-background: rgba(14, 165, 233, 0.05);
  --color-audit-border: rgba(14, 165, 233, 0.2);
  
  /* Data export/import */
  --color-export-background: rgba(245, 158, 11, 0.1);
  --color-export-border: rgba(245, 158, 11, 0.3);
}
```

## Usage Examples

### Component Implementation
How to use CSS variables in component styling.

```css
/* Button component using variables */
.btn {
  padding: var(--space-3) var(--space-5);
  border-radius: var(--radius-button);
  font-size: var(--text-button);
  font-weight: var(--weight-button);
  font-family: var(--font-ui);
  transition: var(--transition-button);
  border: none;
  cursor: pointer;
}

.btn-primary {
  background: var(--color-primary);
  color: var(--color-white);
  box-shadow: var(--shadow-button);
}

.btn:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-offset);
}

/* Card component using variables */
.card {
  background: var(--color-white);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  padding: var(--space-8);
  box-shadow: var(--shadow-card);
  transition: var(--transition-card);
}

/* Input component using variables */
.input {
  width: 100%;
  height: var(--height-input);
  padding: var(--space-3) var(--space-4);
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-input);
  font-size: var(--text-input);
  font-family: var(--font-ui);
  color: var(--color-text);
  background: var(--color-white);
  transition: var(--transition-dropdown);
}

.input:focus {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-focus);
  outline: none;
}
```

### Responsive Variable Usage
Using variables with media queries for responsive design.

```css
/* Responsive typography */
.heading {
  font-size: var(--text-2xl);
  line-height: var(--leading-heading);
  font-weight: var(--weight-heading);
}

@media (max-width: 768px) {
  .heading {
    font-size: var(--text-xl);
  }
}

@media (max-width: 480px) {
  .heading {
    font-size: var(--text-lg);
  }
}

/* Responsive spacing */
.container {
  padding: var(--space-6);
  margin-bottom: var(--space-8);
}

@media (max-width: 768px) {
  .container {
    padding: var(--space-4);
    margin-bottom: var(--space-6);
  }
}
```

## Variable Customization

### Creating Custom Themes
How to extend the variable system for custom themes.

```css
/* Custom theme example - High Contrast Mode */
[data-theme="high-contrast"] {
  --color-text: #000000;
  --color-white: #FFFFFF;
  --color-border: #000000;
  --color-primary: #0000FF;
  --color-success: #008000;
  --color-error: #FF0000;
  --color-warning: #FFD700;
  
  /* Enhanced focus states for high contrast */
  --focus-outline: 3px solid var(--color-primary);
  --focus-offset: 3px;
  
  /* Stronger shadows */
  --shadow-card: 0 4px 16px rgba(0, 0, 0, 0.3);
  --shadow-modal: 0 8px 32px rgba(0, 0, 0, 0.4);
}

/* Custom theme for specific healthcare specialties */
[data-theme="pediatric"] {
  --color-primary: #22C55E;     /* Friendly green */
  --color-secondary: #3B82F6;   /* Playful blue */
  --color-surface: #F0FDF4;     /* Very light green background */
}
```

### Variable Fallbacks
Ensuring compatibility with older browsers.

```css
/* Fallback values for older browsers */
.btn-primary {
  background: #2D6356; /* Fallback */
  background: var(--color-primary);
  
  color: #FFFFFF; /* Fallback */
  color: var(--color-white);
  
  padding: 12px 20px; /* Fallback */
  padding: var(--space-3) var(--space-5);
}

/* Feature detection for CSS custom properties */
@supports (--css: custom-properties) {
  .modern-component {
    /* Modern implementation using variables */
  }
}

@supports not (--css: custom-properties) {
  .modern-component {
    /* Fallback implementation without variables */
  }
}
```

## Performance Considerations

### Variable Optimization
Best practices for CSS variable performance.

```css
/* Use variables efficiently */
:root {
  /* Good: Logical grouping and naming */
  --color-primary: #2D6356;
  --color-primary-hover: #236B59;
  --color-primary-light: rgba(45, 99, 86, 0.1);
}

/* Avoid excessive nesting */
.component {
  /* Good: Direct variable usage */
  color: var(--color-text);
  
  /* Avoid: Over-nesting variables */
  /* color: var(--color-text, var(--fallback-color, #000000)); */
}

/* Use calc() efficiently with variables */
.dynamic-spacing {
  /* Good: Simple calculations */
  margin: calc(var(--space-4) * 2);
  
  /* Avoid: Complex calculations that could be pre-computed */
  /* margin: calc(var(--space-4) * var(--multiplier) + var(--offset)); */
}
```

### Loading Performance
Optimizing CSS variables for fast loading.

```css
/* Critical variables loaded first */
:root {
  /* Essential layout variables */
  --color-primary: #2D6356;
  --color-white: #FFFFFF;
  --color-text: #1F2937;
  --space-4: 16px;
  --radius-md: 8px;
}

/* Non-critical variables can be loaded later */
.extended-variables {
  /* Advanced theming variables */
  --specialized-color: #custom;
}
```

## Maintenance Guidelines

### Variable Naming Conventions
Consistent naming patterns for maintainability.

```css
/* Naming convention: --[category]-[property]-[variant] */
:root {
  /* Colors */
  --color-primary: #2D6356;
  --color-primary-hover: #236B59;
  --color-primary-light: rgba(45, 99, 86, 0.1);
  
  /* Spacing */
  --space-4: 16px;
  --space-mobile-4: 12px;
  
  /* Shadows */
  --shadow-card: 0 4px 12px rgba(0, 0, 0, 0.08);
  --shadow-card-dark: 0 4px 12px rgba(0, 0, 0, 0.3);
  
  /* Typography */
  --text-base: 1rem;
  --text-mobile-base: 0.9rem;
}
```

### Documentation Standards
How to document CSS variables for team usage.

```css
:root {
  /* ======================
     BRAND COLORS
     Use these for all brand-related elements
     ====================== */
  --color-primary: #2D6356;     /* Hadada Green - primary CTAs only */
  --color-secondary: #32517A;   /* Deep Blue - links and secondary actions */
  --color-destructive: #96364C; /* Deep Rose - delete/cancel actions only */
  
  /* ======================
     SPACING SYSTEM
     Based on 4px grid - use for consistent spacing
     ====================== */
  --space-1: 4px;    /* Minimal spacing */
  --space-2: 8px;    /* Small gaps */
  --space-4: 16px;   /* Default spacing */
  --space-8: 32px;   /* Section spacing */
}
```

---

**Related Files:**
- [Color System](../color-system.md) - Color variable specifications and usage
- [Dark Mode](../dark-mode.md) - Theme switching implementation
- [Typography](../typography.md) - Typography variable usage
- [Responsive Design](responsive-design.md) - Responsive variable patterns

*This CSS variable system ensures consistent, maintainable, and theme-aware styling across all HadadaHealth healthcare practice management interfaces while supporting scalability and customization.*