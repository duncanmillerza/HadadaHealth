# Clinical Components

> Healthcare-specific UI components designed for clinical workflows and patient management in HadadaHealth.

## Patient Management Components

### Patient Card (Detailed)
Comprehensive patient information display for clinical workflows.

```html
<div class="patient-card">
  <div class="patient-header">
    <div class="patient-avatar">
      <i class="material-icons">person</i>
    </div>
    <div class="patient-info">
      <h3 class="patient-name">Dr. Sarah Johnson</h3>
      <p class="patient-id">ID: HH-2025-0847</p>
      <p class="patient-contact">sarah.johnson@email.com • +27 11 123 4567</p>
    </div>
    <div class="patient-status">
      <span class="status-badge active">Active</span>
    </div>
  </div>
  
  <div class="patient-disciplines">
    <span class="discipline-tag">Physiotherapy</span>
    <span class="discipline-tag">Occupational Therapy</span>
  </div>
  
  <div class="patient-metadata">
    <div class="meta-row">
      <div class="meta-item">
        <i class="material-icons">cake</i>
        <span>DOB: 15 Mar 1985 (38 years)</span>
      </div>
      <div class="meta-item">
        <i class="material-icons">badge</i>
        <span>ID: 8503155432083</span>
      </div>
    </div>
    <div class="meta-row">
      <div class="meta-item">
        <i class="material-icons">schedule</i>
        <span>Next: Tomorrow 2:00 PM</span>
      </div>
      <div class="meta-item">
        <i class="material-icons">history</i>
        <span>Last: 3 days ago</span>
      </div>
    </div>
  </div>
  
  <div class="patient-actions">
    <button class="btn btn-sm btn-primary">
      <i class="material-icons">description</i>
      Treatment Notes
    </button>
    <button class="btn btn-sm btn-secondary">
      <i class="material-icons">schedule</i>
      Schedule
    </button>
    <button class="btn btn-sm btn-tertiary" aria-label="More actions">
      <i class="material-icons">more_horiz</i>
    </button>
  </div>
</div>
```

```css
.patient-card {
  background: var(--color-white);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-6);
  box-shadow: var(--shadow-card);
  transition: all 0.3s ease;
  border-left: 4px solid transparent;
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

.patient-header {
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.patient-avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--color-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 2px solid var(--color-border);
}

.patient-avatar .material-icons {
  color: var(--color-muted);
  font-size: 28px;
}

.patient-info {
  flex: 1;
  min-width: 0;
}

.patient-name {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 4px 0;
}

.patient-id {
  font-size: 13px;
  color: var(--color-muted);
  font-weight: 500;
  margin: 0 0 4px 0;
}

.patient-contact {
  font-size: 13px;
  color: var(--color-muted);
  margin: 0;
}

.patient-disciplines {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-5);
}

.patient-metadata {
  margin-bottom: var(--space-5);
}

.meta-row {
  display: flex;
  gap: var(--space-6);
  margin-bottom: var(--space-2);
}

.meta-row:last-child {
  margin-bottom: 0;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 13px;
  color: var(--color-muted);
  flex: 1;
}

.meta-item .material-icons {
  font-size: 16px;
  color: var(--color-muted);
}

.patient-actions {
  display: flex;
  gap: var(--space-2);
  margin-top: auto;
}
```

### Discipline Tags
Healthcare specialty indicators with consistent styling.

```css
.discipline-tag {
  background: rgba(45, 99, 86, 0.1);
  color: var(--color-primary);
  padding: 4px 12px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 500;
  border: 1px solid rgba(45, 99, 86, 0.2);
  display: inline-block;
  white-space: nowrap;
}

[data-theme="dark"] .discipline-tag {
  background: rgba(59, 127, 113, 0.15);
  color: var(--color-primary);
  border-color: rgba(59, 127, 113, 0.3);
}

/* Specialty-specific variations */
.discipline-tag.physiotherapy {
  background: rgba(45, 99, 86, 0.1);
  color: var(--color-primary);
}

.discipline-tag.occupational-therapy {
  background: rgba(50, 81, 122, 0.1);
  color: var(--color-secondary);
}

.discipline-tag.speech-therapy {
  background: rgba(14, 165, 233, 0.1);
  color: var(--color-info);
}

.discipline-tag.psychology {
  background: rgba(156, 163, 175, 0.1);
  color: var(--color-muted);
}
```

## Progress Tracking Components

### Clinical Progress Stepper
Multi-step progress indicator for clinical workflows.

