-- Migration: Seed default report templates
-- Purpose: Create system default templates for common report types
-- Dependencies: 005_create_report_writing_system.sql
-- Date: 2025-08-28

-- Insert default Progress Report template
INSERT OR IGNORE INTO report_templates (
    name,
    description,
    template_type,
    practice_id,
    is_active,
    is_system_default,
    fields_schema,
    section_order,
    created_by_user_id
) VALUES (
    'Standard Progress Report',
    'Default template for patient progress reporting with AI-assisted content generation',
    'progress',
    NULL, -- System template (not practice-specific)
    1, -- Active
    1, -- System default
    json('{
        "patient_demographics": {
            "type": "auto_populated",
            "label": "Patient Information",
            "required": true,
            "description": "Auto-populated patient demographic information",
            "fields": ["name", "date_of_birth", "patient_id", "diagnosis"]
        },
        "medical_history": {
            "type": "ai_generated_paragraph",
            "label": "Medical History",
            "required": true,
            "editable": true,
            "ai_source": "treatment_notes",
            "description": "AI-generated summary of patient medical history",
            "placeholder": "Medical history will be automatically generated from treatment notes..."
        },
        "assessment_findings": {
            "type": "rich_text",
            "label": "Assessment Findings",
            "required": true,
            "description": "Current assessment findings and observations",
            "placeholder": "Document current assessment findings..."
        },
        "outcome_measures": {
            "type": "structured_table",
            "label": "Outcome Measures",
            "required": true,
            "description": "Standardized outcome measure scores and interpretation",
            "columns": ["measure_name", "score", "date", "interpretation"]
        },
        "interventions_completed": {
            "type": "rich_text",
            "label": "Interventions Completed",
            "required": true,
            "description": "Summary of interventions and treatments provided",
            "placeholder": "Describe interventions and treatments completed..."
        },
        "progress_summary": {
            "type": "ai_generated_paragraph",
            "label": "Progress Summary",
            "required": true,
            "editable": true,
            "ai_source": "treatment_progress",
            "description": "AI-generated summary of patient progress",
            "placeholder": "Progress summary will be automatically generated..."
        },
        "recommendations": {
            "type": "rich_text",
            "label": "Recommendations & Future Plan",
            "required": true,
            "description": "Treatment recommendations and future care plan",
            "placeholder": "Document recommendations and future treatment plan..."
        },
        "therapist_signature": {
            "type": "digital_signature",
            "label": "Therapist Signature",
            "required": true,
            "description": "Digital signature and credentials of treating therapist"
        }
    }'),
    json('[
        "patient_demographics",
        "medical_history", 
        "assessment_findings",
        "outcome_measures",
        "interventions_completed",
        "progress_summary",
        "recommendations",
        "therapist_signature"
    ]'),
    'system'
);

