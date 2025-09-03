# Cards

> Content card components and layout patterns for HadadaHealth healthcare practice management interfaces.

## Base Card Component

### Standard Card
Foundation card component for content organization.

```css
.card {
  background: var(--color-white);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-8);
  box-shadow: var(--shadow-card);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
}

.card:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

[data-theme="dark"] .card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}
```

### Interactive Card
Clickable card variant for navigation and selection.

```css
.card-interactive {
  cursor: pointer;
  transition: all 0.3s ease;
}

.card-interactive:hover {
  border-color: var(--color-primary);
  transform: translateY(-2px);
}

.card-interactive:focus {
  outline: var(--focus-outline);
  outline-offset: var(--focus-offset);
}
```

## Healthcare-Specific Cards

### Patient Card
Primary component for displaying patient information.

```html
<div class="patient-card">
  <div class="patient-header">
    <div class="patient-avatar">
      <i class="material-icons">person</i>
    </div>
    <div class="patient-info">
      <h3 class="patient-name">Dr. Sarah Johnson</h3>
      <p class="patient-id">ID: HH-2025-0847</p>
      <p class="patient-contact">sarah.johnson@email.com</p>
    </div>
    <div class="patient-status">
      <span class="status-badge active">Active</span>
    </div>
  </div>
  
  <div class="patient-disciplines">
    <span class="discipline-tag">Physiotherapy</span>
    <span class="discipline-tag">Occupational Therapy</span>
  </div>
  
  <div class="patient-meta">
    <div class="meta-item">
      <i class="material-icons">schedule</i>
      <span>Next: Tomorrow 2:00 PM</span>
    </div>
    <div class="meta-item">
      <i class="material-icons">assignment</i>
      <span>Last session: 3 days ago</span>
    </div>
  </div>
  
  <div class="patient-actions">
    <button class="btn btn-sm btn-primary">
      <i class="material-icons">description</i>
      Notes
    </button>
    <button class="btn btn-sm btn-secondary">
      <i class="material-icons">schedule</i>
      Schedule
    </button>
    <button class="btn btn-sm btn-tertiary">
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
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--color-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.patient-avatar .material-icons {
  color: var(--color-muted);
  font-size: 24px;
}

.patient-info {
  flex: 1;
  min-width: 0;
}

.patient-name {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 4px 0;
}

.patient-id {
  font-size: 13px;
  color: var(--color-muted);
  margin: 0 0 2px 0;
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
  margin-bottom: var(--space-4);
}

.patient-meta {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 13px;
  color: var(--color-muted);
}

.meta-item .material-icons {
  font-size: 16px;
}

.patient-actions {
  display: flex;
  gap: var(--space-2);
  margin-top: auto;
}
```

### Appointment Card
Display upcoming and recent appointments.

```html
<div class="appointment-card">
  <div class="appointment-header">
    <div class="appointment-time">
      <div class="time-display">2:00 PM</div>
      <div class="date-display">Tomorrow</div>
    </div>
    <div class="appointment-details">
      <h4 class="patient-name">Sarah Johnson</h4>
      <p class="appointment-type">Physiotherapy Assessment</p>
      <p class="practitioner">Dr. Mike Chen</p>
    </div>
    <div class="appointment-status">
      <span class="status-badge confirmed">Confirmed</span>
    </div>
  </div>
  
  <div class="appointment-actions">
    <button class="btn btn-sm btn-secondary">
      <i class="material-icons">edit</i>
      Reschedule
    </button>
    <button class="btn btn-sm btn-primary">
      <i class="material-icons">video_call</i>
      Join Session
    </button>
  </div>
</div>
```

```css
.appointment-card {
  background: var(--color-white);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  box-shadow: var(--shadow-card);
  transition: all 0.3s ease;
}

.appointment-header {
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.appointment-time {
  text-align: center;
  flex-shrink: 0;
}

.time-display {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-primary);
}

.date-display {
  font-size: 13px;
  color: var(--color-muted);
  margin-top: 2px;
}

.appointment-details {
  flex: 1;
  min-width: 0;
}

.appointment-details .patient-name {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 4px 0;
}

.appointment-type {
  font-size: 14px;
  color: var(--color-text);
  margin: 0 0 2px 0;
}

.practitioner {
  font-size: 13px;
  color: var(--color-muted);
  margin: 0;
}

.appointment-actions {
  display: flex;
  gap: var(--space-2);
  justify-content: flex-end;
}
```

