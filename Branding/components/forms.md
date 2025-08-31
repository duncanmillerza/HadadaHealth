# Forms

> Form controls and input patterns for HadadaHealth healthcare practice management interfaces.

## Input Controls

### Text Input
Standard text input for names, notes, and general text entry.

```css
.input {
  width: 100%;
  height: 48px;
  padding: 14px 16px;
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 15px;
  font-family: var(--font-ui);
  color: var(--color-text);
  background: var(--color-white);
  transition: all 0.2s ease;
}

.input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(45, 99, 86, 0.1);
  outline: none;
}

.input::placeholder {
  color: var(--color-muted);
}
```

```html
<div class="input-group">
  <label class="label" for="patient-name">Patient Name</label>
  <input class="input" id="patient-name" type="text" placeholder="Enter patient full name" required>
</div>
```

### Textarea
Multi-line text input for clinical notes and comments.

```css
.textarea {
  width: 100%;
  min-height: 120px;
  padding: 14px 16px;
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 15px;
  font-family: var(--font-ui);
  color: var(--color-text);
  background: var(--color-white);
  resize: vertical;
  transition: all 0.2s ease;
}

.textarea:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(45, 99, 86, 0.1);
  outline: none;
}
```

```html
<div class="input-group">
  <label class="label" for="treatment-notes">Treatment Notes</label>
  <textarea class="textarea" id="treatment-notes" placeholder="Enter detailed treatment notes..."></textarea>
</div>
```

### Select Dropdown
Dropdown selection for categorical data.

```css
.select {
  width: 100%;
  height: 48px;
  padding: 14px 16px;
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 15px;
  font-family: var(--font-ui);
  color: var(--color-text);
  background: var(--color-white);
  cursor: pointer;
  transition: all 0.2s ease;
  appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%236B7280' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6,9 12,15 18,9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 16px center;
  background-size: 16px;
  padding-right: 48px;
}

.select:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(45, 99, 86, 0.1);
  outline: none;
}
```

```html
<div class="input-group">
  <label class="label" for="discipline">Healthcare Discipline</label>
  <select class="select" id="discipline" required>
    <option value="">Select discipline</option>
    <option value="physiotherapy">Physiotherapy</option>
    <option value="occupational-therapy">Occupational Therapy</option>
    <option value="speech-therapy">Speech-Language Pathology</option>
    <option value="psychology">Clinical Psychology</option>
    <option value="social-work">Social Work</option>
  </select>
</div>
```

## Labels and Help Text

### Label Styling
```css
.label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text);
  margin-bottom: 8px;
  cursor: pointer;
}

.label.required::after {
  content: " *";
  color: var(--color-error);
}
```

### Help Text
```css
.help-text {
  font-size: 13px;
  color: var(--color-muted);
  margin-top: 4px;
  line-height: 1.4;
}

.help-text.error {
  color: var(--color-error);
}

.help-text.success {
  color: var(--color-success);
}
```

```html
<div class="input-group">
  <label class="label required" for="patient-id">Patient ID</label>
  <input class="input" id="patient-id" type="text" placeholder="HH-2025-0000">
  <div class="help-text">Format: HH-YYYY-0000 (automatically generated if left blank)</div>
</div>
```

## Advanced Form Patterns

### Floating Labels
Modern floating label pattern for cleaner forms.

```css
.input-group-floating {
  position: relative;
}

.input-floating {
  width: 100%;
  height: 56px;
  padding: 24px 16px 8px 16px;
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 15px;
  font-family: var(--font-ui);
  color: var(--color-text);
  background: var(--color-white);
  transition: all 0.2s ease;
}

.label-floating {
  position: absolute;
  top: 16px;
  left: 16px;
  font-size: 15px;
  color: var(--color-muted);
  pointer-events: none;
  transition: all 0.2s ease;
  background: var(--color-white);
  padding: 0 4px;
}

.input-floating:focus + .label-floating,
.input-floating:not(:placeholder-shown) + .label-floating {
  top: -8px;
  left: 12px;
  font-size: 12px;
  color: var(--color-primary);
}

.input-floating:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(45, 99, 86, 0.1);
  outline: none;
}
```

```html
<div class="input-group-floating">
  <input class="input-floating" id="patient-name-float" placeholder=" " required>
  <label class="label-floating" for="patient-name-float">Patient Name</label>
</div>
```

