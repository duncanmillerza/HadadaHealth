# Responsive Design

> Mobile-first responsive design implementation for HadadaHealth healthcare practice management interfaces.

## Responsive Design Philosophy

HadadaHealth prioritizes mobile experience as healthcare professionals frequently access the system on tablets and smartphones during patient care. Our responsive design ensures optimal usability across all device types while maintaining clinical professionalism and workflow efficiency.

## Breakpoint System

### Mobile-First Breakpoints
Progressive enhancement from mobile to desktop sizes.

```css
/* Mobile-first breakpoint system */
:root {
  --bp-xs: 0px;           /* Extra small phones */
  --bp-sm: 480px;         /* Small phones */
  --bp-md: 768px;         /* Tablets */
  --bp-lg: 1024px;        /* Small laptops */
  --bp-xl: 1280px;        /* Desktops */
  --bp-2xl: 1536px;       /* Large desktops */
}

/* Media query mixins for consistency */
@media (min-width: 480px) {
  /* Small phones and up */
}

@media (min-width: 768px) {
  /* Tablets and up */
}

@media (min-width: 1024px) {
  /* Small laptops and up */
}

@media (min-width: 1280px) {
  /* Desktops and up */
}
```

### Responsive Containers
Flexible container system for different screen sizes.

```css
.container {
  width: 100%;
  margin-left: auto;
  margin-right: auto;
  padding-left: var(--space-4);
  padding-right: var(--space-4);
}

/* Container max-widths */
@media (min-width: 480px) {
  .container { max-width: 640px; }
}

@media (min-width: 768px) {
  .container { 
    max-width: 768px;
    padding-left: var(--space-6);
    padding-right: var(--space-6);
  }
}

@media (min-width: 1024px) {
  .container { max-width: 1024px; }
}

@media (min-width: 1280px) {
  .container { max-width: 1280px; }
}

/* Full-width container variant */
.container-fluid {
  width: 100%;
  padding-left: var(--space-4);
  padding-right: var(--space-4);
}

@media (min-width: 768px) {
  .container-fluid {
    padding-left: var(--space-6);
    padding-right: var(--space-6);
  }
}
```

## Grid System

### Responsive Grid
Flexible CSS Grid system for healthcare interfaces.

```css
.grid {
  display: grid;
  gap: var(--space-6);
  width: 100%;
}

/* Responsive grid patterns */
.grid-1 { grid-template-columns: 1fr; }
.grid-2 { grid-template-columns: repeat(2, 1fr); }
.grid-3 { grid-template-columns: repeat(3, 1fr); }
.grid-4 { grid-template-columns: repeat(4, 1fr); }

/* Auto-fit grids for dynamic content */
.grid-auto-sm { grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
.grid-auto-md { grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }
.grid-auto-lg { grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); }

/* Mobile-first responsive behavior */
@media (max-width: 767px) {
  .grid-2,
  .grid-3,
  .grid-4 {
    grid-template-columns: 1fr;
    gap: var(--space-4);
  }
}

@media (min-width: 768px) and (max-width: 1023px) {
  .grid-4 {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .grid-3 {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Healthcare-specific grid patterns */
.patient-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--space-6);
}

@media (max-width: 767px) {
  .patient-grid {
    grid-template-columns: 1fr;
    gap: var(--space-4);
  }
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-5);
}
```

## Typography Scaling

### Responsive Typography
Optimized text sizing across devices for healthcare readability.

```css
/* Base typography - mobile first */
h1 {
  font-size: 1.75rem;        /* 28px */
  line-height: var(--leading-tight);
  font-weight: var(--weight-heading);
  margin: var(--space-6) 0 var(--space-4);
}

h2 {
  font-size: 1.25rem;        /* 20px */
  line-height: var(--leading-tight);
  font-weight: var(--weight-heading);
  margin: var(--space-5) 0 var(--space-3);
}

h3 {
  font-size: 1rem;           /* 16px */
  line-height: var(--leading-normal);
  font-weight: var(--weight-heading);
  margin: var(--space-4) 0 var(--space-3);
}

body, p {
  font-size: 0.9rem;         /* 14.4px */
  line-height: var(--leading-body);
}

/* Tablet and up scaling */
@media (min-width: 768px) {
  h1 {
    font-size: 2rem;          /* 32px */
    margin: var(--space-8) 0 var(--space-4);
  }
  
  h2 {
    font-size: 1.5rem;        /* 24px */
    margin: var(--space-6) 0 var(--space-3);
  }
  
  h3 {
    font-size: 1.125rem;      /* 18px */
  }
  
  body, p {
    font-size: 1rem;          /* 16px */
  }
}

/* Desktop scaling */
@media (min-width: 1024px) {
  h1 {
    font-size: 2.5rem;        /* 40px */
  }
  
  h2 {
    font-size: 1.75rem;       /* 28px */
  }
  
  h3 {
    font-size: 1.25rem;       /* 20px */
  }
}

/* UI element typography */
.btn {
  font-size: 13px;
}

@media (min-width: 768px) {
  .btn {
    font-size: 14px;
  }
}

@media (min-width: 1024px) {
  .btn {
    font-size: 15px;
  }
}

/* Clinical content typography - maintains readability */
.clinical-text {
  font-size: 15px;
  line-height: 1.7;
}

@media (min-width: 768px) {
  .clinical-text {
    font-size: 16px;
    line-height: 1.6;
  }
}
```

