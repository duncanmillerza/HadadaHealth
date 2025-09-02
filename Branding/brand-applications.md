# Brand Applications

> Real-world implementation of HadadaHealth brand across clinical interfaces and healthcare contexts

## Clinical Interface Applications

### Patient Management Systems

#### Patient Cards and Lists
```html
<!-- Patient card with brand elements -->
<div class="patient-card">
  <div class="header">
    <div class="avatar">
      <i class="material-icons" style="color: var(--color-primary);">person</i>
    </div>
    <div class="info">
      <h3 class="patient-name">Dr. Sarah Johnson</h3>
      <p class="patient-id">ID: HH-2025-0847</p>
    </div>
    <div class="status-badge success">Active</div>
  </div>
  <div class="disciplines">
    <span class="discipline-tag">Physiotherapy</span>
    <span class="discipline-tag">Occupational Therapy</span>
  </div>
  <div class="actions">
    <button class="btn btn-sm btn-primary">
      <i class="material-icons">description</i>
      Treatment Notes
    </button>
    <button class="btn btn-sm btn-secondary">
      <i class="material-icons">schedule</i>
      Schedule
    </button>
  </div>
</div>
```

**Brand Elements Applied:**
- Primary green for person icons and primary actions
- Discipline tags with brand color background (10% opacity)
- Consistent button system with proper hierarchy
- Professional typography and spacing

#### Clinical Documentation
- Cards display patient information with discipline tags
- Status indicators show treatment progress using brand color system
- Navigation uses primary brand color for professional appearance
- Form controls follow brand spacing and border radius standards

### Appointment Scheduling

#### Calendar Interfaces
```css
.appointment-slot.available {
  background: rgba(45, 99, 86, 0.1);
  border-left: 3px solid var(--color-primary);
}

.appointment-slot.booked {
  background: var(--color-primary);
  color: white;
}

.appointment-slot.pending {
  background: rgba(245, 158, 11, 0.1);
  border-left: 3px solid var(--color-warning);
}
```

**Brand Integration:**
- Primary green for confirmed appointments
- Consistent spacing system for time slots
- Professional color coding that doesn't rely solely on color
- Clear hierarchy using typography system

### Treatment Planning

#### Progress Tracking
```html
<div class="progress-indicator">
  <div class="stepper">
    <div class="dot completed">1</div>
    <div class="line completed"></div>
    <div class="dot active">2</div>
    <div class="line"></div>
    <div class="dot">3</div>
  </div>
  <div class="step-labels">
    <span class="completed">Assessment</span>
    <span class="active">Treatment</span>
    <span>Review</span>
  </div>
</div>
```

**Brand Application:**
- Primary green for completed steps
- Secondary blue for active steps  
- Neutral colors for pending steps
- Consistent spacing and typography

## Healthcare Compliance Applications

### POPIA/GDPR Compliance Integration

#### Data Handling Notifications
```html
<div class="compliance-notice">
  <i class="material-icons info">info</i>
  <div class="content">
    <strong>Patient Data Privacy</strong>
    <p>This information is protected under POPIA regulations. Access is logged for audit purposes.</p>
  </div>
</div>
```

**Compliance Brand Elements:**
- Info blue for privacy notifications
- Professional typography for legal messaging
- Consistent card styling with brand border radius
- Clear iconography with accessible color contrast

#### Audit Trail Display
- All patient data interfaces include POPIA compliance messaging
- Audit trail language emphasizes security and privacy using professional voice
- Clinical documentation templates maintain professional tone
- Export formats use serif typography for formal reports

#### Consent Management
```html
<div class="consent-card">
  <div class="consent-header">
    <i class="material-icons success">check_circle</i>
    <h4>Patient Consent Status</h4>
  </div>
  <div class="consent-items">
    <div class="consent-item granted">
      <span>Treatment Documentation</span>
      <small>Granted: 2025-08-15</small>
    </div>
    <div class="consent-item pending">
      <span>Data Sharing with Specialists</span>
      <small>Pending patient signature</small>
    </div>
  </div>
</div>
```

**Compliance Design Standards:**
- Success green for granted permissions
- Warning colors for pending items
- Clear status indicators with text and color
- Professional layout with brand spacing

### Security Interface Elements

#### Login and Authentication
```css
.login-form {
  background: white;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-modal);
  padding: var(--space-10);
}

.security-notice {
  background: rgba(45, 99, 86, 0.05);
  border-left: 4px solid var(--color-primary);
  padding: var(--space-4);
  margin: var(--space-6) 0;
}
```

## Multi-Disciplinary Support Applications

### Discipline-Specific Features

