"""
Report API Controllers for HadadaHealth

Provides RESTful API endpoints for managing AI-powered clinical reports with
multi-disciplinary support, workflow management, and automated content generation.
"""
import json
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from fastapi import HTTPException, Query, Path, Depends
from pydantic import BaseModel, Field, validator

from modules.database import (
    create_report, get_report_by_id, get_reports_for_user, update_report_status,
    get_report_templates, create_report_notification, get_db_connection, execute_query,
    delete_report
)
from modules.auth import require_auth
from modules.ai_content import ai_generator
from modules.data_aggregation import get_patient_data_summary
from modules.patients import get_patient_by_id


def get_patient_name(patient_id: str) -> str:
    """Get patient full name from patient_id"""
    try:
        # First try as integer (most common case)
        patient = get_patient_by_id(int(patient_id))
        if patient:
            first_name = patient.get('first_name', '')
            surname = patient.get('surname', '')
            return f"{first_name} {surname}".strip()
    except (ValueError, TypeError):
        # If conversion to int fails, try as string
        pass
    
    # If not found, check if there's a direct query for string patient_id
    try:
        query = "SELECT first_name, surname FROM patients WHERE id = ? OR CAST(id AS TEXT) = ?"
        result = execute_query(query, (patient_id, patient_id), fetch='one')
        if result:
            first_name = result.get('first_name', '')
            surname = result.get('surname', '')
            return f"{first_name} {surname}".strip()
    except Exception:
        pass
    
    return "Unknown Patient"


def get_therapist_names(therapist_ids: List[str]) -> str:
    """Get comma-separated therapist full names from list of therapist IDs"""
    if not therapist_ids:
        return "Unassigned"
    
    names = []
    for therapist_id in therapist_ids:
        try:
            # First try therapists table for full names (most common case)
            query = "SELECT name, surname FROM therapists WHERE id = ?"
            result = execute_query(query, (therapist_id,), fetch='one')
            if result:
                name = result['name'] if 'name' in result.keys() else ''
                surname = result['surname'] if 'surname' in result.keys() else ''
                full_name = f"{name} {surname}".strip()
                names.append(full_name if full_name else f"Therapist {therapist_id}")
                continue
            
            # Then try to get from users table and cross-reference with therapists
            query = """
                SELECT u.username, t.name, t.surname 
                FROM users u 
                LEFT JOIN therapists t ON u.linked_therapist_id = t.id 
                WHERE u.id = ?
            """
            result = execute_query(query, (therapist_id,), fetch='one')
            if result:
                if result.get('name') and result.get('surname'):
                    # User has linked therapist record with full name
                    full_name = f"{result['name']} {result['surname']}".strip()
                    names.append(full_name)
                else:
                    # Fall back to username if no therapist record
                    names.append(result['username'])
                continue
            
            # Fallback: try users table directly for username only
            query = "SELECT username FROM users WHERE id = ?"
            result = execute_query(query, (therapist_id,), fetch='one')
            if result:
                names.append(result['username'])
            else:
                names.append(f"Unknown User {therapist_id}")
                
        except Exception as e:
            names.append(f"Unknown {therapist_id}")
    
    return ", ".join(names) if names else "Unassigned"


class ReportResponse(BaseModel):
    """Response model for report data"""
    id: int
    patient_id: str
    report_type: str
    template_id: int
    template_name: Optional[str] = None
    title: str
    status: str
    priority: int
    assigned_therapist_ids: List[str]
    disciplines: List[str]
    requested_by_user_id: Optional[str] = None
    deadline_date: Optional[str] = None
    ai_generated_sections: Optional[Dict[str, Any]] = None
    content: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    # Additional fields for frontend compatibility
    patient: Optional[str] = None  # Patient full name
    assignedTo: Optional[str] = None  # Comma-separated assigned therapist names
    createdDate: Optional[str] = None  # Alias for created_at
    description: Optional[str] = None  # Report description


class ReportCreateRequest(BaseModel):
    """Request model for creating reports"""
    patient_id: str = Field(..., min_length=1, description="Patient identifier")
    report_type: str = Field(..., min_length=1, description="Type of report")
    template_id: int = Field(..., gt=0, description="Template ID to use")
    title: str = Field(..., min_length=1, max_length=255, description="Report title")
    assigned_therapist_ids: List[str] = Field(..., min_items=1, description="List of assigned therapist IDs")
    disciplines: List[str] = Field(..., min_items=1, description="List of involved disciplines")
    deadline_date: Optional[str] = Field(None, description="Deadline in YYYY-MM-DD format")
    priority: int = Field(default=1, ge=1, le=3, description="Priority level (1=low, 2=normal, 3=high)")
    generate_ai_content: bool = Field(default=False, description="Whether to generate AI content immediately")

    @validator('deadline_date')
    def validate_deadline(cls, v):
        if v:
            try:
                deadline = datetime.strptime(v, '%Y-%m-%d')
                if deadline.date() <= datetime.now().date():
                    raise ValueError('Deadline must be in the future')
            except ValueError as e:
                raise ValueError(f'Invalid deadline format or value: {e}')
        return v