-- Insert default Discharge Report template
INSERT OR IGNORE INTO report_templates (
    name,
    description,
    template_type,
    practice_id,
    is_active,
    is_system_default,
    fields_schema,
    section_order,
    created_by_user_id
) VALUES (
    'Standard Discharge Report',
    'Default template for patient discharge summaries',
    'discharge',
    NULL, -- System template
    1, -- Active
    1, -- System default
    json('{
        "patient_demographics": {
            "type": "auto_populated",
            "label": "Patient Information",
            "required": true,
            "description": "Patient demographic and contact information"
        },
        "admission_details": {
            "type": "structured_fields",
            "label": "Admission Details",
            "required": true,
            "description": "Details of admission and initial assessment",
            "fields": {
                "admission_date": {"type": "date", "label": "Admission Date"},
                "discharge_date": {"type": "date", "label": "Discharge Date"},
                "length_of_stay": {"type": "calculated", "label": "Length of Stay"},
                "primary_diagnosis": {"type": "text", "label": "Primary Diagnosis"},
                "secondary_diagnoses": {"type": "textarea", "label": "Secondary Diagnoses"}
            }
        },
        "treatment_summary": {
            "type": "ai_generated_paragraph",
            "label": "Treatment Summary",
            "required": true,
            "editable": true,
            "ai_source": "complete_treatment_history",
            "description": "AI-generated comprehensive treatment summary"
        },
        "functional_outcomes": {
            "type": "structured_table",
            "label": "Functional Outcomes",
            "required": true,
            "description": "Comparison of admission vs discharge functional status",
            "columns": ["domain", "admission_status", "discharge_status", "improvement"]
        },
        "goals_achieved": {
            "type": "checklist",
            "label": "Treatment Goals Achieved",
            "required": true,
            "description": "List of treatment goals and achievement status"
        },
        "discharge_recommendations": {
            "type": "rich_text",
            "label": "Discharge Recommendations",
            "required": true,
            "description": "Post-discharge care recommendations and follow-up plan"
        },
        "equipment_prescribed": {
            "type": "structured_list",
            "label": "Equipment/Aids Prescribed",
            "required": false,
            "description": "List of prescribed equipment or mobility aids"
        },
        "therapist_signature": {
            "type": "digital_signature",
            "label": "Therapist Signature",
            "required": true,
            "description": "Digital signature of discharging therapist"
        }
    }'),
    json('[
        "patient_demographics",
        "admission_details",
        "treatment_summary",
        "functional_outcomes",
        "goals_achieved",
        "discharge_recommendations",
        "equipment_prescribed",
        "therapist_signature"
    ]'),
    'system'
);

-- Insert default Insurance Report template
INSERT OR IGNORE INTO report_templates (
    name,
    description,
    template_type,
    practice_id,
    is_active,
    is_system_default,
    fields_schema,
    section_order,
    created_by_user_id
) VALUES (
    'Standard Insurance Report',
    'Default template for medical aid and insurance claims',
    'insurance',
    NULL, -- System template
    1, -- Active
    1, -- System default
    json('{
        "patient_demographics": {
            "type": "auto_populated",
            "label": "Patient Information",
            "required": true,
            "description": "Patient and medical aid information"
        },
        "medical_aid_details": {
            "type": "structured_fields",
            "label": "Medical Aid Details",
            "required": true,
            "description": "Medical aid scheme and membership information",
            "fields": {
                "scheme_name": {"type": "text", "label": "Medical Aid Scheme"},
                "membership_number": {"type": "text", "label": "Membership Number"},
                "plan_type": {"type": "text", "label": "Plan Type"},
                "authorized_sessions": {"type": "number", "label": "Authorized Sessions"}
            }
        },
        "diagnosis_information": {
            "type": "structured_fields",
            "label": "Diagnosis Information",
            "required": true,
            "description": "ICD-10 codes and diagnostic information",
            "fields": {
                "primary_icd10": {"type": "text", "label": "Primary ICD-10 Code"},
                "secondary_icd10": {"type": "textarea", "label": "Secondary ICD-10 Codes"},
                "diagnosis_date": {"type": "date", "label": "Date of Diagnosis"},
                "referring_practitioner": {"type": "text", "label": "Referring Practitioner"}
            }
        },
        "treatment_necessity": {
            "type": "rich_text",
            "label": "Medical Necessity Statement",
            "required": true,
            "description": "Justification for treatment medical necessity"
        },
        "treatment_provided": {
            "type": "structured_table",
            "label": "Treatment Sessions Provided",
            "required": true,
            "description": "Detailed log of treatment sessions",
            "columns": ["date", "treatment_code", "duration", "description", "progress_notes"]
        },
        "functional_progress": {
            "type": "ai_generated_paragraph",
            "label": "Functional Progress Report",
            "required": true,
            "editable": true,
            "ai_source": "outcome_measures",
            "description": "AI-generated progress summary for insurance review"
        },
        "prognosis_recommendations": {
            "type": "rich_text",
            "label": "Prognosis and Recommendations",
            "required": true,
            "description": "Clinical prognosis and future treatment recommendations"
        },
        "therapist_credentials": {
            "type": "auto_populated",
            "label": "Therapist Credentials",
            "required": true,
            "description": "Therapist qualifications and registration details"
        },
        "therapist_signature": {
            "type": "digital_signature",
            "label": "Therapist Signature",
            "required": true,
            "description": "Digital signature with timestamp"
        }
    }'),
    json('[
        "patient_demographics",
        "medical_aid_details",
        "diagnosis_information",
        "treatment_necessity",
        "treatment_provided",
        "functional_progress",
        "prognosis_recommendations",
        "therapist_credentials",
        "therapist_signature"
    ]'),
    'system'
);

