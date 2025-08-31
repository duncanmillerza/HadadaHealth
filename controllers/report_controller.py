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
    get_report_templates, create_report_notification, get_db_connection, execute_query
)
from modules.auth import require_auth
from modules.ai_content import ai_generator
from modules.data_aggregation import get_patient_data_summary


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
            return [ReportResponse(**report) for report in reports]

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