# Report Writing Feature Specification

## Overview
The proposed feature enables managers to request specific patient reports, which therapists can complete and return within the system. It aims to streamline communication, ensure consistent documentation, and reduce administrative burden.

---

## Workflow

### 1. Report Request by Manager
- Manager selects **report type** (e.g., Discharge, Progress, Insurance, Outcome Summary).
- Request automatically appears on therapist’s dashboard.

### 2. Therapist Dashboard
- Displays pending report requests.
- Therapists can open a request to auto-populate with:
  - Patient information
  - Medical history
  - Assessment details
  - Outcome measures
- Therapist can edit or complete missing details.

### 3. Templates
- System provides default templates for common report types.
- Templates are **customisable** by practice.
- Templates include structured sections (demographics, assessment, intervention, outcomes, recommendations).

### 4. Report Completion & Submission
- Therapists finalise report in editable form.
- Completed report can be sent back to manager with one click.
- Option to **export as PDF** for external sharing.

---

## Key Features
- **Notifications**: Therapist receives notification when new report is requested.
- **Auto-Population**: Patient data pulled from existing profile (reducing duplication).
- **Custom Templates**: Practices can build or modify report templates.
- **Multi-template Support**: Different templates for discharge, progress, insurance, etc.
- **Editable Drafts**: Save progress before submission.
- **Submission Tracking**: Manager can see when report is completed and returned.

---

## Future Enhancements
- AI-assisted drafting of sections (history, progress, recommendations).
- Multi-user collaboration (e.g., OT + Physio joint reports).
- Version control for report edits.
- Integration with billing/claims where relevant.

---

## Example Template Structure

**Progress Report Template**  
- Patient Name / ID  
- Date of Report  
- Medical History (auto-populated, editable)  
- Assessment Findings  
- Outcome Measures (with scores + interpretation)  
- Interventions Completed  
- Progress Summary  
- Recommendations & Plan  
- Therapist Name & Signature  

---

## Benefits
- Saves therapist time with automation.
- Ensures consistency across reports.
- Supports multi-disciplinary collaboration.
- Improves communication between managers and therapists.
- Enhances compliance with reporting requirements (funders, insurers, hospital policies).


---

## Additional Specifications

### 1. Report Prioritization
- Prioritize the creation of **multidisciplinary assessment reports** to ensure holistic patient care and comprehensive documentation.

### 2. AI Integration Level
- **Generate medical history** directly from treatment notes using AI.  
- Provide an **AI-generated summary** of treatment to date, consolidating information from treatment notes.

### 3. Data Sources for AI
AI should pull structured data from:  
- Treatment notes  
- Session records  
- Outcome measures  
- Assessments  
- Patient diagnostic codes (ICD-10)  

### 4. Compliance
- All AI-generated content must include **POPIA-compliant audit trails**.  
- Implement **therapist approval workflows** before any AI-generated report is finalised.  

### 5. Report Customization
- Users should be able to choose:  
  - Whether the report includes input from **multiple disciplines** (e.g., physiotherapy, occupational therapy, and speech therapy).  
  - Or restrict the report to a **single discipline** only.  
