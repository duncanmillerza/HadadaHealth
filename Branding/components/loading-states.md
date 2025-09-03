# Loading States

> Animation and loading systems for HadadaHealth healthcare practice management interfaces.

## Loading State Philosophy

HadadaHealth implements comprehensive loading state systems designed for healthcare environments where clear visual feedback is essential for user confidence and workflow continuity. Loading states provide professional feedback during data operations while maintaining clinical credibility.

## Page Loading (Login Screen Style)

### Full-Screen Page Loading
Used for initial app loading, login screens, and major navigation transitions.

```html
<div class="page-loading-screen" id="page-loading">
  <div class="loading-container">
    <svg class="loading-logo" viewBox="0 0 776 855">
      <path class="logo-path" 
            d="M761 294.183C742.864 291.315 724.487 291.987 706.5 295.183C688.513 298.379 671.195 304.072 655.5 312.063..." 
            stroke="white" 
            stroke-width="30" 
            fill="none"/>
    </svg>
    <div class="loading-text">Loading HadadaHealth...</div>
    <div class="loading-progress">
      <div class="progress-bar">
        <div class="progress-fill"></div>
      </div>
    </div>
  </div>
</div>
```

```css
.page-loading-screen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #2D6356 0%, #32517A 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  opacity: 0;
  visibility: hidden;
  transition: all 0.5s ease;
}

.page-loading-screen.show {
  opacity: 1;
  visibility: visible;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.loading-logo {
  width: 120px;
  height: 140px;
  margin-bottom: 24px;
}

.logo-path {
  stroke-dasharray: 3000;
  stroke-dashoffset: 3000;
  animation: draw 2s ease-in-out forwards,
             undraw 1.5s ease-in-out 2.5s forwards;
}

@keyframes draw {
  to { stroke-dashoffset: 0; }
}

@keyframes undraw {
  to { stroke-dashoffset: -3000; }
}

.loading-text {
  color: white;
  font-size: 1.25rem;
  font-weight: 500;
  margin-bottom: 32px;
  opacity: 0;
  animation: fadeInText 0.5s ease-in-out 1s forwards;
}

@keyframes fadeInText {
  to { opacity: 1; }
}

.loading-progress {
  width: 200px;
}

.progress-bar {
  width: 100%;
  height: 4px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: white;
  border-radius: 2px;
  width: 0;
  animation: fillProgress 3s ease-out 1.5s forwards;
}

@keyframes fillProgress {
  to { width: 100%; }
}
```

### Page Loading JavaScript
```javascript
class PageLoader {
  constructor() {
    this.loadingScreen = document.getElementById('page-loading');
    this.logoPath = document.querySelector('.logo-path');
  }
  
  show() {
    if (this.loadingScreen) {
      this.loadingScreen.classList.add('show');
      
      // Reset animations
      if (this.logoPath) {
        this.logoPath.style.animation = 'none';
        this.logoPath.offsetHeight; // Trigger reflow
        this.logoPath.style.animation = null;
      }
    }
  }
  
  hide() {
    if (this.loadingScreen) {
      setTimeout(() => {
        this.loadingScreen.classList.remove('show');
      }, 4500); // Match animation duration
    }
  }
  
  // Auto-hide after animations complete
  autoHide() {
    setTimeout(() => {
      this.hide();
    }, 4500);
  }
}

// Usage
const pageLoader = new PageLoader();

// Show on app initialization
document.addEventListener('DOMContentLoaded', () => {
  pageLoader.show();
  pageLoader.autoHide();
});
```

## Data Loading (Blur Overlay Style)

### Data Loading Overlay
Used for data fetching, form submissions, and background operations while maintaining context.

```html
<div class="data-loading-overlay" id="data-loading">
  <div class="loading-content">
    <div class="spinner-container">
      <div class="spinner"></div>
    </div>
    <p class="loading-message">Saving patient data...</p>
    <div class="loading-details">Please wait while we securely process your information</div>
  </div>
</div>
```

```css
.data-loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(15, 20, 25, 0.8);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s ease;
}

.data-loading-overlay.show {
  opacity: 1;
  visibility: visible;
}

.loading-content {
  background: var(--color-white);
  border-radius: var(--radius-md);
  padding: var(--space-8);
  box-shadow: var(--shadow-modal);
  text-align: center;
  max-width: 400px;
  margin: var(--space-4);
}

[data-theme="dark"] .loading-content {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
}

.spinner-container {
  display: flex;
  justify-content: center;
  margin-bottom: var(--space-5);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(45, 99, 86, 0.2);
  border-top: 4px solid var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-message {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 var(--space-2) 0;
}

.loading-details {
  font-size: 14px;
  color: var(--color-muted);
  margin: 0;
}
```