## Component Responsive Behavior

### Button Responsive Design
Touch-optimized buttons across device sizes.

```css
.btn {
  padding: 12px 20px;
  font-size: 13px;
  min-height: 44px;        /* iOS touch target minimum */
  border-radius: var(--radius-md);
  transition: var(--transition-button);
}

.btn-sm {
  padding: 8px 16px;
  font-size: 12px;
  min-height: 36px;
}

.btn-lg {
  padding: 16px 28px;
  font-size: 15px;
  min-height: 52px;
}

/* Tablet adjustments */
@media (min-width: 768px) {
  .btn {
    padding: 14px 24px;
    font-size: 14px;
    min-height: 48px;
  }
  
  .btn-sm {
    padding: 10px 18px;
    font-size: 13px;
    min-height: 40px;
  }
  
  .btn-lg {
    padding: 18px 32px;
    font-size: 16px;
    min-height: 56px;
  }
}

/* Desktop refinements */
@media (min-width: 1024px) {
  .btn {
    font-size: 15px;
  }
  
  .btn-sm {
    font-size: 14px;
  }
  
  .btn-lg {
    font-size: 17px;
  }
}

/* Full-width mobile buttons */
@media (max-width: 479px) {
  .btn-mobile-full {
    width: 100%;
    justify-content: center;
  }
  
  .form-actions .btn {
    width: 100%;
    margin-bottom: 12px;
  }
  
  .form-actions .btn:last-child {
    margin-bottom: 0;
  }
}
```

### Form Responsive Design
Healthcare-optimized form layouts for various devices.

```css
.input {
  width: 100%;
  min-height: 44px;        /* Touch-friendly minimum */
  padding: 12px 16px;
  font-size: 16px;         /* Prevents iOS zoom */
  border-radius: var(--radius-md);
}

.textarea {
  min-height: 100px;
  padding: 12px 16px;
  font-size: 16px;
}

.select {
  min-height: 44px;
  padding: 12px 48px 12px 16px;
  font-size: 16px;
}

/* Tablet optimizations */
@media (min-width: 768px) {
  .input {
    min-height: 48px;
    padding: 14px 16px;
    font-size: 15px;
  }
  
  .textarea {
    min-height: 120px;
    padding: 14px 16px;
    font-size: 15px;
  }
  
  .select {
    min-height: 48px;
    padding: 14px 48px 14px 16px;
    font-size: 15px;
  }
}

/* Form layout patterns */
.form-row {
  display: grid;
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}

@media (min-width: 768px) {
  .form-row {
    grid-template-columns: 1fr 1fr;
    gap: var(--space-5);
  }
}

.form-row-thirds {
  display: grid;
  gap: var(--space-4);
}

@media (min-width: 768px) {
  .form-row-thirds {
    grid-template-columns: repeat(3, 1fr);
    gap: var(--space-4);
  }
}

@media (min-width: 1024px) {
  .form-row-thirds {
    gap: var(--space-5);
  }
}
```

### Card Responsive Design
Patient and clinical cards optimized for different screen sizes.

```css
.card {
  padding: var(--space-4);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  margin-bottom: var(--space-4);
}

@media (min-width: 768px) {
  .card {
    padding: var(--space-6);
    margin-bottom: var(--space-6);
  }
}

@media (min-width: 1024px) {
  .card {
    padding: var(--space-8);
  }
}

/* Patient card responsive behavior */
.patient-card {
  padding: var(--space-4);
}

.patient-card .patient-header {
  flex-direction: column;
  gap: var(--space-3);
}

@media (min-width: 480px) {
  .patient-card .patient-header {
    flex-direction: row;
    gap: var(--space-4);
  }
}

@media (min-width: 768px) {
  .patient-card {
    padding: var(--space-6);
  }
}

/* Patient actions responsive layout */
.patient-actions {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}

@media (max-width: 479px) {
  .patient-actions {
    flex-direction: column;
  }
  
  .patient-actions .btn {
    width: 100%;
    justify-content: center;
  }
}

@media (min-width: 480px) and (max-width: 767px) {
  .patient-actions .btn {
    flex: 1;
    min-width: 120px;
  }
}
```

