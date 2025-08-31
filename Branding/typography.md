# Typography

> Font systems and typographic hierarchy for HadadaHealth healthcare practice management interfaces.

## Font Systems

### Digital Typography (UI)
**Primary Font Stack:** `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`

**Usage Context:**
- All digital interfaces and web applications
- Clinical documentation forms and inputs
- Navigation and interactive elements
- Patient management interfaces

**Rationale:**
- System fonts ensure optimal performance and native OS integration
- High legibility for healthcare professionals in various lighting conditions
- Consistent rendering across devices and browsers
- No external font loading delays

### Print Typography (Export Only)
**Print Font Stack:** `Georgia, "Times New Roman", Times, serif`

**Usage Context:**
- PDF exports and clinical reports
- Formal documentation and correspondence
- Patient letters and official documents
- Printed forms and templates

**Important Restriction:**
- **Never use serif fonts in digital UI interfaces**
- Reserved exclusively for PDF exports and print previews
- Should not appear in the main application interface

## Typographic Hierarchy

### Heading Levels

#### H1 - Primary Page Headings
```css
h1 {
  font-size: 2.5rem;        /* 40px */
  font-weight: 600;
  letter-spacing: -0.025em;
  margin: var(--space-8) 0 var(--space-4);
  color: var(--color-text);
}
```
**Usage:** Main page titles, primary section headers

#### H2 - Section Headings  
```css
h2 {
  font-size: 1.75rem;       /* 28px */
  font-weight: 600;
  letter-spacing: -0.025em;
  margin: var(--space-6) 0 var(--space-3);
  color: var(--color-text);
}
```
**Usage:** Major section dividers, card titles

#### H3 - Subsection Headings
```css
h3 {
  font-size: 1.25rem;       /* 20px */
  font-weight: 500;
  letter-spacing: -0.025em;
  margin: var(--space-5) 0 var(--space-3);
  color: var(--color-text);
}
```
**Usage:** Component titles, form section headers

### Body Text

#### Primary Body Text
```css
body, p {
  font-size: 1rem;          /* 16px */
  line-height: 1.6;
  color: var(--color-text);
  font-family: var(--font-ui);
}
```
**Usage:** Main content, paragraphs, clinical notes

#### UI Text (Buttons and Form Elements)
```css
.btn, .input, .label {
  font-size: 15px;
  font-weight: 500;
  font-family: var(--font-ui);
}
```
**Usage:** Interactive elements, form controls

#### Small Text and Metadata
```css
.text-sm {
  font-size: 14px;          /* Labels, secondary information */
}

.text-xs {
  font-size: 13px;          /* Metadata, timestamps, IDs */
}
```

## Mobile Typography Scaling

### Responsive Font Sizes

| Element | Desktop | Mobile | Small Mobile |
|---------|---------|--------|--------------|
| H1 | 2.5rem (40px) | 2rem (32px) | 1.75rem (28px) |
| H2 | 1.75rem (28px) | 1.5rem (24px) | 1.25rem (20px) |
| H3 | 1.25rem (20px) | 1.125rem (18px) | 1rem (16px) |
| Body | 1rem (16px) | 1rem (16px) | 0.9rem (14.4px) |
| Button | 15px | 14px | 13px |

### Mobile Implementation
```css
/* Mobile scaling */
@media (max-width: 768px) {
  h1 {
    font-size: 2rem;
    margin: var(--space-6) 0 var(--space-4);
  }
  
  h2 {
    font-size: 1.5rem;
  }
  
  h3 {
    font-size: 1.125rem;
  }
}

@media (max-width: 480px) {
  h1 { font-size: 1.75rem; }
  h2 { font-size: 1.25rem; }
  h3 { font-size: 1rem; }
  body { font-size: 0.9rem; }
}
```

## Clinical Typography Patterns

### Patient Information Display
```css
.patient-name {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 4px 0;
}

.patient-id {
  font-size: 13px;
  color: var(--color-muted);
  font-weight: 400;
  margin: 0;
}
```

