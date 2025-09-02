# Animations

> Scroll-triggered animations and motion design for HadadaHealth healthcare practice management interfaces.

## Animation Philosophy

HadadaHealth implements a professional animation system designed specifically for healthcare environments. Animations provide polish and feedback while maintaining clinical credibility and supporting accessibility requirements. All animations respect user preferences and performance constraints.

## Scroll-Triggered Animations

### Fade-Up Animations
Smooth content reveals as users scroll through interface sections.

```css
.animate-fade-up {
  opacity: 0;
  transform: translateY(20px);
  animation: fadeUp 0.6s ease-out forwards;
  animation-play-state: paused;
}

@keyframes fadeUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Staggered delays for sequential elements */
.animate-delay-100 { animation-delay: 0.1s; }
.animate-delay-200 { animation-delay: 0.2s; }
.animate-delay-300 { animation-delay: 0.3s; }
.animate-delay-400 { animation-delay: 0.4s; }
```

### Slide Animations
Directional content reveals for emphasizing relationships.

```css
.animate-slide-left {
  opacity: 0;
  transform: translateX(-30px);
  animation: slideLeft 0.8s ease-out forwards;
  animation-play-state: paused;
}

.animate-slide-right {
  opacity: 0;
  transform: translateX(30px);
  animation: slideRight 0.8s ease-out forwards;
  animation-play-state: paused;
}

@keyframes slideLeft {
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideRight {
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
```

### Scale Animations
Gentle zoom effects for prominent content.

```css
.animate-scale {
  opacity: 0;
  transform: scale(0.9);
  animation: scaleIn 0.5s ease-out forwards;
  animation-play-state: paused;
}

@keyframes scaleIn {
  to {
    opacity: 1;
    transform: scale(1);
  }
}
```

### Intersection Observer Implementation
Efficient scroll-based animation triggering system.

```javascript
class ScrollAnimations {
  constructor() {
    this.observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    };
    
    this.init();
  }
  
  init() {
    this.observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          this.triggerAnimation(entry.target);
        }
      });
    }, this.observerOptions);
    
    this.observeElements();
  }
  
  observeElements() {
    const animatedElements = document.querySelectorAll(
      '.animate-fade-up, .animate-slide-left, .animate-slide-right, .animate-scale'
    );
    
    animatedElements.forEach(el => {
      // Set initial state
      el.style.animationPlayState = 'paused';
      this.observer.observe(el);
    });
  }
  
  triggerAnimation(element) {
    // Trigger main element animation
    element.style.animationPlayState = 'running';
    element.style.opacity = '1';
    
    // Handle staggered child animations
    const children = element.querySelectorAll('[data-animate-child]');
    children.forEach((child, index) => {
      setTimeout(() => {
        child.style.animationPlayState = 'running';
        child.style.opacity = '1';
      }, index * 100);
    });
    
    // Stop observing after animation triggers
    this.observer.unobserve(element);
  }
  
  // Cleanup method
  destroy() {
    if (this.observer) {
      this.observer.disconnect();
    }
  }
}

// Initialize scroll animations
document.addEventListener('DOMContentLoaded', () => {
  const scrollAnimations = new ScrollAnimations();
  
  // Cleanup on page unload
  window.addEventListener('beforeunload', () => {
    scrollAnimations.destroy();
  });
});
```

## Interactive Animations

### Button Animations
Enhanced button feedback with professional touch.

```css
.btn {
  position: relative;
  transition: all 0.2s ease;
  transform: translateY(0);
}

.btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(45, 99, 86, 0.25);
}

.btn:active {
  transform: translateY(1px);
  transition-duration: 0.1s;
}

/* Ripple effect container */
.btn {
  overflow: hidden;
}

/* Ripple animation (added via JavaScript) */
.ripple {
  position: absolute;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  pointer-events: none;
  animation: ripple 0.6s linear;
}

@keyframes ripple {
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

### Card Hover Animations
Sophisticated card interactions for clinical interfaces.

```css
.card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  transform: translateY(0) scale(1);
}

.card:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

[data-theme="dark"] .card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

/* Patient card specific animations */
.patient-card {
  border-left: 4px solid transparent;
  transition: all 0.3s ease;
}

