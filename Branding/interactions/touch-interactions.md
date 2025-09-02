# Touch Interactions

> Mobile touch feedback and gesture support for HadadaHealth healthcare practice management interfaces.

## Touch Interaction Philosophy

HadadaHealth implements comprehensive touch interactions designed specifically for healthcare professionals who frequently use tablets and smartphones in clinical environments. Touch interactions provide immediate feedback while maintaining professional standards and supporting clinical workflows.

## Basic Touch Feedback

### Touch States
Immediate visual response to touch interactions across all interface elements.

```css
/* Base touch feedback */
.touchable {
  -webkit-tap-highlight-color: transparent;
  user-select: none;
  cursor: pointer;
  transition: all 0.1s ease;
}

.touchable:active {
  transform: scale(0.98);
  opacity: 0.8;
}

/* Button touch feedback */
.btn:active,
.card:active {
  transform: scale(0.98);
  transition: transform 0.1s ease;
}

/* Navigation link touch feedback */
.mobile-nav-link:active {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(0.95);
}

[data-theme="dark"] .mobile-nav-link:active {
  background: rgba(59, 127, 113, 0.2);
}
```

### Ripple Effect System
Material Design-inspired ripple animations for tactile feedback.

```html
<button class="btn btn-primary ripple-container">
  Save Patient Data
</button>
```

```css
.ripple-container {
  position: relative;
  overflow: hidden;
}

.ripple {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
  animation: rippleEffect 0.6s linear;
  background: rgba(255, 255, 255, 0.3);
}

@keyframes rippleEffect {
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
class RippleEffect {
  constructor() {
    this.init();
  }
  
  init() {
    document.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: true });
    document.addEventListener('click', this.handleClick.bind(this));
  }
  
  handleTouchStart(e) {
    const target = e.target.closest('.ripple-container');
    if (target) {
      this.createRipple(e, target);
    }
  }
  
  handleClick(e) {
    // Fallback for mouse users
    const target = e.target.closest('.ripple-container');
    if (target && e.type === 'click' && !e.isTrusted) return;
    if (target) {
      this.createRipple(e, target);
    }
  }
  
  createRipple(event, element) {
    const ripple = document.createElement('span');
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.height, rect.width);
    
    // Get touch point or click point
    const clientX = event.touches ? event.touches[0].clientX : event.clientX;
    const clientY = event.touches ? event.touches[0].clientY : event.clientY;
    
    const x = clientX - rect.left - size / 2;
    const y = clientY - rect.top - size / 2;
    
    ripple.className = 'ripple';
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    
    element.appendChild(ripple);
    
    // Remove ripple after animation
    setTimeout(() => {
      if (ripple.parentNode) {
        ripple.parentNode.removeChild(ripple);
      }
    }, 600);
  }
}

// Initialize ripple effects
document.addEventListener('DOMContentLoaded', () => {
  new RippleEffect();
});
```

## Gesture Support

### Swipe Gestures
Touch gesture handling for patient cards and lists.

