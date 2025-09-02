"""
Report Business Logic Module

Provides business logic for report workflows, validation, permissions,
and automated report generation processes.
"""
import json
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum

from modules.database import (
    create_report, get_report_by_id, get_reports_for_user, update_report_status,
    get_report_templates, create_report_notification, get_user_notifications,
    mark_notification_read, get_patient_disciplines
)
from modules.ai_content import ai_generator
from modules.data_aggregation import get_patient_data_summary


class ReportStatus(Enum):
    """Enumeration of report statuses"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"  
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class ReportPriority(Enum):
    """Enumeration of report priorities"""
    LOW = 1
    NORMAL = 2
    HIGH = 3


class ReportWorkflowService:
    """Service for managing report workflows and business logic"""

    @staticmethod
    def create_manager_initiated_report(
        patient_id: str,
        report_type: str,
        template_id: int,
        title: str,
        assigned_therapist_ids: List[str],
        disciplines: List[str],
        manager_user_id: str,
        deadline_date: Optional[str] = None,
        priority: int = 2,
        auto_generate_ai: bool = True
    ) -> int:
        """
        Create a manager-initiated report with proper workflow
        
        Args:
            patient_id: Patient identifier
            report_type: Type of report
            template_id: Template to use
            title: Report title
            assigned_therapist_ids: List of therapist IDs to assign
            disciplines: List of disciplines involved
            manager_user_id: Manager who initiated the request
            deadline_date: Optional deadline in YYYY-MM-DD format
            priority: Priority level (1-3)
            auto_generate_ai: Whether to automatically generate AI content
        
        Returns:
            Created report ID
        """
        # Validate deadline if provided
        if deadline_date:
            deadline = datetime.strptime(deadline_date, '%Y-%m-%d')
            if deadline.date() <= datetime.now().date():
                raise ValueError("Deadline must be in the future")

        # Create the report
        report_id = create_report(
            patient_id=patient_id,
            report_type=report_type,
            template_id=template_id,
            title=title,
            assigned_therapist_ids=assigned_therapist_ids,
            disciplines=disciplines,
            requested_by_user_id=manager_user_id,
            deadline_date=deadline_date,
            priority=priority
        )

        # Send notifications to assigned therapists
        for therapist_id in assigned_therapist_ids:
            if therapist_id != manager_user_id:  # Don't notify self
                priority_text = ReportWorkflowService._get_priority_text(priority)
                deadline_text = f" (Due: {deadline_date})" if deadline_date else ""
                
                create_report_notification(
                    report_id=report_id,
                    user_id=therapist_id,
                    notification_type='request',
                    message=f'{priority_text} report assigned: "{title}"{deadline_text}'
                )

        # Auto-generate AI content if requested
        if auto_generate_ai:
            try:
                ReportWorkflowService._trigger_ai_generation(report_id, patient_id, disciplines)
            except Exception as e:
                # Log error but don't fail report creation
                print(f"AI content generation failed for report {report_id}: {e}")

        return report_id

    @staticmethod
    def create_therapist_initiated_report(
        patient_id: str,
        report_type: str,
        template_id: int,
        title: str,
        therapist_user_id: str,
        disciplines: Optional[List[str]] = None,
        deadline_date: Optional[str] = None,
        priority: int = 1
    ) -> int:
        """
        Create a therapist-initiated report
        
        Args:
            patient_id: Patient identifier
            report_type: Type of report
            template_id: Template to use
            title: Report title
            therapist_user_id: Therapist creating the report
            disciplines: Optional disciplines (will auto-detect if not provided)
            deadline_date: Optional self-imposed deadline
            priority: Priority level (typically lower for self-initiated)
        
        Returns:
            Created report ID
        """
        # Auto-detect disciplines if not provided
        if not disciplines:
            # Try to determine disciplines from patient history
            patient_disciplines = get_patient_disciplines(patient_id)
            disciplines = [d['discipline'] for d in patient_disciplines] if patient_disciplines else ['general']

        # Create the report (therapist assigns to themselves)
        report_id = create_report(
            patient_id=patient_id,
            report_type=report_type,
            template_id=template_id,
            title=title,
            assigned_therapist_ids=[therapist_user_id],
            disciplines=disciplines,
            requested_by_user_id=None,  # Self-initiated
            deadline_date=deadline_date,
            priority=priority
        )

        # Immediately move to in_progress status (therapist can start working)
        update_report_status(
            report_id=report_id,
            status=ReportStatus.IN_PROGRESS.value,
            updated_by_user_id=therapist_user_id
        )

        return report_id

    @staticmethod
    def update_report_workflow(
        report_id: int,
        new_status: str,
        user_id: str,
        content_updates: Optional[Dict[str, Any]] = None,
        notify_stakeholders: bool = True
    ) -> bool:
        """
        Update report status with proper workflow notifications
        
        Args:
            report_id: Report ID
            new_status: New status to set
            user_id: User making the update
            content_updates: Optional content updates
            notify_stakeholders: Whether to send notifications
        
        Returns:
            True if successful, False otherwise
        """
        # Get current report
        report = get_report_by_id(report_id)
        if not report:
            raise ValueError("Report not found")

        old_status = report['status']
        
        # Update the report
        success = update_report_status(
            report_id=report_id,
            status=new_status,
            content=content_updates,
            user_id=user_id
        )

        if success and notify_stakeholders and old_status != new_status:
            ReportWorkflowService._send_status_change_notifications(
                report_id, report, old_status, new_status, user_id
            )

        return success

    @staticmethod
    def get_overdue_reports(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all overdue reports for a user or system-wide
        
        Args:
            user_id: Optional user ID to filter by
        
        Returns:
            List of overdue reports
        """
        if user_id:
            # Get user's reports
            pending_reports = get_reports_for_user(user_id, status=ReportStatus.PENDING.value)
            in_progress_reports = get_reports_for_user(user_id, status=ReportStatus.IN_PROGRESS.value)
            all_reports = pending_reports + in_progress_reports
        else:
            # This would need a system-wide query - simplified for now
            return []

        overdue_reports = []
        current_date = datetime.now().date()

        for report in all_reports:
            if report.get('deadline_date'):
                deadline = datetime.strptime(report['deadline_date'], '%Y-%m-%d').date()
                if deadline < current_date:
                    # Calculate days overdue
                    days_overdue = (current_date - deadline).days
                    report['days_overdue'] = days_overdue
                    overdue_reports.append(report)

        return sorted(overdue_reports, key=lambda x: x['days_overdue'], reverse=True)

    @staticmethod
    def get_urgent_reports(user_id: str) -> List[Dict[str, Any]]:
        """
        Get urgent reports (high priority or due soon)
        
        Args:
            user_id: User ID to get reports for
        
        Returns:
            List of urgent reports
        """
        reports = get_reports_for_user(user_id, limit=100)
        urgent_reports = []
        current_date = datetime.now().date()

        for report in reports:
            if report['status'] not in [ReportStatus.COMPLETED.value, ReportStatus.CANCELLED.value]:
                is_urgent = False
                urgency_reason = []

                # High priority
                if report['priority'] == ReportPriority.HIGH.value:
                    is_urgent = True
                    urgency_reason.append("High priority")

                # Due within 2 days
                if report.get('deadline_date'):
                    deadline = datetime.strptime(report['deadline_date'], '%Y-%m-%d').date()
                    days_until_due = (deadline - current_date).days
                    
                    if days_until_due < 0:
                        is_urgent = True
                        urgency_reason.append(f"Overdue by {abs(days_until_due)} days")
                    elif days_until_due <= 2:
                        is_urgent = True
                        urgency_reason.append(f"Due in {days_until_due} days")

                if is_urgent:
                    report['urgency_reason'] = urgency_reason
                    urgent_reports.append(report)

        return urgent_reports

    @staticmethod
    def get_report_analytics(user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get report analytics for dashboard
        
        Args:
            user_id: Optional user ID to filter by
        
        Returns:
            Analytics data
        """
        if not user_id:
            return {}

        # Get reports by status
        pending = get_reports_for_user(user_id, status=ReportStatus.PENDING.value)
        in_progress = get_reports_for_user(user_id, status=ReportStatus.IN_PROGRESS.value)
        completed = get_reports_for_user(user_id, status=ReportStatus.COMPLETED.value, limit=50)

        # Calculate completion rates
        total_reports = len(pending) + len(in_progress) + len(completed)
        completion_rate = (len(completed) / total_reports * 100) if total_reports > 0 else 0

        # Get overdue count
        overdue = ReportWorkflowService.get_overdue_reports(user_id)
        
        # Calculate average completion time for recent reports
        recent_completed = [r for r in completed if r.get('completed_at')][:20]
        avg_completion_days = 0
        
        if recent_completed:
            total_days = 0
            count = 0
            for report in recent_completed:
                if report.get('created_at') and report.get('completed_at'):
                    created = datetime.fromisoformat(report['created_at'].replace('Z', '+00:00'))
                    completed_at = datetime.fromisoformat(report['completed_at'].replace('Z', '+00:00'))
                    days = (completed_at - created).days
                    total_days += days
                    count += 1
            
            if count > 0:
                avg_completion_days = total_days / count

        return {
            'total_reports': total_reports,
            'pending_count': len(pending),
            'in_progress_count': len(in_progress),
            'completed_count': len(completed),
            'overdue_count': len(overdue),
            'completion_rate': round(completion_rate, 1),
            'average_completion_days': round(avg_completion_days, 1),
            'urgent_reports': len(ReportWorkflowService.get_urgent_reports(user_id))
        }

    @staticmethod
    def validate_report_permissions(report_id: int, user_id: str, required_action: str) -> Tuple[bool, str]:
        """
        Validate user permissions for report actions
        
        Args:
            report_id: Report ID
            user_id: User ID
            required_action: Action being attempted (read, write, delete)
        
        Returns:
            Tuple of (is_allowed, error_message)
        """
        report = get_report_by_id(report_id)
        if not report:
            return False, "Report not found"

        assigned_therapists = json.loads(report['assigned_therapist_ids']) if isinstance(report['assigned_therapist_ids'], str) else report['assigned_therapist_ids']
        
        # Check if user is assigned to report
        is_assigned = user_id in assigned_therapists
        is_requester = report['requested_by_user_id'] == user_id

        if required_action == 'read':
            # Can read if assigned, requester, or admin/manager
            if is_assigned or is_requester:
                return True, ""
            else:
                return False, "Access denied: not assigned to this report"

        elif required_action == 'write':
            # Can write if assigned to report
            if is_assigned:
                return True, ""
            else:
                return False, "Access denied: not assigned to this report"

        elif required_action == 'delete':
            # Only requester or admin can delete
            if is_requester:
                return True, ""
            else:
                return False, "Access denied: only requester can delete report"

        return False, "Invalid action"

    @staticmethod
    def _get_priority_text(priority: int) -> str:
        """Get human-readable priority text"""
        priority_map = {
            1: "Low priority",
            2: "Normal priority", 
            3: "HIGH PRIORITY"
        }
        return priority_map.get(priority, "Normal priority")

    @staticmethod
    def _send_status_change_notifications(
        report_id: int,
        report: Dict[str, Any],
        old_status: str,
        new_status: str,
        user_id: str
    ):
        """Send notifications when report status changes"""
        try:
            assigned_therapists = json.loads(report['assigned_therapist_ids']) if isinstance(report['assigned_therapist_ids'], str) else report['assigned_therapist_ids']
            requester = report.get('requested_by_user_id')

            # Determine notification message
            status_messages = {
                ReportStatus.IN_PROGRESS.value: "started working on",
                ReportStatus.COMPLETED.value: "completed",
                ReportStatus.CANCELLED.value: "cancelled"
            }

            action = status_messages.get(new_status, f"changed status to {new_status}")
            message = f'Report "{report["title"]}" has been {action}'

            # Notify stakeholders
            recipients = set()
            if requester and requester != user_id:
                recipients.add(requester)
            
            for therapist_id in assigned_therapists:
                if therapist_id != user_id:
                    recipients.add(therapist_id)

            for recipient in recipients:
                create_report_notification(
                    report_id=report_id,
                    user_id=recipient,
                    notification_type='reminder',
                    message=message
                )

        except Exception as e:
            print(f"Failed to send status change notifications: {e}")

    @staticmethod
    def _trigger_ai_generation(report_id: int, patient_id: str, disciplines: List[str]):
        """
        Trigger AI content generation (async wrapper for background processing)
        
        Args:
            report_id: Report ID
            patient_id: Patient ID  
            disciplines: List of disciplines
        """
        # This would typically be queued for background processing
        # For now, it's a placeholder for the async AI generation
        print(f"AI content generation triggered for report {report_id}")


class ReportTemplateService:
    """Service for managing report templates"""

    @staticmethod
    def get_available_templates(practice_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get available report templates for a practice
        
        Args:
            practice_id: Optional practice ID for practice-specific templates
        
        Returns:
            List of available templates
        """
        return get_report_templates(practice_id=practice_id)

    @staticmethod
    def validate_template_fields(template_id: int, content: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate report content against template schema
        
        Args:
            template_id: Template ID
            content: Report content to validate
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        templates = get_report_templates()
        template = next((t for t in templates if t['id'] == template_id), None)
        
        if not template:
            return False, ["Template not found"]

        try:
            fields_schema = json.loads(template['fields_schema']) if isinstance(template['fields_schema'], str) else template['fields_schema']
        except json.JSONDecodeError:
            return False, ["Invalid template schema"]

        errors = []
        
        # Validate required fields
        for field in fields_schema:
            field_id = field.get('id')
            if field.get('required', False) and field_id not in content:
                errors.append(f"Required field '{field.get('label', field_id)}' is missing")

        # Validate field types and constraints
        for field_id, value in content.items():
            field_def = next((f for f in fields_schema if f.get('id') == field_id), None)
            if field_def:
                field_type = field_def.get('type')
                
                if field_type == 'number' and not isinstance(value, (int, float)):
                    errors.append(f"Field '{field_def.get('label', field_id)}' must be a number")
                elif field_type == 'date' and not isinstance(value, str):
                    errors.append(f"Field '{field_def.get('label', field_id)}' must be a date string")
                # Add more field type validations as needed

        return len(errors) == 0, errors


class ReportNotificationService:
    """Service for managing report-related notifications"""

    @staticmethod
    def get_user_report_notifications(user_id: str, unread_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get report notifications for a user
        
        Args:
            user_id: User ID
            unread_only: Whether to return only unread notifications
        
        Returns:
            List of notifications
        """
        is_read_filter = False if unread_only else None
        return get_user_notifications(user_id, is_read=is_read_filter)

    @staticmethod
    def mark_notification_as_read(notification_id: int) -> bool:
        """
        Mark a notification as read
        
        Args:
            notification_id: Notification ID
        
        Returns:
            True if successful, False otherwise
        """
        return mark_notification_read(notification_id)

    @staticmethod
    def send_deadline_reminders():
        """
        Send reminders for reports approaching deadlines (background task)
        This would typically be run as a scheduled task
        """
        # This is a placeholder for a background task that would:
        # 1. Query for reports due within X days
        # 2. Send reminder notifications
        # 3. Update overdue status for past-due reports
        print("Deadline reminder task triggered")


# Export main services
__all__ = [
    'ReportWorkflowService',
    'ReportTemplateService', 
    'ReportNotificationService',
    'ReportStatus',
    'ReportPriority'
]