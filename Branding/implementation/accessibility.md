# Accessibility

> WCAG 2.1 AA compliance guidelines and healthcare-specific accessibility considerations for HadadaHealth interfaces.

## Accessibility Philosophy

HadadaHealth is committed to providing accessible healthcare practice management interfaces that serve all healthcare professionals and patients, including those with disabilities. Our accessibility implementation goes beyond compliance to create truly inclusive experiences that support diverse clinical environments and user needs.

## WCAG 2.1 AA Compliance

### Color and Contrast
Comprehensive color accessibility ensuring readability for all users.

#### Contrast Requirements
```css
/* Text contrast ratios meet WCAG AA standards */
:root {
  /* High contrast text combinations */
  --contrast-primary-on-white: 7.2:1;    /* #2D6356 on #FFFFFF */
  --contrast-text-on-white: 12.6:1;      /* #1F2937 on #FFFFFF */
  --contrast-muted-on-white: 4.5:1;      /* #6B7280 on #FFFFFF */
  
  /* Dark mode contrast ratios */
  --contrast-text-on-dark: 13.1:1;       /* #F3F4F6 on #0F1419 */
  --contrast-primary-on-dark: 5.8:1;     /* #3B7F71 on #0F1419 */
}

/* Ensure interactive elements meet contrast requirements */
.btn-primary {
  background: var(--color-primary);      /* 4.5:1 minimum met */
  color: var(--color-white);
}

.btn-secondary {
  background: var(--color-white);
  color: var(--color-primary);           /* 7.2:1 contrast ratio */
  border: 2px solid var(--color-primary);
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .btn {
    border-width: 2px;
    font-weight: var(--font-semibold);
  }
  
  .card {
    border-width: 2px;
  }
  
  .input:focus {
    outline: 3px solid var(--color-primary);
    outline-offset: 2px;
  }
}
```

#### Color Independence
Never rely solely on color to convey information.

```html
<!-- Good: Color + icon + text -->
<div class="status-item">
  <i class="material-icons status-icon success" aria-hidden="true">check_circle</i>
  <span class="status-text">Assessment Complete</span>
  <span class="sr-only">Status: Completed successfully</span>
</div>

<!-- Good: Status with multiple indicators -->
<div class="patient-status">
  <span class="status-badge active">
    <i class="material-icons" aria-hidden="true">person</i>
    Active Patient
  </span>
</div>

<!-- Bad: Color only -->
<div style="color: green;">Complete</div>
```

### Keyboard Navigation
Comprehensive keyboard accessibility for healthcare workflows.

#### Focus Management
```css
/* Visible focus indicators */
.focusable:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-offset);
  border-radius: var(--focus-radius);
}

/* Skip links for main content */
.skip-link {
  position: absolute;
  top: -40px;
  left: 6px;
  background: var(--color-primary);
  color: white;
  padding: 8px 16px;
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

/* Focus trap for modals */
.modal.active {
  /* JavaScript handles focus trap */
}

/* Logical tab order */
.form-section {
  /* Ensure form fields follow logical tab sequence */
}

/* Remove focus from non-interactive elements */
.decoration {
  outline: none;
  -webkit-tap-highlight-color: transparent;
}
```

#### Keyboard Interaction Patterns
```html
<!-- Navigation with proper keyboard support -->
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

<!-- Interactive cards with keyboard support -->
<div class="patient-card" 
     role="button" 
     tabindex="0"
     aria-label="Patient: Dr. Sarah Johnson"
     onkeydown="handleCardKeydown(event)">
  <!-- Card content -->
</div>

<script>
function handleCardKeydown(event) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    openPatientDetails();
  }
}
</script>
```

### Screen Reader Support
Comprehensive screen reader accessibility for clinical interfaces.