### Treatment Summary Card
Display treatment progress and key metrics.

```html
<div class="treatment-card">
  <div class="treatment-header">
    <h3 class="treatment-title">Physiotherapy Progress</h3>
    <span class="treatment-period">Last 30 days</span>
  </div>
  
  <div class="treatment-metrics">
    <div class="metric">
      <div class="metric-value">8</div>
      <div class="metric-label">Sessions</div>
    </div>
    <div class="metric">
      <div class="metric-value">85%</div>
      <div class="metric-label">Improvement</div>
    </div>
    <div class="metric">
      <div class="metric-value">2</div>
      <div class="metric-label">Assessments</div>
    </div>
  </div>
  
  <div class="treatment-progress">
    <div class="progress-header">
      <span>Recovery Progress</span>
      <span class="progress-percent">85%</span>
    </div>
    <div class="progress-bar">
      <div class="progress-fill" style="width: 85%"></div>
    </div>
  </div>
  
  <div class="treatment-next">
    <i class="material-icons">schedule</i>
    <span>Next session: Tomorrow at 2:00 PM</span>
  </div>
</div>
```

```css
.treatment-card {
  background: var(--color-white);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-6);
  box-shadow: var(--shadow-card);
}

.treatment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-5);
}

.treatment-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
}

.treatment-period {
  font-size: 13px;
  color: var(--color-muted);
}

.treatment-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}

.metric {
  text-align: center;
}

.metric-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-primary);
  margin-bottom: 4px;
}

.metric-label {
  font-size: 13px;
  color: var(--color-muted);
}

.treatment-progress {
  margin-bottom: var(--space-4);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-2);
  font-size: 14px;
}

.progress-percent {
  font-weight: 600;
  color: var(--color-primary);
}

.progress-bar {
  height: 8px;
  background: var(--color-border);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-primary);
  transition: width 0.3s ease;
}

.treatment-next {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 14px;
  color: var(--color-muted);
  background: var(--color-surface);
  padding: var(--space-3);
  border-radius: var(--radius-md);
}
```

## Status Indicators

### Status Badges
```css
.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 9999px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-badge.active {
  background: rgba(5, 150, 105, 0.1);
  color: var(--color-success);
}

.status-badge.inactive {
  background: rgba(107, 114, 128, 0.1);
  color: var(--color-muted);
}

.status-badge.confirmed {
  background: rgba(45, 99, 86, 0.1);
  color: var(--color-primary);
}

.status-badge.pending {
  background: rgba(245, 158, 11, 0.1);
  color: var(--color-warning);
}

.status-badge.cancelled {
  background: rgba(220, 53, 69, 0.1);
  color: var(--color-error);
}
```

### Discipline Tags
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
}

[data-theme="dark"] .discipline-tag {
  background: rgba(59, 127, 113, 0.15);
  color: var(--color-primary);
  border-color: rgba(59, 127, 113, 0.3);
}
```

## Card Layouts

### Grid Layout
```css
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--space-6);
  margin: var(--space-6) 0;
}

@media (max-width: 768px) {
  .card-grid {
    grid-template-columns: 1fr;
    gap: var(--space-4);
  }
}
```

### List Layout
```css
.card-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.card-list .card {
  flex-direction: row;
  align-items: center;
  padding: var(--space-5);
}
```

### Dashboard Layout
```html
<div class="dashboard-cards">
  <div class="card-row">
    <div class="stat-card">
      <div class="stat-value">24</div>
      <div class="stat-label">Today's Appointments</div>
      <div class="stat-change positive">
        <i class="material-icons">trending_up</i>
        +12% from yesterday
      </div>
    </div>
    
    <div class="stat-card">
      <div class="stat-value">156</div>
      <div class="stat-label">Active Patients</div>
      <div class="stat-change neutral">
        <i class="material-icons">trending_flat</i>
        No change
      </div>
    </div>
    
    <div class="stat-card">
      <div class="stat-value">92%</div>
      <div class="stat-label">Attendance Rate</div>
      <div class="stat-change positive">
        <i class="material-icons">trending_up</i>
        +3% this week
      </div>
    </div>
  </div>
