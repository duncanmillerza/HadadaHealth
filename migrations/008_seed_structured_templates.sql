-- Migration 008: Seed structured report templates
-- Inserts the Discharge Summary and Outpatient Planning Record templates

-- Insert Discharge Summary Template
INSERT OR REPLACE INTO structured_templates (
    id,
    name,
    display_name,
    description,
    category,
    template_structure,
    auto_populate_mapping,
    is_active,
    version
) VALUES (
    1,
    'discharge_summary',
    'Discharge Summary',
    'Comprehensive discharge report for inpatient rehabilitation episodes',
    'clinical',
    '{
        "sections": [
            {
                "id": "administrative",
                "title": "Patient Demographics & Administrative Data",
                "type": "form_section",
                "deletable": false,
                "fields": [
                    {"id": "report_date", "label": "Report Date", "type": "date", "required": true, "auto_populate": "current_date"},
                    {"id": "patient_name", "label": "Patient Name", "type": "text", "required": true, "auto_populate": "patient.full_name", "readonly": true},
                    {"id": "funder_name", "label": "Funder Name", "type": "text", "auto_populate": "patient.medical_aid_name"},
                    {"id": "membership_number", "label": "Membership Number", "type": "text", "auto_populate": "patient.medical_aid_number"},
                    {"id": "authorization_number", "label": "Authorization Number", "type": "text"},
                    {"id": "diagnosis", "label": "Diagnosis", "type": "text", "auto_populate": "patient.primary_diagnosis"},
                    {"id": "icd_10_codes", "label": "ICD 10 Code(s)", "type": "text", "auto_populate": "patient.icd_codes"},
                    {"id": "date_of_admission", "label": "Date of Admission", "type": "date"},
                    {"id": "date_of_incident", "label": "Date of Incident", "type": "date"},
                    {"id": "discharge_date", "label": "Discharge Date", "type": "date", "required": true},
                    {"id": "attending_physician", "label": "Attending Physician", "type": "text"}
                ]
            },
            {
                "id": "practice_info",
                "title": "Practice Information",
                "type": "form_section",
                "deletable": true,
                "fields": [
                    {"id": "therapy_practice", "label": "Therapy Practice", "type": "text", "auto_populate": "practice.name"}
                ]
            },
            {
                "id": "background_history",
                "title": "BACKGROUND HISTORY",
                "type": "ai_generated_section",
                "deletable": true,
                "fields": [
                    {"id": "background_content", "type": "rich_textarea", "ai_prompt": "Generate comprehensive background history from patient clinical notes, medical history, and social context"}
                ]
            },
            {
                "id": "medical_status",
                "title": "MEDICAL STATUS",
                "type": "ai_generated_section",
                "deletable": true,
                "fields": [
                    {"id": "medical_status_content", "type": "rich_textarea", "ai_prompt": "Summarize current medical condition, medications, and medical management from clinical assessments"}
                ]
            },
            {
                "id": "functional_status",
                "title": "Functional Status",
                "type": "form_section",
                "deletable": true,
                "fields": [
                    {"id": "skin_status", "label": "Skin", "type": "textarea", "source": "clinician"},
                    {"id": "bladder_bowel", "label": "Bladder and Bowel", "type": "textarea", "source": "clinician"},
                    {"id": "discharge_medication", "label": "Discharge Medication", "type": "textarea", "source": "clinician"},
                    {"id": "medical_follow_up", "label": "Medical Follow Up", "type": "textarea", "source": "clinician"}
                ]
            },
            {
                "id": "rehabilitation_outcomes",
                "title": "Rehabilitation Outcomes Matrix",
                "type": "outcomes_table",
                "deletable": true,
                "fields": [
                    {"id": "environmental_factors", "label": "Environmental & Contextual Factors", "type": "textarea", "ai_generated": true},
                    {"id": "assistive_devices", "label": "Assistive Devices, Technology & Home Adaptations", "type": "textarea", "ai_generated": true},
                    {"id": "education_training", "label": "Education & Training Completed", "type": "textarea", "ai_generated": true},
                    {"id": "psychosocial_summary", "label": "Psychosocial Summary & Recommendations", "type": "textarea", "ai_generated": true}
                ]
            },
            {
                "id": "goals_achievement",
                "title": "Goals Achievement Summary",
                "type": "goals_section",
                "deletable": true,
                "fields": [
                    {"id": "cognition_goals", "label": "Cognition/Perception/Vision Goals", "type": "textarea"},
                    {"id": "communication_goals", "label": "Communication Goals", "type": "textarea"},
                    {"id": "self_care_goals", "label": "Self-Care Goals", "type": "textarea"},
                    {"id": "mobility_goals", "label": "Mobility Goals", "type": "textarea"},
                    {"id": "leisure_goals", "label": "Leisure Goals", "type": "textarea"},
                    {"id": "psychological_goals", "label": "Psychological Well-being Goals", "type": "textarea"},
                    {"id": "education_goals", "label": "Patient and Caregiver Education", "type": "textarea"}
                ]
            },
            {
                "id": "functional_assessment",
                "title": "Functional Assessment Tables",
                "type": "assessment_tables",
                "deletable": true,
                "tables": [
                    {
                        "id": "rom_strength",
                        "title": "ROM/Strength Assessment",
                        "columns": ["Aspect", "Admission", "Discharge"],
                        "rows": [
                            {"aspect": "Upper extremity", "admission": "", "discharge": ""},
                            {"aspect": "Wrist", "admission": "", "discharge": ""},
                            {"aspect": "Hand", "admission": "", "discharge": ""},
                            {"aspect": "Coordination/Speed", "admission": "", "discharge": ""},
                            {"aspect": "Sensation", "admission": "", "discharge": ""},
                            {"aspect": "Passive joint motion", "admission": "", "discharge": ""},
                            {"aspect": "Joint pain", "admission": "", "discharge": ""}
                        ]
                    },
                    {
                        "id": "cognitive_assessment",
                        "title": "Cognitive/Communication Assessment",
                        "fields": [
                            {"id": "cognition", "label": "Cognition", "type": "textarea"},
                            {"id": "self_care", "label": "Self-care", "type": "textarea"},
                            {"id": "communication", "label": "Communication", "type": "textarea"},
                            {"id": "swallowing", "label": "Swallowing", "type": "textarea"}
                        ]
                    }
                ]
            },
            {
                "id": "treating_clinicians",
                "title": "Professional Information",
                "type": "form_section",
                "deletable": true,
                "fields": [
                    {"id": "rehab_manager", "label": "Rehab Programme Manager", "type": "text"},
                    {"id": "physiotherapist", "label": "Physiotherapist", "type": "text"},
                    {"id": "occupational_therapist", "label": "Occupational Therapist", "type": "text"},
                    {"id": "speech_therapist", "label": "Speech Therapist", "type": "text"},
                    {"id": "social_worker", "label": "Social Worker", "type": "text"},
                    {"id": "psychologist", "label": "Psychologist", "type": "text"},
                    {"id": "dietician", "label": "Dietician", "type": "text"}
                ]
            },
            {
                "id": "follow_up",
                "title": "Referrals and Follow-up",
                "type": "form_section",
                "deletable": true,
                "fields": [
                    {"id": "therapeutic_followup", "label": "Therapeutic Follow-up Recommendations", "type": "rich_textarea"},
                    {"id": "outpatient_physiotherapy", "label": "Outpatient Physiotherapy Practice", "type": "text"},
                    {"id": "outpatient_ot", "label": "Outpatient Occupational Therapy Practice", "type": "text"},
                    {"id": "outpatient_speech", "label": "Outpatient Speech Therapy Practice", "type": "text"}
                ]
            }
        ]
    }',
    '{
        "patient.full_name": "first_name || '' '' || surname",
        "patient.medical_aid_name": "medical_aid_name", 
        "patient.medical_aid_number": "medical_aid_number",
        "patient.plan_name": "plan_name",
        "patient.claim_number": "claim_number", 
        "patient.case_manager": "case_manager",
        "patient.primary_diagnosis": "icd10_codes",
        "patient.icd_codes": "icd10_codes",
        "patient.date_of_birth": "date_of_birth",
        "patient.gender": "gender",
        "patient.clinic": "clinic",
        "patient.medical_history_ai": "medical_history_ai",
        "current_date": "date(''now'')"
    }',
    1,
    1
);