#### ARIA Labels and Descriptions
```html
<!-- Patient information with proper labeling -->
<section aria-labelledby="patient-info-heading">
  <h2 id="patient-info-heading">Patient Information</h2>
  
  <div class="patient-details">
    <div class="detail-item">
      <span id="patient-name-label">Patient Name:</span>
      <span aria-labelledby="patient-name-label">Dr. Sarah Johnson</span>
    </div>
    
    <div class="detail-item">
      <span id="patient-id-label">Patient ID:</span>
      <span aria-labelledby="patient-id-label">HH-2025-0847</span>
    </div>
  </div>
</section>

<!-- Form with proper associations -->
<form aria-labelledby="appointment-form-title">
  <h2 id="appointment-form-title">Schedule Appointment</h2>
  
  <div class="form-group">
    <label for="appointment-date">Appointment Date</label>
    <input type="date" 
           id="appointment-date" 
           aria-describedby="date-help date-error"
           aria-required="true"
           aria-invalid="false">
    <div id="date-help" class="help-text">Select preferred appointment date</div>
    <div id="date-error" class="error-text" role="alert" aria-live="polite"></div>
  </div>
</form>

<!-- Status updates with live regions -->
<div aria-live="polite" aria-atomic="true" class="status-updates">
  <!-- Dynamic status messages appear here -->
</div>

<div aria-live="assertive" aria-atomic="true" class="urgent-alerts">
  <!-- Critical alerts appear here -->
</div>
```

#### Screen Reader Only Content
```css
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.sr-only-focusable:focus {
  position: static;
  width: auto;
  height: auto;
  padding: initial;
  margin: initial;
  overflow: visible;
  clip: auto;
  white-space: normal;
}
```

```html
<!-- Hidden context for screen readers -->
<h3>
  Treatment Progress
  <span class="sr-only">for Dr. Sarah Johnson</span>
</h3>

<!-- Button with descriptive label -->
<button class="btn-icon" aria-label="Edit treatment notes for Dr. Sarah Johnson">
  <i class="material-icons" aria-hidden="true">edit</i>
  <span class="sr-only">Edit treatment notes</span>
</button>

<!-- Progress indicator with text alternative -->
<div class="progress-bar" role="progressbar" aria-valuenow="75" aria-valuemin="0" aria-valuemax="100">
  <div class="progress-fill" style="width: 75%"></div>
  <span class="sr-only">Treatment progress: 75% complete</span>
</div>
```

## Healthcare-Specific Accessibility

### Clinical Workflow Accessibility
Accessibility patterns specific to healthcare practice management.

#### Patient Data Accessibility
```html
<!-- Patient card with comprehensive accessibility -->
<article class="patient-card" 
         role="article"
         aria-labelledby="patient-name-847"
         tabindex="0">
  <header class="patient-header">
    <div class="patient-avatar" aria-hidden="true">
      <i class="material-icons">person</i>
    </div>
    <div class="patient-info">
      <h3 id="patient-name-847" class="patient-name">Dr. Sarah Johnson</h3>
      <p class="patient-id">
        <span class="sr-only">Patient ID: </span>
        HH-2025-0847
      </p>
    </div>
    <div class="patient-status" aria-label="Patient status">
      <span class="status-badge active">
        <span class="sr-only">Status: </span>
        Active
      </span>
    </div>
  </header>
  
  <div class="patient-disciplines">
    <span class="sr-only">Healthcare disciplines: </span>
    <span class="discipline-tag">Physiotherapy</span>
    <span class="discipline-tag">Occupational Therapy</span>
  </div>
  
  <div class="patient-metadata">
    <div class="meta-item">
      <i class="material-icons" aria-hidden="true">schedule</i>
      <span>
        <span class="sr-only">Next appointment: </span>
        Tomorrow 2:00 PM
      </span>
    </div>
  </div>
</article>
```