## Navigation Responsive Design

### Desktop vs Mobile Navigation
Adaptive navigation systems for different device types.

```css
/* Desktop navigation (hidden on mobile) */
.desktop-nav {
  background: var(--color-primary);
  padding: var(--space-5) var(--space-6);
  display: none;
}

@media (min-width: 769px) {
  .desktop-nav {
    display: flex;
    align-items: center;
    gap: var(--space-6);
  }
  
  body {
    padding-top: 0;
    padding-bottom: 0;
  }
}

/* Mobile navigation (hidden on desktop) */
.mobile-nav {
  background: linear-gradient(to right, #2D6356, #32517A);
  padding: 12px 0;
  padding-bottom: calc(12px + env(safe-area-inset-bottom));
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-around;
  z-index: 1000;
}

@media (max-width: 768px) {
  body {
    padding-bottom: 80px;
  }
}

@media (min-width: 769px) {
  .mobile-nav {
    display: none;
  }
}

/* Navigation link responsive sizing */
.nav-link {
  padding: var(--space-2) var(--space-4);
  font-size: 14px;
}

@media (min-width: 1024px) {
  .nav-link {
    padding: var(--space-3) var(--space-5);
    font-size: 15px;
  }
}

.mobile-nav-link {
  min-width: 48px;
  padding: 8px 12px;
  font-size: 11px;
}

@media (min-width: 480px) {
  .mobile-nav-link {
    font-size: 12px;
    padding: 10px 14px;
  }
}
```

## Healthcare-Specific Responsive Patterns

### Clinical Workflow Responsive Design
Optimized layouts for clinical documentation and workflows.

```css
/* Assessment form responsive layout */
.assessment-sections {
  padding: var(--space-4);
}

@media (min-width: 768px) {
  .assessment-sections {
    padding: var(--space-6);
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-8);
  }
}

@media (min-width: 1024px) {
  .assessment-sections {
    padding: var(--space-8);
  }
}

/* Timeline responsive behavior */
.timeline-item {
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-2);
  padding: var(--space-3);
}

@media (min-width: 480px) {
  .timeline-item {
    flex-direction: row;
    align-items: center;
    gap: var(--space-4);
    padding: var(--space-4);
  }
}

/* Progress stepper responsive layout */
.stepper {
  overflow-x: auto;
  padding-bottom: var(--space-4);
}

@media (min-width: 768px) {
  .stepper {
    overflow-x: visible;
    padding-bottom: 0;
  }
}

.step {
  min-width: 100px;
  flex-shrink: 0;
}

@media (min-width: 768px) {
  .step {
    min-width: auto;
    flex: 1;
  }
}
```

### Dashboard Responsive Layout
Healthcare dashboard optimized for various screen sizes.

```css
.dashboard {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-4);
}

@media (min-width: 768px) {
  .dashboard {
    grid-template-columns: 1fr 300px;
    gap: var(--space-6);
    padding: var(--space-6);
  }
}

@media (min-width: 1024px) {
  .dashboard {
    grid-template-columns: 1fr 350px;
    gap: var(--space-8);
    padding: var(--space-8);
  }
}

/* Dashboard widgets responsive grid */
.dashboard-widgets {
  display: grid;
  gap: var(--space-4);
}

@media (min-width: 480px) {
  .dashboard-widgets {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .dashboard-widgets {
    grid-template-columns: repeat(3, 1fr);
    gap: var(--space-5);
  }
}

/* Stat cards responsive layout */
.stat-cards {
  display: grid;
  gap: var(--space-4);
}

@media (min-width: 480px) {
  .stat-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 768px) {
  .stat-cards {
    grid-template-columns: repeat(4, 1fr);
  }
}
```

## Performance Optimizations

### Responsive Images
Optimized image loading for healthcare interfaces.

```css
/* Responsive image sizing */
.responsive-image {
  width: 100%;
  height: auto;
  max-width: 100%;
}

/* Avatar responsive sizing */
.patient-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
}

@media (min-width: 768px) {
  .patient-avatar {
    width: 48px;
    height: 48px;
  }
}

@media (min-width: 1024px) {
  .patient-avatar {
    width: 56px;
    height: 56px;
  }
}

/* Logo responsive sizing */
.brand-logo {
  height: 32px;
  width: auto;
}

@media (min-width: 768px) {
  .brand-logo {
    height: 40px;
  }
}

@media (min-width: 1024px) {
  .brand-logo {
    height: 48px;
  }
}
```

