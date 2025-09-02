# Hover Effects

> Desktop interaction animations and hover states for HadadaHealth healthcare practice management interfaces.

## Hover Effect Philosophy

HadadaHealth implements sophisticated hover effects designed specifically for desktop healthcare environments. Hover states provide immediate visual feedback and enhance usability while maintaining clinical professionalism. All hover effects are designed to support rapid clinical workflows without being distracting.

## Component Hover States

### Button Hover Effects
Professional button interactions with appropriate feedback.

```css
.btn {
  transition: all 0.2s ease;
  transform: translateY(0);
}

.btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(45, 99, 86, 0.25);
}

.btn-primary:hover {
  box-shadow: 0 4px 12px rgba(45, 99, 86, 0.3);
  background: #236B59; /* Slightly darker primary */
}

.btn-secondary:hover {
  background: var(--color-primary);
  color: var(--color-white);
  border-color: var(--color-primary);
}

.btn-tertiary:hover {
  color: var(--color-primary);
  text-decoration: none;
  background: rgba(45, 99, 86, 0.05);
}

.btn-destructive:hover {
  box-shadow: 0 4px 12px rgba(150, 54, 76, 0.3);
  background: #7D2D40; /* Slightly darker destructive */
}

/* Icon button hover */
.btn-icon:hover {
  background: rgba(45, 99, 86, 0.1);
  transform: scale(1.05);
}

/* Disabled state - no hover effect */
.btn:disabled:hover {
  transform: none;
  box-shadow: none;
}
```

### Card Hover Effects
Sophisticated card interactions for clinical interfaces.

```css
.card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
  transform: translateY(0) scale(1);
}

.card:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  border-color: rgba(45, 99, 86, 0.2);
}

[data-theme="dark"] .card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  border-color: rgba(59, 127, 113, 0.3);
}

/* Interactive card with pointer cursor */
.card-interactive:hover {
  cursor: pointer;
  border-color: var(--color-primary);
}

/* Patient card specific hover */
.patient-card {
  border-left: 4px solid transparent;
  transition: all 0.3s ease;
}

.patient-card:hover {
  border-left-color: var(--color-primary);
  background: rgba(45, 99, 86, 0.02);
  transform: translateX(4px);
  cursor: pointer;
}

[data-theme="dark"] .patient-card:hover {
  background: rgba(59, 127, 113, 0.1);
}

/* Treatment card hover with progress emphasis */
.treatment-card:hover .progress-fill {
  background: var(--color-secondary);
  box-shadow: 0 0 8px rgba(50, 81, 122, 0.3);
}
```

### Form Control Hover Effects
Enhanced form interactions for clinical data entry.

```css
.input {
  transition: all 0.2s ease;
  border-color: var(--color-border);
}

.input:hover {
  border-color: rgba(45, 99, 86, 0.4);
}

.input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(45, 99, 86, 0.1);
}

/* Select dropdown hover */
.select:hover {
  border-color: rgba(45, 99, 86, 0.4);
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%232D6356' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6,9 12,15 18,9'%3e%3c/polyline%3e%3c/svg%3e");
}

/* Textarea resize handle highlight */
.textarea:hover {
  border-color: rgba(45, 99, 86, 0.4);
  resize: both;
}

/* Checkbox and radio hover */
.checkbox:hover,
.radio:hover {
  outline: 2px solid rgba(45, 99, 86, 0.2);
  outline-offset: 2px;
}

/* Label hover when associated with form controls */
.label:hover {
  color: var(--color-primary);
  cursor: pointer;
}
```

## Navigation Hover Effects

### Desktop Navigation Hover
Professional navigation interactions with smooth transitions.

```css
.nav-link {
  transition: all 0.2s ease;
  opacity: 0.9;
  border-bottom: 2px solid transparent;
}

.nav-link:hover {
  opacity: 1;
  background: rgba(255, 255, 255, 0.1);
  border-bottom-color: rgba(255, 255, 255, 0.5);
}

.nav-link.active {
  opacity: 1;
  border-bottom-color: var(--color-white);
}

/* Theme toggle hover */
.theme-toggle:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* User menu hover */
.user-button:hover {
  background: rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-md);
}
```

