# Report Creation Wizard - User Guide

> **New 5-Step Report Creation Wizard**  
> Replacing the legacy single-step modal with an intuitive, guided workflow

## Overview

The Report Creation Wizard is a 5-step guided process for creating AI-powered clinical reports. It provides booking-based recommendations, therapist suggestions, and automated content generation to streamline the report creation workflow.

## Accessing the Wizard

**From Dashboard:**
- Click the **"Create New Report"** button in the reports dashboard
- Or use the **"+"** button in the reports section

**Programmatic Access:**
```javascript
// Open wizard for therapist workflow
openReportWizard('therapist');

// Open wizard for manager workflow (assign to therapist)
openReportWizard('manager');
```

## Step-by-Step Guide

### Step 1: Patient Selection

**Purpose:** Select the patient for whom the report will be created.

**Features:**
- **Patient Search:** Start typing patient name to search
- **Recent Patients:** Quick access to your 5 most recent patients
- **Patient Information:** View patient ID, name, and date of birth

**Requirements:**
- A patient must be selected to proceed
- Patient must exist in the system

**Navigation:** Click patient card to select, then "Next" to proceed.

---

### Step 2: Report Type & Template

**Purpose:** Choose the type of report and template to use.

**Features:**
- **Report Types:** Discharge, Progress, Insurance, Assessment, Outcome Summary
- **Template Selection:** Choose from available templates for the selected type
- **Auto-Generated Title:** Automatically creates title based on patient name, report type, and date
- **Template Preview:** View template details and structure

**Requirements:**
- Report type must be selected
- Template must be chosen
- Title must be provided (can be customized)

**Navigation:** All fields required before proceeding to "Next".

---

### Step 3: Disciplines

**Purpose:** Select the disciplines involved in the patient's care.

**Features:**
- **Booking-Based Recommendations:** Disciplines automatically suggested based on patient's booking history
- **Recommendation Details:** Shows number of bookings and last seen date for each discipline
- **Manual Selection:** Check/uncheck disciplines as needed
- **Multi-Disciplinary Support:** Select multiple disciplines for comprehensive reports

**Available Disciplines:**
- Physiotherapy
- Occupational Therapy  
- Speech Therapy
- Psychology

**Requirements:**
- At least one discipline must be selected

**Navigation:** Select disciplines and click "Next".

---

### Step 4: Therapist Assignment

**Purpose:** Assign therapists to work on the report.

**Features:**
- **Suggested Therapists:** Based on patient booking history within selected disciplines
- **Therapist Details:** Shows therapist name, disciplines, and history with patient
- **Other Available Therapists:** All other therapists in selected disciplines
- **Multiple Assignment:** Select multiple therapists for collaborative reports
- **Auto-Assignment:** For therapist workflow, current user is automatically included

**Therapist Information Displayed:**
- Name and primary discipline
- Number of sessions with this patient
- Last session date
- "Suggested" badge for therapists with patient history

**Requirements:**
- At least one therapist must be assigned

**Navigation:** Select therapists and click "Next".

---

### Step 5: Priority & Timeline

**Purpose:** Set report priority and deadline.

**Features:**
- **Priority Levels:**
  - **Low (1):** Standard processing
  - **Medium (2):** Normal priority (default)
  - **High (3):** Urgent processing
- **Deadline Setting:** Optional deadline date (must be in the future)
- **Quick Deadline Options:** 1 week, 2 weeks, 1 month shortcuts
- **Final Review:** Summary of all selections

**Requirements:**
- Priority is automatically set to Medium (can be changed)
- Deadline is optional but must be a future date if provided

**Navigation:** Review settings and click "Create Report" to complete.

---

## Summary Panel

Throughout the wizard, a **real-time summary panel** on the right displays:

- **Patient:** Selected patient name
- **Report Type:** Chosen report type and title
- **Disciplines:** Selected disciplines
- **Therapists:** Assigned therapists
- **Priority:** Current priority setting
- **Deadline:** Set deadline or "No deadline"

## Workflow Types

### Therapist Workflow
- **Purpose:** Individual therapists creating reports for their patients
- **Auto-Assignment:** Therapist is automatically assigned to the report
- **Permissions:** Can assign additional therapists if needed

### Manager Workflow  
- **Purpose:** Managers assigning report creation to specific therapists
- **Full Assignment:** Must manually select all therapists
- **Oversight:** Manager receives notifications when report is completed

## AI Content Generation

**Automatic Generation:**
- Medical history based on patient booking history
- Treatment summaries from selected disciplines
- Generated content is highlighted in the final report
- Content can be edited and refined after creation

**Data Sources:**
- Treatment notes from selected disciplines
- Outcome measure scores
- Booking patterns and frequency
- Previous assessment data

## Keyboard Shortcuts

- **Escape:** Close wizard
- **Enter:** Proceed to next step (when valid)
- **Tab:** Navigate between form fields

## Error Handling

**Common Validation Errors:**
- No patient selected
- Missing report type or template
- No disciplines selected
- No therapists assigned
- Invalid deadline (past date)

**Network Errors:**
- Automatic retry for failed API calls
- Clear error messages with recovery options
- Form state preserved during errors

## Legacy Compatibility

**Backward Compatibility:**
- Old `openReportRequestModal()` calls are automatically redirected to the new wizard
- Existing bookmarks and integrations continue to work
- Gradual migration from legacy single-step modal

## Best Practices

1. **Patient Selection:** Use the search feature for faster patient lookup
2. **Disciplines:** Trust the booking-based recommendations for accuracy
3. **Therapists:** Select therapists with patient history for continuity of care
4. **Deadlines:** Set realistic deadlines accounting for therapist workloads
5. **Review:** Always review the summary before creating the report

## Troubleshooting

**No therapists showing in Step 4:**
- Ensure disciplines are selected in Step 3
- Check that therapists exist for the selected disciplines
- Verify patient has booking history with available therapists

**Template not loading:**
- Check network connection
- Ensure selected report type supports templates
- Try refreshing the page

**Wizard won't proceed:**
- Check for validation errors (highlighted in red)
- Ensure all required fields are completed
- Verify dates are in correct format

## Technical Notes

**Browser Support:**
- Chrome 80+, Firefox 78+, Safari 13+
- Requires JavaScript enabled
- LocalStorage used for form state

**Data Validation:**
- Client-side validation for immediate feedback  
- Server-side validation for security
- POPIA-compliant data handling

**Performance:**
- Progressive loading of data
- Efficient caching of patient and therapist data
- Optimized for mobile and tablet use

---

*For technical support or feature requests, contact the development team.*