class ReportUpdateRequest(BaseModel):
    """Request model for updating reports"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[str] = Field(None, description="Report status")
    priority: Optional[int] = Field(None, ge=1, le=3)
    assigned_therapist_ids: Optional[List[str]] = Field(None)
    disciplines: Optional[List[str]] = Field(None)
    deadline_date: Optional[str] = Field(None)
    content: Optional[Dict[str, Any]] = Field(None, description="Report content")

    @validator('status')
    def validate_status(cls, v):
        if v and v not in ['pending', 'in_progress', 'completed', 'overdue', 'cancelled']:
            raise ValueError('Invalid status')
        return v


class AIContentGenerationRequest(BaseModel):
    """Request model for AI content generation"""
    content_type: str = Field(..., description="Type of content to generate (medical_history, treatment_summary)")
    disciplines: Optional[List[str]] = Field(None, description="Specific disciplines to include")
    force_regenerate: bool = Field(default=False, description="Force regeneration even if cached content exists")


class ReportDashboardResponse(BaseModel):
    """Response model for dashboard data"""
    pending_reports: List[ReportResponse]
    overdue_reports: List[ReportResponse]
    completed_reports: List[ReportResponse]
    report_counts: Dict[str, int]
    urgent_notifications: List[Dict[str, Any]]


class DisciplineRecommendation(BaseModel):
    """Model for discipline recommendations with booking stats"""
    discipline: str
    bookings_count: int
    last_seen: str


class TherapistSuggestion(BaseModel):
    """Model for therapist suggestions with patient booking history"""
    user_id: str
    name: str
    disciplines: List[str]
    bookings_count_with_patient: int
    last_seen: str


class WizardOptionsResponse(BaseModel):
    """Response model for wizard options"""
    allowed_report_types: List[str]
    priorities: List[Dict[str, Any]]
    user_role: str
    user_defaults: Dict[str, Any]
    recommended_disciplines: Optional[List[DisciplineRecommendation]] = None
    suggested_therapists: Optional[List[TherapistSuggestion]] = None
    other_therapists: Optional[List[Dict[str, Any]]] = None


class TherapistCompletionRequest(BaseModel):
    """Request model for marking therapist portion as complete"""
    completion_notes: Optional[str] = Field(None, description="Optional notes about completion")


class TherapistCompletionResponse(BaseModel):
    """Response model for therapist completion"""
    id: int
    report_id: int
    therapist_id: str
    completed_at: str
    completion_notes: Optional[str]


class ReportCompletionStatusResponse(BaseModel):
    """Response model for report completion status"""
    report_id: int
    total_assigned_therapists: int
    completed_therapists: int
    completion_percentage: float
    is_fully_completed: bool
    assigned_therapist_ids: List[str]
    therapist_completions: List[TherapistCompletionResponse]


class ReportController:
    """Controller for report management operations"""

    @staticmethod
    async def create_report(request: ReportCreateRequest, current_user: dict = Depends(require_auth)):
        """
        Create a new report
        
        Args:
            request: Report creation data
            current_user: Authenticated user info
        
        Returns:
            Created report data
        """
        try:
            # Create the report
            report_id = create_report(
                patient_id=request.patient_id,
                report_type=request.report_type,
                template_id=request.template_id,
                title=request.title,
                assigned_therapist_ids=request.assigned_therapist_ids,
                disciplines=request.disciplines,
                requested_by_user_id=current_user.get('user_id'),
                deadline_date=request.deadline_date,
                priority=request.priority
            )

            # Create notifications for assigned therapists
            for therapist_id in request.assigned_therapist_ids:
                if therapist_id != current_user.get('user_id'):  # Don't notify self
                    create_report_notification(
                        report_id=report_id,
                        user_id=therapist_id,
                        notification_type='request',
                        message=f'New report assigned: {request.title}'
                    )

            # Generate AI content if requested
            if request.generate_ai_content:
                try:
                    await ReportController._generate_ai_content_for_report(
                        report_id, request.patient_id, request.disciplines
                    )
                except Exception as e:
                    # Log error but don't fail report creation
                    print(f"AI content generation failed: {e}")

            # Return the created report
            report = get_report_by_id(report_id)
            
            # Parse JSON fields back to arrays for the response model
            if isinstance(report['assigned_therapist_ids'], str):
                report['assigned_therapist_ids'] = json.loads(report['assigned_therapist_ids'])
            if isinstance(report['disciplines'], str):
                report['disciplines'] = json.loads(report['disciplines'])
            if isinstance(report['ai_generated_sections'], str) and report['ai_generated_sections']:
                report['ai_generated_sections'] = json.loads(report['ai_generated_sections'])
            if isinstance(report['content'], str) and report['content']:
                report['content'] = json.loads(report['content'])
                
            return ReportResponse(**report)

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to create report: {str(e)}")

    @staticmethod
    def get_report(report_id: int = Path(..., description="Report ID"), 
                   current_user: dict = Depends(require_auth)):
        """
        Get a specific report by ID
        
        Args:
            report_id: ID of the report to retrieve
            current_user: Authenticated user info
        
        Returns:
            Report data
        """
        report = get_report_by_id(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        # Check permissions - user must be assigned to report or be the requester
        user_id = current_user.get('user_id')
        assigned_therapists = json.loads(report['assigned_therapist_ids']) if isinstance(report['assigned_therapist_ids'], str) else report['assigned_therapist_ids']
        
        if (user_id not in assigned_therapists and 
            report['requested_by_user_id'] != user_id and
            current_user.get('role') not in ['admin', 'manager']):
            raise HTTPException(status_code=403, detail="Access denied")

        return ReportResponse(**report)

    @staticmethod
    def update_report(report_id: int = Path(..., description="Report ID"),
                      request: ReportUpdateRequest = None,
                      current_user: dict = Depends(require_auth)):
        """
        Update an existing report
        
        Args:
            report_id: ID of the report to update
            request: Update data
            current_user: Authenticated user info
        
        Returns:
            Updated report data
        """
        # Check if report exists and user has permission
        existing_report = get_report_by_id(report_id)
        if not existing_report:
            raise HTTPException(status_code=404, detail="Report not found")

        user_id = current_user.get('user_id')
        assigned_therapists = json.loads(existing_report['assigned_therapist_ids']) if isinstance(existing_report['assigned_therapist_ids'], str) else existing_report['assigned_therapist_ids']
        
        if (user_id not in assigned_therapists and 
            existing_report['requested_by_user_id'] != user_id and
            current_user.get('role') not in ['admin', 'manager']):
            raise HTTPException(status_code=403, detail="Access denied")

        try:
            # Build update data
            update_data = {}
            if request.title:
                update_data['title'] = request.title
            if request.priority:
                update_data['priority'] = request.priority
            if request.assigned_therapist_ids:
                update_data['assigned_therapist_ids'] = json.dumps(request.assigned_therapist_ids)
            if request.disciplines:
                update_data['disciplines'] = json.dumps(request.disciplines)
            if request.deadline_date:
                update_data['deadline_date'] = request.deadline_date
            if request.content:
                update_data['content'] = json.dumps(request.content)

            # Update the report
            success = update_report_status(
                report_id=report_id,
                status=request.status or existing_report['status'],
                content=update_data,
                updated_by_user_id=user_id
            )

            if not success:
                raise HTTPException(status_code=400, detail="Failed to update report")

            # Get updated report
            updated_report = get_report_by_id(report_id)
            return ReportResponse(**updated_report)

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to update report: {str(e)}")

    @staticmethod
    def delete_report(report_id: int = Path(..., description="Report ID"),
                     current_user: dict = Depends(require_auth)):
        """
        Delete a report
        
        Args:
            report_id: ID of the report to delete
            current_user: Authenticated user info
        
        Returns:
            Success message
        """
        # Check if report exists and user has permission
        existing_report = get_report_by_id(report_id)
        if not existing_report:
            raise HTTPException(status_code=404, detail="Report not found")

        user_id = current_user.get('user_id')
        user_role = current_user.get('role', 'user')
        
        assigned_therapists = json.loads(existing_report['assigned_therapist_ids']) if isinstance(existing_report['assigned_therapist_ids'], str) else existing_report['assigned_therapist_ids']
        
        # Check permissions - allow deletion if:
        # 1. User is admin/manager
        # 2. User created the report
        # 3. User is assigned to the report
        is_admin = user_role.lower() in ['admin', 'manager'] 
        is_creator = existing_report.get('requested_by_user_id') == user_id
        is_assigned = user_id in assigned_therapists if assigned_therapists else False
        
        if not (is_admin or is_creator or is_assigned):
            raise HTTPException(status_code=403, detail="Access denied. You don't have permission to delete this report.")

        try:
            # Import the database function to avoid naming conflict
            from modules.database import delete_report as db_delete_report
            
            # Delete the report
            success = db_delete_report(report_id)
            
            if not success:
                raise HTTPException(status_code=400, detail="Failed to delete report")
            
            return {"message": "Report deleted successfully", "report_id": report_id}

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to delete report: {str(e)}")

    @staticmethod
    def reassign_report(report_id: int, request: dict, current_user: dict):
        """
        Reassign a report to different therapists
        
        Args:
            report_id: ID of the report to reassign
            request: Dict containing assigned_therapist_ids
            current_user: Authenticated user info
        
        Returns:
            Success response with updated report info
        """
        try:
            # Check if report exists
            report = get_report_by_id(report_id)
            if not report:
                raise HTTPException(status_code=404, detail="Report not found")
            
            # Get the new therapist IDs
            new_therapist_ids = request.get('assigned_therapist_ids', [])
            if not new_therapist_ids:
                raise HTTPException(status_code=400, detail="At least one therapist must be assigned")
            
            # Convert to JSON string for storage
            therapist_ids_json = json.dumps(new_therapist_ids)
            
            # Update the report with new therapist assignments
            execute_query(
                "UPDATE reports SET assigned_therapist_ids = ?, updated_at = datetime('now') WHERE id = ?",
                (therapist_ids_json, report_id)
            )
            
            # Clear all existing therapist completions since we're reassigning
            execute_query(
                "DELETE FROM report_therapist_completions WHERE report_id = ?",
                (report_id,)
            )
            
            # Reset report status to pending (completion triggers will handle status updates)
            execute_query(
                "UPDATE reports SET status = 'pending', completed_at = NULL WHERE id = ?",
                (report_id,)
            )
            
            # Also update the structured template instance if it exists
            # Get the template_instance_id from the report
            template_instance_id = report.get('template_instance_id')
            if template_instance_id:
                execute_query(
                    "UPDATE structured_template_instances SET assigned_therapist_ids = ?, updated_at = datetime('now') WHERE id = ?",
                    (therapist_ids_json, template_instance_id)
                )
            
            return {
                "success": True,
                "message": "Report reassigned successfully",
                "report_id": report_id,
                "assigned_therapist_ids": new_therapist_ids
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to reassign report: {str(e)}")

    @staticmethod
    def get_user_reports(status: Optional[str] = Query(None, description="Filter by status"),
                        limit: int = Query(50, ge=1, le=100, description="Maximum reports to return"),
                        current_user: dict = Depends(require_auth)):
        """
        Get reports for the current user
        
        Args:
            status: Optional status filter
            limit: Maximum number of reports to return
            current_user: Authenticated user info
        
        Returns:
            List of user's reports
        """
        try:
            user_id = current_user.get('user_id')
            reports = get_reports_for_user(user_id=user_id, status=status, limit=limit)
            
            # Enrich reports with additional fields for frontend compatibility
            enriched_reports = []
            for report in reports:
                # Create a copy of the report data
                enriched_report = dict(report)
                
                # Add patient name
                enriched_report['patient'] = get_patient_name(report['patient_id'])
                
                # Add assigned therapist names
                enriched_report['assignedTo'] = get_therapist_names(report['assigned_therapist_ids'])
                
                # Add created date alias
                enriched_report['createdDate'] = report.get('created_at')
                
                # Add description from title or report type
                enriched_report['description'] = f"{report['report_type'].title()} report for {enriched_report['patient']}"
                
                enriched_reports.append(ReportResponse(**enriched_report))
            
            return enriched_reports

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to retrieve reports: {str(e)}")

    @staticmethod
    def get_dashboard_data(current_user: dict = Depends(require_auth)):
        """
        Get dashboard data for the current user
        
        Args:
            current_user: Authenticated user info
        
        Returns:
            Dashboard data including pending, overdue, and completed reports
        """
        try:
            user_id = current_user.get('user_id')
            
            # Get reports by status
            pending_reports = get_reports_for_user(user_id, status='pending')
            in_progress_reports = get_reports_for_user(user_id, status='in_progress')
            completed_reports = get_reports_for_user(user_id, status='completed', limit=10)
            
            # Identify overdue reports
            overdue_reports = []
            current_date = datetime.now().date()
            
            for report in pending_reports + in_progress_reports:
                if report.get('deadline_date'):
                    deadline = datetime.strptime(report['deadline_date'], '%Y-%m-%d').date()
                    if deadline < current_date:
                        overdue_reports.append(report)

            # Create report counts
            report_counts = {
                'pending': len(pending_reports),
                'in_progress': len(in_progress_reports),
                'completed': len(completed_reports),
                'overdue': len(overdue_reports)
            }

            # Convert reports to proper format for response models
            def format_report_for_response(report_data):
                """Convert database report to response format"""
                return {
                    'id': report_data['id'],
                    'patient_id': report_data['patient_id'],
                    'report_type': report_data['report_type'],
                    'template_id': report_data['template_id'],
                    'template_name': report_data.get('template_name'),
                    'title': report_data['title'],
                    'status': report_data['status'],
                    'priority': report_data['priority'],
                    'assigned_therapist_ids': report_data['assigned_therapist_ids'],
                    'disciplines': report_data['disciplines'],
                    'requested_by_user_id': report_data.get('requested_by_user_id'),
                    'deadline_date': report_data.get('deadline_date'),
                    'ai_generated_sections': report_data.get('ai_generated_sections') or {},
                    'content': report_data.get('content') or {},
                    'created_at': report_data.get('created_at'),
                    'updated_at': report_data.get('updated_at'),
                    'completed_at': report_data.get('completed_at')
                }
            
            return ReportDashboardResponse(
                pending_reports=[ReportResponse(**format_report_for_response(r)) for r in pending_reports],
                overdue_reports=[ReportResponse(**format_report_for_response(r)) for r in overdue_reports],
                completed_reports=[ReportResponse(**format_report_for_response(r)) for r in completed_reports],
                report_counts=report_counts,
                urgent_notifications=[]  # Placeholder for notifications
            )

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to retrieve dashboard data: {str(e)}")

    @staticmethod
    async def generate_ai_content(report_id: int = Path(..., description="Report ID"),
                                  request: AIContentGenerationRequest = None,
                                  current_user: dict = Depends(require_auth)):
        """
        Generate AI content for a report
        
        Args:
            report_id: ID of the report
            request: AI generation parameters
            current_user: Authenticated user info
        
        Returns:
            Generated AI content
        """
        # Check if report exists and user has permission
        report = get_report_by_id(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        user_id = current_user.get('user_id')
        assigned_therapists = json.loads(report['assigned_therapist_ids']) if isinstance(report['assigned_therapist_ids'], str) else report['assigned_therapist_ids']
        
        if (user_id not in assigned_therapists and 
            report['requested_by_user_id'] != user_id and
            current_user.get('role') not in ['admin', 'manager']):
            raise HTTPException(status_code=403, detail="Access denied")

        try:
            if request.content_type == 'medical_history':
                result = await ai_generator.generate_medical_history(
                    patient_id=report['patient_id'],
                    disciplines=request.disciplines or json.loads(report['disciplines']),
                    force_regenerate=request.force_regenerate
                )
            elif request.content_type == 'treatment_summary':
                result = await ai_generator.generate_treatment_summary(
                    patient_id=report['patient_id'],
                    disciplines=request.disciplines or json.loads(report['disciplines']),
                    force_regenerate=request.force_regenerate
                )
            else:
                raise HTTPException(status_code=400, detail="Invalid content type")

            return {
                "content": result['content'],
                "source": result['source'],
                "generated_at": datetime.now().isoformat(),
                "tokens_used": result.get('tokens_used', 0)
            }

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to generate AI content: {str(e)}")

    @staticmethod
    async def _generate_ai_content_for_report(report_id: int, patient_id: str, disciplines: List[str]):
        """
        Internal method to generate AI content for a report
        
        Args:
            report_id: Report ID
            patient_id: Patient ID
            disciplines: List of disciplines
        """
        try:
            # Generate medical history
            medical_history = await ai_generator.generate_medical_history(
                patient_id=patient_id,
                disciplines=disciplines
            )
            
            # Generate treatment summary
            treatment_summary = await ai_generator.generate_treatment_summary(
                patient_id=patient_id,
                disciplines=disciplines
            )
            
            # Update report with AI-generated sections
            ai_sections = {
                'medical_history': {
                    'content': medical_history['content'],
                    'generated_at': datetime.now().isoformat(),
                    'source': medical_history['source']
                },
                'treatment_summary': {
                    'content': treatment_summary['content'],
                    'generated_at': datetime.now().isoformat(),
                    'source': treatment_summary['source']
                }
            }
            
            update_report_status(
                report_id=report_id,
                status='in_progress',  # Move to in_progress after AI content generation
                content={'ai_generated_sections': json.dumps(ai_sections)}
            )

        except Exception as e:
            print(f"Failed to generate AI content for report {report_id}: {e}")
            # Don't raise - this is called during report creation

    @staticmethod
    def get_wizard_options(
        patient_id: Optional[str] = Query(None, description="Patient ID for recommendations"),
        disciplines: Optional[str] = Query(None, description="Comma-separated disciplines for therapist filtering"),
        current_user: dict = Depends(require_auth)
    ):
        """
        Get wizard options with booking-based recommendations
        
        Args:
            patient_id: Optional patient ID for personalized recommendations
            disciplines: Optional comma-separated disciplines for therapist filtering
            current_user: Authenticated user info
        
        Returns:
            Wizard options with recommendations
        """
        try:
            user_role = current_user.get('role', 'therapist')
            user_id = current_user.get('user_id')
            
            # Base options available to all users
            allowed_report_types = ["discharge", "progress", "insurance", "outcome_summary", "assessment"]
            priorities = [
                {"value": 1, "label": "Low", "color": "#6b7280"},
                {"value": 2, "label": "Medium", "color": "#f59e0b"}, 
                {"value": 3, "label": "High", "color": "#ef4444"}
            ]
            
            # User defaults based on role
            user_defaults = {
                "priority": 2,  # Medium by default
                "assigned_therapist_ids": [user_id] if user_role == 'therapist' else []
            }
            
            response_data = {
                "allowed_report_types": allowed_report_types,
                "priorities": priorities,
                "user_role": user_role,
                "user_defaults": user_defaults
            }
            
            # Add patient-specific recommendations if patient_id provided
            if patient_id:
                recommended_disciplines = ReportController._get_recommended_disciplines(patient_id)
                response_data["recommended_disciplines"] = recommended_disciplines
                
                # Add therapist suggestions if disciplines are also provided
                if disciplines:
                    discipline_list = [d.strip() for d in disciplines.split(',') if d.strip()]
                    suggested_therapists, other_therapists = ReportController._get_therapist_suggestions(
                        patient_id, discipline_list
                    )
                    response_data["suggested_therapists"] = suggested_therapists
                    response_data["other_therapists"] = other_therapists
            
            return WizardOptionsResponse(**response_data)
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to get wizard options: {str(e)}")

    @staticmethod
    def _get_recommended_disciplines(patient_id: str) -> List[DisciplineRecommendation]:
        """Get discipline recommendations based on patient booking history"""
        query = """
            SELECT 
                b.profession as discipline,
                COUNT(*) as bookings_count,
                MAX(b.date) as last_seen
            FROM bookings b
            WHERE b.patient_id = ? AND b.profession IS NOT NULL
            GROUP BY b.profession
            ORDER BY bookings_count DESC, last_seen DESC
        """
        
        try:
            results = execute_query(query, (patient_id,), fetch='all')
            recommendations = []
            
            for row in results:
                row_dict = dict(row)
                recommendations.append(DisciplineRecommendation(
                    discipline=row_dict['discipline'],
                    bookings_count=row_dict['bookings_count'],
                    last_seen=row_dict['last_seen']
                ))
            
            return recommendations
            
        except Exception as e:
            print(f"Error getting discipline recommendations: {e}")
            return []

    @staticmethod
    def _get_therapist_suggestions(
        patient_id: str, 
        selected_disciplines: List[str]
    ) -> Tuple[List[TherapistSuggestion], List[Dict[str, Any]]]:
        """Get therapist suggestions based on patient booking history and selected disciplines"""
        
        if not selected_disciplines:
            return [], []
        
        # Map frontend discipline names to database profession names
        discipline_mapping = {
            'physiotherapy': 'Physiotherapy',
            'occupational_therapy': 'Occupational Therapy', 
            'speech_therapy': 'Speech Therapy',
            'psychology': 'Psychology'
        }
        
        # Convert frontend discipline names to database profession names
        db_disciplines = []
        for discipline in selected_disciplines:
            mapped_discipline = discipline_mapping.get(discipline.lower())
            if mapped_discipline:
                db_disciplines.append(mapped_discipline)
            else:
                # Fallback: try to convert directly (e.g., 'physiotherapy' -> 'Physiotherapy')
                db_disciplines.append(discipline.replace('_', ' ').title())
        
        # Get therapists who have treated this patient in the selected disciplines
        discipline_placeholders = ','.join(['?' for _ in db_disciplines])
        suggested_query = """
            SELECT 
                t.id as user_id,
                t.name,
                t.profession as primary_discipline,
                COUNT(b.id) as bookings_count_with_patient,
                MAX(b.date) as last_seen
            FROM therapists t
            JOIN bookings b ON t.id = b.therapist
            WHERE b.patient_id = ? 
                AND t.profession IN ({})
            GROUP BY t.id, t.name, t.profession
            ORDER BY bookings_count_with_patient DESC, last_seen DESC
        """.format(discipline_placeholders)
        
        # Get other therapists in selected disciplines who haven't treated this patient
        other_query = """
            SELECT 
                t.id as user_id,
                t.name,
                t.profession as primary_discipline
            FROM therapists t
            WHERE t.profession IN ({})
                AND t.id NOT IN (
                    SELECT DISTINCT b.therapist 
                    FROM bookings b 
                    WHERE b.patient_id = ? AND b.therapist IS NOT NULL
                )
            ORDER BY t.name
        """.format(discipline_placeholders)
        
        try:
            # Get suggested therapists (those with history)
            suggested_results = execute_query(
                suggested_query, 
                (patient_id, *db_disciplines), 
                fetch='all'
            )
            
            suggested_therapists = []
            for row in suggested_results:
                row_dict = dict(row)
                suggested_therapists.append(TherapistSuggestion(
                    user_id=str(row_dict['user_id']),
                    name=row_dict['name'],
                    disciplines=[row_dict['primary_discipline']],  # Simplified for now
                    bookings_count_with_patient=row_dict['bookings_count_with_patient'],
                    last_seen=row_dict['last_seen']
                ))
            
            # Get other available therapists
            other_results = execute_query(
                other_query,
                (*db_disciplines, patient_id),
                fetch='all'
            )
            
            other_therapists = []
            for row in other_results:
                row_dict = dict(row)
                other_therapists.append({
                    "user_id": str(row_dict['user_id']),
                    "name": row_dict['name'],
                    "disciplines": [row_dict['primary_discipline']],
                    "bookings_count_with_patient": 0,
                    "last_seen": None
                })
            
            return suggested_therapists, other_therapists
            
        except Exception as e:
            print(f"Error getting therapist suggestions: {e}")
            return [], []

    @staticmethod
    async def complete_therapist_portion(
        report_id: int = Path(..., description="Report ID"),
        request: TherapistCompletionRequest = None,
        current_user: dict = Depends(require_auth)
    ):
        """
        Mark the current therapist's portion of the report as complete
        
        Args:
            report_id: ID of the report
            request: Optional completion notes
            current_user: Authenticated user info
        
        Returns:
            Completion status and updated report information
        """
        try:
            # Check if report exists
            report = get_report_by_id(report_id)
            if not report:
                raise HTTPException(status_code=404, detail="Report not found")
            
            therapist_id = str(current_user.get('user_id', current_user.get('username', 'unknown')))
            
            # Check if therapist is assigned to this report
            assigned_therapist_ids = json.loads(report.get('assigned_therapist_ids', '[]'))
            if therapist_id not in assigned_therapist_ids:
                raise HTTPException(status_code=403, detail="You are not assigned to this report")
            
            # Check if therapist has already completed their portion
            existing_completion = execute_query(
                "SELECT id FROM report_therapist_completions WHERE report_id = ? AND therapist_id = ?",
                (report_id, therapist_id),
                fetch='one'
            )
            
            if existing_completion:
                raise HTTPException(status_code=400, detail="You have already completed your portion of this report")
            
            # Insert therapist completion
            completion_notes = request.completion_notes if request else None
            completion_id = execute_query(
                """
                INSERT INTO report_therapist_completions (report_id, therapist_id, completion_notes)
                VALUES (?, ?, ?)
                """,
                (report_id, therapist_id, completion_notes),
                fetch='lastrowid'
            )
            
            # Get updated completion status
            completion_status = await ReportController.get_report_completion_status(report_id)
            
            return {
                "success": True,
                "message": "Your portion of the report has been marked as complete",
                "completion_id": completion_id,
                "completion_status": completion_status
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to complete therapist portion: {str(e)}")
    
    @staticmethod
    async def get_report_completion_status(report_id: int):
        """
        Get detailed completion status for a report
        
        Args:
            report_id: ID of the report
        
        Returns:
            Detailed completion status including individual therapist completions
        """
        try:
            # Get report info
            report = get_report_by_id(report_id)
            if not report:
                raise HTTPException(status_code=404, detail="Report not found")
            
            # Get assigned therapist IDs
            assigned_therapist_ids = json.loads(report.get('assigned_therapist_ids', '[]'))
            total_assigned = len(assigned_therapist_ids)
            
            # Get therapist completions
            completions = execute_query(
                """
                SELECT id, report_id, therapist_id, completed_at, completion_notes
                FROM report_therapist_completions
                WHERE report_id = ?
                ORDER BY completed_at DESC
                """,
                (report_id,),
                fetch='all'
            )
            
            completed_count = len(completions) if completions else 0
            completion_percentage = (completed_count / total_assigned * 100) if total_assigned > 0 else 0
            is_fully_completed = completed_count >= total_assigned
            
            # Format therapist completions
            therapist_completions = []
            if completions:
                for completion in completions:
                    therapist_completions.append(TherapistCompletionResponse(
                        id=completion['id'],
                        report_id=completion['report_id'],
                        therapist_id=completion['therapist_id'],
                        completed_at=completion['completed_at'],
                        completion_notes=completion['completion_notes']
                    ))
            
            return ReportCompletionStatusResponse(
                report_id=report_id,
                total_assigned_therapists=total_assigned,
                completed_therapists=completed_count,
                completion_percentage=completion_percentage,
                is_fully_completed=is_fully_completed,
                assigned_therapist_ids=assigned_therapist_ids,
                therapist_completions=therapist_completions
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get completion status: {str(e)}")
    
    @staticmethod
    async def remove_therapist_completion(
        report_id: int = Path(..., description="Report ID"),
        current_user: dict = Depends(require_auth)
    ):
        """
        Remove the current therapist's completion (undo completion)
        
        Args:
            report_id: ID of the report
            current_user: Authenticated user info
        
        Returns:
            Updated completion status
        """
        try:
            # Check if report exists
            report = get_report_by_id(report_id)
            if not report:
                raise HTTPException(status_code=404, detail="Report not found")
            
            therapist_id = str(current_user.get('user_id', current_user.get('username', 'unknown')))
            
            # Check if therapist has completed their portion
            existing_completion = execute_query(
                "SELECT id FROM report_therapist_completions WHERE report_id = ? AND therapist_id = ?",
                (report_id, therapist_id),
                fetch='one'
            )
            
            if not existing_completion:
                raise HTTPException(status_code=400, detail="You have not completed your portion of this report")
            
            # Remove therapist completion
            execute_query(
                "DELETE FROM report_therapist_completions WHERE report_id = ? AND therapist_id = ?",
                (report_id, therapist_id),
                fetch='none'
            )
            
            # Get updated completion status
            completion_status = await ReportController.get_report_completion_status(report_id)
            
            return {
                "success": True,
                "message": "Your completion has been removed",
                "completion_status": completion_status
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to remove therapist completion: {str(e)}")


# Additional utility functions
def get_report_templates_endpoint():
    """Get available report templates"""
    try:
        templates = get_report_templates()
        return templates
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to retrieve templates: {str(e)}")


def get_patient_data_for_report(patient_id: str, disciplines: Optional[List[str]] = None):
    """Get patient data summary for report generation"""
    try:
        return get_patient_data_summary(patient_id, disciplines)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to retrieve patient data: {str(e)}")


# Template Management Functions for Task 5.2+

class TemplateCreateRequest(BaseModel):
    """Request model for creating custom templates"""
    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    description: Optional[str] = Field(None, description="Template description") 
    template_type: str = Field(..., description="Template type")
    practice_id: Optional[str] = Field(None, description="Practice ID (None for system templates)")
    fields_schema: Dict[str, Any] = Field(..., description="JSON schema defining template fields")
    section_order: List[str] = Field(..., description="Ordered list of section names")
    
    @validator('template_type')
    def validate_template_type(cls, v):
        valid_types = ['discharge', 'progress', 'insurance', 'outcome_summary', 'assessment', 'custom']
        if v not in valid_types:
            raise ValueError(f'Template type must be one of: {valid_types}')
        return v


class TemplateUpdateRequest(BaseModel):
    """Request model for updating templates"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    fields_schema: Optional[Dict[str, Any]] = None
    section_order: Optional[List[str]] = None
    is_active: Optional[bool] = None