### CSS Loading Strategy
Optimized CSS delivery for different screen sizes.

```css
/* Critical mobile styles (inlined) */
.critical-mobile {
  /* Essential mobile styles */
}

/* Non-critical tablet+ styles (loaded separately) */
@media (min-width: 768px) {
  .enhanced-tablet {
    /* Enhanced tablet features */
  }
}

@media (min-width: 1024px) {
  .enhanced-desktop {
    /* Desktop enhancements */
  }
}
```

## Accessibility Considerations

### Touch Target Sizing
WCAG-compliant touch targets across devices.

```css
/* Minimum touch target sizes */
.touchable {
  min-width: 44px;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (min-width: 768px) {
  .touchable {
    min-width: 32px;
    min-height: 32px;
  }
}

/* Touch target spacing */
.touch-list .touch-item {
  margin-bottom: 8px;
}

@media (min-width: 768px) {
  .touch-list .touch-item {
    margin-bottom: 4px;
  }
}
```

### Focus Management
Responsive focus states for keyboard navigation.

```css
.focusable:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-offset);
}

/* Larger focus indicators on touch devices */
@media (pointer: coarse) {
  .focusable:focus-visible {
    outline-width: 3px;
    outline-offset: 3px;
  }
}
```

## Testing Guidelines

### Device Testing Matrix
Recommended devices and screen sizes for testing.

```
Mobile Devices:
- iPhone SE (375×667) - Small mobile baseline
- iPhone 12/13 (390×844) - Standard mobile
- iPhone 12/13 Pro Max (428×926) - Large mobile
- Samsung Galaxy S21 (360×800) - Android standard

Tablets:
- iPad (768×1024) - Standard tablet
- iPad Air (820×1180) - Modern tablet
- iPad Pro 11" (834×1194) - Professional tablet

Desktop:
- MacBook Air (1440×900) - Small laptop
- Standard Desktop (1920×1080) - Common desktop
- Large Desktop (2560×1440) - High resolution

Healthcare-Specific Testing:
- Medical tablet cart screens
- Wall-mounted clinic displays
- Handheld devices with gloves
- Various lighting conditions
```

### Breakpoint Testing
Systematic approach to responsive testing.

```javascript
// Responsive testing breakpoints
const testBreakpoints = [
  { name: 'Mobile Small', width: 375 },
  { name: 'Mobile Large', width: 480 },
  { name: 'Tablet', width: 768 },
  { name: 'Laptop', width: 1024 },
  { name: 'Desktop', width: 1280 },
  { name: 'Large Desktop', width: 1536 }
];

// Test critical healthcare workflows at each breakpoint:
// - Patient registration
// - Appointment scheduling  
// - Clinical documentation
// - Report generation
// - Emergency access patterns
```

## Healthcare-Specific Considerations

### Clinical Environment Adaptations
Responsive design considerations for healthcare settings.

```css
/* High contrast mode for clinical displays */
@media (prefers-contrast: high) {
  .clinical-interface {
    border-width: 2px;
    font-weight: var(--font-semibold);
  }
}

/* Reduced motion for sensitive clinical environments */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}

/* Print styles for clinical reports */
@media print {
  body {
    font-family: var(--font-serif);
    font-size: 12pt;
    line-height: 1.5;
    color: black;
    background: white;
  }
  
  .no-print {
    display: none !important;
  }
  
  .print-break {
    page-break-before: always;
  }
}
```

### POPIA Compliance Responsive Design
Privacy-aware responsive patterns for healthcare data.

```css
/* Responsive privacy indicators */
.privacy-indicator {
  font-size: 12px;
  padding: 4px 8px;
}

@media (min-width: 768px) {
  .privacy-indicator {
    font-size: 13px;
    padding: 6px 12px;
  }
}

/* Responsive data masking for shared screens */
@media (max-width: 768px) {
  .sensitive-data.public-view {
    filter: blur(4px);
  }
  
  .sensitive-data.public-view:hover,
  .sensitive-data.public-view:focus {
    filter: none;
  }
}
```

---

**Related Files:**
- [CSS Variables](css-variables.md) - Responsive variable usage
- [Mobile Navigation](../components/navigation.md) - Mobile navigation implementation
- [Touch Interactions](../interactions/touch-interactions.md) - Mobile touch patterns
- [Accessibility](accessibility.md) - Responsive accessibility guidelines

*This responsive design system ensures optimal healthcare practice management interfaces across all device types while maintaining clinical professionalism, workflow efficiency, and accessibility compliance.*