-- Insert default Outcome Summary template
INSERT OR IGNORE INTO report_templates (
    name,
    description,
    template_type,
    practice_id,
    is_active,
    is_system_default,
    fields_schema,
    section_order,
    created_by_user_id
) VALUES (
    'Standard Outcome Summary',
    'Default template for outcome measure summaries and analysis',
    'outcome_summary',
    NULL, -- System template
    1, -- Active
    1, -- System default
    json('{
        "patient_demographics": {
            "type": "auto_populated",
            "label": "Patient Information",
            "required": true,
            "description": "Basic patient demographic information"
        },
        "assessment_period": {
            "type": "structured_fields",
            "label": "Assessment Period",
            "required": true,
            "description": "Time period covered by this outcome summary",
            "fields": {
                "start_date": {"type": "date", "label": "Assessment Start Date"},
                "end_date": {"type": "date", "label": "Assessment End Date"},
                "total_sessions": {"type": "number", "label": "Total Treatment Sessions"},
                "assessment_frequency": {"type": "select", "label": "Assessment Frequency", "options": ["Weekly", "Bi-weekly", "Monthly", "Quarterly"]}
            }
        },
        "outcome_measures_summary": {
            "type": "ai_generated_structured",
            "label": "Outcome Measures Summary",
            "required": true,
            "editable": true,
            "ai_source": "outcome_measure_data",
            "description": "AI-generated analysis of outcome measure trends and significance",
            "structure": {
                "measures_used": {"type": "list", "label": "Outcome Measures Used"},
                "baseline_scores": {"type": "table", "label": "Baseline Scores"},
                "current_scores": {"type": "table", "label": "Current Scores"},
                "change_analysis": {"type": "ai_paragraph", "label": "Statistical Analysis of Changes"}
            }
        },
        "functional_improvements": {
            "type": "structured_table",
            "label": "Functional Improvements",
            "required": true,
            "description": "Documented functional improvements over assessment period",
            "columns": ["functional_domain", "baseline_status", "current_status", "improvement_percentage", "clinical_significance"]
        },
        "goal_attainment": {
            "type": "structured_fields",
            "label": "Goal Attainment Analysis",
            "required": true,
            "description": "Analysis of treatment goal achievement",
            "fields": {
                "goals_set": {"type": "number", "label": "Total Goals Set"},
                "goals_achieved": {"type": "number", "label": "Goals Fully Achieved"},
                "goals_partially_achieved": {"type": "number", "label": "Goals Partially Achieved"},
                "achievement_rate": {"type": "calculated", "label": "Achievement Rate (%)"}
            }
        },
        "clinical_interpretation": {
            "type": "ai_generated_paragraph",
            "label": "Clinical Interpretation",
            "required": true,
            "editable": true,
            "ai_source": "comprehensive_analysis",
            "description": "AI-assisted clinical interpretation of outcome data"
        },
        "recommendations": {
            "type": "rich_text",
            "label": "Recommendations Based on Outcomes",
            "required": true,
            "description": "Clinical recommendations based on outcome analysis"
        },
        "therapist_signature": {
            "type": "digital_signature",
            "label": "Therapist Signature",
            "required": true,
            "description": "Digital signature of analyzing therapist"
        }
    }'),
    json('[
        "patient_demographics",
        "assessment_period",
        "outcome_measures_summary",
        "functional_improvements",
        "goal_attainment",
        "clinical_interpretation",
        "recommendations",
        "therapist_signature"
    ]'),
    'system'
);