### Input Groups with Icons
```css
.input-group-icon {
  position: relative;
}

.input-icon {
  padding-left: 48px;
}

.input-group-icon .material-icons {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-muted);
  font-size: 20px;
  pointer-events: none;
}

.input-icon:focus + .material-icons {
  color: var(--color-primary);
}
```

```html
<div class="input-group-icon">
  <input class="input input-icon" type="email" placeholder="Enter email address">
  <i class="material-icons">email</i>
</div>
```

## Validation States

### Error State
```css
.input.error {
  border-color: var(--color-error);
  box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.1);
}

.input.error:focus {
  border-color: var(--color-error);
  box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.15);
}
```

### Success State
```css
.input.success {
  border-color: var(--color-success);
  box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.1);
}

.input.success:focus {
  border-color: var(--color-success);
  box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.15);
}
```

### Validation Messages
```html
<div class="input-group">
  <label class="label required" for="patient-email">Email Address</label>
  <input class="input error" id="patient-email" type="email" value="invalid-email">
  <div class="help-text error">
    <i class="material-icons" style="font-size: 14px; vertical-align: middle;">error</i>
    Please enter a valid email address
  </div>
</div>

<div class="input-group">
  <label class="label required" for="patient-phone">Phone Number</label>
  <input class="input success" id="patient-phone" type="tel" value="+27 11 123 4567">
  <div class="help-text success">
    <i class="material-icons" style="font-size: 14px; vertical-align: middle;">check_circle</i>
    Phone number verified
  </div>
</div>
```

## Healthcare-Specific Form Controls

### Date and Time Inputs
```css
.input-date,
.input-time {
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%236B7280' stroke-width='2'%3e%3crect x='3' y='4' width='18' height='18' rx='2' ry='2'%3e%3c/rect%3e%3cline x1='16' y1='2' x2='16' y2='6'%3e%3c/line%3e%3cline x1='8' y1='2' x2='8' y2='6'%3e%3c/line%3e%3cline x1='3' y1='10' x2='21' y2='10'%3e%3c/line%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 16px center;
  background-size: 16px;
  padding-right: 48px;
}
```

```html
<div class="form-row">
  <div class="input-group">
    <label class="label" for="appointment-date">Appointment Date</label>
    <input class="input input-date" id="appointment-date" type="date" required>
  </div>
  <div class="input-group">
    <label class="label" for="appointment-time">Appointment Time</label>
    <input class="input input-time" id="appointment-time" type="time" required>
  </div>
</div>
```

### Patient ID Input
```html
<div class="input-group">
  <label class="label" for="patient-id">Patient ID</label>
  <input class="input" id="patient-id" type="text" 
         pattern="HH-[0-9]{4}-[0-9]{4}" 
         placeholder="HH-2025-0000"
         title="Format: HH-YYYY-0000">
  <div class="help-text">Leave blank for auto-generation</div>
</div>
```

### Treatment Duration Input
```html
<div class="input-group">
  <label class="label" for="session-duration">Session Duration (minutes)</label>
  <input class="input" id="session-duration" type="number" 
         min="15" max="180" step="15" 
         placeholder="60">
  <div class="help-text">Standard sessions: 30, 45, or 60 minutes</div>
</div>
```

## Checkbox and Radio Controls

### Checkbox Styling
```css
.checkbox-group {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin: 16px 0;
}

.checkbox {
  width: 20px;
  height: 20px;
  margin: 0;
  cursor: pointer;
  accent-color: var(--color-primary);
}

.checkbox-label {
  cursor: pointer;
  font-size: 14px;
  line-height: 1.5;
  color: var(--color-text);
}
```

```html
<div class="checkbox-group">
  <input class="checkbox" type="checkbox" id="consent-treatment" required>
  <label class="checkbox-label" for="consent-treatment">
    I consent to treatment and understand the privacy policy in accordance with POPIA requirements
  </label>
</div>
```

### Radio Button Groups
```css
.radio-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.radio-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.radio {
  width: 20px;
  height: 20px;
  margin: 0;
  cursor: pointer;
  accent-color: var(--color-primary);
}

.radio-label {
  cursor: pointer;
  font-size: 14px;
  color: var(--color-text);
}
```

