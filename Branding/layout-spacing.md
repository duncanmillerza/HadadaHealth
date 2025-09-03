# Layout & Spacing System

> 4px grid-based spacing system with consistent border radius and shadow specifications

## Spacing System

### 4px Grid Foundation
Based on 4px grid system for mathematical consistency and visual harmony:

```css
:root {
  --space-1: 4px;   /* Micro spacing, tight elements */
  --space-2: 8px;   /* Small spacing, related elements */
  --space-3: 12px;  /* Compact spacing, form groups */
  --space-4: 16px;  /* Default spacing, comfortable separation */
  --space-5: 20px;  /* Medium spacing, section padding */
  --space-6: 24px;  /* Large spacing, component margins */
  --space-8: 32px;  /* Extra large spacing, card padding */
  --space-10: 40px; /* Section spacing */
  --space-12: 48px; /* Major section separation */
}
```

### Usage Guidelines

#### Component Spacing
- **Inside cards:** `--space-8` (32px) padding
- **Between form fields:** `--space-4` (16px) margin
- **Button padding:** `--space-4` horizontal, `--space-3` vertical
- **Section margins:** `--space-10` (40px) between major sections

#### Layout Spacing
- **Container padding:** `--space-4` (16px) on mobile, `--space-6` (24px) on desktop
- **Grid gaps:** `--space-6` (24px) for card grids
- **Content margins:** `--space-8` (32px) between distinct content blocks

## Border Radius

### Single Radius System
- **Standard:** 8px for all components
- **Consistency:** Use single radius value across entire system
- **Application:** Buttons, cards, inputs, modals, badges

```css
:root {
  --radius-md: 8px; /* Single radius for all components */
}

.btn, .card, .input, .modal, .badge {
  border-radius: var(--radius-md);
}
```

### Healthcare Context
- **Clinical consistency:** Single radius creates professional, cohesive appearance
- **Touch accessibility:** 8px provides adequate visual definition without sharp edges
- **Brand recognition:** Consistent radius becomes part of visual identity

## Shadow System

### Shadow Specifications

```css
:root {
  /* Light mode shadows */
  --shadow-card: 0 4px 12px rgba(0,0,0,.08);
  --shadow-modal: 0 8px 24px rgba(0,0,0,.12);
  --shadow-button-hover: 0 4px 12px rgba(45,99,86,.25);
  
  /* Dark mode shadows - more pronounced */
  --shadow-card-dark: 0 4px 12px rgba(0,0,0,.3);
  --shadow-modal-dark: 0 8px 24px rgba(0,0,0,.5);
}

[data-theme="dark"] {
  --shadow-card: var(--shadow-card-dark);
  --shadow-modal: var(--shadow-modal-dark);
}
```

### Shadow Applications

#### Card Shadows
- **Default state:** Subtle elevation with `--shadow-card`
- **Hover state:** Increased shadow intensity
- **Active state:** Reduced shadow for pressed appearance

```css
.card {
  box-shadow: var(--shadow-card);
  transition: box-shadow 0.2s ease;
}

.card:hover {
  box-shadow: 0 8px 20px rgba(0,0,0,.15);
}
```

#### Modal Shadows
- **Background:** Strong shadow for clear separation
- **Layering:** Higher z-index with pronounced shadow

```css
.modal {
  box-shadow: var(--shadow-modal);
}
```

#### Button Shadows
- **Primary buttons:** Colored shadow matching button color
- **Hover enhancement:** 25% shadow intensity increase

```css
.btn-primary {
  box-shadow: 0 2px 4px rgba(45,99,86,.2);
}

.btn-primary:hover {
  box-shadow: var(--shadow-button-hover);
}
```

## Focus States

### Focus Specifications
Consistent focus indicators across all interactive elements for accessibility compliance.

```css
:root {
  --focus-outline: 2px solid rgba(45,99,86,.4);
  --focus-offset: 2px;
  --focus-radius: 8px;
}

.btn:focus,
.input:focus,
.card:focus {
  outline: var(--focus-outline);
  outline-offset: var(--focus-offset);
  border-radius: var(--focus-radius);
}
```

### Focus Applications

#### Interactive Elements
- **Buttons:** Outline with brand color at 40% opacity
- **Form inputs:** Border color change + outline
- **Cards:** Outline when keyboard accessible
- **Navigation:** Clear focus progression

```css
.input:focus {
  border-color: var(--color-primary);
  outline: var(--focus-outline);
  outline-offset: var(--focus-offset);
}
```

#### Healthcare Accessibility
- **Clinical workflows:** Clear focus progression for efficient navigation
- **Keyboard users:** Visible focus states for accessibility compliance
- **Screen readers:** Proper focus management for assistive technology

## Layout Patterns

### Container Systems

#### Content Containers
```css
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--space-4);
}

@media (min-width: 769px) {
  .container {
    padding: 0 var(--space-6);
  }
}
```

#### Section Spacing
```css
.section {
  margin: var(--space-10) 0;
}

.section + .section {
  margin-top: var(--space-12);
}
```

### Grid Systems

#### Card Grids
```css
.card-grid {
  display: grid;
  gap: var(--space-6);
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
}
```

#### Form Layouts
```css
.form-group {
  margin-bottom: var(--space-4);
}

.form-grid {
  display: grid;
  gap: var(--space-4);
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
}
```

## Mobile Adaptations

### Responsive Spacing
- **Mobile containers:** Reduce padding to `--space-4` (16px)
- **Touch targets:** Maintain minimum 44px with adequate spacing
- **Content margins:** Reduce by 25% on mobile screens

```css
@media (max-width: 768px) {
  .container {
    padding: 0 var(--space-4);
  }
  
  .card {
    padding: var(--space-6); /* Reduced from --space-8 */
  }
  
  .section {
    margin: var(--space-6) 0; /* Reduced from --space-10 */
  }
}
```

## Implementation Best Practices

### Consistency Rules
1. **Always use spacing variables** - Never hardcode spacing values
2. **Maintain 4px grid** - All spacing should be multiples of 4px
3. **Single border radius** - Use 8px consistently across all components
4. **Contextual shadows** - Match shadow intensity to component importance
5. **Accessible focus states** - Ensure all interactive elements have clear focus indicators

### Healthcare Considerations
- **Clinical efficiency:** Consistent spacing creates predictable interfaces
- **Touch accessibility:** Adequate spacing prevents input errors
- **Professional appearance:** Systematic spacing maintains clinical credibility
- **Multi-device support:** Responsive spacing adapts to various clinical environments

## Quality Assurance

### Testing Checklist
- [ ] All spacing uses CSS custom properties
- [ ] Focus states are visible and consistent
- [ ] Shadows render correctly in both light and dark themes
- [ ] Touch targets meet 44px minimum requirement
- [ ] Border radius is consistent across all components

---

*Consistent layout and spacing creates professional, accessible healthcare interfaces that support efficient clinical workflows.*