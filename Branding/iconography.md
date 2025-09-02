# Iconography System

> Material Icons for consistent healthcare interfaces with accessibility standards

## Overview

HadadaHealth uses **Material Icons** (Google Material Design Icons) for consistency with modern healthcare interfaces and accessibility standards.

### Implementation
- **Library:** Google Material Icons
- **CDN:** `https://fonts.googleapis.com/icon?family=Material+Icons`
- **Usage:** `<i class="material-icons">icon_name</i>`
- **Alternative:** Material Symbols for newer implementations

## Icon Styles

### Standard Material Icons
- **Style:** Filled (default)
- **Weight:** 400 (regular)
- **Grade:** 0 (standard)
- **Optical Size:** 24px (default)

### Available Variants
- **Outlined:** For secondary actions and less emphasis
- **Rounded:** For softer, more approachable interfaces
- **Sharp:** For technical/clinical precision (use sparingly)

## Sizing Standards

### Size Scale
- **Small:** 16px - Inline with text, compact spaces
- **Default:** 24px - Standard UI elements, buttons
- **Medium:** 32px - Cards, larger touch targets
- **Large:** 48px - Primary actions, headers
- **Extra Large:** 64px+ - Landing pages, empty states

### Healthcare-Specific Sizing
- **Form icons:** 20px (aligned with 48px input height)
- **Navigation icons:** 24px (standard touch target)
- **Status indicators:** 16px (inline with text)
- **Primary actions:** 24px (button icons)

## Color Guidelines

### Icon Colors
- **Primary actions:** `#2D6356` (Hadada Green)
- **Secondary actions:** `#32517A` (Deep Blue)
- **Destructive actions:** `#96364C` (Deep Rose)
- **Default state:** `#6B7280` (Muted Gray)
- **Disabled state:** `#E5E7EB` (Border Gray)
- **Active state:** `#2D6356` (Primary Green)

### Clinical Context Colors
- **Success/Complete:** `#059669` (Success Green)
- **Warning/Review:** `#F59E0B` (Warning Amber)
- **Error/Urgent:** `#DC3545` (Error Red)
- **Info/Note:** `#0EA5E9` (Info Blue)

## Healthcare Icon Library

### Patient Management
- **add_circle:** Add new patient
- **person:** Patient profile
- **group:** Multiple patients/family
- **contact_page:** Patient details
- **badge:** Patient ID/credentials
- **elderly:** Senior patient indicator

### Clinical Documentation
- **description:** Treatment notes
- **assignment:** Assessment forms
- **fact_check:** Completed documentation
- **edit:** Edit/modify notes
- **history:** Patient history
- **timeline:** Progress tracking

### Appointments & Scheduling
- **event:** Appointments
- **schedule:** Time slots
- **today:** Current day
- **date_range:** Date picker
- **access_time:** Time picker
- **notification_important:** Reminders

### Medical/Clinical
- **medical_services:** General medical
- **healing:** Physiotherapy/rehabilitation
- **psychology:** Mental health
- **hearing:** Audiology/speech therapy
- **accessibility:** Occupational therapy
- **monitor_heart:** Vital signs
- **medication:** Prescriptions

### Navigation & Actions
- **dashboard:** Main dashboard
- **folder:** File organization
- **search:** Search functionality
- **filter_list:** Filter/sort
- **settings:** Configuration
- **help:** Help/support
- **logout:** Sign out
- **menu:** Navigation menu

### Status & Feedback
- **check_circle:** Success/completed
- **error:** Error state
- **warning:** Warning/caution
- **info:** Information
- **pending:** In progress
- **cancel:** Cancelled/removed

### Communication
- **email:** Email correspondence
- **phone:** Phone contact
- **message:** Messages/notes
- **print:** Print documents
- **share:** Share information
- **download:** Export/download

## Implementation Guidelines

### Accessibility
- **Alt text:** Always include meaningful alternative text
- **ARIA labels:** Use `aria-label` for icon-only buttons
- **Color independence:** Never rely solely on color to convey meaning
- **Touch targets:** Minimum 44px touch target for mobile
- **Keyboard navigation:** Ensure icons are keyboard accessible

### Usage Rules

#### Do's
- Use standard Material Icons when available
- Maintain consistent sizing within interface sections
- Pair destructive icons with destructive colors
- Use outlined variants for secondary actions
- Include text labels alongside icons when space permits
- Test icons with screen readers

#### Don'ts
- Mix icon styles within the same interface
- Use custom icons unless absolutely necessary
- Rely on color alone to indicate icon meaning
- Use icons smaller than 16px in production
- Ignore accessibility requirements
- Use medical symbols without proper context

## Clinical Interface Applications

### Patient Cards
```html
<div class="patient-card">
  <i class="material-icons" style="color: #2D6356;">person</i>
  <span>Patient Name</span>
  <i class="material-icons status-icon" style="color: #059669;">check_circle</i>
</div>
```

### Treatment Actions
```html
<button class="btn btn-primary">
  <i class="material-icons">description</i>
  Add Treatment Note
</button>
```

### Navigation Menu
```html
<nav>
  <a href="/dashboard">
    <i class="material-icons">dashboard</i>
    Dashboard
  </a>
  <a href="/patients">
    <i class="material-icons">group</i>
    Patients
  </a>
</nav>
```

## Responsive Behavior
- **Mobile:** Reduce icon sizes by 2-4px for compact layouts
- **Tablet:** Maintain standard sizing with adequate touch targets
- **Desktop:** Use standard or larger sizes for better visibility
- **High DPI:** Icons scale automatically with CSS pixel density

## Performance Considerations
- **Loading:** Use icon fonts for faster rendering
- **Caching:** Leverage Google Fonts CDN caching
- **Fallbacks:** Provide text fallbacks for failed icon loads
- **Bundle size:** Consider Material Symbols for smaller bundle sizes

---

*Consistent iconography creates intuitive healthcare interfaces while maintaining professional clinical standards.*