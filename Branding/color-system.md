# Color System

> Comprehensive color palette and usage guidelines for HadadaHealth brand system.

## Primary Palette

### Primary Color
**Hadada Green** - `#2D6356`
- **Usage:** Primary CTAs, focus states, brand anchor
- **Application:** Save buttons, active states, progress indicators
- **Accessibility:** Meets WCAG AA contrast requirements on white backgrounds
- **Context:** The sole brand anchor - use sparingly for maximum impact

### Secondary Color  
**Deep Blue** - `#32517A`
- **Usage:** Links, secondary CTAs, active steps in workflows  
- **Application:** Navigation links, wizard active states, secondary actions
- **Context:** Supports primary color for interactive elements

### Destructive Color
**Deep Rose** - `#96364C`  
- **Usage:** Delete buttons, cancel actions, destructive operations
- **Application:** Remove patient, cancel appointment, delete records
- **Context:** Exclusively for delete/cancel operations

## Neutral Palette

### Text Colors
```css
--color-text: #1F2937;          /* Primary text - dark gray */
--color-muted: #6B7280;         /* Secondary text - medium gray */
```

### Interface Colors  
```css
--color-border: #E5E7EB;        /* Borders and dividers */
--color-surface: #F9FAFB;       /* Card and section backgrounds */
--color-white: #FFFFFF;         /* Pure white backgrounds */
```

## Status Colors

### Light Mode Status Colors
```css
--color-success: #059669;       /* Success states, completed actions */
--color-info: #0EA5E9;          /* Information, help text, notes */
--color-warning: #F59E0B;       /* Warnings, cautions, pending states */
--color-error: #DC3545;         /* Errors, validation failures */
```

### Dark Mode Status Colors
```css
--color-success: #10B981;       /* Brighter success for dark backgrounds */
--color-info: #3B82F6;          /* Standard blue for dark mode info */
--color-warning: #F59E0B;       /* Consistent warning across themes */
--color-error: #EF4444;         /* Enhanced error visibility on dark */
```

## Dark Mode Palette

### Enhanced Dark Mode Colors
```css
--color-primary-dark: #3B7F71;       /* Lighter primary for better contrast */
--color-secondary-dark: #4F6FBF;     /* Brighter blue for dark backgrounds */
--color-destructive-dark: #B8556B;   /* Muted destructive for dark theme */

--color-text-dark: #F3F4F6;          /* Light text on dark backgrounds */
--color-muted-dark: #9CA3AF;         /* Muted text with sufficient contrast */
--color-border-dark: #374151;        /* Dark mode borders */
--color-surface-dark: #0F1419;       /* Very dark background surface */
--color-white-dark: #1F2937;         /* Dark theme card backgrounds */
```

## Usage Rules

### Brand Color Guidelines
1. **Primary color** is the sole brand anchor - use sparingly for maximum impact
2. **Secondary color** supports primary for links and secondary actions  
3. **Destructive color** exclusively for delete/cancel operations
4. **Neutrals** form the foundation - use generously for text, borders, backgrounds
5. Never use colors outside this defined palette without approval

### Color Accessibility Requirements
- All color combinations must meet WCAG AA contrast ratio (4.5:1) minimum
- Never rely solely on color to convey information  
- Include text labels alongside color-coded elements
- Test with common color vision deficiencies

## Clinical Context Applications

### Patient Status Indicators
```css
/* Treatment completion status */
.status-complete { color: var(--color-success); }
.status-in-progress { color: var(--color-warning); }
.status-review-needed { color: var(--color-error); }
.status-scheduled { color: var(--color-info); }
```

### Discipline Tags
```css
.discipline-tag {
  background: rgba(45, 99, 86, 0.1);    /* Primary green with 10% opacity */
  color: var(--color-primary);
  border: 1px solid rgba(45, 99, 86, 0.2);
}

[data-theme="dark"] .discipline-tag {
  background: rgba(59, 127, 113, 0.15); /* Darker theme adjustment */
  color: var(--color-primary);
  border-color: rgba(59, 127, 113, 0.3);
}
```

### Progress Indicators
```css
.progress-active { background: var(--color-secondary); }
.progress-completed { background: var(--color-primary); }
.progress-pending { 
  background: var(--color-surface);
  border: 2px solid var(--color-border);
}
```

## Implementation Examples

### CSS Custom Properties Setup
```css
:root {
  /* Brand Colors - Same across themes */
  --color-primary: #2D6356;
  --color-secondary: #32517A;
  --color-destructive: #96364C;
  
  /* Light mode defaults */
  --color-text: #1F2937;
  --color-muted: #6B7280;
  --color-border: #E5E7EB;
  --color-surface: #F9FAFB;
  --color-white: #FFFFFF;
  
  /* Status colors */
  --color-success: #059669;
  --color-info: #0EA5E9;
  --color-warning: #F59E0B;
  --color-error: #DC3545;
}

[data-theme="dark"] {
  --color-primary: #3B7F71;
  --color-secondary: #4F6FBF;
  --color-destructive: #B8556B;
  
  --color-text: #F3F4F6;
  --color-muted: #9CA3AF;
  --color-border: #374151;
  --color-surface: #0F1419;
  --color-white: #1F2937;
  
  --color-success: #10B981;
  --color-info: #3B82F6;
  --color-warning: #F59E0B;
  --color-error: #EF4444;
}
```

### Button Color Applications
```css
.btn-primary {
  background: var(--color-primary);
  color: var(--color-white);
}

.btn-secondary {
  background: var(--color-white);
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
}

.btn-destructive {
  background: var(--color-destructive);
  color: var(--color-white);
}
```

### Form Validation Colors
```css
.input.success {
  border-color: var(--color-success);
}

.input.error {
  border-color: var(--color-error);
}

.validation-message.success {
  color: var(--color-success);
}

.validation-message.error {
  color: var(--color-error);
}
```

## Testing Guidelines

### Contrast Testing
- Use tools like WebAIM Contrast Checker for all color combinations
- Test with actual healthcare professionals in clinical lighting conditions
- Verify readability on various device types (phones, tablets, desktops)

### Color Vision Testing  
- Test with Deuteranopia (red-green color blindness) simulation
- Ensure information is accessible without color differentiation
- Include icons or text labels alongside color coding

### Device Testing
- Verify colors on various screen types (LCD, OLED, e-ink)
- Test in different lighting conditions (bright clinical lighting, dimmed rooms)
- Check color reproduction on both calibrated and uncalibrated displays

## Healthcare-Specific Considerations

### Clinical Documentation
- Use neutral colors for text-heavy documentation
- Reserve status colors for genuine status indications
- Maintain professional appearance in patient-facing materials

### Multi-Disciplinary Support  
- Colors should not favor any single healthcare specialty
- Universal healthcare appeal across all professional contexts
- Consistent meaning across different clinical workflows

### POPIA/GDPR Compliance
- Color coding must not accidentally expose sensitive patient information
- Status indicators should be meaningful but not reveal private details
- Audit trail interfaces should use neutral, professional colors

---

**Related Files:**
- [Dark Mode](dark-mode.md) - Complete theme switching implementation
- [CSS Variables](implementation/css-variables.md) - Technical implementation details
- [Accessibility](implementation/accessibility.md) - WCAG compliance guidelines

*This color system ensures consistent, accessible, and professional color usage across all HadadaHealth interfaces while supporting healthcare workflow requirements.*