-- Insert default Multi-disciplinary Assessment template
INSERT OR IGNORE INTO report_templates (
    name,
    description,
    template_type,
    practice_id,
    is_active,
    is_system_default,
    fields_schema,
    section_order,
    created_by_user_id
) VALUES (
    'Multi-disciplinary Assessment Report',
    'Comprehensive assessment template for multi-disciplinary team reports',
    'assessment',
    NULL, -- System template
    1, -- Active
    1, -- System default
    json('{
        "patient_demographics": {
            "type": "auto_populated",
            "label": "Patient Information",
            "required": true,
            "description": "Complete patient demographic and referral information"
        },
        "referral_information": {
            "type": "structured_fields",
            "label": "Referral Information",
            "required": true,
            "description": "Details of referral source and reason",
            "fields": {
                "referral_source": {"type": "text", "label": "Referral Source"},
                "referral_date": {"type": "date", "label": "Referral Date"},
                "referral_reason": {"type": "textarea", "label": "Reason for Referral"},
                "disciplines_requested": {"type": "multi_select", "label": "Disciplines Requested", "options": ["Physiotherapy", "Occupational Therapy", "Speech Therapy", "Psychology", "Social Work"]}
            }
        },
        "medical_history": {
            "type": "ai_generated_paragraph",
            "label": "Comprehensive Medical History",
            "required": true,
            "editable": true,
            "ai_source": "multi_disciplinary_notes",
            "description": "AI-compiled comprehensive medical history from all disciplines"
        },
        "discipline_assessments": {
            "type": "dynamic_sections",
            "label": "Individual Discipline Assessments",
            "required": true,
            "description": "Separate assessment sections for each involved discipline",
            "sections": {
                "physiotherapy": {
                    "label": "Physiotherapy Assessment",
                    "fields": ["physical_examination", "movement_analysis", "pain_assessment", "functional_capacity"]
                },
                "occupational_therapy": {
                    "label": "Occupational Therapy Assessment", 
                    "fields": ["adl_assessment", "cognitive_screening", "environmental_assessment", "equipment_needs"]
                },
                "speech_therapy": {
                    "label": "Speech-Language Pathology Assessment",
                    "fields": ["communication_assessment", "swallowing_evaluation", "cognitive_communication", "recommendations"]
                }
            }
        },
        "integrated_findings": {
            "type": "ai_generated_paragraph",
            "label": "Integrated Assessment Findings",
            "required": true,
            "editable": true,
            "ai_source": "cross_disciplinary_analysis",
            "description": "AI-generated synthesis of findings across all disciplines"
        },
        "collaborative_goals": {
            "type": "structured_table",
            "label": "Collaborative Treatment Goals",
            "required": true,
            "description": "Shared goals across disciplines with responsibility assignments",
            "columns": ["goal_description", "primary_discipline", "supporting_disciplines", "target_timeframe", "success_criteria"]
        },
        "treatment_recommendations": {
            "type": "rich_text",
            "label": "Integrated Treatment Recommendations",
            "required": true,
            "description": "Comprehensive treatment plan incorporating all disciplines"
        },
        "team_signatures": {
            "type": "multi_signature",
            "label": "Multi-disciplinary Team Signatures",
            "required": true,
            "description": "Digital signatures from all assessing disciplines"
        }
    }'),
    json('[
        "patient_demographics",
        "referral_information",
        "medical_history",
        "discipline_assessments",
        "integrated_findings",
        "collaborative_goals",
        "treatment_recommendations",
        "team_signatures"
    ]'),
    'system'
);

-- Create trigger to auto-increment template versions
CREATE TRIGGER IF NOT EXISTS increment_template_version
    AFTER UPDATE OF fields_schema, section_order ON report_templates
    WHEN NEW.fields_schema != OLD.fields_schema OR NEW.section_order != OLD.section_order
BEGIN
    UPDATE report_templates 
    SET version = version + 1, updated_at = datetime('now')
    WHERE id = NEW.id;
END;