</div>
```

```css
.dashboard-cards {
  margin: var(--space-6) 0;
}

.card-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-5);
}

.stat-card {
  background: var(--color-white);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-6);
  box-shadow: var(--shadow-card);
  text-align: center;
}

.stat-value {
  font-size: 2.25rem;
  font-weight: 700;
  color: var(--color-primary);
  margin-bottom: var(--space-2);
}

.stat-label {
  font-size: 14px;
  color: var(--color-muted);
  margin-bottom: var(--space-3);
}

.stat-change {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-1);
  font-size: 13px;
  font-weight: 500;
}

.stat-change.positive {
  color: var(--color-success);
}

.stat-change.negative {
  color: var(--color-error);
}

.stat-change.neutral {
  color: var(--color-muted);
}

.stat-change .material-icons {
  font-size: 16px;
}
```

## Mobile Optimizations

### Mobile Card Adaptations
```css
@media (max-width: 768px) {
  .card {
    padding: var(--space-5);
    margin: 0 var(--space-4);
  }
  
  .patient-card {
    padding: var(--space-4);
  }
  
  .patient-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-3);
  }
  
  .patient-actions {
    width: 100%;
    justify-content: space-between;
  }
  
  .patient-actions .btn {
    flex: 1;
  }
  
  .treatment-metrics {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .card-grid {
    padding: 0 var(--space-4);
  }
}
```

## Accessibility Guidelines

### Card Accessibility
- Use semantic HTML structure within cards
- Include proper heading hierarchy
- Ensure sufficient color contrast for all text
- Provide keyboard navigation for interactive cards
- Include screen reader friendly labels

### Implementation Examples
```html
<!-- Accessible patient card -->
<article class="patient-card" tabindex="0" role="button" aria-label="Patient: Sarah Johnson">
  <header class="patient-header">
    <div class="patient-avatar" aria-hidden="true">
      <i class="material-icons">person</i>
    </div>
    <div class="patient-info">
      <h3 class="patient-name">Dr. Sarah Johnson</h3>
      <p class="patient-id">ID: HH-2025-0847</p>
    </div>
  </header>
  
  <!-- Card content with proper semantic structure -->
  <div class="patient-disciplines" aria-label="Healthcare disciplines">
    <span class="discipline-tag">Physiotherapy</span>
    <span class="discipline-tag">Occupational Therapy</span>
  </div>
  
  <footer class="patient-actions">
    <button class="btn btn-sm btn-primary" aria-label="View treatment notes for Sarah Johnson">
      <i class="material-icons" aria-hidden="true">description</i>
      Notes
    </button>
  </footer>
</article>
```

### Focus Management
```css
.card[tabindex]:focus {
  outline: var(--focus-outline);
  outline-offset: var(--focus-offset);
}

.card-interactive:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(45, 99, 86, 0.1);
}
```

## Healthcare-Specific Considerations

### Patient Privacy
- Ensure card content doesn't expose sensitive information at a glance
- Use initials or patient IDs instead of full names where appropriate
- Consider data masking in shared-screen scenarios
- Support quick card minimization for privacy

### Clinical Workflow Integration
- Design cards for rapid information scanning
- Include contextual actions relevant to each healthcare specialty
- Support batch operations on multiple cards
- Maintain consistent information hierarchy across specialties

### POPIA Compliance
- Include appropriate data access indicators
- Support audit trail requirements with card interaction logging
- Ensure data retention policies are reflected in card design
- Provide clear data export and deletion options

---

**Related Files:**
- [Color System](../color-system.md) - Card color specifications
- [Buttons](buttons.md) - Card action button implementations
- [Patient Components](clinical-components.md) - Specialized patient interface cards
- [Typography](../typography.md) - Card text styling guidelines

*This card system provides consistent, accessible, and professional content organization across all HadadaHealth healthcare practice management interfaces while supporting clinical workflows and patient privacy requirements.*