```html
<div class="progress-indicator">
  <div class="progress-header">
    <h3>Treatment Progress</h3>
    <span class="progress-summary">Step 2 of 4</span>
  </div>
  
  <div class="stepper">
    <div class="step completed">
      <div class="dot">
        <i class="material-icons">check</i>
      </div>
      <div class="step-content">
        <div class="step-title">Assessment</div>
        <div class="step-subtitle">Completed</div>
      </div>
    </div>
    
    <div class="step-connector completed"></div>
    
    <div class="step active">
      <div class="dot">2</div>
      <div class="step-content">
        <div class="step-title">Treatment</div>
        <div class="step-subtitle">In Progress</div>
      </div>
    </div>
    
    <div class="step-connector"></div>
    
    <div class="step">
      <div class="dot">3</div>
      <div class="step-content">
        <div class="step-title">Review</div>
        <div class="step-subtitle">Pending</div>
      </div>
    </div>
    
    <div class="step-connector"></div>
    
    <div class="step">
      <div class="dot">4</div>
      <div class="step-content">
        <div class="step-title">Discharge</div>
        <div class="step-subtitle">Pending</div>
      </div>
    </div>
  </div>
</div>
```

```css
.progress-indicator {
  background: var(--color-white);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-6);
  margin: var(--space-6) 0;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-5);
}

.progress-header h3 {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
}

.progress-summary {
  font-size: 14px;
  color: var(--color-muted);
  font-weight: 500;
}

.stepper {
  display: flex;
  align-items: center;
  gap: 0;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  position: relative;
}

.dot {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s ease;
  margin-bottom: var(--space-3);
  z-index: 2;
}

.step:not(.completed):not(.active) .dot {
  background: var(--color-surface);
  color: var(--color-muted);
  border: 2px solid var(--color-border);
}

.step.active .dot {
  background: var(--color-secondary);
  color: white;
  border: 2px solid var(--color-secondary);
}

.step.completed .dot {
  background: var(--color-primary);
  color: white;
  border: 2px solid var(--color-primary);
}

.step.completed .dot .material-icons {
  font-size: 18px;
}

.step-content {
  text-align: center;
  min-width: 80px;
}

.step-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 2px;
}

.step-subtitle {
  font-size: 12px;
  color: var(--color-muted);
}

.step.active .step-title {
  color: var(--color-secondary);
}

.step.completed .step-title {
  color: var(--color-primary);
}

.step-connector {
  flex: 1;
  height: 2px;
  background: var(--color-border);
  margin: 0 -20px -30px -20px;
  z-index: 1;
}

.step-connector.completed {
  background: var(--color-primary);
}
```

### Treatment Status Indicators
Visual status indicators for treatment progress.

```html
<div class="treatment-status-grid">
  <div class="status-item">
    <i class="material-icons status-icon success">check_circle</i>
    <div class="status-content">
      <div class="status-title">Assessment Complete</div>
      <div class="status-subtitle">Initial evaluation documented</div>
    </div>
  </div>
  
  <div class="status-item">
    <i class="material-icons status-icon warning">schedule</i>
    <div class="status-content">
      <div class="status-title">Treatment In Progress</div>
      <div class="status-subtitle">Session 3 of 8 scheduled</div>
    </div>
  </div>
  
  <div class="status-item">
    <i class="material-icons status-icon info">assignment</i>
    <div class="status-content">
      <div class="status-title">Progress Review Due</div>
      <div class="status-subtitle">Schedule review appointment</div>
    </div>
  </div>
  
  <div class="status-item">
    <i class="material-icons status-icon error">priority_high</i>
    <div class="status-content">
      <div class="status-title">Action Required</div>
      <div class="status-subtitle">Missing consent form</div>
    </div>
  </div>
</div>
```

```css
.treatment-status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-4);
  margin: var(--space-6) 0;
}

.status-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  background: var(--color-white);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  transition: all 0.2s ease;
}

.status-item:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-card);
}

.status-icon {
  font-size: 24px;
  flex-shrink: 0;
  margin-top: 2px;
}

.status-icon.success { color: var(--color-success); }
.status-icon.warning { color: var(--color-warning); }
.status-icon.error { color: var(--color-error); }
.status-icon.info { color: var(--color-info); }

.status-content {
  flex: 1;
  min-width: 0;
}

.status-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 4px 0;
}

.status-subtitle {
  font-size: 13px;
  color: var(--color-muted);
  margin: 0;
}
```

## Assessment Components

### Assessment Form Card
Structured assessment form with clear sections.

