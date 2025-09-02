# Auto-Population Data Sources Mapping

Please fill in the **Data Source Location** column with where to find each piece of information in your system.

## Template Field Mapping Table

| Field Name | Template Field ID | Type | Status | Current Source | **Data Source Location** (Please fill in) |
|---|---|---|---|---|---|
| **Report Date** | `report_date` | date | IMPORTED | System date | ✅ System date |
| **Patient Name** | `patient_name` | text | IMPORTED | patients.first_name + surname | ✅ patients table |
| **Funder Name** | `funder_name` | text | IMPORTED | patients.medical_aid_name | ✅ patients table |
| **Membership Number** | `membership_number` | text | IMPORTED | patients.medical_aid_number | ✅ patients table |
| **Authorization Number** | `authorization_number` | text | IMPORTED | Not implemented | |
| **Diagnosis** | `diagnosis` | text | IMPORTED | patients.icd10_codes | ✅ patients table |
| **ICD 10 Code(s)** | `icd_10_codes` | text | IMPORTED | patients.icd10_codes | ✅ patients table |
| **Date of Admission** | `date_of_admission` | date | IMPORTED | MIN(bookings.date) | ✅ bookings table |
| **Date of Incident** | `date_of_incident` | date | IMPORTED | Same as admission | |
| **Therapy Practice** | `therapy_practice` | text | IMPORTED | patients.clinic | ✅ patients table |
| **Patient Contact** | `patient_contact` | tel | IMPORTED | patients.contact_number | ✅ patients table |
| **Patient File Number** | `patient_file_number` | text | IMPORTED | patients.id | ✅ patients table |
| **Plan Name** | `plan_name` | text | IMPORTED | patients.plan_name | ✅ patients table |
| **Case Manager** | `case_manager` | text | IMPORTED | patients.case_manager | ✅ patients table |
| **Claim Number** | `claim_number` | text | IMPORTED | patients.claim_number | ✅ patients table |

## Professional Information Fields

| Professional Role | Template Field ID | Status | Current Source | **Data Source Location** (Please fill in) |
|---|---|---|---|---|
| **Rehabilitation Programme Manager** | `rehab_manager` | IMPORTED | Not implemented | |
| **Physiotherapist** | `physiotherapist` | IMPORTED | therapists table via bookings | ✅ therapists + bookings |
| **Occupational Therapist** | `occupational_therapist` | IMPORTED | therapists table via bookings | ✅ therapists + bookings |
| **Speech Therapist** | `speech_therapist` | IMPORTED | therapists table via bookings | ✅ therapists + bookings |
| **Social Worker** | `social_worker` | IMPORTED | Not implemented | |
| **Psychologist** | `psychologist` | IMPORTED | therapists table via bookings | ✅ therapists + bookings |
| **Dietician** | `dietician` | IMPORTED | Not implemented | |

## Assessment Data Fields

| Assessment Area | Template Field ID | Status | Current Source | **Data Source Location** (Please fill in) |
|---|---|---|---|---|
| **Mobility Status** | `mobility_status` | IMPORTED | Not implemented | |
| **Strength Measurements** | `strength_measurements` | IMPORTED | Not implemented | |
| **Upper Extremity Function** | `upper_extremity` | IMPORTED | Not implemented | |
| **Coordination/Speed** | `coordination_speed` | IMPORTED | Not implemented | |
| **Sensation** | `sensation` | IMPORTED | Not implemented | |
| **Passive Joint Motion** | `passive_joint_motion` | IMPORTED | Not implemented | |
| **Joint Pain Scores** | `joint_pain` | IMPORTED | Not implemented | |
| **Cognition** | `cognition` | IMPORTED | Not implemented | |
| **Self-Care** | `self_care` | IMPORTED | Not implemented | |
| **Communication** | `communication` | IMPORTED | Not implemented | |
| **Swallowing** | `swallowing` | IMPORTED | Not implemented | |

## AI-Generated Content Fields

| Content Section | Template Field ID | Status | Current Source | **Data Source Location** (Please fill in) |
|---|---|---|---|---|
| **Background History** | `background_content` | AI-GENERATED | treatment_notes + patients.medical_history_ai | ✅ treatment_notes table |
| **Medical Status** | `medical_status_content` | AI-GENERATED | Recent treatment_notes | ✅ treatment_notes table |
| **Medical History** | `medical_history_content` | AI-GENERATED | patients.medical_history_ai | ✅ patients table |
| **Environmental Context** | `environmental_content` | AI-GENERATED | treatment_notes (OT assessments) | |
| **Environmental Factors** | `environmental_factors` | AI-GENERATED | treatment_notes (OT discharge planning) | |
| **Assistive Devices** | `assistive_devices` | AI-GENERATED | treatment_notes (equipment recommendations) | |
| **Education & Training** | `education_training` | AI-GENERATED | treatment_notes (patient education records) | |
| **Psychosocial Summary** | `psychosocial_summary` | AI-GENERATED | treatment_notes (psychology/social work) | |

## Outpatient Planning Record (OPR) Additional Fields

| Field Name | Template Field ID | Status | Current Source | **Data Source Location** (Please fill in) |
|---|---|---|---|---|
| **Date of Onset/Incident** | `date_of_onset` | IMPORTED | Same as admission date | |
| **Date of Assessment** | `date_of_assessment` | IMPORTED | Not implemented | |
| **Place of Assessment** | `place_of_assessment` | IMPORTED | patients.clinic | ✅ patients table |
| **Treating/Referring Doctor** | `treating_doctor` | IMPORTED | Not implemented | |
| **Pre-incident Function** | `pre_incident_function` | IMPORTED | Not implemented | |
| **Current Function** | `current_function` | IMPORTED | Not implemented | |
| **Predicted Function** | `predicted_function` | IMPORTED | Not implemented | |
| **Practice Numbers** | `practice_numbers` | IMPORTED | Not implemented | |

## FIM/FAM Assessment Tables

| Assessment Type | Template Field ID | Status | Current Source | **Data Source Location** (Please fill in) |
|---|---|---|---|---|
| **FIM Score Table** | `fim_table` | IMPORTED | Not implemented | |
| **FAM Scale Table** | `fam_table` | IMPORTED | Not implemented | |

## Instructions for Implementation

1. **Review each field** and specify where the data can be found in your system
2. **Database tables**: Specify table name and column name
3. **Calculated fields**: Describe the calculation logic
4. **External systems**: Note if data comes from external APIs or systems
5. **Missing data**: Mark fields where data doesn't exist yet

## Priority Levels

**High Priority (Immediate Impact)**:
- Authorization Number
- Date of Incident (if different from admission)
- Assessment data (FIM/FAM scores)
- Professional staff assignments

**Medium Priority (Enhanced Features)**:
- Specialized assessment measurements
- External system integrations
- Advanced clinical calculations

**Low Priority (Future Enhancements)**:
- Complex calculated fields
- External API integrations
- Advanced reporting metrics

---

*Once you've filled in the data source locations, we can implement the enhanced auto-population for all these fields.*