.patient-card:hover {
  border-left-color: var(--color-primary);
  background: rgba(45, 99, 86, 0.02);
  transform: translateX(4px);
}

[data-theme="dark"] .patient-card:hover {
  background: rgba(59, 127, 113, 0.1);
}
```

### Form Field Animations
Polished form interactions for clinical data entry.

```css
.input {
  transition: all 0.2s ease;
  border-color: var(--color-border);
}

.input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(45, 99, 86, 0.1);
  transform: scale(1.01);
}

/* Floating label animations */
.label-floating {
  transition: all 0.2s ease;
  transform: translateY(0) scale(1);
}

.input-floating:focus + .label-floating,
.input-floating:not(:placeholder-shown) + .label-floating {
  transform: translateY(-24px) scale(0.85);
  color: var(--color-primary);
}
```

## Loading Animations

### Spinner Animations
Professional loading indicators for healthcare operations.

```css
.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(45, 99, 86, 0.2);
  border-top: 3px solid var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Pulsing dot loader for subtle operations */
.pulse-loader {
  display: flex;
  gap: 4px;
  align-items: center;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary);
  animation: pulse-dot 1.4s ease-in-out infinite both;
}

.pulse-dot:nth-child(1) { animation-delay: -0.32s; }
.pulse-dot:nth-child(2) { animation-delay: -0.16s; }
.pulse-dot:nth-child(3) { animation-delay: 0s; }

@keyframes pulse-dot {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}
```

### Progress Animations
Smooth progress bar animations for data operations.

```css
.progress-bar {
  overflow: hidden;
  background: var(--color-border);
  border-radius: 4px;
  height: 8px;
}

.progress-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: 4px;
  transition: width 0.3s ease;
  transform-origin: left center;
}

/* Indeterminate progress animation */
.progress-indeterminate {
  position: relative;
  overflow: hidden;
}

.progress-indeterminate::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(45, 99, 86, 0.5),
    transparent
  );
  animation: slide 1.5s ease-in-out infinite;
}

@keyframes slide {
  0% { left: -100%; }
  100% { left: 100%; }
}
```

## Logo Animations

### Logo Draw Animation
Sophisticated logo animation for loading screens.

```css
.logo-animated {
  stroke-dasharray: 3000;
  stroke-dashoffset: 3000;
}

.logo-draw {
  animation: drawLogo 2s ease-in-out forwards;
}

.logo-undraw {
  animation: undrawLogo 1.5s ease-in-out forwards;
}

@keyframes drawLogo {
  to {
    stroke-dashoffset: 0;
  }
}

@keyframes undrawLogo {
  to {
    stroke-dashoffset: -3000;
  }
}

/* Logo hover animation */
.logo-interactive {
  transition: all 0.2s ease;
}

.logo-interactive:hover {
  transform: scale(1.05);
  filter: drop-shadow(0 4px 8px rgba(45, 99, 86, 0.2));
}
```

## Accessibility Considerations

### Reduced Motion Support
Comprehensive support for users who prefer reduced motion.

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
  
  /* Disable transforms for reduced motion */
  .animate-fade-up,
  .animate-slide-left,
  .animate-slide-right,
  .animate-scale {
    transform: none !important;
    opacity: 1 !important;
  }
  
  /* Keep essential loading animations but make them faster */
  .spinner {
    animation-duration: 0.5s !important;
  }
  
  /* Disable hover transforms */
  .card:hover,
  .btn:hover {
    transform: none !important;
  }
}
```

### Focus Animations
Accessible focus management with smooth transitions.

```css
.focusable {
  transition: outline 0.2s ease;
}

.focusable:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-offset);
  animation: focusGlow 0.3s ease-out;
}

@keyframes focusGlow {
  0% {
    outline-color: transparent;
  }
  100% {
    outline-color: rgba(45, 99, 86, 0.6);
  }
}
```

## Performance Optimization

### Hardware Acceleration
Optimized animations for smooth performance.

```css
/* Use transform and opacity for best performance */
.animate-optimized {
  will-change: transform, opacity;
  backface-visibility: hidden;
  perspective: 1000px;
}

/* Remove will-change after animation completes */
.animation-complete {
  will-change: auto;
}

/* Use transform instead of changing layout properties */
.slide-transform {
  transform: translateX(0);
  transition: transform 0.3s ease;
}

.slide-transform.moved {
  transform: translateX(100px);
}
```

