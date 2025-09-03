# Buttons

> Interactive button system for HadadaHealth healthcare practice management interfaces.

## Button Hierarchy

### Primary Button
Main actions and primary calls-to-action in healthcare workflows.

```css
.btn-primary {
  background: var(--color-primary);
  color: var(--color-white);
  border: none;
  padding: 14px 24px;
  border-radius: var(--radius-md);
  font-size: 15px;
  font-weight: 500;
  font-family: var(--font-ui);
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(45, 99, 86, 0.2);
  min-height: 48px;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(45, 99, 86, 0.25);
}

.btn-primary:active {
  transform: translateY(1px);
}
```

**Usage:** Save, Create, Submit, Schedule Appointment, Generate Report

### Secondary Button
Alternative actions and secondary calls-to-action.

```css
.btn-secondary {
  background: var(--color-white);
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
  padding: 14px 24px;
  border-radius: var(--radius-md);
  font-size: 15px;
  font-weight: 500;
  font-family: var(--font-ui);
  cursor: pointer;
  transition: all 0.2s ease;
  min-height: 48px;
}

.btn-secondary:hover {
  background: var(--color-primary);
  color: var(--color-white);
  transform: translateY(-1px);
}
```

**Usage:** Cancel, Edit, View Details, Back

### Tertiary Button  
Text-based buttons for minimal actions.

```css
.btn-tertiary {
  background: transparent;
  color: var(--color-secondary);
  border: none;
  padding: 14px 16px;
  font-size: 15px;
  font-weight: 500;
  font-family: var(--font-ui);
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
  transition: all 0.2s ease;
  min-height: 48px;
}

.btn-tertiary:hover {
  color: var(--color-primary);
  text-decoration: none;
}
```

**Usage:** Text links, minimal actions, "Learn more" links

### Destructive Button
Delete, remove, and cancel operations.

```css
.btn-destructive {
  background: var(--color-destructive);
  color: var(--color-white);
  border: none;
  padding: 14px 24px;
  border-radius: var(--radius-md);
  font-size: 15px;
  font-weight: 500;
  font-family: var(--font-ui);
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(150, 54, 76, 0.2);
  min-height: 48px;
}

.btn-destructive:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(150, 54, 76, 0.25);
}
```

**Usage:** Delete Patient, Cancel Appointment, Remove Record

## Button Sizes

### Standard Button (Default)
```css
.btn {
  padding: 14px 24px;
  font-size: 15px;
  min-height: 48px;
}
```

### Small Button
For compact spaces and secondary actions.

```css
.btn-sm {
  padding: 8px 16px;
  font-size: 14px;
  min-height: 36px;
}
```

### Large Button  
For primary actions and mobile interfaces.

```css
.btn-lg {
  padding: 18px 32px;
  font-size: 16px;
  min-height: 56px;
}
```

## Button States

### Disabled State
```css
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn:disabled:hover {
  transform: none;
  box-shadow: none;
}

/* Enhanced disabled state for dark mode */
[data-theme="dark"] .btn:disabled {
  opacity: 0.3;
  background: var(--color-border) !important;
  color: rgba(255, 255, 255, 0.3) !important;
  border-color: transparent !important;
}
```

### Loading State
```css
.btn.loading {
  position: relative;
  color: transparent;
  pointer-events: none;
}

.btn.loading::after {
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

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
```

### Focus State
```css
.btn:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-offset);
}
```

## Button with Icons

### Icon + Text Pattern
```html
<button class="btn btn-primary">
  <i class="material-icons icon-20">description</i>
  <span>Add Treatment Note</span>
</button>
```

```css
.btn .material-icons {
  margin-right: 8px;
  font-size: 20px;
}

.icon-20 { font-size: 20px; }
.icon-16 { font-size: 16px; }
.icon-24 { font-size: 24px; }
```

### Icon-Only Button
```html
<button class="btn btn-icon" aria-label="Edit patient details">
  <i class="material-icons">edit</i>
</button>
```

```css
.btn-icon {
  width: 48px;
  height: 48px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-icon.btn-sm {
  width: 36px;
  height: 36px;
}
```

## Clinical Button Patterns