#### Clinical Forms Accessibility
```html
<!-- Assessment form with full accessibility -->
<form class="assessment-form" aria-labelledby="assessment-title">
  <h2 id="assessment-title">Initial Assessment - Physiotherapy</h2>
  
  <fieldset>
    <legend>Subjective Assessment</legend>
    
    <div class="form-group">
      <label for="chief-complaint">Chief Complaint</label>
      <textarea id="chief-complaint"
                aria-describedby="complaint-help"
                aria-required="true"
                rows="4">
      </textarea>
      <div id="complaint-help" class="help-text">
        Describe the patient's primary concern in their own words
      </div>
    </div>
    
    <div class="form-group">
      <fieldset>
        <legend>Pain Scale Assessment</legend>
        <div class="pain-scale" role="group" aria-labelledby="pain-scale-legend">
          <div id="pain-scale-legend" class="sr-only">
            Rate pain level from 0 (no pain) to 10 (severe pain)
          </div>
          <input type="range" 
                 id="pain-level"
                 min="0" 
                 max="10" 
                 value="0"
                 aria-describedby="pain-description"
                 aria-valuetext="No pain">
          <div id="pain-description" class="pain-labels">
            <span>0 - No Pain</span>
            <span>10 - Severe Pain</span>
          </div>
        </div>
      </fieldset>
    </div>
  </fieldset>
</form>
```

### Medical Terminology Accessibility
Making healthcare terminology accessible to all users.

```html
<!-- Medical terms with explanations -->
<div class="clinical-term">
  <span class="term">ROM</span>
  <span class="expansion sr-only">Range of Motion</span>
  <button class="info-button" 
          aria-label="Definition of Range of Motion"
          aria-describedby="rom-definition">
    <i class="material-icons" aria-hidden="true">info</i>
  </button>
  <div id="rom-definition" class="definition-popup" role="tooltip">
    Range of Motion: The extent of movement possible at a joint
  </div>
</div>

<!-- Measurement units with context -->
<span class="measurement">
  30°
  <span class="sr-only">degrees</span>
  <span class="measurement-context">(normal range: 60°)</span>
</span>
```

## Touch and Motor Accessibility

### Touch Target Sizing
WCAG-compliant touch targets for healthcare environments.

```css
/* Minimum touch target sizes */
.touch-target {
  min-width: 44px;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Larger targets for critical actions */
.critical-action {
  min-width: 56px;
  min-height: 56px;
}

/* Spacing between touch targets */
.touch-list .touch-item {
  margin-bottom: 8px;
}

.touch-list .touch-item:last-child {
  margin-bottom: 0;
}

/* Touch target indicators for debugging */
.debug-touch .touch-target::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border: 1px dashed red;
  pointer-events: none;
}
```

### Motor Impairment Support
Design patterns supporting users with motor impairments.

```css
/* Larger click areas */
.large-click-area {
  padding: var(--space-6);
  cursor: pointer;
}

/* Sticky focus for easier navigation */
.sticky-focus:focus {
  outline: 3px solid var(--color-primary);
  outline-offset: 3px;
}

/* Hover tolerance for precise clicking */
.hover-tolerant {
  padding: 4px;
  margin: -4px;
}

/* Extended timing for interactions */
.patient-card {
  transition: all 0.5s ease; /* Longer transition for motor impairments */
}
```

### Alternative Input Methods
Support for various input devices used in healthcare.

```html
<!-- Voice control landmarks -->
<main id="main-content" role="main" aria-label="Patient management">
  <!-- Main content -->
</main>

<nav role="navigation" aria-label="Patient actions">
  <!-- Navigation -->
</nav>

<aside role="complementary" aria-label="Patient information sidebar">
  <!-- Sidebar content -->
</aside>

<!-- Switch control support -->
<div class="switch-navigation">
  <button class="switch-target" data-switch-id="1">Open Patient Details</button>
  <button class="switch-target" data-switch-id="2">Schedule Appointment</button>
  <button class="switch-target" data-switch-id="3">View Treatment History</button>
</div>
```

## Cognitive Accessibility

### Clear Information Architecture
Reducing cognitive load for healthcare professionals under stress.

```html
<!-- Clear page structure -->
<main>
  <header class="page-header">
    <h1>Patient Management</h1>
    <nav aria-label="Page actions">
      <button class="btn btn-primary">
        <i class="material-icons" aria-hidden="true">add</i>
        Add New Patient
      </button>
    </nav>
  </header>
  
  <section class="filters-section">
    <h2>Filter Patients</h2>
    <!-- Simple, clearly labeled filters -->
  </section>
  
  <section class="results-section">
    <h2>Patient List</h2>
    <div class="results-summary" aria-live="polite">
      Showing 24 patients
    </div>
    <!-- Patient results -->
  </section>
</main>

<!-- Progressive disclosure -->
<div class="expandable-section">
  <button class="expand-toggle" 
          aria-expanded="false" 
          aria-controls="advanced-options">
    Advanced Options
    <i class="material-icons" aria-hidden="true">expand_more</i>
  </button>
  <div id="advanced-options" class="expandable-content" hidden>
    <!-- Advanced options content -->
  </div>
</div>
```