def create_custom_template(name: str, description: Optional[str], template_type: str,
                          practice_id: Optional[str], fields_schema: Dict[str, Any],
                          section_order: List[str], created_by_user_id: str) -> Dict[str, Any]:
    """
    Create a new custom template with validation
    
    Args:
        name: Template name
        description: Template description
        template_type: Type of template
        practice_id: Practice ID (None for system templates)
        fields_schema: JSON schema defining fields
        section_order: Ordered list of sections
        created_by_user_id: User creating the template
    
    Returns:
        Dictionary with success status and template_id or error
    """
    try:
        # Validate field schema first
        validation_result = validate_template_schema(fields_schema)
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": f"Invalid field schema: {', '.join(validation_result['errors'])}"
            }
        
        # Sanitize input data
        sanitized_data = sanitize_template_data({
            "name": name,
            "description": description,
            "fields_schema": fields_schema
        })
        
        # Create template in database
        template_id = create_report_template(
            name=sanitized_data["name"],
            description=sanitized_data["description"], 
            template_type=template_type,
            practice_id=practice_id,
            fields_schema=json.dumps(sanitized_data["fields_schema"]),
            section_order=json.dumps(section_order),
            created_by_user_id=created_by_user_id
        )
        
        return {
            "success": True,
            "template_id": template_id
        }
        
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            return {
                "success": False,
                "error": "A template with this name already exists"
            }
        return {
            "success": False,
            "error": f"Failed to create template: {str(e)}"
        }