#### Physiotherapy Interface
```html
<div class="discipline-section physiotherapy">
  <div class="discipline-header">
    <i class="material-icons">healing</i>
    <h3>Physiotherapy Assessment</h3>
  </div>
  <div class="measurement-grid">
    <div class="measurement-item">
      <label>ROM - Shoulder Flexion</label>
      <input type="number" class="input" placeholder="Degrees">
    </div>
    <div class="measurement-item">
      <label>Pain Level (0-10)</label>
      <input type="number" class="input" min="0" max="10">
    </div>
  </div>
</div>
```

#### Occupational Therapy Interface
```html
<div class="discipline-section occupational-therapy">
  <div class="discipline-header">
    <i class="material-icons">accessibility</i>
    <h3>Occupational Therapy Goals</h3>
  </div>
  <div class="adl-checklist">
    <div class="adl-item">
      <label class="checkbox-label">
        <input type="checkbox" class="checkbox">
        <span class="checkmark"></span>
        Independent dressing
      </label>
    </div>
    <div class="adl-item">
      <label class="checkbox-label">
        <input type="checkbox" class="checkbox">
        <span class="checkmark"></span>
        Kitchen safety
      </label>
    </div>
  </div>
</div>
```

**Multi-Disciplinary Design Principles:**
- Discipline tags use primary green with 10% opacity background
- Color coding supports but doesn't replace text labels
- Interface accommodates various healthcare specialties
- Workflow patterns support collaborative care models
- Universal healthcare appeal in all variations

### Collaborative Care Features

#### Team Communication
```html
<div class="team-message">
  <div class="message-header">
    <span class="author">Dr. Smith (Physiotherapy)</span>
    <span class="timestamp">2 hours ago</span>
  </div>
  <div class="message-content">
    Patient showing significant improvement in mobility. 
    Ready for OT assessment of daily living activities.
  </div>
  <div class="message-actions">
    <button class="btn btn-sm btn-secondary">Reply</button>
    <button class="btn btn-sm btn-tertiary">Forward to OT</button>
  </div>
</div>
```

## Print and Export Applications

### Clinical Reports
- Export formats use serif typography (Georgia) for formal reports
- Brand logo appears subtly in header/footer
- Professional layout with ample white space
- POPIA compliance statements included

### Prescription and Referral Forms
```css
@media print {
  .clinical-document {
    font-family: var(--font-serif);
    color: black;
    background: white;
  }
  
  .document-header {
    border-bottom: 2px solid var(--color-primary);
    padding-bottom: var(--space-4);
    margin-bottom: var(--space-6);
  }
  
  .watermark {
    position: absolute;
    opacity: 0.1;
    background-image: url('monogram-green.svg');
  }
}
```

### Business Documents
- Letterheads use Wordmark Green logo
- Business cards feature Text Green variation
- Invoice templates maintain brand consistency
- Email signatures use 120px width maximum for compatibility

## Mobile Healthcare Applications

### Tablet Interface for Clinicians
```css
@media (min-width: 768px) and (max-width: 1024px) {
  .clinical-interface {
    padding: var(--space-6);
    gap: var(--space-4);
  }
  
  .patient-card {
    grid-template-columns: auto 1fr auto;
    align-items: center;
  }
}
```

### Smartphone Quick Access
```css
@media (max-width: 767px) {
  .quick-actions {
    position: fixed;
    bottom: var(--space-20);
    right: var(--space-4);
    z-index: 1000;
  }
  
  .quick-action-btn {
    background: var(--color-primary);
    color: white;
    border-radius: 50%;
    width: 56px;
    height: 56px;
    box-shadow: var(--shadow-modal);
  }
}
```

## Quality Assurance for Brand Applications

### Clinical Implementation Checklist
- [ ] Patient privacy maintained in all interfaces
- [ ] POPIA compliance messaging included where appropriate
- [ ] Professional appearance suitable for clinical settings
- [ ] Multi-disciplinary language used appropriately
- [ ] Brand colors used consistently across all features
- [ ] Typography hierarchy maintained in clinical documents
- [ ] Accessibility standards met for all user interfaces

### Brand Consistency Verification
- [ ] Logo usage follows guidelines across all applications
- [ ] Color palette applied correctly in all contexts
- [ ] Typography system implemented consistently
- [ ] Spacing and layout standards maintained
- [ ] Voice and tone appropriate for healthcare context
- [ ] Interactive elements follow brand interaction patterns

---

*Real-world brand applications ensure consistent, professional healthcare interfaces that build trust, support clinical workflows, and maintain regulatory compliance across all user touchpoints.*