### Status and Labels
```css
.status-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--color-muted);
}

.discipline-tag {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-primary);
}
```

### Form Typography
```css
.label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text);
  margin-bottom: 8px;
  display: block;
}

.input {
  font-size: 15px;
  font-family: var(--font-ui);
  color: var(--color-text);
}

.help-text {
  font-size: 13px;
  color: var(--color-muted);
  margin-top: 4px;
}
```

## Print Typography (Export Only)

### Clinical Report Typography
```css
/* PDF/Print styles only */
@media print, .pdf-export {
  body {
    font-family: var(--font-serif);
    font-size: 12pt;
    line-height: 1.5;
  }
  
  .report-title {
    font-size: 18pt;
    font-weight: bold;
    margin-bottom: 16pt;
  }
  
  .report-section-header {
    font-size: 14pt;
    font-weight: bold;
    margin: 12pt 0 6pt 0;
  }
  
  .patient-info {
    font-size: 11pt;
    margin-bottom: 12pt;
  }
}
```

### Print-Specific Considerations
- **Serif fonts** improve readability on paper
- **Point sizes** rather than pixels for print
- **Higher contrast** for physical document legibility
- **Appropriate margins** for binding and handling

## Accessibility Guidelines

### Readability Requirements
- **Minimum font size:** 16px for body text to prevent iOS zoom
- **Line height:** 1.6 for body text to improve readability
- **Contrast:** All text must meet WCAG AA contrast requirements (4.5:1)
- **Font weight:** Minimum 400 weight for body text, 500+ for UI elements

### Special Considerations
```css
/* Ensure minimum touch target sizing */
.btn, .input, .interactive-text {
  min-height: 44px;
  font-size: 15px;
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .text-muted {
    color: var(--color-text);
  }
}

/* Reduced motion accessibility */
@media (prefers-reduced-motion: reduce) {
  * {
    transition: none !important;
  }
}
```

## Implementation Examples

### CSS Custom Properties
```css
:root {
  /* Typography */
  --font-ui: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --font-serif: Georgia, "Times New Roman", Times, serif;
  
  /* Font sizes */
  --text-xs: 13px;
  --text-sm: 14px;
  --text-base: 16px;
  --text-lg: 18px;
  --text-xl: 20px;
  --text-2xl: 24px;
  --text-3xl: 28px;
  --text-4xl: 32px;
  --text-5xl: 40px;
  
  /* Line heights */
  --leading-tight: 1.25;
  --leading-normal: 1.6;
  --leading-relaxed: 1.75;
}
```

### Utility Classes
```css
/* Text sizing utilities */
.text-xs { font-size: var(--text-xs); }
.text-sm { font-size: var(--text-sm); }
.text-base { font-size: var(--text-base); }
.text-lg { font-size: var(--text-lg); }

/* Text styling utilities */
.font-medium { font-weight: 500; }
.font-semibold { font-weight: 600; }
.font-bold { font-weight: 700; }

/* Color utilities */
.text-primary { color: var(--color-primary); }
.text-muted { color: var(--color-muted); }
.text-success { color: var(--color-success); }
.text-error { color: var(--color-error); }
```

## Healthcare-Specific Guidelines

### Clinical Documentation
- Use consistent hierarchy for medical forms
- Ensure critical information is visually prominent
- Maintain professional appearance in patient-facing materials
- Support rapid scanning during clinical workflows

### Multi-Language Considerations
- Font stack supports extended Latin character sets
- Consider South African language requirements
- Test with medical terminology in multiple languages
- Ensure proper rendering of special medical characters

### Performance Optimization
- System fonts eliminate external font loading
- Consistent font stack reduces layout shifts
- Optimized for healthcare app performance requirements
- Minimal typography CSS for faster loading

---

**Related Files:**
- [Color System](color-system.md) - Text color applications
- [Forms](components/forms.md) - Typography in form contexts
- [Accessibility](implementation/accessibility.md) - WCAG compliance details

*This typography system ensures consistent, readable, and professional text presentation across all HadadaHealth interfaces while supporting healthcare workflow requirements and accessibility standards.*