```javascript
class SwipeGestures {
  constructor() {
    this.startX = null;
    this.startY = null;
    this.threshold = 50; // Minimum swipe distance
    this.maxVertical = 100; // Maximum vertical movement for horizontal swipe
    
    this.init();
  }
  
  init() {
    document.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: true });
    document.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
    document.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: true });
  }
  
  handleTouchStart(e) {
    const touch = e.touches[0];
    this.startX = touch.clientX;
    this.startY = touch.clientY;
    this.targetElement = e.target.closest('.swipeable');
  }
  
  handleTouchMove(e) {
    if (!this.startX || !this.startY || !this.targetElement) return;
    
    const touch = e.touches[0];
    const deltaX = touch.clientX - this.startX;
    const deltaY = Math.abs(touch.clientY - this.startY);
    
    // Prevent vertical scrolling during horizontal swipe
    if (Math.abs(deltaX) > 10 && deltaY < this.maxVertical) {
      e.preventDefault();
      
      // Visual feedback during swipe
      const swipeProgress = Math.min(Math.abs(deltaX) / 200, 1);
      this.updateSwipeVisual(this.targetElement, deltaX, swipeProgress);
    }
  }
  
  handleTouchEnd(e) {
    if (!this.startX || !this.startY || !this.targetElement) {
      this.reset();
      return;
    }
    
    const touch = e.changedTouches[0];
    const deltaX = touch.clientX - this.startX;
    const deltaY = Math.abs(touch.clientY - this.startY);
    
    // Check if it's a valid horizontal swipe
    if (Math.abs(deltaX) > this.threshold && deltaY < this.maxVertical) {
      if (deltaX > 0) {
        this.handleSwipeRight(this.targetElement);
      } else {
        this.handleSwipeLeft(this.targetElement);
      }
    } else {
      // Reset visual state if swipe was incomplete
      this.resetSwipeVisual(this.targetElement);
    }
    
    this.reset();
  }
  
  updateSwipeVisual(element, deltaX, progress) {
    if (deltaX > 0) {
      // Swipe right - show positive action
      element.style.transform = `translateX(${Math.min(deltaX * 0.3, 60)}px)`;
      element.style.background = `rgba(5, 150, 105, ${progress * 0.1})`;
    } else {
      // Swipe left - show negative action
      element.style.transform = `translateX(${Math.max(deltaX * 0.3, -60)}px)`;
      element.style.background = `rgba(220, 53, 69, ${progress * 0.1})`;
    }
  }
  
  resetSwipeVisual(element) {
    element.style.transform = '';
    element.style.background = '';
  }
  
  handleSwipeRight(element) {
    // Handle swipe right action (e.g., mark as complete)
    this.showSwipeAction(element, 'right', 'Marked as complete');
    this.resetSwipeVisual(element);
  }
  
  handleSwipeLeft(element) {
    // Handle swipe left action (e.g., archive/delete)
    this.showSwipeAction(element, 'left', 'Archived');
    this.resetSwipeVisual(element);
  }
  
  showSwipeAction(element, direction, message) {
    // Show temporary feedback message
    const feedback = document.createElement('div');
    feedback.className = `swipe-feedback swipe-${direction}`;
    feedback.textContent = message;
    feedback.style.cssText = `
      position: absolute;
      top: 50%;
      ${direction === 'right' ? 'right' : 'left'}: 16px;
      transform: translateY(-50%);
      padding: 8px 12px;
      background: ${direction === 'right' ? 'var(--color-success)' : 'var(--color-error)'};
      color: white;
      border-radius: var(--radius-md);
      font-size: 13px;
      font-weight: 500;
      z-index: 10;
      animation: fadeInOut 2s ease-out;
    `;
    
    element.style.position = 'relative';
    element.appendChild(feedback);
    
    setTimeout(() => {
      if (feedback.parentNode) {
        feedback.parentNode.removeChild(feedback);
      }
    }, 2000);
  }
  
  reset() {
    this.startX = null;
    this.startY = null;
    this.targetElement = null;
  }
}

// Initialize swipe gestures
document.addEventListener('DOMContentLoaded', () => {
  new SwipeGestures();
});
```

### Pull-to-Refresh
Healthcare-appropriate pull-to-refresh for patient lists and data.

```html
<div class="pull-refresh-container" id="patient-list-container">
  <div class="pull-refresh-indicator">
    <div class="refresh-icon">
      <i class="material-icons">refresh</i>
    </div>
    <div class="refresh-text">Pull to refresh patient list</div>
  </div>
  
  <div class="patient-list">
    <!-- Patient cards here -->
  </div>
</div>
```

```css
.pull-refresh-container {
  position: relative;
  overflow: hidden;
  transition: transform 0.3s ease;
}

.pull-refresh-indicator {
  position: absolute;
  top: -80px;
  left: 0;
  right: 0;
  height: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  z-index: 1;
}

.refresh-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
  transform: scale(0);
  transition: transform 0.2s ease;
}

.refresh-icon .material-icons {
  font-size: 18px;
}

.refresh-text {
  font-size: 13px;
  color: var(--color-muted);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.pull-refresh-container.pulling {
  transform: translateY(80px);
}

.pull-refresh-container.pulling .refresh-icon {
  transform: scale(1);
  animation: none;
}

.pull-refresh-container.pulling .refresh-text {
  opacity: 1;
}

.pull-refresh-container.refreshing .refresh-icon {
  animation: spin 1s linear infinite;
}

.pull-refresh-container.refreshing .refresh-text {
  opacity: 1;
}
```

