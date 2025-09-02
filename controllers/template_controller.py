"""
Structured Template API Controllers for HadadaHealth

Provides RESTful API endpoints for managing structured report templates with
auto-population, draft saving, section deletion, and AI content generation.
"""
import json
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from fastapi import HTTPException, Query, Path, Depends
from pydantic import BaseModel, Field, validator
import sqlite3

from modules.database import get_db_connection, execute_query
from modules.auth import require_auth
from modules.ai_content import ai_generator
from modules.data_aggregation import get_patient_data_summary


class StructuredTemplateResponse(BaseModel):
    """Response model for structured template data"""
    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    category: str
    template_structure: Dict[str, Any]
    auto_populate_mapping: Optional[Dict[str, str]] = None
    is_active: bool
    version: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TemplateInstanceResponse(BaseModel):
    """Response model for template instance data"""
    id: int
    template_id: int
    template_name: str
    patient_id: int
    patient_name: str
    therapist_id: Optional[str] = None  # Legacy field for backward compatibility
    assigned_therapist_ids: Optional[List[str]] = None  # New field for multiple therapists
    assigned_therapist_names: Optional[str] = None  # Display names for the therapists
    instance_data: Dict[str, Any]
    sections_deleted: Optional[List[str]] = None
    status: str
    title: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None


class TemplateInstanceCreateRequest(BaseModel):
    """Request model for creating template instances"""
    template_id: int = Field(..., gt=0, description="Template ID to use")
    patient_id: int = Field(..., gt=0, description="Patient identifier")
    therapist_id: Optional[str] = Field(None, description="Creating therapist ID (legacy)")
    therapist_ids: Optional[List[str]] = Field(None, description="List of assigned therapist IDs")
    title: Optional[str] = Field(None, max_length=255, description="Custom instance title")


class TemplateInstanceUpdateRequest(BaseModel):
    """Request model for updating template instances"""
    instance_data: Optional[Dict[str, Any]] = Field(None, description="Template field values")
    sections_deleted: Optional[List[str]] = Field(None, description="List of deleted section IDs")
    status: Optional[str] = Field(None, description="Instance status")
    title: Optional[str] = Field(None, max_length=255, description="Instance title")

    @validator('status')
    def validate_status(cls, v):
        if v is not None and v not in ['draft', 'completed', 'archived']:
            raise ValueError('Status must be draft, completed, or archived')
        return v


def get_structured_templates(active_only: bool = True) -> List[StructuredTemplateResponse]:
    """
    Get all structured templates
    
    Args:
        active_only: If True, only return active templates
    
    Returns:
        List of structured templates
    """
    try:
        query = """
            SELECT id, name, display_name, description, category, 
                   template_structure, auto_populate_mapping, is_active, 
                   version, created_at, updated_at
            FROM structured_templates
            WHERE 1=1
        """
        params = ()
        
        if active_only:
            query += " AND is_active = 1"
            
        query += " ORDER BY display_name"
        
        templates = execute_query(query, params, fetch='all')
        
        result = []
        for template in templates:
            template_dict = dict(template)
            template_dict['template_structure'] = json.loads(template_dict['template_structure'])
            if template_dict['auto_populate_mapping']:
                template_dict['auto_populate_mapping'] = json.loads(template_dict['auto_populate_mapping'])
            result.append(StructuredTemplateResponse(**template_dict))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve templates: {str(e)}")