def update_template(template_id: int, updates: Dict[str, Any], 
                   updated_by_user_id: str) -> Dict[str, Any]:
    """
    Update an existing template
    
    Args:
        template_id: ID of template to update
        updates: Dictionary of fields to update
        updated_by_user_id: User performing the update
    
    Returns:
        Dictionary with success status
    """
    try:
        # Check if template exists
        template = get_template_by_id(template_id)
        if not template:
            return {"success": False, "error": "Template not found"}
        
        # Validate fields_schema if being updated
        if "fields_schema" in updates:
            validation_result = validate_template_schema(updates["fields_schema"])
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"Invalid field schema: {', '.join(validation_result['errors'])}"
                }
        
        # Sanitize update data
        if any(field in updates for field in ["name", "description", "fields_schema"]):
            updates = sanitize_template_data(updates)
        
        # Create new version before updating
        version_result = create_template_version(
            template_id=template_id,
            changes=updates,
            change_summary="Template updated",
            created_by_user_id=updated_by_user_id
        )
        
        # Update template in database
        update_report_template(template_id, updates)
        
        return {"success": True, "version_number": version_result.get("version_number")}
        
    except Exception as e:
        return {"success": False, "error": f"Failed to update template: {str(e)}"}


def get_template_by_id(template_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a specific template by ID
    
    Args:
        template_id: Template ID
    
    Returns:
        Template data or None if not found
    """
    try:
        query = "SELECT * FROM report_templates WHERE id = ?"
        result = execute_query(query, (template_id,), fetch='one')
        
        if result:
            template = dict(result)
            template['fields_schema'] = json.loads(template['fields_schema'])
            template['section_order'] = json.loads(template['section_order'])
            return template
        return None
        
    except Exception as e:
        print(f"Error getting template by ID: {e}")
        return None


def validate_template_schema(fields_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate template field schema
    
    Args:
        fields_schema: Dictionary defining template fields
    
    Returns:
        Dictionary with validation result and any errors
    """
    errors = []
    supported_types = [
        "auto_populated", "ai_generated_paragraph", "rich_text", "structured_table",
        "structured_fields", "digital_signature", "multiple_choice", "checklist",
        "dynamic_sections", "multi_signature", "paragraph", "date_picker", "number_input"
    ]
    
    for field_name, field_config in fields_schema.items():
        # Check if field has required properties
        if not isinstance(field_config, dict):
            errors.append(f"Field '{field_name}' must be an object")
            continue
            
        if "type" not in field_config:
            errors.append(f"Field '{field_name}' missing required 'type' property")
            continue
            
        if "label" not in field_config:
            errors.append(f"Field '{field_name}' missing required 'label' property")
            continue
        
        # Check field type
        field_type = field_config["type"]
        if field_type not in supported_types:
            errors.append(f"Field '{field_name}' has unsupported type '{field_type}'")
            continue
        
        # Type-specific validation
        if field_type == "multiple_choice":
            if "options" not in field_config or not isinstance(field_config["options"], list):
                errors.append(f"Multiple choice field '{field_name}' must have 'options' array")
        
        elif field_type == "structured_table":
            if "columns" not in field_config or not isinstance(field_config["columns"], list):
                errors.append(f"Structured table field '{field_name}' must have 'columns' array")
        
        elif field_type == "ai_generated_paragraph":
            if "ai_source" not in field_config:
                errors.append(f"AI generated field '{field_name}' must have 'ai_source' property")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def preview_template(template_data: Dict[str, Any], 
                    sample_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generate HTML preview of a template
    
    Args:
        template_data: Template structure
        sample_data: Optional sample data to populate fields
    
    Returns:
        Dictionary with preview HTML and success status
    """
    try:
        fields_schema = template_data["fields_schema"]
        section_order = template_data["section_order"]
        
        html_parts = ["<div class='template-preview'>"]
        html_parts.append(f"<h2>{template_data['name']}</h2>")
        
        for section_name in section_order:
            if section_name not in fields_schema:
                continue
                
            field_config = fields_schema[section_name]
            field_label = field_config["label"]
            field_type = field_config["type"]
            
            html_parts.append(f"<div class='field-section' data-field='{section_name}'>")
            html_parts.append(f"<label class='field-label'>{field_label}")
            if field_config.get("required"):
                html_parts.append(" <span class='required'>*</span>")
            html_parts.append("</label>")
            
            # Generate field HTML based on type
            if field_type == "auto_populated":
                if sample_data and section_name in sample_data:
                    data = sample_data[section_name]
                    html_parts.append("<div class='auto-populated-field'>")
                    for key, value in data.items():
                        html_parts.append(f"<p><strong>{key.replace('_', ' ').title()}:</strong> {value}</p>")
                    html_parts.append("</div>")
                else:
                    html_parts.append("<div class='auto-populated-field'>[Auto-populated patient data]</div>")
            
            elif field_type == "rich_text":
                placeholder = field_config.get("placeholder", "Enter text...")
                html_parts.append(f"<div class='rich-text-field'>[Rich text editor: {placeholder}]</div>")
            
            elif field_type == "multiple_choice":
                options = field_config.get("options", [])
                html_parts.append("<select class='multiple-choice-field'>")
                for option in options:
                    html_parts.append(f"<option value='{option}'>{option}</option>")
                html_parts.append("</select>")
            
            elif field_type == "digital_signature":
                html_parts.append("<div class='signature-field'>[Digital signature pad]</div>")
            
            elif field_type == "structured_table":
                columns = field_config.get("columns", [])
                html_parts.append("<table class='structured-table'>")
                html_parts.append("<thead><tr>")
                for col in columns:
                    html_parts.append(f"<th>{col.replace('_', ' ').title()}</th>")
                html_parts.append("</tr></thead>")
                html_parts.append("<tbody><tr>")
                for col in columns:
                    html_parts.append("<td>[Sample data]</td>")
                html_parts.append("</tr></tbody></table>")
            
            else:
                html_parts.append(f"<div class='field-placeholder'>[{field_type} field]</div>")
            
            html_parts.append("</div>")
        
        html_parts.append("</div>")
        
        return {
            "success": True,
            "preview_html": "\n".join(html_parts)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to generate preview: {str(e)}"
        }


def get_practice_templates(practice_id: str, current_user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get templates available to a specific practice
    
    Args:
        practice_id: Practice identifier
        current_user_id: ID of requesting user (for permission checks)
    
    Returns:
        List of available templates or error dict
    """
    try:
        # Check user permissions if provided
        if current_user_id and not user_has_practice_access(current_user_id, practice_id):
            return {"success": False, "error": "Permission denied"}
        
        # Get practice-specific and system templates
        templates = get_report_templates(practice_id=practice_id)
        
        return templates
        
    except Exception as e:
        return {"success": False, "error": f"Failed to retrieve templates: {str(e)}"}


def sanitize_template_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize template data to prevent XSS and other security issues
    
    Args:
        data: Raw template data
    
    Returns:
        Sanitized data
    """
    import re
    
    def sanitize_string(text: str) -> str:
        if not isinstance(text, str):
            return text
        # Remove script tags and dangerous HTML
        text = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]*(?:javascript|vbscript|onload|onerror)[^>]*>', '', text, flags=re.IGNORECASE)
        return text.strip()
    
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_string(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_template_data(value)
        else:
            sanitized[key] = value
    
    return sanitized


# Database helper functions for template management

def create_report_template(name: str, description: Optional[str], template_type: str,
                          practice_id: Optional[str], fields_schema: str,
                          section_order: str, created_by_user_id: str) -> int:
    """Create a new report template in database"""
    query = """
        INSERT INTO report_templates 
        (name, description, template_type, practice_id, fields_schema, section_order, created_by_user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    
    result = execute_query(query, (
        name, description, template_type, practice_id, 
        fields_schema, section_order, created_by_user_id
    ), fetch='none')
    
    # Get the last inserted ID
    query_id = "SELECT last_insert_rowid()"
    id_result = execute_query(query_id, (), fetch='one')
    return id_result[0] if id_result else None


def update_report_template(template_id: int, updates: Dict[str, Any]):
    """Update an existing report template"""
    set_clauses = []
    params = []
    
    for field, value in updates.items():
        if field in ['name', 'description', 'template_type', 'is_active']:
            set_clauses.append(f"{field} = ?")
            params.append(value)
        elif field in ['fields_schema', 'section_order']:
            set_clauses.append(f"{field} = ?")
            params.append(json.dumps(value) if isinstance(value, (dict, list)) else value)
    
    if set_clauses:
        params.append(template_id)
        query = f"UPDATE report_templates SET {', '.join(set_clauses)} WHERE id = ?"
        execute_query(query, tuple(params), fetch='none')


# Permission and access control functions

def user_has_permission(user_id: str, permission: str, practice_id: Optional[str] = None) -> bool:
    """Check if user has specific permission"""
    # Get user role
    user_role = get_user_role(user_id)
    
    # Admin and managers can create/edit templates
    if permission in ['create_template', 'edit_template']:
        return user_role in ['admin', 'manager']
    
    # Only admins and managers can approve templates
    if permission == 'approve_template':
        return user_role in ['admin', 'manager']
    
    return False


def user_has_practice_access(user_id: str, practice_id: str) -> bool:
    """Check if user has access to specific practice"""
    query = "SELECT practice_id FROM users WHERE id = ?"
    result = execute_query(query, (user_id,), fetch='one')
    
    if result:
        user_practice = result[0] if result[0] else None
        return user_practice == practice_id or user_practice is None  # None = admin access
    
    return False


def get_user_role(user_id: str) -> str:
    """Get user role for permission checking"""
    query = "SELECT role FROM users WHERE id = ?"
    result = execute_query(query, (user_id,), fetch='one')
    
    if result:
        return result[0]
    
    return 'therapist'  # Default role


def check_template_permission(user_id: str, action: str) -> bool:
    """Check if user can perform template action"""
    role = get_user_role(user_id)
    
    permission_matrix = {
        'admin': ['create', 'edit', 'approve', 'delete'],
        'manager': ['create', 'edit', 'approve'],
        'therapist': []  # Read-only
    }
    
    return action in permission_matrix.get(role, [])


# Template versioning functions for Task 5.6

def create_template_version(template_id: int, changes: Dict[str, Any],
                           change_summary: str, created_by_user_id: str) -> Dict[str, Any]:
    """
    Create a new version of a template
    
    Args:
        template_id: ID of template being versioned
        changes: Dictionary of changes being made
        change_summary: Summary of changes
        created_by_user_id: User creating the version
    
    Returns:
        Dictionary with success status and version number
    """
    try:
        # Get current version number
        query = "SELECT version FROM report_templates WHERE id = ?"
        result = execute_query(query, (template_id,), fetch='one')
        
        if not result:
            return {"success": False, "error": "Template not found"}
        
        current_version = result[0]
        new_version = current_version + 1
        
        # Store the version in a template_versions table (if exists)
        # For now, just increment the version number on the main template
        update_query = "UPDATE report_templates SET version = ? WHERE id = ?"
        execute_query(update_query, (new_version, template_id), fetch='none')
        
        return {
            "success": True,
            "version_number": new_version
        }
        
    except Exception as e:
        return {"success": False, "error": f"Failed to create version: {str(e)}"}


def approve_template(template_id: int, version_number: int, approved_by_user_id: str,
                    approval_notes: str) -> Dict[str, Any]:
    """
    Approve a template version for production use
    
    Args:
        template_id: Template ID
        version_number: Version to approve
        approved_by_user_id: User approving the template
        approval_notes: Notes about the approval
    
    Returns:
        Dictionary with success status
    """
    try:
        # Check if user has approval permission
        if not check_template_permission(approved_by_user_id, 'approve'):
            return {"success": False, "error": "Permission denied"}
        
        # Mark template as approved
        query = """
            UPDATE report_templates 
            SET is_active = 1, updated_at = datetime('now')
            WHERE id = ? AND version = ?
        """
        
        execute_query(query, (template_id, version_number), fetch='none')
        
        return {"success": True}
        
    except Exception as e:
        return {"success": False, "error": f"Failed to approve template: {str(e)}"}


def get_template_history(template_id: int) -> List[Dict[str, Any]]:
    """
    Get version history for a template
    
    Args:
        template_id: Template ID
    
    Returns:
        List of version history records
    """
    try:
        # For now, return basic version info from the main template
        # In a full implementation, this would query a template_versions table
        query = """
            SELECT version as version_number, created_at, updated_at, created_by_user_id
            FROM report_templates 
            WHERE id = ?
        """
        
        result = execute_query(query, (template_id,), fetch='one')
        
        if result:
            return [{
                "version_number": result[0],
                "created_at": result[1],
                "created_by": result[3],
                "change_summary": "Template version"
            }]
        
        return []
        
    except Exception as e:
        print(f"Error getting template history: {e}")
        return []


def revert_template_version(template_id: int, target_version: int, 
                           reverted_by_user_id: str, revert_reason: str) -> Dict[str, Any]:
    """
    Revert template to a previous version
    
    Args:
        template_id: Template ID
        target_version: Version to revert to
        reverted_by_user_id: User performing the revert
        revert_reason: Reason for reverting
    
    Returns:
        Dictionary with success status
    """
    try:
        # Check if user has edit permission
        if not check_template_permission(reverted_by_user_id, 'edit'):
            return {"success": False, "error": "Permission denied"}
        
        # For now, just update the version number
        # In a full implementation, this would restore the actual template data
        query = "UPDATE report_templates SET version = ? WHERE id = ?"
        execute_query(query, (target_version, template_id), fetch='none')
        
        return {"success": True}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# Create global instance
report_controller = ReportController()