```javascript
class PullToRefresh {
  constructor(container, onRefresh) {
    this.container = container;
    this.onRefresh = onRefresh;
    this.startY = null;
    this.currentY = null;
    this.pullDistance = 0;
    this.threshold = 80;
    this.isRefreshing = false;
    
    this.init();
  }
  
  init() {
    this.container.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: true });
    this.container.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
    this.container.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: true });
  }
  
  handleTouchStart(e) {
    if (this.isRefreshing || this.container.scrollTop > 0) return;
    
    this.startY = e.touches[0].clientY;
  }
  
  handleTouchMove(e) {
    if (this.isRefreshing || !this.startY || this.container.scrollTop > 0) return;
    
    this.currentY = e.touches[0].clientY;
    this.pullDistance = Math.max(0, this.currentY - this.startY);
    
    if (this.pullDistance > 10) {
      e.preventDefault();
      
      const pullRatio = Math.min(this.pullDistance / this.threshold, 1);
      const translateY = this.pullDistance * 0.4; // Damping effect
      
      this.container.style.transform = `translateY(${translateY}px)`;
      
      if (pullRatio >= 1) {
        this.container.classList.add('pulling');
      } else {
        this.container.classList.remove('pulling');
      }
    }
  }
  
  handleTouchEnd(e) {
    if (this.isRefreshing || !this.startY) return;
    
    if (this.pullDistance >= this.threshold) {
      this.triggerRefresh();
    } else {
      this.resetPull();
    }
    
    this.startY = null;
    this.currentY = null;
    this.pullDistance = 0;
  }
  
  triggerRefresh() {
    this.isRefreshing = true;
    this.container.classList.add('refreshing');
    this.container.classList.remove('pulling');
    this.container.style.transform = 'translateY(80px)';
    
    // Call the refresh callback
    Promise.resolve(this.onRefresh()).then(() => {
      this.completeRefresh();
    }).catch(() => {
      this.completeRefresh();
    });
  }
  
  completeRefresh() {
    setTimeout(() => {
      this.isRefreshing = false;
      this.container.classList.remove('refreshing');
      this.resetPull();
    }, 500); // Brief delay to show completion
  }
  
  resetPull() {
    this.container.style.transform = '';
    this.container.classList.remove('pulling', 'refreshing');
  }
}

// Initialize pull-to-refresh
document.addEventListener('DOMContentLoaded', () => {
  const patientListContainer = document.getElementById('patient-list-container');
  
  if (patientListContainer) {
    new PullToRefresh(patientListContainer, async () => {
      // Refresh patient data
      await fetchPatientData();
      // Update UI with new data
      updatePatientList();
    });
  }
});
```

## Touch-Optimized Components

### Touch-Friendly Buttons
Buttons optimized for touch interaction in clinical environments.

```css
/* Touch target sizing */
.btn-touch {
  min-height: 44px;
  min-width: 44px;
  padding: 12px 20px;
  font-size: 16px;
}

/* Large touch targets for critical actions */
.btn-critical {
  min-height: 56px;
  font-size: 18px;
  font-weight: 600;
  padding: 16px 32px;
}

/* Icon-only touch buttons */
.btn-icon-touch {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.btn-icon-touch .material-icons {
  font-size: 24px;
}

/* Touch feedback */
.btn-touch:active {
  transform: scale(0.96);
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
}
```

### Touch-Optimized Forms
Form controls designed for touch input in healthcare contexts.

```css
/* Touch-friendly input sizing */
.input-touch {
  min-height: 48px;
  font-size: 16px; /* Prevents iOS zoom */
  padding: 14px 16px;
  border-radius: var(--radius-md);
}

/* Large touch areas for checkboxes and radios */
.checkbox-touch,
.radio-touch {
  width: 24px;
  height: 24px;
  margin: 12px;
}

/* Touch-friendly select dropdowns */
.select-touch {
  min-height: 48px;
  font-size: 16px;
  padding: 14px 48px 14px 16px;
  background-size: 20px;
  background-position: right 16px center;
}

/* Floating action button for common actions */
.fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--color-primary);
  color: white;
  border: none;
  box-shadow: 0 4px 12px rgba(45, 99, 86, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  z-index: 1000;
}

.fab:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(45, 99, 86, 0.5);
}

.fab:active {
  transform: scale(1.05);
}

.fab .material-icons {
  font-size: 28px;
}

/* FAB for adding new patients */
.fab-add-patient {
  bottom: calc(80px + env(safe-area-inset-bottom)); /* Above mobile nav */
}
```

## Haptic Feedback Integration

### Vibration API Support
Subtle haptic feedback for touch interactions on supported devices.