def get_structured_template_by_id(template_id: int) -> StructuredTemplateResponse:
    """
    Get a structured template by ID
    
    Args:
        template_id: Template ID
        
    Returns:
        Template details
    """
    try:
        query = """
            SELECT id, name, display_name, description, category,
                   template_structure, auto_populate_mapping, is_active,
                   version, created_at, updated_at
            FROM structured_templates
            WHERE id = ?
        """
        
        template = execute_query(query, (template_id,), fetch='one')
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        template_dict = dict(template)
        template_dict['template_structure'] = json.loads(template_dict['template_structure'])
        if template_dict['auto_populate_mapping']:
            template_dict['auto_populate_mapping'] = json.loads(template_dict['auto_populate_mapping'])
            
        return StructuredTemplateResponse(**template_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve template: {str(e)}")


def create_template_instance(request: TemplateInstanceCreateRequest) -> TemplateInstanceResponse:
    """
    Create a new template instance with auto-populated data
    
    Args:
        request: Template instance creation request
        
    Returns:
        Created template instance
    """
    try:
        print(f"🔍 Controller: create_template_instance started")
        
        # Get template details
        template = get_structured_template_by_id(request.template_id)
        print(f"🔍 Controller: Got template {template.name}")
        
        # Get patient data for auto-population
        patient_data = get_patient_for_auto_population(request.patient_id)
        print(f"🔍 Controller: Got patient data for {patient_data.get('full_name', 'unknown')}")
        
        # Auto-populate instance data
        print(f"🔍 Controller: About to call auto_populate_template_data")
        instance_data = auto_populate_template_data(
            template.template_structure, 
            template.auto_populate_mapping, 
            patient_data
        )
        print(f"🔍 Controller: auto_populate_template_data returned {len(instance_data)} fields")
        
        # Handle multiple therapist IDs - use new format or fall back to legacy
        therapist_ids = []
        if request.therapist_ids:
            therapist_ids = request.therapist_ids
        elif request.therapist_id:
            therapist_ids = [request.therapist_id]
        
        # Create the instance
        query = """
            INSERT INTO structured_template_instances 
            (template_id, patient_id, therapist_id, assigned_therapist_ids, instance_data, status, title, created_at)
            VALUES (?, ?, ?, ?, ?, 'draft', ?, CURRENT_TIMESTAMP)
        """
        
        title = request.title or f"{template.display_name} - {patient_data.get('full_name', 'Unknown')}"
        
        # For backward compatibility, still populate therapist_id with first therapist
        primary_therapist_id = therapist_ids[0] if therapist_ids else None
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, (
            request.template_id,
            request.patient_id, 
            primary_therapist_id,
            json.dumps(therapist_ids),
            json.dumps(instance_data),
            title
        ))
        instance_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Get the created instance
        created_instance = get_template_instance_by_id(instance_id)
        
        # Create corresponding report entry immediately
        try:
            print(f"🔗 Creating initial report entry for template instance {instance_id}")
            create_initial_report_from_instance(instance_id, created_instance, request)
            print(f"✅ Initial report entry created for template instance {instance_id}")
        except Exception as e:
            print(f"⚠️ Warning: Failed to create initial report entry: {e}")
            # Don't fail the template creation if report creation fails
        
        return created_instance
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create template instance: {str(e)}")