```html
<div class="input-group">
  <label class="label">Priority Level</label>
  <div class="radio-group">
    <div class="radio-item">
      <input class="radio" type="radio" id="priority-routine" name="priority" value="routine">
      <label class="radio-label" for="priority-routine">Routine</label>
    </div>
    <div class="radio-item">
      <input class="radio" type="radio" id="priority-urgent" name="priority" value="urgent">
      <label class="radio-label" for="priority-urgent">Urgent</label>
    </div>
    <div class="radio-item">
      <input class="radio" type="radio" id="priority-emergency" name="priority" value="emergency">
      <label class="radio-label" for="priority-emergency">Emergency</label>
    </div>
  </div>
</div>
```

## Form Layout Patterns

### Form Row Layout
```css
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
    gap: var(--space-3);
  }
}
```

### Patient Information Form
```html
<form class="patient-form">
  <div class="form-row">
    <div class="input-group">
      <label class="label required" for="first-name">First Name</label>
      <input class="input" id="first-name" type="text" required>
    </div>
    <div class="input-group">
      <label class="label required" for="last-name">Last Name</label>
      <input class="input" id="last-name" type="text" required>
    </div>
  </div>
  
  <div class="form-row">
    <div class="input-group">
      <label class="label" for="date-of-birth">Date of Birth</label>
      <input class="input" id="date-of-birth" type="date">
    </div>
    <div class="input-group">
      <label class="label" for="id-number">ID Number</label>
      <input class="input" id="id-number" type="text" pattern="[0-9]{13}">
    </div>
  </div>
  
  <div class="input-group">
    <label class="label required" for="primary-discipline">Primary Discipline</label>
    <select class="select" id="primary-discipline" required>
      <option value="">Select primary discipline</option>
      <option value="physiotherapy">Physiotherapy</option>
      <option value="occupational-therapy">Occupational Therapy</option>
      <option value="speech-therapy">Speech-Language Pathology</option>
    </select>
  </div>
  
  <div class="form-actions">
    <button type="submit" class="btn btn-primary">Save Patient</button>
    <button type="button" class="btn btn-secondary">Cancel</button>
  </div>
</form>
```

## Mobile Optimizations

### Mobile Form Styling
```css
@media (max-width: 768px) {
  .input,
  .textarea,
  .select {
    font-size: 16px; /* Prevents iOS zoom */
    height: 44px;
    padding: 12px 16px;
  }
  
  .textarea {
    min-height: 100px;
  }
  
  .input-floating {
    height: 52px;
    padding: 20px 16px 8px 16px;
  }
  
  .form-actions .btn {
    width: 100%;
    margin-bottom: 12px;
  }
}
```

## Accessibility Guidelines

### Form Accessibility Requirements
- All form controls must have associated labels
- Use `required` attribute and visual indicators for mandatory fields
- Provide clear error messages with specific guidance
- Ensure sufficient color contrast for all states
- Support keyboard navigation throughout forms

### Screen Reader Support
```html
<!-- Proper labeling -->
<label for="patient-notes">Treatment Notes</label>
<textarea id="patient-notes" aria-describedby="notes-help"></textarea>
<div id="notes-help" class="help-text">
  Enter detailed treatment notes including assessment findings and treatment plan
</div>

<!-- Error messages -->
<input class="input error" aria-describedby="email-error" aria-invalid="true">
<div id="email-error" class="help-text error" role="alert">
  Please enter a valid email address
</div>
```

### High Contrast Mode
```css
@media (prefers-contrast: high) {
  .input,
  .textarea,
  .select {
    border-width: 2px;
  }
  
  .input:focus,
  .textarea:focus,
  .select:focus {
    outline: 3px solid var(--color-primary);
    outline-offset: 2px;
  }
}
```

## Healthcare Compliance

### POPIA Requirements
- Include clear consent checkboxes for data processing
- Provide privacy policy links where personal data is collected
- Use secure input patterns for sensitive medical information
- Include data retention information in help text

### Clinical Data Forms
- Use consistent terminology across all healthcare specialties
- Include validation for medical record numbers and IDs
- Provide clear save states and auto-save indicators
- Support multiple healthcare professional workflows

---

**Related Files:**
- [Buttons](buttons.md) - Form action button styling
- [Color System](../color-system.md) - Form control color specifications
- [Typography](../typography.md) - Form text styling
- [Accessibility](../implementation/accessibility.md) - Detailed accessibility guidelines

*This form system ensures consistent, accessible, and professional form controls across all HadadaHealth healthcare practice management interfaces while supporting clinical workflows and compliance requirements.*