### Animation Performance JavaScript
```javascript
class AnimationPerformance {
  constructor() {
    this.runningAnimations = new Set();
    this.rafId = null;
  }
  
  // Batch DOM updates for better performance
  batchAnimationUpdates(callback) {
    if (this.rafId) {
      cancelAnimationFrame(this.rafId);
    }
    
    this.rafId = requestAnimationFrame(() => {
      callback();
      this.rafId = null;
    });
  }
  
  // Throttle scroll-based animations
  throttleScrollAnimations = this.throttle((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        this.triggerAnimation(entry.target);
      }
    });
  }, 16); // ~60fps
  
  throttle(func, delay) {
    let timeoutId;
    let lastExecTime = 0;
    
    return function (...args) {
      const currentTime = Date.now();
      
      if (currentTime - lastExecTime > delay) {
        func.apply(this, args);
        lastExecTime = currentTime;
      } else {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
          func.apply(this, args);
          lastExecTime = Date.now();
        }, delay - (currentTime - lastExecTime));
      }
    };
  }
  
  // Clean up animations when elements leave viewport
  cleanupAnimation(element) {
    element.style.willChange = 'auto';
    this.runningAnimations.delete(element);
  }
}
```

## Healthcare-Specific Animation Patterns

### Clinical Data Reveal
Animations for revealing sensitive medical information.

```css
.clinical-data-reveal {
  opacity: 0;
  transform: translateY(10px);
  transition: all 0.4s ease;
}

.clinical-data-reveal.revealed {
  opacity: 1;
  transform: translateY(0);
}

/* Stagger medical records */
.medical-record {
  opacity: 0;
  animation: revealRecord 0.3s ease-out forwards;
}

.medical-record:nth-child(1) { animation-delay: 0.1s; }
.medical-record:nth-child(2) { animation-delay: 0.2s; }
.medical-record:nth-child(3) { animation-delay: 0.3s; }

@keyframes revealRecord {
  to {
    opacity: 1;
  }
}
```

### Status Change Animations
Smooth transitions for treatment status updates.

```css
.status-transition {
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.status-success {
  background: var(--color-success);
  animation: statusSuccess 0.6s ease-out;
}

.status-error {
  background: var(--color-error);
  animation: statusError 0.6s ease-out;
}

@keyframes statusSuccess {
  0% {
    background: var(--color-warning);
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    background: var(--color-success);
    transform: scale(1);
  }
}

@keyframes statusError {
  0% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-5px);
  }
  75% {
    transform: translateX(5px);
  }
  100% {
    transform: translateX(0);
  }
}
```

## Implementation Guidelines

### Animation Timing
- **Micro-interactions:** 0.1-0.2s (button presses, hover states)
- **UI transitions:** 0.2-0.3s (modal opening, form validation)
- **Page transitions:** 0.3-0.5s (route changes, major state changes)
- **Loading animations:** 1s+ (continuous until complete)

### Easing Functions
```css
:root {
  --ease-out-cubic: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-in-cubic: cubic-bezier(0.4, 0, 1, 1);
  --ease-bounce: cubic-bezier(0.175, 0.885, 0.32, 1.275);
  --ease-back: cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

/* Professional healthcare animations use subtle easing */
.professional-animation {
  transition: all 0.3s var(--ease-out-cubic);
}
```

### Testing Guidelines
- Test all animations across different devices and browsers
- Verify performance with Chrome DevTools Performance panel
- Test with reduced motion preferences enabled
- Ensure animations don't interfere with clinical workflows
- Validate accessibility with screen readers

---

**Related Files:**
- [Loading States](../components/loading-states.md) - Loading animation implementations
- [Touch Interactions](touch-interactions.md) - Mobile animation patterns
- [Hover Effects](hover-effects.md) - Desktop interaction animations
- [Accessibility](../implementation/accessibility.md) - Animation accessibility guidelines

*This animation system ensures professional, accessible, and performance-optimized motion design across all HadadaHealth healthcare practice management interfaces while maintaining clinical credibility and supporting user accessibility needs.*