```html
<div class="assessment-card">
  <div class="assessment-header">
    <h3>Initial Assessment - Physiotherapy</h3>
    <div class="assessment-meta">
      <span class="assessment-date">March 15, 2025</span>
      <span class="assessment-practitioner">Dr. Mike Chen</span>
    </div>
  </div>
  
  <div class="assessment-sections">
    <div class="assessment-section">
      <h4 class="section-title">
        <i class="material-icons">assignment</i>
        Subjective Assessment
      </h4>
      <div class="section-content">
        <div class="assessment-field">
          <label class="field-label">Chief Complaint</label>
          <p class="field-value">Lower back pain for 3 weeks, worsening with sitting</p>
        </div>
        <div class="assessment-field">
          <label class="field-label">Pain Scale (0-10)</label>
          <div class="pain-scale">
            <span class="pain-value">7</span>
            <div class="pain-bar">
              <div class="pain-fill" style="width: 70%"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="assessment-section">
      <h4 class="section-title">
        <i class="material-icons">visibility</i>
        Objective Assessment
      </h4>
      <div class="section-content">
        <div class="assessment-field">
          <label class="field-label">Range of Motion</label>
          <p class="field-value">Lumbar flexion limited to 30° (normal 60°)</p>
        </div>
        <div class="assessment-field">
          <label class="field-label">Muscle Strength</label>
          <p class="field-value">Hip flexors 4/5, otherwise normal</p>
        </div>
      </div>
    </div>
  </div>
  
  <div class="assessment-actions">
    <button class="btn btn-primary">
      <i class="material-icons">save</i>
      Save Assessment
    </button>
    <button class="btn btn-secondary">
      <i class="material-icons">print</i>
      Print Report
    </button>
  </div>
</div>
```

```css
.assessment-card {
  background: var(--color-white);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  margin: var(--space-6) 0;
}

.assessment-header {
  padding: var(--space-6);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
  border-radius: var(--radius-md) var(--radius-md) 0 0;
}

.assessment-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0 0 var(--space-2) 0;
}

.assessment-meta {
  display: flex;
  gap: var(--space-4);
  font-size: 14px;
  color: var(--color-muted);
}

.assessment-sections {
  padding: var(--space-6);
}

.assessment-section {
  margin-bottom: var(--space-6);
}

.assessment-section:last-child {
  margin-bottom: 0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 var(--space-4) 0;
}

.section-title .material-icons {
  color: var(--color-primary);
  font-size: 20px;
}

.section-content {
  padding-left: var(--space-8);
}

.assessment-field {
  margin-bottom: var(--space-4);
}

.assessment-field:last-child {
  margin-bottom: 0;
}

.field-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--space-2);
}

.field-value {
  font-size: 15px;
  color: var(--color-text);
  margin: 0;
  line-height: 1.5;
}

.pain-scale {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.pain-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-error);
  min-width: 24px;
}

.pain-bar {
  flex: 1;
  height: 8px;
  background: var(--color-border);
  border-radius: 4px;
  overflow: hidden;
  max-width: 200px;
}

.pain-fill {
  height: 100%;
  background: var(--color-error);
  transition: width 0.3s ease;
}

.assessment-actions {
  padding: var(--space-6);
  border-top: 1px solid var(--color-border);
  display: flex;
  gap: var(--space-3);
  justify-content: flex-end;
}
```

## Appointment Components

### Appointment Timeline
Daily appointment schedule visualization.

```html
<div class="appointment-timeline">
  <div class="timeline-header">
    <h3>Today's Appointments</h3>
    <span class="timeline-date">March 15, 2025</span>
  </div>
  
  <div class="timeline-content">
    <div class="timeline-item">
      <div class="timeline-time">09:00</div>
      <div class="timeline-event">
        <div class="event-patient">Sarah Johnson</div>
        <div class="event-type">Physiotherapy - Initial Assessment</div>
        <div class="event-duration">60 minutes</div>
      </div>
      <div class="event-status confirmed"></div>
    </div>
    
    <div class="timeline-item">
      <div class="timeline-time">10:30</div>
      <div class="timeline-event">
        <div class="event-patient">Michael Chen</div>
        <div class="event-type">Occupational Therapy - Follow-up</div>
        <div class="event-duration">45 minutes</div>
      </div>
      <div class="event-status confirmed"></div>
    </div>
    
    <div class="timeline-item current">
      <div class="timeline-time">14:00</div>
      <div class="timeline-event">
        <div class="event-patient">Emma Wilson</div>
        <div class="event-type">Speech Therapy - Progress Review</div>
        <div class="event-duration">30 minutes</div>
      </div>
      <div class="event-status in-progress"></div>
    </div>
    
    <div class="timeline-item">
      <div class="timeline-time">15:00</div>
      <div class="timeline-event">
        <div class="event-patient">David Brown</div>
        <div class="event-type">Psychology - Consultation</div>
        <div class="event-duration">50 minutes</div>
      </div>
      <div class="event-status pending"></div>
    </div>
  </div>
</div>
```