### Error Prevention and Recovery
Accessible error handling for clinical data entry.

```html
<!-- Form validation with clear messaging -->
<form class="patient-form" novalidate>
  <div class="form-group">
    <label for="patient-email">Email Address</label>
    <input type="email" 
           id="patient-email"
           aria-describedby="email-help email-error"
           aria-required="true"
           aria-invalid="false">
    
    <div id="email-help" class="help-text">
      We'll use this to send appointment reminders
    </div>
    
    <div id="email-error" 
         class="error-message" 
         role="alert" 
         aria-live="polite"
         hidden>
      Please enter a valid email address (example: name@domain.com)
    </div>
  </div>
  
  <!-- Form submission with confirmation -->
  <div class="form-actions">
    <button type="submit" class="btn btn-primary">
      Save Patient Information
    </button>
    <div class="save-status" aria-live="polite" aria-atomic="true">
      <!-- Status messages appear here -->
    </div>
  </div>
</form>

<!-- Undo functionality for critical actions -->
<div class="undo-notification" role="alert" aria-live="assertive">
  <span>Patient archived.</span>
  <button class="btn btn-sm btn-secondary">
    Undo
    <span class="sr-only">archive action</span>
  </button>
</div>
```

## Healthcare Environment Considerations

### Clinical Lighting Adaptations
Accessibility considerations for various healthcare lighting conditions.

```css
/* High contrast mode for bright clinical lighting */
@media (prefers-contrast: high) {
  :root {
    --color-text: #000000;
    --color-white: #FFFFFF;
    --color-border: #000000;
  }
  
  .card {
    border-width: 2px;
  }
  
  .btn {
    border-width: 2px;
    font-weight: var(--font-semibold);
  }
}

/* Reduced eye strain for extended use */
@media (prefers-color-scheme: dark) {
  :root {
    /* Softer colors for extended screen time */
    --color-text: #E5E7EB;
    --color-surface: #1F2937;
  }
}
```

### Interruption Handling
Design patterns supporting clinical workflow interruptions.

```html
<!-- Auto-save indicators -->
<div class="auto-save-status" aria-live="polite">
  <span class="save-indicator">
    <i class="material-icons" aria-hidden="true">cloud_done</i>
    <span class="sr-only">Auto-saved</span>
    Last saved 2 minutes ago
  </span>
</div>

<!-- Session timeout warnings -->
<div class="timeout-warning" 
     role="dialog" 
     aria-labelledby="timeout-title"
     aria-describedby="timeout-message">
  <h3 id="timeout-title">Session Timeout Warning</h3>
  <p id="timeout-message">
    Your session will expire in 5 minutes due to inactivity. 
    Would you like to extend your session?
  </p>
  <div class="dialog-actions">
    <button class="btn btn-primary">Extend Session</button>
    <button class="btn btn-secondary">Logout Now</button>
  </div>
</div>
```

## Testing and Validation

### Accessibility Testing Checklist
Comprehensive testing approach for healthcare interfaces.

```
Automated Testing:
□ axe-core accessibility scanning
□ Color contrast ratio validation
□ HTML semantic validation
□ ARIA attribute validation

Manual Testing:
□ Keyboard navigation testing
□ Screen reader testing (NVDA, JAWS, VoiceOver)
□ High contrast mode testing
□ Zoom testing up to 200%
□ Voice control testing

Healthcare-Specific Testing:
□ Clinical workflow interruption scenarios
□ Emergency access pattern testing
□ Medical device integration testing
□ Multi-language content testing
□ POPIA compliance accessibility review
```

### Screen Reader Testing Script
Systematic approach to screen reader testing.

