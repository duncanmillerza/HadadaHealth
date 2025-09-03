# Discharge Summary Template Specification

## Patient Demographics & Administrative Data
*These fields should be imported directly from the patient record system*

- **Report Date** - `IMPORTED` - Auto-populated with current date
- **Patient Name** - `IMPORTED` - From patient record
- **Funder Name** - `IMPORTED` - From insurance/medical aid record
- **Membership Number** - `IMPORTED` - From insurance record
- **Authorization Number** - `IMPORTED` - From pre-authorization system (Still to be implemented)
- **Diagnosis** - `IMPORTED` - From patient record
- **ICD 10 Code(s)** - `IMPORTED` - From patient record
- **Date of Admission** - `IMPORTED` - From admission record
- **Date of Incident** - `IMPORTED` - From clinical record
- **Discharge Date** - `Clinician added` - Date Selector
- **Attending Physician** - `Clinician added` - Text 

## Practice Information
*These fields should be imported from practice management system*

- **Therapy Practice** - `IMPORTED` - From practice registry if treatment record available for that practice

## Clinical Content Sections

### Background History
- **Content** - `AI-GENERATED` - Synthesized from clinical notes, admission records, and patient history
- **Purpose**: This section will automatically compile relevant medical history, social history, and contextual factors from existing documentation

### Medical Status
- **Content** - `AI-GENERATED` - Generated from current medical assessments and clinical notes
- **Purpose**: Summarizes current medical condition, medications, and medical management

### Functional Status Sections
- **Skin** - `Clinician added` - From nursing assessments and wound care notes
- **Bladder and Bowel** - `Clinician added` - From nursing assessments and continence evaluations
- **Discharge Medication** - `Clinician added` - Base list imported, summary generated
- **Medical Follow Up** - `Clinician added` - From discharge planning notes and physician recommendations

## Rehabilitation Outcomes Matrix

### Summary Sections (All AI-GENERATED from therapy notes if available. If not leave blank and to be Clinician added)
- **Environmental & Contextual Factors** - Compiled from OT assessments and discharge planning
- **Assistive Devices, Technology & Home Adaptations** - From equipment recommendations and home evaluations
- **Education & Training Completed** - From therapy session notes and patient education records
- **Psychosocial Summary & Recommendations** - From social work and psychology assessments

## Goals Achievement Summary
Clinician added

- **Cognition/Perception/Vision Goals** 
- **Communication Goals** 
- **Self-Care Goals** 
- **Mobility Goals** 
- **Leisure Goals** 
- **Psychological Well-being Goals** 
- **Patient and Caregiver Education** 

## Functional Assessment Tables
*These should be populated from standardized assessment tools*

### ROM/Strength Assessment
- **Mobility Status** - `IMPORTED` - From standardized mobility assessments
- **Strength Measurements** - `IMPORTED` - From physiotherapy strength testing
- **Upper Extremity Function** - `IMPORTED` - From occupational therapy assessments
- **Coordination/Speed** - `IMPORTED` - From standardized testing
- **Sensation** - `IMPORTED` - From sensory assessments
- **Passive Joint Motion** - `IMPORTED` - From range of motion measurements
- **Joint Pain Scores** - `IMPORTED` - From pain assessment tools

### Cognitive/Communication Assessment
- **Cognition** - `IMPORTED` - From cognitive assessment batteries
- **Self-Care** - `IMPORTED` - From functional independence measures
- **Communication** - `IMPORTED` - From speech-language assessments
- **Swallowing** - `IMPORTED` - From swallowing evaluations

## Professional Information
*IMPORTED from staff directory and assignment records*

- **Treating Clinicians** - All professional details and registration numbers


## Referrals and Follow-up
Clinician added

- **Therapeutic Follow-up Recommendations** - Synthesized from all disciplines' recommendations
- **Outpatient Practice Details** - Contact information and appointment scheduling

---

## Implementation Notes

**Why these automation levels were chosen:**

1. **IMPORTED fields** are objective data points that already exist in your system - importing them eliminates manual data entry errors and ensures consistency.

2. **AI-GENERATED content** leverages your clinical documentation to create comprehensive summaries that would otherwise require significant manual writing time. This addresses your goal of 60% reduction in documentation time.

3. **Standardized assessments** remain IMPORTED because they require clinical judgment and validated measurement tools.

4. **Clinician added** for complex items or those that require clinical reasoning. 

The AI generation will be most effective for synthesis tasks - taking existing clinical notes, assessments, and documentation to create coherent summaries and recommendations. This maintains clinical accuracy while dramatically reducing the administrative burden on healthcare professionals.