```css
.appointment-timeline {
  background: var(--color-white);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
}

.timeline-header {
  padding: var(--space-6);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.timeline-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.timeline-date {
  font-size: 14px;
  color: var(--color-muted);
  font-weight: 500;
}

.timeline-content {
  padding: var(--space-4);
}

.timeline-item {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4);
  margin: var(--space-2) 0;
  border-radius: var(--radius-md);
  transition: all 0.2s ease;
  position: relative;
}

.timeline-item:hover {
  background: var(--color-surface);
}

.timeline-item.current {
  background: rgba(45, 99, 86, 0.05);
  border: 1px solid rgba(45, 99, 86, 0.2);
}

.timeline-time {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
  min-width: 60px;
  text-align: center;
}

.timeline-event {
  flex: 1;
  min-width: 0;
}

.event-patient {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 2px;
}

.event-type {
  font-size: 14px;
  color: var(--color-text);
  margin-bottom: 2px;
}

.event-duration {
  font-size: 13px;
  color: var(--color-muted);
}

.event-status {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.event-status.confirmed {
  background: var(--color-primary);
}

.event-status.in-progress {
  background: var(--color-warning);
  animation: pulse 2s infinite;
}

.event-status.pending {
  background: var(--color-muted);
}

.event-status.cancelled {
  background: var(--color-error);
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}
```

## Mobile Optimizations

### Mobile Clinical Components
```css
@media (max-width: 768px) {
  .patient-card {
    padding: var(--space-4);
  }
  
  .patient-header {
    flex-direction: row;
    gap: var(--space-3);
  }
  
  .patient-avatar {
    width: 48px;
    height: 48px;
  }
  
  .patient-actions {
    flex-wrap: wrap;
  }
  
  .patient-actions .btn {
    flex: 1;
    min-width: 120px;
  }
  
  .meta-row {
    flex-direction: column;
    gap: var(--space-2);
  }
  
  .stepper {
    overflow-x: auto;
    padding-bottom: var(--space-4);
  }
  
  .step {
    min-width: 100px;
  }
  
  .treatment-status-grid {
    grid-template-columns: 1fr;
  }
  
  .assessment-sections {
    padding: var(--space-4);
  }
  
  .section-content {
    padding-left: 0;
  }
  
  .timeline-item {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-2);
  }
  
  .timeline-time {
    min-width: auto;
    text-align: left;
    font-size: 14px;
  }
}
```

## Accessibility & Healthcare Compliance

### Clinical Data Accessibility
```html
<!-- Proper ARIA labels for clinical data -->
<div class="patient-card" role="article" aria-labelledby="patient-name-847">
  <h3 id="patient-name-847" class="patient-name">Dr. Sarah Johnson</h3>
  <div class="patient-disciplines" aria-label="Healthcare disciplines">
    <span class="discipline-tag" role="img" aria-label="Physiotherapy specialist">Physiotherapy</span>
  </div>
</div>

<!-- Assessment forms with proper labeling -->
<div class="assessment-field">
  <label class="field-label" for="pain-scale">Pain Scale (0-10)</label>
  <input id="pain-scale" type="range" min="0" max="10" value="7" 
         aria-describedby="pain-help">
  <div id="pain-help" class="help-text">0 = No pain, 10 = Severe pain</div>
</div>
```

### POPIA Compliance Features
- Patient information is appropriately masked/truncated in list views
- Clear indicators for data access levels and permissions
- Support for audit trail requirements with interaction logging
- Privacy-first design patterns for sensitive medical information

---

**Related Files:**
- [Patient Cards](cards.md) - Detailed card component implementations
- [Forms](forms.md) - Clinical form patterns and validation
- [Color System](../color-system.md) - Status indicator color specifications
- [Accessibility](../implementation/accessibility.md) - Healthcare accessibility requirements

*These clinical components ensure professional, accessible, and compliant healthcare interface patterns across all HadadaHealth practice management workflows while supporting multi-disciplinary clinical requirements.*