### Data Loading JavaScript
```javascript
class DataLoader {
  constructor() {
    this.overlay = document.getElementById('data-loading');
    this.messageEl = this.overlay?.querySelector('.loading-message');
    this.detailsEl = this.overlay?.querySelector('.loading-details');
  }
  
  show(message = 'Processing...', details = '') {
    if (this.overlay) {
      if (this.messageEl) this.messageEl.textContent = message;
      if (this.detailsEl) this.detailsEl.textContent = details;
      
      this.overlay.classList.add('show');
      document.body.style.overflow = 'hidden';
    }
  }
  
  hide() {
    if (this.overlay) {
      this.overlay.classList.remove('show');
      document.body.style.overflow = '';
    }
  }
  
  // Healthcare-specific loading messages
  showSavingPatient() {
    this.show(
      'Saving patient data...', 
      'Securely processing patient information in compliance with POPIA'
    );
  }
  
  showGeneratingReport() {
    this.show(
      'Generating clinical report...', 
      'Compiling assessment data and treatment notes'
    );
  }
  
  showSchedulingAppointment() {
    this.show(
      'Scheduling appointment...', 
      'Checking availability and updating calendar'
    );
  }
}

// Usage
const dataLoader = new DataLoader();

// Example: Form submission
async function savePatientData(formData) {
  dataLoader.showSavingPatient();
  
  try {
    const response = await fetch('/api/patients', {
      method: 'POST',
      body: formData
    });
    
    if (response.ok) {
      // Success handling
    }
  } catch (error) {
    // Error handling
  } finally {
    dataLoader.hide();
  }
}
```

## Inline Loading States

### Button Loading States
Loading states for form submission and action buttons.

```css
.btn.loading {
  position: relative;
  color: transparent;
  pointer-events: none;
  cursor: not-allowed;
}

.btn.loading::after {
  content: "";
  position: absolute;
  top: 50%;
  left: 50%;
  width: 18px;
  height: 18px;
  margin: -9px 0 0 -9px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid rgba(255, 255, 255, 0.8);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.btn-secondary.loading::after {
  border: 2px solid rgba(45, 99, 86, 0.3);
  border-top: 2px solid var(--color-primary);
}
```

```html
<!-- Button loading states -->
<button class="btn btn-primary loading">Save Patient</button>
<button class="btn btn-secondary loading">Generate Report</button>
```

### Card Loading Skeletons
Placeholder content while cards load.

```html
<div class="card-skeleton">
  <div class="skeleton-header">
    <div class="skeleton-avatar"></div>
    <div class="skeleton-info">
      <div class="skeleton-line skeleton-title"></div>
      <div class="skeleton-line skeleton-subtitle"></div>
    </div>
  </div>
  <div class="skeleton-content">
    <div class="skeleton-line skeleton-text"></div>
    <div class="skeleton-line skeleton-text short"></div>
  </div>
  <div class="skeleton-actions">
    <div class="skeleton-button"></div>
    <div class="skeleton-button"></div>
  </div>
</div>
```

```css
.card-skeleton {
  background: var(--color-white);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-6);
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-header {
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.skeleton-avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--color-border);
}

.skeleton-info {
  flex: 1;
}

.skeleton-line {
  height: 16px;
  background: var(--color-border);
  border-radius: 4px;
  margin-bottom: 8px;
}

.skeleton-title {
  width: 70%;
  height: 20px;
}

.skeleton-subtitle {
  width: 50%;
}

.skeleton-content {
  margin-bottom: var(--space-5);
}

.skeleton-text {
  width: 100%;
}

.skeleton-text.short {
  width: 60%;
}

.skeleton-actions {
  display: flex;
  gap: var(--space-2);
}

.skeleton-button {
  width: 100px;
  height: 36px;
  background: var(--color-border);
  border-radius: var(--radius-md);
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}
```

## Progress Indicators

### Determinate Progress Bar
For operations with known duration or progress.

```html
<div class="progress-container">
  <div class="progress-header">
    <span class="progress-label">Uploading medical records</span>
    <span class="progress-percentage">65%</span>
  </div>
  <div class="progress-bar">
    <div class="progress-fill" style="width: 65%"></div>
  </div>
  <div class="progress-details">
    <span>Uploading file 3 of 5</span>
    <span>2.1 MB / 3.2 MB</span>
  </div>
</div>
```

```css
.progress-container {
  background: var(--color-white);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  margin: var(--space-4) 0;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-3);
}

.progress-label {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text);
}

.progress-percentage {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-primary);
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: var(--color-border);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: var(--space-3);
}

.progress-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-details {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: var(--color-muted);
}
```