```
1. Navigation Testing:
   - Can user navigate main menu with screen reader?
   - Are all interactive elements announced correctly?
   - Is page structure (headings, landmarks) clear?

2. Form Testing:
   - Are all form labels properly associated?
   - Are validation errors announced clearly?
   - Can user complete patient registration process?

3. Data Table Testing:
   - Are patient data tables properly structured?
   - Can user navigate between cells effectively?
   - Are table headers announced correctly?

4. Dynamic Content Testing:
   - Are status updates announced via live regions?
   - Do loading states provide audio feedback?
   - Are modal dialogs properly announced?

5. Healthcare-Specific Testing:
   - Can user complete clinical assessment forms?
   - Are medical abbreviations explained?
   - Is urgent information properly prioritized?
```

## POPIA and Healthcare Compliance

### Privacy-First Accessibility
Accessible design that maintains patient privacy compliance.

```html
<!-- Privacy-aware patient information display -->
<div class="patient-summary" 
     role="region" 
     aria-label="Patient summary (contains sensitive information)">
  
  <div class="privacy-notice" role="note">
    <i class="material-icons" aria-hidden="true">security</i>
    <span class="sr-only">Privacy notice: </span>
    This information is confidential and protected under POPIA
  </div>
  
  <div class="patient-details">
    <!-- Patient information with appropriate masking -->
    <div class="detail-item">
      <span class="detail-label">Patient Name:</span>
      <span class="detail-value" 
            aria-label="Patient name (click to reveal)"
            tabindex="0"
            onkeydown="revealSensitiveInfo(event)">
        Dr. S*** J******
      </span>
    </div>
  </div>
</div>

<!-- Audit trail accessibility -->
<section aria-labelledby="audit-heading">
  <h3 id="audit-heading">Access History</h3>
  <div class="audit-trail" role="log" aria-live="polite">
    <div class="audit-entry">
      <span class="sr-only">Access logged: </span>
      Dr. Smith accessed patient record at 14:32 on March 15, 2025
    </div>
  </div>
</section>
```

## Implementation Tools

### Accessibility Testing Tools Integration
```javascript
// axe-core integration for automated testing
import axe from '@axe-core/react';

if (process.env.NODE_ENV === 'development') {
  axe(React, ReactDOM, 1000, {
    rules: {
      // Healthcare-specific rules
      'color-contrast': { enabled: true },
      'keyboard-navigation': { enabled: true },
      'aria-labels': { enabled: true },
      'focus-management': { enabled: true }
    }
  });
}

// Custom healthcare accessibility checks
function validateHealthcareAccessibility() {
  // Check for medical term definitions
  const medicalTerms = document.querySelectorAll('.medical-term');
  medicalTerms.forEach(term => {
    if (!term.querySelector('.definition') && !term.getAttribute('aria-describedby')) {
      console.warn('Medical term missing definition:', term.textContent);
    }
  });
  
  // Check for patient data privacy indicators
  const sensitiveData = document.querySelectorAll('.patient-data');
  sensitiveData.forEach(data => {
    if (!data.querySelector('.privacy-notice') && !data.getAttribute('aria-label').includes('confidential')) {
      console.warn('Patient data missing privacy indicator');
    }
  });
}
```

### Development Accessibility Guidelines
```css
/* Development-only accessibility helpers */
.a11y-debug * {
  outline: 1px solid red !important;
}

.a11y-debug [role] {
  outline-color: blue !important;
}

.a11y-debug [aria-label],
.a11y-debug [aria-labelledby],
.a11y-debug [aria-describedby] {
  outline-color: green !important;
}

/* Focus debugging */
.focus-debug :focus {
  outline: 3px solid yellow !important;
  outline-offset: 2px !important;
}
```

---

**Related Files:**
- [Color System](../color-system.md) - Color contrast specifications
- [Typography](../typography.md) - Accessible text sizing and spacing
- [Forms](../components/forms.md) - Accessible form patterns
- [Touch Interactions](../interactions/touch-interactions.md) - Touch accessibility guidelines

*This accessibility system ensures WCAG 2.1 AA compliance and healthcare-specific accessibility requirements across all HadadaHealth practice management interfaces, creating inclusive experiences for all healthcare professionals and patients.*