-- Insert Outpatient Planning Record Template  
INSERT OR REPLACE INTO structured_templates (
    id,
    name,
    display_name,
    description,
    category,
    template_structure,
    auto_populate_mapping,
    is_active,
    version
) VALUES (
    2,
    'outpatient_planning_record',
    'Outpatient Planning Record (OPR)',
    'Comprehensive outpatient planning and treatment tracking report',
    'clinical',
    '{
        "sections": [
            {
                "id": "administrative",
                "title": "Patient Demographics & Administrative Data",
                "type": "form_section",
                "deletable": false,
                "fields": [
                    {"id": "report_date", "label": "Report Date", "type": "date", "required": true, "auto_populate": "current_date"},
                    {"id": "patient_name", "label": "Patient Name", "type": "text", "required": true, "auto_populate": "patient.full_name", "readonly": true},
                    {"id": "patient_contact", "label": "Patient/Contact Number", "type": "tel", "auto_populate": "patient.phone_number"},
                    {"id": "patient_file_number", "label": "Patient File Number", "type": "text", "auto_populate": "patient.id"},
                    {"id": "funder_name", "label": "Funder Name", "type": "text", "auto_populate": "patient.medical_aid_name"},
                    {"id": "membership_number", "label": "Membership Number", "type": "text", "auto_populate": "patient.medical_aid_number"},
                    {"id": "outpatient_auth_number", "label": "Outpatient Authorization Number", "type": "text"},
                    {"id": "diagnosis", "label": "Diagnosis", "type": "text", "auto_populate": "patient.primary_diagnosis"},
                    {"id": "icd_10_codes", "label": "ICD 10 Code(s)", "type": "text", "auto_populate": "patient.icd_codes"},
                    {"id": "date_of_onset", "label": "Date of Onset/Incident", "type": "date"},
                    {"id": "date_of_assessment", "label": "Date of Assessment", "type": "date"},
                    {"id": "place_of_assessment", "label": "Place of Assessment", "type": "text"},
                    {"id": "treating_doctor", "label": "Treating/Referring Doctor", "type": "text"},
                    {"id": "pre_incident_function", "label": "Pre-incident Level of Functioning", "type": "textarea"},
                    {"id": "current_function", "label": "Current Level of Function", "type": "textarea"},
                    {"id": "predicted_function", "label": "Predicted Level of Functioning at Discharge", "type": "textarea"},
                    {"id": "practice_numbers", "label": "Practice Numbers", "type": "text"}
                ]
            },
            {
                "id": "fim_scores",
                "title": "FIM Score Assessment",
                "type": "assessment_table",
                "deletable": true,
                "table": {
                    "id": "fim_table",
                    "columns": [
                        "Date", "Eating", "Grooming", "Bathing", "Dressing - Upper", "Dressing – Lower",
                        "Toileting", "Bladder", "Bowel", "TRF Bed/Chair/WC", "TRF Toilet", "TRF Bath/Shower",
                        "Walk / WC", "Stairs", "Motor Total /91", "Comprehension", "Expression",
                        "Social interaction", "Problem Solving", "Memory", "Cognitive Total /35", "Total /126"
                    ],
                    "rows": 3,
                    "editable": true
                }
            },
            {
                "id": "fam_scores",
                "title": "FAM Scale Assessment", 
                "type": "assessment_table",
                "deletable": true,
                "table": {
                    "id": "fam_table",
                    "columns": [
                        "Date", "Swallowing", "Car Transfer", "Community Mobility", "Motor Total /21",
                        "Reading", "Writing", "Speech Intelligibility", "Emotional Status",
                        "Adjustment to Limitations", "Leisure Activities", "Orientation", "Concentration",
                        "Safety Awareness", "Cognitive/Psychosocial /63", "Total /84"
                    ],
                    "rows": 3,
                    "editable": true
                }
            },
            {
                "id": "medical_history",
                "title": "Relevant Medical History",
                "type": "ai_generated_section",
                "deletable": true,
                "fields": [
                    {"id": "medical_history_content", "type": "rich_textarea", "ai_prompt": "Generate comprehensive medical history summary from patient clinical records"}
                ]
            },
            {
                "id": "environmental_context",
                "title": "Environmental & Personal Context",
                "type": "ai_generated_section",
                "deletable": true,
                "fields": [
                    {"id": "environmental_content", "type": "rich_textarea", "ai_prompt": "Summarize equipment, home adaptations, family education, barriers and resources from assessments"}
                ]
            },
            {
                "id": "clinical_presentation",
                "title": "Clinical Presentation Summary",
                "type": "form_section",
                "deletable": true,
                "subsections": [
                    {
                        "title": "Physiotherapy",
                        "fields": [
                            {"id": "pt_clinical_summary", "type": "textarea", "ai_generated": true}
                        ]
                    },
                    {
                        "title": "Occupational Therapy",
                        "fields": [
                            {"id": "ot_clinical_summary", "type": "textarea", "ai_generated": true}
                        ]
                    },
                    {
                        "title": "Speech Therapy",
                        "fields": [
                            {"id": "st_clinical_summary", "type": "textarea", "ai_generated": true}
                        ]
                    }
                ]
            },
            {
                "id": "treatment_planning",
                "title": "Monthly Treatment Plan & Goals",
                "type": "treatment_grid",
                "deletable": true,
                "grid": {
                    "columns": [
                        "Date", "Health Condition Management", "Training & Care Management",
                        "Therapy Functional Goals", "24 Hour Programme", "Reintegration",
                        "Psychosocial Wellbeing", "Treating Therapists"
                    ],
                    "sections": [
                        {"title": "Current Month", "rows": 2},
                        {"title": "Treatment Record", "rows": 2}
                    ]
                }
            },
            {
                "id": "goal_setting",
                "title": "Goal Setting Discussion",
                "type": "form_section",
                "deletable": true,
                "fields": [
                    {"id": "goal_setting_date", "label": "Date of Outpatient Planning/Goal Setting Discussion", "type": "date"},
                    {"id": "session_goals", "label": "Goals for Requested Number of Sessions", "type": "textarea", "help": "Must be adjusted according to authorised sessions and patient/family goals"},
                    {"id": "treating_therapists", "label": "Treating Therapists", "type": "textarea", "placeholder": "PT:\\nOT:\\nST:"}
                ]
            }
        ]
    }',
    '{
        "patient.full_name": "first_name || '' '' || surname",
        "patient.phone_number": "contact_number",
        "patient.id": "id",
        "patient.medical_aid_name": "medical_aid_name", 
        "patient.medical_aid_number": "medical_aid_number",
        "patient.plan_name": "plan_name",
        "patient.claim_number": "claim_number",
        "patient.case_manager": "case_manager", 
        "patient.primary_diagnosis": "icd10_codes",
        "patient.icd_codes": "icd10_codes",
        "patient.date_of_birth": "date_of_birth",
        "patient.gender": "gender",
        "patient.clinic": "clinic",
        "current_date": "date(''now'')"
    }',
    1,
    1
);