```javascript
class HapticFeedback {
  constructor() {
    this.isSupported = 'vibrate' in navigator;
  }
  
  // Light tap feedback
  light() {
    if (this.isSupported) {
      navigator.vibrate(10);
    }
  }
  
  // Medium feedback for selections
  medium() {
    if (this.isSupported) {
      navigator.vibrate(20);
    }
  }
  
  // Strong feedback for important actions
  strong() {
    if (this.isSupported) {
      navigator.vibrate(50);
    }
  }
  
  // Error pattern
  error() {
    if (this.isSupported) {
      navigator.vibrate([100, 50, 100]);
    }
  }
  
  // Success pattern
  success() {
    if (this.isSupported) {
      navigator.vibrate([50, 25, 25]);
    }
  }
}

// Initialize haptic feedback
const haptic = new HapticFeedback();

// Use with touch interactions
document.addEventListener('DOMContentLoaded', () => {
  // Button presses
  document.querySelectorAll('.btn-primary').forEach(btn => {
    btn.addEventListener('touchstart', () => haptic.light(), { passive: true });
  });
  
  // Critical actions
  document.querySelectorAll('.btn-destructive').forEach(btn => {
    btn.addEventListener('touchstart', () => haptic.medium(), { passive: true });
  });
  
  // Form submissions
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', (e) => {
      if (form.checkValidity()) {
        haptic.success();
      } else {
        haptic.error();
      }
    });
  });
});
```

## Healthcare-Specific Touch Patterns

### Patient Card Touch Actions
Enhanced touch interactions for patient management.

```html
<div class="patient-card swipeable touchable">
  <div class="patient-info">
    <h3 class="patient-name">Dr. Sarah Johnson</h3>
    <p class="patient-id">HH-2025-0847</p>
  </div>
  
  <div class="touch-actions">
    <button class="btn-icon-touch btn-primary" aria-label="View patient details">
      <i class="material-icons">visibility</i>
    </button>
    <button class="btn-icon-touch btn-secondary" aria-label="Schedule appointment">
      <i class="material-icons">schedule</i>
    </button>
    <button class="btn-icon-touch btn-tertiary" aria-label="More actions">
      <i class="material-icons">more_vert</i>
    </button>
  </div>
</div>
```

### Emergency Quick Actions
Touch-optimized emergency action patterns.

```html
<div class="emergency-actions">
  <button class="btn-emergency" data-action="emergency-contact">
    <i class="material-icons">emergency</i>
    <span>Emergency Contact</span>
  </button>
  
  <button class="btn-emergency" data-action="urgent-appointment">
    <i class="material-icons">local_hospital</i>
    <span>Urgent Appointment</span>
  </button>
</div>
```

```css
.btn-emergency {
  min-height: 64px;
  padding: 16px;
  background: var(--color-error);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3);
  transition: all 0.2s ease;
  flex: 1;
}

.btn-emergency:active {
  transform: scale(0.95);
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.2);
}

.btn-emergency .material-icons {
  font-size: 32px;
}
```

## Accessibility & Touch

### Touch Accessibility Guidelines
```css
/* Focus visible for keyboard users even on touch devices */
.touchable:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-offset);
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .touchable:active {
    border: 2px solid currentColor;
  }
}

/* Larger touch targets for accessibility */
@media (pointer: coarse) {
  .btn-sm {
    min-height: 44px;
    padding: 12px 16px;
  }
  
  .checkbox,
  .radio {
    width: 20px;
    height: 20px;
  }
}
```

### Screen Reader Support
```html
<!-- Touch interactions with proper ARIA labels -->
<div class="patient-card swipeable" 
     role="article" 
     aria-label="Patient: Dr. Sarah Johnson"
     tabindex="0">
  
  <!-- Touch actions with descriptive labels -->
  <button class="btn-icon-touch" 
          aria-label="View detailed information for Dr. Sarah Johnson">
    <i class="material-icons" aria-hidden="true">visibility</i>
  </button>
</div>

<!-- Swipe instructions for screen readers -->
<div class="sr-only">
  Swipe right to mark as complete, swipe left to archive
</div>
```

## Performance Optimization

### Touch Event Optimization
```javascript
// Passive event listeners for better scroll performance
const touchOptions = { passive: true, capture: false };

element.addEventListener('touchstart', handler, touchOptions);
element.addEventListener('touchmove', handler, { passive: false }); // Only when preventing default
element.addEventListener('touchend', handler, touchOptions);

// Debounce rapid touch events
function debounceTouch(func, delay) {
  let timeoutId;
  return function (...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(this, args), delay);
  };
}

// Throttle continuous touch events
function throttleTouch(func, delay) {
  let lastCall = 0;
  return function (...args) {
    const now = Date.now();
    if (now - lastCall >= delay) {
      lastCall = now;
      func.apply(this, args);
    }
  };
}
```

---

**Related Files:**
- [Animations](animations.md) - Touch animation patterns
- [Mobile Design](../implementation/responsive-design.md) - Mobile-first touch considerations
- [Buttons](../components/buttons.md) - Touch-optimized button implementations
- [Accessibility](../implementation/accessibility.md) - Touch accessibility guidelines

*This touch interaction system ensures professional, accessible, and responsive touch feedback across all HadadaHealth healthcare practice management interfaces while supporting clinical workflows and various mobile device types.*