### Workflow Navigation Hover
Enhanced hover states for clinical workflow navigation.

```css
.workflow-step {
  transition: all 0.2s ease;
  color: var(--color-muted);
}

.workflow-step:hover {
  color: var(--color-text);
  cursor: pointer;
}

.workflow-step:hover .material-icons {
  background: rgba(45, 99, 86, 0.1);
  border-color: var(--color-primary);
  transform: scale(1.05);
}

.workflow-step.completed:hover .material-icons {
  background: var(--color-secondary);
  border-color: var(--color-secondary);
}

.workflow-step.active:hover .material-icons {
  box-shadow: 0 0 0 4px rgba(50, 81, 122, 0.2);
}

/* Specialty tab hover */
.specialty-tab {
  transition: all 0.2s ease;
  border-bottom: 3px solid transparent;
}

.specialty-tab:hover {
  color: var(--color-text);
  background: var(--color-surface);
  border-bottom-color: rgba(45, 99, 86, 0.3);
}

.specialty-tab.active:hover {
  border-bottom-color: var(--color-primary);
}
```

## Color Swatch Interactions

### Interactive Color Demonstrations
Enhanced hover effects for brand color swatches.

```css
.swatch {
  transition: all 0.3s ease;
  cursor: pointer;
}

.swatch:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.swatch:hover .chip {
  filter: brightness(1.1) saturate(1.2);
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

/* Color chip with specific hover effects */
.chip {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.swatch-primary:hover .chip {
  box-shadow: 0 4px 12px rgba(45, 99, 86, 0.4);
}

.swatch-secondary:hover .chip {
  box-shadow: 0 4px 12px rgba(50, 81, 122, 0.4);
}

.swatch-destructive:hover .chip {
  box-shadow: 0 4px 12px rgba(150, 54, 76, 0.4);
}

/* Tooltip on hover for color information */
.swatch:hover::after {
  content: attr(data-color-name);
  position: absolute;
  bottom: -30px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  z-index: 10;
}
```

## Clinical Component Hover Effects

### Status Indicator Hover
Enhanced hover states for treatment and patient status indicators.

```css
.status-badge {
  transition: all 0.2s ease;
  cursor: default;
}

.status-badge.interactive {
  cursor: pointer;
}

.status-badge.interactive:hover {
  transform: scale(1.05);
  filter: brightness(1.1);
}

.status-badge.active:hover {
  box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.2);
}

.status-badge.pending:hover {
  box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.2);
}

.status-badge.error:hover {
  box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.2);
}

/* Discipline tag hover */
.discipline-tag {
  transition: all 0.2s ease;
  cursor: pointer;
}

.discipline-tag:hover {
  background: rgba(45, 99, 86, 0.15);
  border-color: var(--color-primary);
  transform: translateY(-1px);
}

[data-theme="dark"] .discipline-tag:hover {
  background: rgba(59, 127, 113, 0.25);
}
```

### Progress Indicator Hover
Enhanced hover effects for clinical progress tracking.

```css
.stepper .step {
  transition: all 0.2s ease;
}

.stepper .step:hover {
  cursor: pointer;
}

.stepper .step:hover .dot {
  transform: scale(1.1);
  box-shadow: 0 0 0 4px rgba(45, 99, 86, 0.1);
}

.stepper .step.completed:hover .dot {
  box-shadow: 0 0 0 4px rgba(45, 99, 86, 0.2);
}

.stepper .step.active:hover .dot {
  box-shadow: 0 0 0 4px rgba(50, 81, 122, 0.2);
}

.stepper .step:hover .step-title {
  color: var(--color-primary);
}

/* Progress bar hover effects */
.progress-bar {
  transition: all 0.2s ease;
}

.progress-container:hover .progress-bar {
  box-shadow: 0 0 0 1px rgba(45, 99, 86, 0.2);
  border-radius: 4px;
}

.progress-container:hover .progress-fill {
  filter: brightness(1.1);
}
```