### Treatment Action Buttons
```html
<div class="treatment-actions">
  <button class="btn btn-primary">
    <i class="material-icons icon-20">add</i>
    New Assessment
  </button>
  <button class="btn btn-secondary">
    <i class="material-icons icon-20">schedule</i>
    Schedule Follow-up
  </button>
  <button class="btn btn-tertiary">
    <i class="material-icons icon-20">history</i>
    View History
  </button>
</div>
```

### Patient Management Buttons
```html
<div class="patient-actions">
  <button class="btn btn-primary">
    <i class="material-icons icon-20">person_add</i>
    Add Patient
  </button>
  <button class="btn btn-secondary">
    <i class="material-icons icon-20">edit</i>
    Edit Details
  </button>
  <button class="btn btn-destructive">
    <i class="material-icons icon-20">delete</i>
    Archive Patient
  </button>
</div>
```

### Form Action Buttons
```html
<div class="form-actions">
  <button type="submit" class="btn btn-primary">
    <i class="material-icons icon-20">save</i>
    Save Changes
  </button>
  <button type="button" class="btn btn-secondary">
    Cancel
  </button>
</div>
```

## Interactive Enhancements

### Ripple Effect
Material Design-inspired ripple animation for tactile feedback.

```css
.btn {
  position: relative;
  overflow: hidden;
}

/* Ripple animation added via JavaScript */
.ripple {
  position: absolute;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  pointer-events: none;
  animation: ripple 0.6s linear;
}

@keyframes ripple {
  0% {
    opacity: 1;
    transform: scale(0);
  }
  100% {
    opacity: 0;
    transform: scale(2);
  }
}
```

```javascript
// Button ripple effect implementation
document.querySelectorAll('.btn').forEach(button => {
  button.addEventListener('click', function(e) {
    const ripple = document.createElement('span');
    const rect = this.getBoundingClientRect();
    const size = Math.max(rect.height, rect.width);
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;
    
    ripple.className = 'ripple';
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    
    this.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
  });
});
```

## Mobile Optimizations

### Touch-Friendly Sizing
```css
@media (max-width: 768px) {
  .btn {
    min-height: 44px;
    font-size: 14px;
    padding: 12px 20px;
  }
  
  .btn-lg {
    min-height: 52px;
    padding: 16px 28px;
  }
  
  .btn-sm {
    min-height: 40px;
    font-size: 13px;
  }
}
```

### Full-Width Mobile Buttons
```css
@media (max-width: 480px) {
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

## Accessibility Guidelines

### Minimum Requirements
- **Touch targets:** 44px minimum for mobile devices
- **Color contrast:** Meet WCAG AA standards (4.5:1 ratio)
- **Focus indicators:** Visible focus states for keyboard navigation
- **Screen readers:** Descriptive labels for all buttons

### Implementation
```html
<!-- Descriptive button text -->
<button class="btn btn-primary">
  Schedule Appointment
</button>

<!-- Icon-only buttons need aria-label -->
<button class="btn btn-icon" aria-label="Edit patient information">
  <i class="material-icons">edit</i>
</button>

<!-- Loading state announcement -->
<button class="btn btn-primary loading" aria-label="Saving patient data">
  Save Changes
</button>
```

### High Contrast Mode Support
```css
@media (prefers-contrast: high) {
  .btn {
    border-width: 2px;
  }
  
  .btn-tertiary {
    border: 1px solid currentColor;
    background: var(--color-white);
  }
}
```

## Healthcare-Specific Guidelines

### Clinical Context Usage
- Use **primary buttons** for patient care actions (Save Assessment, Schedule Treatment)
- Use **secondary buttons** for administrative actions (Edit Details, View Reports)
- Use **destructive buttons** sparingly and only for genuine deletion/removal
- Always include confirmation dialogs for destructive actions

### Professional Appearance
- Maintain consistent button styling across all healthcare specialties
- Use clear, professional language in button text
- Include relevant healthcare icons when space permits
- Ensure buttons work well in clinical lighting conditions

### POPIA Compliance
- Include confirmation steps for actions involving patient data export
- Use clear language for data-related actions ("Export Patient Data", not "Export")
- Ensure destructive actions include appropriate warnings

---

**Related Files:**
- [Color System](../color-system.md) - Button color specifications
- [Typography](../typography.md) - Button text styling
- [Forms](forms.md) - Form-specific button usage
- [Touch Interactions](../interactions/touch-interactions.md) - Mobile button interactions

*This button system ensures consistent, accessible, and professional interactive elements across all HadadaHealth healthcare practice management interfaces.*