def get_template_instance_by_id(instance_id: int) -> TemplateInstanceResponse:
    """
    Get a template instance by ID
    
    Args:
        instance_id: Template instance ID
        
    Returns:
        Template instance details
    """
    try:
        query = """
            SELECT ti.id, ti.template_id, ti.patient_id, ti.therapist_id, 
                   ti.assigned_therapist_ids,
                   ti.instance_data, ti.sections_deleted, ti.status, ti.title,
                   ti.created_at, ti.updated_at, ti.completed_at,
                   st.display_name as template_name,
                   p.first_name || ' ' || p.surname as patient_name
            FROM structured_template_instances ti
            JOIN structured_templates st ON ti.template_id = st.id
            JOIN patients p ON ti.patient_id = p.id
            WHERE ti.id = ?
        """
        
        instance = execute_query(query, (instance_id,), fetch='one')
        
        if not instance:
            raise HTTPException(status_code=404, detail="Template instance not found")
        
        instance_dict = dict(instance)
        instance_dict['instance_data'] = json.loads(instance_dict['instance_data'])
        if instance_dict['sections_deleted']:
            instance_dict['sections_deleted'] = json.loads(instance_dict['sections_deleted'])
        
        # Handle assigned therapist IDs and get names
        assigned_therapist_ids = []
        if instance_dict.get('assigned_therapist_ids'):
            try:
                assigned_therapist_ids = json.loads(instance_dict['assigned_therapist_ids'])
            except (json.JSONDecodeError, TypeError):
                # Fallback to legacy single therapist_id if assigned_therapist_ids is invalid
                if instance_dict.get('therapist_id'):
                    assigned_therapist_ids = [instance_dict['therapist_id']]
        elif instance_dict.get('therapist_id'):
            # Fallback to legacy single therapist for older records
            assigned_therapist_ids = [instance_dict['therapist_id']]
        
        instance_dict['assigned_therapist_ids'] = assigned_therapist_ids
        
        # Get therapist names using the existing helper function
        from controllers.report_controller import get_therapist_names
        instance_dict['assigned_therapist_names'] = get_therapist_names(assigned_therapist_ids)
            
        return TemplateInstanceResponse(**instance_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve template instance: {str(e)}")


def update_template_instance(instance_id: int, request: TemplateInstanceUpdateRequest) -> TemplateInstanceResponse:
    """
    Update a template instance
    
    Args:
        instance_id: Template instance ID
        request: Update request
        
    Returns:
        Updated template instance
    """
    print(f"🔄 update_template_instance called: instance_id={instance_id}")
    print(f"📝 Request data: {request}")
    print(f"📊 Instance data size: {len(str(request.instance_data)) if request.instance_data else 0} chars")
    print(f"📋 Status: {request.status}")
    
    try:
        # Check if instance exists
        existing_instance = get_template_instance_by_id(instance_id)
        print(f"✅ Found existing instance: {existing_instance.id if existing_instance else 'None'}")
        
        update_fields = []
        params = []
        
        if request.instance_data is not None:
            update_fields.append("instance_data = ?")
            params.append(json.dumps(request.instance_data))
            
        if request.sections_deleted is not None:
            update_fields.append("sections_deleted = ?")
            params.append(json.dumps(request.sections_deleted))
            
        if request.status is not None:
            update_fields.append("status = ?")
            params.append(request.status)
            
        if request.title is not None:
            update_fields.append("title = ?")
            params.append(request.title)
        
        if not update_fields:
            print("⚠️ No update fields provided, returning existing instance")
            return existing_instance
            
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(instance_id)
        
        query = f"""
            UPDATE structured_template_instances 
            SET {', '.join(update_fields)}
            WHERE id = ?
        """
        
        print(f"🔍 SQL Query: {query}")
        print(f"🔍 SQL Params: {params}")
        
        execute_query(query, tuple(params))
        print("✅ Database update completed")
        
        # If status is completed, create or update corresponding report entry
        if request.status == 'completed':
            print("🔗 Status is 'completed', creating/updating report entry...")
            try:
                create_or_update_report_from_instance(instance_id, existing_instance, request)
                print("✅ Report entry created/updated successfully")
            except Exception as e:
                print(f"⚠️ Warning: Failed to create report entry: {e}")
                # Don't fail the template save if report creation fails
        
        updated_instance = get_template_instance_by_id(instance_id)
        print(f"📊 Updated instance retrieved: {updated_instance.id if updated_instance else 'None'}")
        
        return updated_instance
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update template instance: {str(e)}")


def create_initial_report_from_instance(instance_id: int, instance: TemplateInstanceResponse, request: TemplateInstanceCreateRequest):
    """
    Create initial report entry when a template instance is created
    
    Args:
        instance_id: Template instance ID
        instance: Template instance data
        request: Creation request
    """
    from modules.database import execute_query
    
    try:
        # Determine report type based on template
        report_type = 'discharge' if instance.template_name == 'Discharge Summary' else 'progress'
        
        # Get therapist IDs - use new multiple format or fall back to legacy
        therapist_ids = []
        if request.therapist_ids:
            therapist_ids = request.therapist_ids
        elif request.therapist_id:
            therapist_ids = [request.therapist_id]
        
        # Create initial report data
        report_data = {
            'patient_id': str(instance.patient_id),
            'report_type': report_type, 
            'template_id': instance.template_id,
            'title': f"{instance.patient_name} - {instance.template_name}",
            'assigned_therapist_ids': therapist_ids,
            'disciplines': ['physiotherapy'],  # Default discipline
            'priority': 2,
            'deadline_date': None,
            'requested_by_user_id': therapist_ids[0] if therapist_ids else request.therapist_id,
            'content': {},  # Start with empty content
            'status': 'pending'  # Start as pending, becomes completed when template is completed
        }
        
        # Insert into reports table
        insert_report_query = """
            INSERT INTO reports (
                patient_id, report_type, template_id, title, status, priority,
                assigned_therapist_ids, disciplines, requested_by_user_id,
                content, template_instance_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        
        execute_query(insert_report_query, (
            report_data['patient_id'],
            report_data['report_type'],
            report_data['template_id'],
            report_data['title'],
            report_data['status'],
            report_data['priority'],
            json.dumps(report_data['assigned_therapist_ids']),
            json.dumps(report_data['disciplines']),
            report_data['requested_by_user_id'],
            json.dumps(report_data['content']),
            instance_id
        ))
        
        print(f"✅ Created initial report entry for template instance {instance_id}")
        
    except Exception as e:
        print(f"❌ Error creating initial report from template instance: {e}")
        raise


def create_or_update_report_from_instance(instance_id: int, instance: TemplateInstanceResponse, request: TemplateInstanceUpdateRequest):
    """
    Create or update a report entry when a template instance is completed
    
    Args:
        instance_id: Template instance ID
        instance: Template instance data
        request: Update request
    """
    # Import here to avoid circular imports
    from modules.database import create_report, get_report_by_id, execute_query
    
    try:
        # Check if a report already exists for this template instance
        existing_report_query = """
            SELECT id FROM reports 
            WHERE template_instance_id = ?
        """
        existing_report = execute_query(existing_report_query, (instance_id,), fetch='one')
        
        if existing_report:
            # Update existing report to completed status
            print(f"📝 Updating existing report ID: {existing_report['id']} to completed status")
            update_report_query = """
                UPDATE reports 
                SET status = 'completed', 
                    content = ?,
                    completed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE template_instance_id = ?
            """
            execute_query(update_report_query, (json.dumps(request.instance_data), instance_id))
        else:
            # This shouldn't happen with the new flow, but keep as fallback
            print(f"⚠️ No existing report found for template instance {instance_id}, creating one...")
            
            # Determine report type based on template
            report_type = 'discharge' if instance.template_name == 'Discharge Summary' else 'progress'
            
            # Create the report
            report_data = {
                'patient_id': str(instance.patient_id),
                'report_type': report_type, 
                'template_id': instance.template_id,
                'title': f"{instance.patient_name} - {instance.template_name}",
                'assigned_therapist_ids': ['1'],  # Default to current user
                'disciplines': ['physiotherapy'],  # Default discipline
                'priority': 2,
                'deadline_date': None,
                'requested_by_user_id': '1',  # Default to current user
                'content': request.instance_data,
                'status': 'completed'
            }
            
            # Insert into reports table
            insert_report_query = """
                INSERT INTO reports (
                    patient_id, report_type, template_id, title, status, priority,
                    assigned_therapist_ids, disciplines, requested_by_user_id,
                    content, template_instance_id, completed_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            
            execute_query(insert_report_query, (
                report_data['patient_id'],
                report_data['report_type'],
                report_data['template_id'],
                report_data['title'],
                report_data['status'],
                report_data['priority'],
                json.dumps(report_data['assigned_therapist_ids']),
                json.dumps(report_data['disciplines']),
                report_data['requested_by_user_id'],
                json.dumps(report_data['content']),
                instance_id
            ))
            
            print(f"✅ Created new report entry for template instance {instance_id}")
            
    except Exception as e:
        print(f"❌ Error creating report from template instance: {e}")
        raise


def get_template_instances_for_patient(patient_id: int, status: Optional[str] = None) -> List[TemplateInstanceResponse]:
    """
    Get all template instances for a patient
    
    Args:
        patient_id: Patient ID
        status: Optional status filter
        
    Returns:
        List of template instances
    """
    try:
        query = """
            SELECT ti.id, ti.template_id, ti.patient_id, ti.therapist_id,
                   ti.instance_data, ti.sections_deleted, ti.status, ti.title,
                   ti.created_at, ti.updated_at, ti.completed_at,
                   st.display_name as template_name,
                   p.first_name || ' ' || p.surname as patient_name
            FROM structured_template_instances ti
            JOIN structured_templates st ON ti.template_id = st.id
            JOIN patients p ON ti.patient_id = p.id
            WHERE ti.patient_id = ?
        """
        params = [patient_id]
        
        if status:
            query += " AND ti.status = ?"
            params.append(status)
            
        query += " ORDER BY ti.created_at DESC"
        
        instances = execute_query(query, tuple(params), fetch='all')
        
        result = []
        for instance in instances:
            instance_dict = dict(instance)
            instance_dict['instance_data'] = json.loads(instance_dict['instance_data'])
            if instance_dict['sections_deleted']:
                instance_dict['sections_deleted'] = json.loads(instance_dict['sections_deleted'])
            result.append(TemplateInstanceResponse(**instance_dict))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve template instances: {str(e)}")


def delete_template_instance(instance_id: int) -> Dict[str, str]:
    """
    Delete a template instance
    
    Args:
        instance_id: Template instance ID
        
    Returns:
        Success message
    """
    try:
        # Check if instance exists
        get_template_instance_by_id(instance_id)
        
        query = "DELETE FROM structured_template_instances WHERE id = ?"
        execute_query(query, (instance_id,))
        
        return {"message": "Template instance deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete template instance: {str(e)}")


def get_patient_for_auto_population(patient_id: int) -> Dict[str, Any]:
    """
    Get comprehensive patient data for auto-population including clinical records
    
    Args:
        patient_id: Patient ID
        
    Returns:
        Comprehensive patient data dictionary with clinical information
    """
    try:
        # Get core patient demographics and administrative data
        patient_query = """
            SELECT id, first_name, surname as last_name, contact_number as phone_number, email,
                   date_of_birth, account_id_number as id_number, gender, medical_aid_name,
                   medical_aid_number, plan_name, claim_number, case_manager, icd10_codes as icd_10_codes,
                   patient_important_info, medical_history_ai, address_line1, address_line2, 
                   town, postal_code, clinic
            FROM patients
            WHERE id = ?
        """
        
        patient = execute_query(patient_query, (patient_id,), fetch='one')
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        patient_dict = dict(patient)
        patient_dict['full_name'] = f"{patient_dict['first_name']} {patient_dict['last_name']}"
        patient_dict['primary_diagnosis'] = patient_dict['icd_10_codes']
        
        # Get admission/incident dates from earliest booking
        admission_query = """
            SELECT MIN(date) as date_of_admission, 
                   GROUP_CONCAT(DISTINCT profession) as disciplines_involved
            FROM bookings 
            WHERE patient_id = ? AND date IS NOT NULL
        """
        
        admission_data = execute_query(admission_query, (patient_id,), fetch='one')
        if admission_data and admission_data['date_of_admission']:
            patient_dict['date_of_admission'] = admission_data['date_of_admission']
            patient_dict['disciplines_involved'] = admission_data['disciplines_involved']
        
        # Get clinical notes for AI generation context
        notes_query = """
            SELECT subjective_findings, objective_findings, treatment, plan, profession,
                   therapist_name, appointment_date
            FROM treatment_notes 
            WHERE patient_id = ? 
            ORDER BY appointment_date DESC 
            LIMIT 20
        """
        
        clinical_notes = execute_query(notes_query, (patient_id,), fetch='all')
        patient_dict['clinical_notes'] = [dict(note) for note in clinical_notes] if clinical_notes else []
        
        # Get treating therapists and professional information
        therapists_query = """
            SELECT DISTINCT t.name, t.surname, t.profession, t.hpcsa_number,
                   t.email, t.clinic
            FROM therapists t
            JOIN bookings b ON t.id = b.therapist
            WHERE b.patient_id = ?
        """
        
        therapists = execute_query(therapists_query, (patient_id,), fetch='all')
        patient_dict['treating_therapists'] = [dict(therapist) for therapist in therapists] if therapists else []
        
        # Organize therapists by profession for easy access
        therapist_by_profession = {}
        for therapist in patient_dict['treating_therapists']:
            profession = therapist['profession']
            if profession not in therapist_by_profession:
                therapist_by_profession[profession] = []
            therapist_by_profession[profession].append(f"{therapist['name']} {therapist['surname']}")
        
        patient_dict['physiotherapist'] = ', '.join(therapist_by_profession.get('physiotherapy', []))
        patient_dict['occupational_therapist'] = ', '.join(therapist_by_profession.get('occupational therapy', []))
        patient_dict['speech_therapist'] = ', '.join(therapist_by_profession.get('speech therapy', []))
        patient_dict['psychologist'] = ', '.join(therapist_by_profession.get('psychology', []))
        
        # Get practice information
        if patient_dict['clinic']:
            patient_dict['therapy_practice'] = patient_dict['clinic']
        
        return patient_dict
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve patient data: {str(e)}")


def parse_icd10_codes(icd10_codes_json: str) -> List[str]:
    """
    Parse ICD10 codes from JSON string format
    
    Args:
        icd10_codes_json: JSON string like '["M07.20","E10.2"]'
        
    Returns:
        List of ICD10 codes
    """
    if not icd10_codes_json:
        return []
    
    try:
        # Handle both string and already-parsed formats
        if isinstance(icd10_codes_json, list):
            return icd10_codes_json
        
        # Parse JSON string
        return json.loads(icd10_codes_json)
    except (json.JSONDecodeError, TypeError):
        # Fallback: try to extract codes from string manually
        if isinstance(icd10_codes_json, str):
            # Remove brackets and quotes, split by comma
            clean_string = icd10_codes_json.strip('[]"')
            if clean_string:
                return [code.strip(' "') for code in clean_string.split(',') if code.strip(' "')]
        return []


def lookup_icd10_descriptions(icd10_codes: List[str]) -> Dict[str, str]:
    """
    Look up ICD10 code descriptions from the ICD10 database
    
    Args:
        icd10_codes: List of ICD10 codes to look up
        
    Returns:
        Dictionary mapping codes to descriptions
    """
    if not icd10_codes:
        return {}
    
    try:
        icd10_db_path = '/Users/duncanmiller/Documents/HadadaHealth/data/icd10_with_pmb.db'
        conn = sqlite3.connect(icd10_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Create placeholders for IN clause
        placeholders = ','.join('?' for _ in icd10_codes)
        query = f"SELECT code, description FROM icd10_codes WHERE code IN ({placeholders})"
        
        cursor.execute(query, icd10_codes)
        results = cursor.fetchall()
        conn.close()
        
        return {row['code']: row['description'] for row in results}
        
    except Exception as e:
        print(f"Warning: Could not lookup ICD10 descriptions: {str(e)}")
        return {}


def format_diagnosis_text(icd10_codes_json: str) -> str:
    """
    Format diagnosis text with ICD10 codes and descriptions
    
    Args:
        icd10_codes_json: JSON string of ICD10 codes
        
    Returns:
        Formatted diagnosis text
    """
    codes = parse_icd10_codes(icd10_codes_json)
    if not codes:
        return ""
    
    descriptions = lookup_icd10_descriptions(codes)
    
    # Format each diagnosis with code and description
    formatted_diagnoses = []
    for code in codes:
        if code in descriptions:
            formatted_diagnoses.append(f"{code}: {descriptions[code]}")
        else:
            formatted_diagnoses.append(code)  # Fallback to just the code
    
    return "; ".join(formatted_diagnoses)


def auto_populate_template_data(
    template_structure: Dict[str, Any], 
    mapping: Optional[Dict[str, str]], 
    patient_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Auto-populate template fields with comprehensive patient data and AI-generated content
    
    Args:
        template_structure: Template structure definition
        mapping: Field mapping configuration
        patient_data: Comprehensive patient data including clinical records
        
    Returns:
        Auto-populated template data with imported and AI-generated content
    """
    populated_data = {}
    
    # Add current date and time fields
    current_date = datetime.now().strftime('%Y-%m-%d')
    populated_data['current_date'] = current_date
    populated_data['report_date'] = current_date
    
    print(f"🔍 Debug: Starting auto_populate_template_data")
    print(f"🔍 Debug: mapping exists: {mapping is not None}")
    
    # Auto-populate fields based on mapping
    if mapping:
        for template_field, patient_field in mapping.items():
            if template_field.startswith('patient.'):
                field_name = template_field.replace('patient.', '')
                if patient_field in patient_data and patient_data[patient_field]:
                    populated_data[field_name] = patient_data[patient_field]
            elif template_field == 'current_date':
                populated_data['report_date'] = current_date
    
    # Enhanced auto-population for fields not covered by mapping system
    # Add admission/incident dates and other clinical data
    if patient_data.get('date_of_admission'):
        populated_data['date_of_admission'] = patient_data['date_of_admission']
        populated_data['date_of_incident'] = patient_data['date_of_admission']  # Use admission as fallback
    
    # Process ICD10 codes properly and lookup diagnosis descriptions
    print(f"🔍 Debug: patient_data keys: {list(patient_data.keys())}")
    print(f"🔍 Debug: icd_10_codes in patient_data: {'icd_10_codes' in patient_data}")
    if patient_data.get('icd_10_codes'):
        print(f"🔍 Debug: icd_10_codes value: {patient_data['icd_10_codes']}")
        icd10_codes_raw = patient_data['icd_10_codes']
        
        # Parse ICD10 codes from JSON format
        icd10_codes = parse_icd10_codes(icd10_codes_raw)
        print(f"🔍 Debug: parsed icd10_codes: {icd10_codes}")
        
        # Store the cleaned codes as comma-separated string
        populated_data['icd_10_codes'] = ", ".join(icd10_codes) if icd10_codes else ""
        
        # Generate diagnosis text with descriptions
        populated_data['diagnosis'] = format_diagnosis_text(icd10_codes_raw)
        print(f"🔍 Debug: formatted diagnosis: {populated_data['diagnosis']}")
    else:
        print("🔍 Debug: No icd_10_codes found in patient_data")
    
    # IMPORTED Practice Information
    populated_data.update({
        'therapy_practice': patient_data.get('therapy_practice', patient_data.get('clinic', '')),
    })
    
    # IMPORTED Professional Information
    populated_data.update({
        'physiotherapist': patient_data.get('physiotherapist', ''),
        'occupational_therapist': patient_data.get('occupational_therapist', ''),
        'speech_therapist': patient_data.get('speech_therapist', ''),
        'psychologist': patient_data.get('psychologist', ''),
    })
    
    # AI-GENERATED Content (will be generated when template instance is created)
    # These fields are marked for AI generation but start empty
    ai_generated_fields = [
        'background_content',  # Background History
        'medical_status_content',  # Medical Status
        'medical_history_content',  # Medical History 
        'environmental_content',  # Environmental & Personal Context
        'environmental_factors',  # Rehabilitation Outcomes
        'assistive_devices',
        'education_training',
        'psychosocial_summary',
    ]
    
    for field in ai_generated_fields:
        if field not in populated_data:
            populated_data[field] = ''  # Will be populated by AI generation
    
    # Generate AI content for key sections if clinical notes are available
    if patient_data.get('clinical_notes'):
        try:
            from modules.ai_content import ai_generator
            
            # Generate Background History
            if patient_data.get('medical_history_ai') or patient_data.get('clinical_notes'):
                background_prompt = "Generate comprehensive background history from patient clinical notes, medical history, and social context"
                populated_data['background_content'] = ai_generator.generate_clinical_content(
                    prompt=background_prompt,
                    patient_data=patient_data,
                    context_type='background_history'
                )
            
            # Generate Medical Status
            recent_notes = patient_data['clinical_notes'][:5]  # Most recent 5 notes
            if recent_notes:
                medical_status_prompt = "Summarize current medical condition, medications, and medical management from clinical assessments"
                populated_data['medical_status_content'] = ai_generator.generate_clinical_content(
                    prompt=medical_status_prompt,
                    patient_data={'clinical_notes': recent_notes, **patient_data},
                    context_type='medical_status'
                )
                
        except ImportError:
            # AI module not available, leave fields empty for manual entry
            pass
        except Exception as e:
            # Log error but don't fail the template creation
            print(f"AI content generation warning: {str(e)}")
    
    return populated_data


def generate_ai_content_for_section(
    instance_id: int, 
    section_id: str, 
    field_id: str
) -> Dict[str, Any]:
    """
    Generate AI content for a specific template section field
    
    Args:
        instance_id: Template instance ID
        section_id: Section identifier
        field_id: Field identifier
        
    Returns:
        Generated content
    """
    try:
        instance = get_template_instance_by_id(instance_id)
        template = get_structured_template_by_id(instance.template_id)
        
        # Find the specific field configuration
        field_config = None
        for section in template.template_structure.get('sections', []):
            if section['id'] == section_id:
                for field in section.get('fields', []):
                    if field['id'] == field_id:
                        field_config = field
                        break
                break
        
        if not field_config or not field_config.get('ai_prompt'):
            raise HTTPException(status_code=400, detail="Field is not AI-generatable")
        
        # Special handling for background_history field
        if field_id == 'background_content' and section_id == 'background_history':
            from modules.patients import get_patient_medical_history
            existing_history = get_patient_medical_history(instance.patient_id)
            
            if existing_history:
                generated_content = existing_history
            else:
                # Fallback to generating new content if no existing history
                patient_data = get_patient_data_summary(instance.patient_id)
                ai_prompt = field_config['ai_prompt']
                generated_content = ai_generator.generate_clinical_content(
                    prompt=ai_prompt,
                    patient_data=patient_data,
                    context_type='template_field'
                )
        else:
            # Get patient data for context
            patient_data = get_patient_data_summary(instance.patient_id)
            
            # Generate AI content
            ai_prompt = field_config['ai_prompt']
            generated_content = ai_generator.generate_clinical_content(
                prompt=ai_prompt,
                patient_data=patient_data,
                context_type='template_field'
            )
        
        return {
            'field_id': field_id,
            'content': generated_content,
            'generated_at': datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate AI content: {str(e)}")


def regenerate_ai_content_for_section(
    instance_id: int, 
    section_id: str, 
    field_id: str
) -> Dict[str, Any]:
    """
    Regenerate AI content from treatment notes for a specific template section field
    
    Args:
        instance_id: Template instance ID
        section_id: Section identifier
        field_id: Field identifier
        
    Returns:
        Generated content from treatment notes
    """
    try:
        print(f"DEBUG: Regenerating AI content for instance {instance_id}, section {section_id}, field {field_id}")
        
        instance = get_template_instance_by_id(instance_id)
        template = get_structured_template_by_id(instance.template_id)
        
        print(f"DEBUG: Found instance and template")
        
        # Find the specific field configuration
        field_config = None
        for section in template.template_structure.get('sections', []):
            if section['id'] == section_id:
                for field in section.get('fields', []):
                    if field['id'] == field_id:
                        field_config = field
                        break
                break
        
        print(f"DEBUG: Field config found: {field_config}")
        
        if not field_config or not field_config.get('ai_prompt'):
            raise HTTPException(status_code=400, detail="Field is not AI-generatable")
        
        print(f"DEBUG: Getting patient data summary")
        # Always generate new content from treatment notes for regeneration
        patient_data = get_patient_data_summary(instance.patient_id)
        
        print(f"DEBUG: Patient data retrieved, generating AI content")
        # Use the same template prompt for all fields, including regeneration
        ai_prompt = field_config['ai_prompt']
        print(f"DEBUG: Using prompt: {ai_prompt}")
        
        generated_content = ai_generator.generate_clinical_content(
            prompt=ai_prompt,
            patient_data=patient_data,
            context_type='template_field'
        )
        
        print(f"DEBUG: AI content generated successfully")
        
        return {
            'field_id': field_id,
            'content': generated_content,
            'generated_at': datetime.now().isoformat(),
            'regenerated': True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG: Exception in regenerate_ai_content_for_section: {e}")
        print(f"DEBUG: Exception type: {type(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to regenerate AI content: {str(e)}")