## Table and List Hover Effects

### Patient List Hover
Row hover effects for patient and appointment lists.

```css
.table-row,
.list-item {
  transition: all 0.2s ease;
  border-radius: var(--radius-md);
}

.table-row:hover,
.list-item:hover {
  background: rgba(45, 99, 86, 0.03);
  cursor: pointer;
  transform: translateX(2px);
}

[data-theme="dark"] .table-row:hover,
[data-theme="dark"] .list-item:hover {
  background: rgba(59, 127, 113, 0.08);
}

/* Appointment timeline item hover */
.timeline-item {
  transition: all 0.2s ease;
  border-radius: var(--radius-md);
}

.timeline-item:hover {
  background: var(--color-surface);
  cursor: pointer;
  padding-left: calc(var(--space-4) + 4px);
  border-left: 4px solid var(--color-primary);
}

.timeline-item.current:hover {
  background: rgba(45, 99, 86, 0.08);
  border-left-color: var(--color-secondary);
}

/* Table header hover for sortable columns */
.table-header.sortable {
  transition: all 0.2s ease;
}

.table-header.sortable:hover {
  background: var(--color-surface);
  cursor: pointer;
  color: var(--color-primary);
}

.table-header.sortable:hover .sort-icon {
  opacity: 1;
  color: var(--color-primary);
}
```

## Advanced Hover Patterns

### Logo Hover Effects
Professional logo interactions for branding elements.

```css
.logo-interactive {
  transition: all 0.2s ease;
  cursor: pointer;
}

.logo-interactive:hover {
  transform: scale(1.05);
  filter: drop-shadow(0 4px 8px rgba(45, 99, 86, 0.2));
}

/* Mobile navigation logo hover */
.mobile-nav-link.home-logo:hover svg {
  transform: scale(1.05);
  filter: drop-shadow(0 6px 12px rgba(0, 0, 0, 0.2));
}

/* Brand wordmark hover */
.nav-brand:hover {
  opacity: 0.9;
  cursor: pointer;
}
```

### Icon Hover Effects
Consistent icon interaction patterns.

```css
.icon-interactive {
  transition: all 0.2s ease;
  cursor: pointer;
  border-radius: 50%;
  padding: 8px;
}

.icon-interactive:hover {
  background: rgba(45, 99, 86, 0.1);
  color: var(--color-primary);
  transform: scale(1.1);
}

/* Status icon hover with contextual colors */
.status-icon.success:hover {
  color: var(--color-success);
  background: rgba(5, 150, 105, 0.1);
}

.status-icon.warning:hover {
  color: var(--color-warning);
  background: rgba(245, 158, 11, 0.1);
}

.status-icon.error:hover {
  color: var(--color-error);
  background: rgba(220, 53, 69, 0.1);
}

.status-icon.info:hover {
  color: var(--color-info);
  background: rgba(14, 165, 233, 0.1);
}
```

## Healthcare-Specific Hover Patterns

### Emergency Action Hover
Special hover effects for urgent healthcare actions.

```css
.btn-emergency {
  transition: all 0.2s ease;
}

.btn-emergency:hover {
  background: #B91C1C; /* Brighter red for urgency */
  transform: scale(1.02);
  box-shadow: 0 6px 20px rgba(185, 28, 28, 0.4);
}

/* Critical action hover with enhanced feedback */
.btn-critical:hover {
  animation: pulse-critical 2s infinite;
}

@keyframes pulse-critical {
  0% { box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3); }
  50% { box-shadow: 0 6px 20px rgba(220, 53, 69, 0.5); }
  100% { box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3); }
}
```

### POPIA Compliance Hover
Hover effects for data privacy and compliance elements.