### Step Progress Indicator
For multi-step processes like patient registration or assessment workflows.

```html
<div class="step-progress">
  <div class="step-indicator">
    <div class="step completed">
      <div class="step-number">
        <i class="material-icons">check</i>
      </div>
      <div class="step-label">Patient Info</div>
    </div>
    
    <div class="step-connector completed"></div>
    
    <div class="step active">
      <div class="step-number">2</div>
      <div class="step-label">Medical History</div>
    </div>
    
    <div class="step-connector"></div>
    
    <div class="step">
      <div class="step-number">3</div>
      <div class="step-label">Assessment</div>
    </div>
    
    <div class="step-connector"></div>
    
    <div class="step">
      <div class="step-number">4</div>
      <div class="step-label">Review</div>
    </div>
  </div>
</div>
```

```css
.step-progress {
  background: var(--color-white);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-6);
  margin: var(--space-4) 0;
}

.step-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-width: 150px;
}

.step-number {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  margin-bottom: var(--space-2);
  transition: all 0.3s ease;
}

.step:not(.completed):not(.active) .step-number {
  background: var(--color-surface);
  color: var(--color-muted);
  border: 2px solid var(--color-border);
}

.step.active .step-number {
  background: var(--color-secondary);
  color: white;
  border: 2px solid var(--color-secondary);
}

.step.completed .step-number {
  background: var(--color-primary);
  color: white;
  border: 2px solid var(--color-primary);
}

.step.completed .step-number .material-icons {
  font-size: 18px;
}

.step-label {
  font-size: 13px;
  font-weight: 500;
  text-align: center;
  color: var(--color-text);
}

.step-connector {
  flex: 1;
  height: 2px;
  background: var(--color-border);
  margin: 0 var(--space-3) var(--space-8) var(--space-3);
}

.step-connector.completed {
  background: var(--color-primary);
}
```

## Healthcare-Specific Loading Messages

### Clinical Loading Messages
```javascript
const clinicalLoadingMessages = {
  // Patient operations
  savingPatient: {
    message: 'Saving patient information...',
    details: 'Securely storing data in compliance with POPIA regulations'
  },
  
  loadingPatient: {
    message: 'Loading patient records...',
    details: 'Retrieving treatment history and assessments'
  },
  
  // Assessment operations
  savingAssessment: {
    message: 'Saving assessment data...',
    details: 'Recording clinical findings and measurements'
  },
  
  generatingReport: {
    message: 'Generating clinical report...',
    details: 'Compiling assessment data and treatment recommendations'
  },
  
  // Scheduling operations
  checkingAvailability: {
    message: 'Checking appointment availability...',
    details: 'Reviewing practitioner schedules and room bookings'
  },
  
  schedulingAppointment: {
    message: 'Scheduling appointment...',
    details: 'Confirming booking and sending notifications'
  },
  
  // Data export/import
  exportingData: {
    message: 'Exporting patient data...',
    details: 'Preparing secure data export with POPIA compliance'
  },
  
  importingRecords: {
    message: 'Importing medical records...',
    details: 'Processing and validating uploaded documents'
  }
};
```

## Performance Considerations

### Loading State Optimization
```css
/* Use transform and opacity for smooth animations */
.loading-element {
  will-change: transform, opacity;
}

/* Remove will-change after loading completes */
.loading-complete {
  will-change: auto;
}

/* Reduce animations for users who prefer reduced motion */
@media (prefers-reduced-motion: reduce) {
  .spinner,
  .progress-fill,
  .logo-path {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
  }
  
  .skeleton-line {
    animation: none;
    opacity: 0.5;
  }
}
```

### Memory Management
```javascript
class LoadingStateManager {
  constructor() {
    this.activeLoaders = new Set();
  }
  
  showLoader(loaderId, type = 'data') {
    this.activeLoaders.add(loaderId);
    // Show appropriate loader
  }
  
  hideLoader(loaderId) {
    this.activeLoaders.delete(loaderId);
    // Hide loader and cleanup
  }
  
  hideAll() {
    this.activeLoaders.clear();
    // Hide all active loaders
  }
  
  // Cleanup on page unload
  cleanup() {
    this.hideAll();
  }
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  loadingManager.cleanup();
});
```

---

**Related Files:**
- [Dark Mode](../dark-mode.md) - Theme-aware loading states
- [Buttons](buttons.md) - Button loading state implementations
- [Color System](../color-system.md) - Loading state color specifications
- [Animations](../interactions/animations.md) - Advanced loading animations

*This loading state system ensures professional, accessible, and contextually appropriate feedback during all data operations in HadadaHealth healthcare practice management interfaces while maintaining clinical credibility and user confidence.*