```css
.privacy-notice {
  transition: all 0.2s ease;
  cursor: help;
}

.privacy-notice:hover {
  background: rgba(14, 165, 233, 0.05);
  border-color: var(--color-info);
}

.data-export-btn:hover {
  background: rgba(245, 158, 11, 0.1);
  border-color: var(--color-warning);
  color: var(--color-warning);
}

.data-export-btn:hover::after {
  content: "POPIA compliant export";
  position: absolute;
  bottom: -30px;
  left: 0;
  background: rgba(245, 158, 11, 0.9);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
}
```

## Accessibility Considerations

### Focus vs Hover
Ensuring hover effects don't interfere with keyboard navigation.

```css
/* Hover effects only for pointer devices */
@media (hover: hover) and (pointer: fine) {
  .hover-only:hover {
    /* Hover effects here */
  }
}

/* Focus states should be distinct from hover */
.interactive:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-offset);
}

/* Combined hover and focus states */
.interactive:hover,
.interactive:focus-visible {
  color: var(--color-primary);
}

.interactive:hover:focus-visible {
  outline-color: var(--color-secondary);
}
```

### High Contrast Mode
Ensuring hover effects work in high contrast environments.

```css
@media (prefers-contrast: high) {
  .card:hover {
    border: 2px solid currentColor;
    box-shadow: none;
  }
  
  .btn:hover {
    border: 2px solid currentColor;
    box-shadow: none;
  }
  
  .status-badge:hover {
    outline: 2px solid currentColor;
    outline-offset: 2px;
  }
}
```

### Reduced Motion Support
Respecting user motion preferences for hover effects.

```css
@media (prefers-reduced-motion: reduce) {
  .card:hover,
  .btn:hover,
  .logo-interactive:hover {
    transform: none;
    transition: color 0.2s ease, background-color 0.2s ease;
  }
  
  .swatch:hover .chip {
    transform: none;
    filter: brightness(1.1);
  }
}
```

## Performance Optimization

### Hover Performance
Optimized hover effects for smooth interactions.

```css
/* Use transform and opacity for better performance */
.hover-optimized {
  will-change: transform, opacity;
  backface-visibility: hidden;
}

.hover-optimized:hover {
  will-change: auto; /* Remove will-change after hover */
}

/* Avoid layout-triggering properties in hover */
.efficient-hover {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.efficient-hover:hover {
  transform: translateY(-2px); /* Use transform instead of margin/padding */
}

/* Debounce hover effects for performance */
.debounced-hover {
  transition: all 0.3s ease;
}
```

### Memory Management
```javascript
// Efficient hover event handling
class HoverManager {
  constructor() {
    this.hoveredElements = new Set();
  }
  
  addHoverEffect(element) {
    if (!this.hoveredElements.has(element)) {
      element.addEventListener('mouseenter', this.handleMouseEnter);
      element.addEventListener('mouseleave', this.handleMouseLeave);
      this.hoveredElements.add(element);
    }
  }
  
  removeHoverEffect(element) {
    element.removeEventListener('mouseenter', this.handleMouseEnter);
    element.removeEventListener('mouseleave', this.handleMouseLeave);
    this.hoveredElements.delete(element);
  }
  
  handleMouseEnter = (e) => {
    e.target.classList.add('hovered');
  }
  
  handleMouseLeave = (e) => {
    e.target.classList.remove('hovered');
  }
  
  cleanup() {
    this.hoveredElements.forEach(element => {
      this.removeHoverEffect(element);
    });
    this.hoveredElements.clear();
  }
}
```

---

**Related Files:**
- [Animations](animations.md) - Animation patterns for hover effects
- [Touch Interactions](touch-interactions.md) - Mobile-first interaction patterns
- [Buttons](../components/buttons.md) - Button hover state implementations
- [Accessibility](../implementation/accessibility.md) - Hover accessibility guidelines

*This hover effect system ensures professional, accessible, and performance-optimized desktop interactions across all HadadaHealth healthcare practice management interfaces while supporting clinical workflows and maintaining medical credibility.*