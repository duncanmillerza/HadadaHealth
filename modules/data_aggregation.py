"""
Data Aggregation Layer for AI Report Generation

Provides comprehensive data collection and aggregation from multiple sources
including treatment notes, outcome measures, assessments, and patient records
for AI-powered report generation.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass

from modules.database import get_db_connection, execute_query


@dataclass
class PatientDataSummary:
    """Comprehensive patient data summary for AI processing"""
    patient_id: str
    demographics: Dict[str, Any]
    treatment_notes: List[Dict[str, Any]]
    outcome_measures: List[Dict[str, Any]]
    assessments: List[Dict[str, Any]]
    appointments: List[Dict[str, Any]]
    billing_info: List[Dict[str, Any]]
    disciplines_involved: List[str]
    date_range: tuple
    data_completeness: Dict[str, bool]


class DataAggregationService:
    """Service for aggregating patient data from multiple sources"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def aggregate_patient_data(self, patient_id: str, disciplines: Optional[List[str]] = None,
                             date_range: Optional[tuple] = None, include_billing: bool = False) -> PatientDataSummary:
        """
        Aggregate comprehensive patient data for AI processing
        
        Args:
            patient_id: Patient identifier
            disciplines: Optional list of disciplines to filter
            date_range: Optional tuple of (start_date, end_date)
            include_billing: Whether to include billing information
        
        Returns:
            PatientDataSummary object with aggregated data
        """
        self.logger.info(f"Aggregating data for patient {patient_id}")
        
        # Set default date range if not provided
        if not date_range:
            end_date = datetime.now().date().isoformat()
            start_date = (datetime.now() - timedelta(days=365)).date().isoformat()
            date_range = (start_date, end_date)
        
        # Aggregate data from all sources
        demographics = self._get_patient_demographics(patient_id)
        treatment_notes = self._get_treatment_notes(patient_id, disciplines, date_range)
        outcome_measures = self._get_outcome_measures(patient_id, disciplines, date_range)
        assessments = self._get_assessments(patient_id, disciplines, date_range)
        appointments = self._get_appointments(patient_id, disciplines, date_range)
        billing_info = self._get_billing_info(patient_id, date_range) if include_billing else []
        
        # Determine disciplines involved
        disciplines_involved = self._extract_disciplines(treatment_notes, outcome_measures, assessments)
        
        # Assess data completeness
        data_completeness = self._assess_data_completeness(
            demographics, treatment_notes, outcome_measures, assessments, appointments
        )
        
        return PatientDataSummary(
            patient_id=patient_id,
            demographics=demographics,
            treatment_notes=treatment_notes,
            outcome_measures=outcome_measures,
            assessments=assessments,
            appointments=appointments,
            billing_info=billing_info,
            disciplines_involved=disciplines_involved,
            date_range=date_range,
            data_completeness=data_completeness
        )
    
    def _get_patient_demographics(self, patient_id: str) -> Dict[str, Any]:
        """Get patient demographic information"""
        try:
            # Try different patient table variations that might exist
            queries = [
                "SELECT * FROM patients WHERE patient_id = ?",
                "SELECT * FROM patients WHERE id = ?",
                "SELECT * FROM bookings WHERE patient_id = ? LIMIT 1"  # Fallback to booking data
            ]
            
            for query in queries:
                try:
                    result = execute_query(query, (patient_id,), fetch='one')
                    if result:
                        demo_data = dict(result)
                        # Standardize field names
                        standardized = {
                            'patient_id': demo_data.get('patient_id', patient_id),
                            'name': demo_data.get('name', demo_data.get('patient_name', 'Unknown')),
                            'date_of_birth': demo_data.get('date_of_birth', demo_data.get('dob')),
                            'gender': demo_data.get('gender'),
                            'phone': demo_data.get('phone', demo_data.get('phone_number')),
                            'email': demo_data.get('email'),
                            'address': demo_data.get('address'),
                            'medical_aid': demo_data.get('medical_aid', demo_data.get('medical_aid_name')),
                            'emergency_contact': demo_data.get('emergency_contact'),
                            'referring_doctor': demo_data.get('referring_doctor'),
                            'primary_diagnosis': demo_data.get('primary_diagnosis')
                        }
                        # Remove None values
                        return {k: v for k, v in standardized.items() if v is not None}
                except Exception:
                    continue
            
            self.logger.warning(f"No patient demographics found for {patient_id}")
            return {'patient_id': patient_id, 'name': 'Unknown', 'data_source': 'none'}
            
        except Exception as e:
            self.logger.error(f"Error getting patient demographics for {patient_id}: {e}")
            return {'patient_id': patient_id, 'name': 'Unknown', 'data_source': 'error'}
    
    def _get_treatment_notes(self, patient_id: str, disciplines: Optional[List[str]] = None, 
                           date_range: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Get treatment notes data"""
        try:
            self.logger.info(f"Getting treatment notes for patient {patient_id}")
            print(f"DEBUG: _get_treatment_notes called for patient {patient_id}")
            base_query = """
            SELECT appointment_date, start_time, profession, therapist_name,
                   subjective_findings, objective_findings, treatment, plan, 
                   duration, supplementary_note as notes
            FROM treatment_notes
            WHERE patient_id = ?
            """
            params = [patient_id]
            
            # Add date range filter - convert DD/MM/YYYY to YYYY-MM-DD for comparison
            if date_range:
                base_query += """ AND date(substr(appointment_date, 7, 4) || '-' || 
                                 substr(appointment_date, 4, 2) || '-' || 
                                 substr(appointment_date, 1, 2)) >= ? 
                                 AND date(substr(appointment_date, 7, 4) || '-' || 
                                 substr(appointment_date, 4, 2) || '-' || 
                                 substr(appointment_date, 1, 2)) <= ?"""
                params.extend(date_range)
            
            # Add discipline filter
            if disciplines:
                placeholders = ', '.join(['?' for _ in disciplines])
                base_query += f" AND profession IN ({placeholders})"
                params.extend(disciplines)
            
            base_query += " ORDER BY appointment_date DESC, start_time DESC"
            
            print(f"DEBUG: Treatment notes query: {base_query}")
            print(f"DEBUG: Treatment notes params: {tuple(params)}")
            
            results = execute_query(base_query, tuple(params), fetch='all')
            print(f"DEBUG: Treatment notes query returned {len(results) if results else 0} rows")
            
            if not results:
                print(f"DEBUG: No treatment notes found for patient {patient_id}")
                return []
            
            notes = []
            for row in results:
                note = {
                    "appointment_date": row[0],
                    "start_time": row[1],
                    "profession": row[2],
                    "therapist_name": row[3],
                    "subjective_findings": row[4] or "",
                    "objective_findings": row[5] or "",
                    "treatment": row[6] or "",
                    "plan": row[7] or "",
                    "duration": row[8],
                    "notes": row[9] if len(row) > 9 else "",
                    "session_type": row[10] if len(row) > 10 else "treatment"
                }
                notes.append(note)
            
            print(f"DEBUG: Successfully processed {len(notes)} treatment notes for patient {patient_id}")
            self.logger.info(f"Retrieved {len(notes)} treatment notes for patient {patient_id}")
            return notes
            
        except Exception as e:
            print(f"DEBUG: Error retrieving treatment notes for {patient_id}: {e}")
            self.logger.warning(f"Could not retrieve treatment notes for {patient_id}: {e}")
            return []
    
    def _get_outcome_measures(self, patient_id: str, disciplines: Optional[List[str]] = None,
                            date_range: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Get outcome measures data"""
        try:
            # Check if outcome_measures table exists
            table_check = execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name='outcome_measures'")
            if not table_check:
                self.logger.warning(f"Outcome measures table does not exist")
                return []
                
            base_query = """
            SELECT measure_name, score, date_recorded, notes, profession, 
                   baseline_score, interpretation, assessor_name
            FROM outcome_measures
            WHERE patient_id = ?
            """
            params = [patient_id]
            
            # Add date range filter
            if date_range:
                base_query += " AND date_recorded >= ? AND date_recorded <= ?"
                params.extend(date_range)
            
            # Add discipline filter
            if disciplines:
                placeholders = ', '.join(['?' for _ in disciplines])
                base_query += f" AND profession IN ({placeholders})"
                params.extend(disciplines)
            
            base_query += " ORDER BY date_recorded DESC, measure_name"
            
            results = execute_query(base_query, tuple(params), fetch='all')
            if not results:
                return []
            
            measures = []
            for row in results:
                measure = {
                    "measure_name": row[0],
                    "score": row[1],
                    "date_recorded": row[2],
                    "notes": row[3] or "",
                    "profession": row[4],
                    "baseline_score": row[5] if len(row) > 5 else None,
                    "interpretation": row[6] if len(row) > 6 else "",
                    "assessor_name": row[7] if len(row) > 7 else ""
                }
                
                # Calculate improvement if baseline exists
                if measure["baseline_score"] and measure["score"]:
                    try:
                        improvement = float(measure["score"]) - float(measure["baseline_score"])
                        measure["improvement"] = improvement
                        measure["improvement_percentage"] = (improvement / float(measure["baseline_score"]) * 100) if float(measure["baseline_score"]) != 0 else 0
                    except (ValueError, TypeError):
                        measure["improvement"] = None
                
                measures.append(measure)
            
            self.logger.info(f"Retrieved {len(measures)} outcome measures for {patient_id}")
            return measures
            
        except Exception as e:
            self.logger.warning(f"Could not retrieve outcome measures for {patient_id}: {e}")
            return []
    
    def _get_assessments(self, patient_id: str, disciplines: Optional[List[str]] = None,
                        date_range: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Get assessment data"""
        try:
            # Check if assessments table exists
            table_check = execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name='assessments'")
            if not table_check:
                self.logger.warning(f"Assessments table does not exist")
                return []
                
            base_query = """
            SELECT assessment_type, assessment_date, findings, recommendations, 
                   profession, assessor_name, assessment_status
            FROM assessments
            WHERE patient_id = ?
            """
            params = [patient_id]
            
            # Add date range filter
            if date_range:
                base_query += " AND assessment_date >= ? AND assessment_date <= ?"
                params.extend(date_range)
            
            # Add discipline filter
            if disciplines:
                placeholders = ', '.join(['?' for _ in disciplines])
                base_query += f" AND profession IN ({placeholders})"
                params.extend(disciplines)
            
            base_query += " ORDER BY assessment_date DESC"
            
            results = execute_query(base_query, tuple(params), fetch='all')
            if not results:
                return []
            
            assessments = []
            for row in results:
                assessment = {
                    "assessment_type": row[0],
                    "assessment_date": row[1],
                    "findings": row[2] or "",
                    "recommendations": row[3] or "",
                    "profession": row[4],
                    "assessor_name": row[5] or "",
                    "assessment_status": row[6] if len(row) > 6 else "completed"
                }
                assessments.append(assessment)
            
            self.logger.info(f"Retrieved {len(assessments)} assessments for {patient_id}")
            return assessments
            
        except Exception as e:
            self.logger.warning(f"Could not retrieve assessments for {patient_id}: {e}")
            return []
    
    def _get_appointments(self, patient_id: str, disciplines: Optional[List[str]] = None,
                         date_range: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Get appointment history"""
        try:
            base_query = """
            SELECT date as appointment_date, time as start_time, therapist, 
                   profession, name as appointment_type, notes
            FROM bookings
            WHERE patient_id = ?
            """
            params = [patient_id]
            
            # Add date range filter
            if date_range:
                base_query += " AND appointment_date >= ? AND appointment_date <= ?"
                params.extend(date_range)
            
            # Add discipline filter
            if disciplines:
                placeholders = ', '.join(['?' for _ in disciplines])
                base_query += f" AND profession IN ({placeholders})"
                params.extend(disciplines)
            
            base_query += " ORDER BY appointment_date DESC, start_time DESC"
            
            results = execute_query(base_query, tuple(params), fetch='all')
            if not results:
                return []
            
            appointments = []
            for row in results:
                appointment = {
                    "appointment_date": row[0],
                    "start_time": row[1],
                    "end_time": row[2],
                    "therapist_name": row[3],
                    "profession": row[4],
                    "appointment_status": row[5] if len(row) > 5 else "unknown",
                    "appointment_type": row[6] if len(row) > 6 else "standard",
                    "notes": row[7] if len(row) > 7 else ""
                }
                appointments.append(appointment)
            
            self.logger.info(f"Retrieved {len(appointments)} appointments for {patient_id}")
            return appointments
            
        except Exception as e:
            self.logger.warning(f"Could not retrieve appointments for {patient_id}: {e}")
            return []
    
    def _get_billing_info(self, patient_id: str, date_range: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Get billing information"""
        try:
            base_query = """
            SELECT billing_date, service_code, service_description, amount, 
                   billed_to, payment_status, invoice_number
            FROM billing
            WHERE patient_id = ?
            """
            params = [patient_id]
            
            # Add date range filter
            if date_range:
                base_query += " AND billing_date >= ? AND billing_date <= ?"
                params.extend(date_range)
            
            base_query += " ORDER BY billing_date DESC"
            
            results = execute_query(base_query, tuple(params), fetch='all')
            if not results:
                return []
            
            billing_records = []
            for row in results:
                record = {
                    "billing_date": row[0],
                    "service_code": row[1],
                    "service_description": row[2],
                    "amount": row[3],
                    "billed_to": row[4],
                    "payment_status": row[5] if len(row) > 5 else "unknown",
                    "invoice_number": row[6] if len(row) > 6 else ""
                }
                billing_records.append(record)
            
            self.logger.info(f"Retrieved {len(billing_records)} billing records for {patient_id}")
            return billing_records
            
        except Exception as e:
            self.logger.warning(f"Could not retrieve billing info for {patient_id}: {e}")
            return []
    
    def _extract_disciplines(self, treatment_notes: List[Dict], outcome_measures: List[Dict], 
                           assessments: List[Dict]) -> List[str]:
        """Extract unique disciplines involved in patient care"""
        disciplines = set()
        
        # Extract from treatment notes
        for note in treatment_notes:
            if note.get('profession'):
                disciplines.add(note['profession'])
        
        # Extract from outcome measures
        for measure in outcome_measures:
            if measure.get('profession'):
                disciplines.add(measure['profession'])
        
        # Extract from assessments
        for assessment in assessments:
            if assessment.get('profession'):
                disciplines.add(assessment['profession'])
        
        return sorted(list(disciplines))
    
    def _assess_data_completeness(self, demographics: Dict, treatment_notes: List, 
                                outcome_measures: List, assessments: List, 
                                appointments: List) -> Dict[str, bool]:
        """Assess completeness of patient data"""
        return {
            'has_demographics': bool(demographics.get('name', '').strip()),
            'has_treatment_notes': len(treatment_notes) > 0,
            'has_outcome_measures': len(outcome_measures) > 0,
            'has_assessments': len(assessments) > 0,
            'has_appointments': len(appointments) > 0,
            'has_contact_info': bool(demographics.get('phone') or demographics.get('email')),
            'has_medical_aid': bool(demographics.get('medical_aid')),
            'has_recent_data': self._has_recent_data(treatment_notes, outcome_measures)
        }
    
    def _has_recent_data(self, treatment_notes: List, outcome_measures: List) -> bool:
        """Check if patient has data from the last 30 days"""
        cutoff_date = (datetime.now() - timedelta(days=30)).date().isoformat()
        
        # Check treatment notes
        for note in treatment_notes:
            if note.get('appointment_date', '') >= cutoff_date:
                return True
        
        # Check outcome measures
        for measure in outcome_measures:
            if measure.get('date_recorded', '') >= cutoff_date:
                return True
        
        return False
    
    def get_cross_disciplinary_summary(self, patient_id: str, date_range: Optional[tuple] = None) -> Dict[str, Any]:
        """
        Get cross-disciplinary summary for multi-disciplinary reports
        
        Args:
            patient_id: Patient identifier
            date_range: Optional date range filter
        
        Returns:
            Dictionary with cross-disciplinary insights
        """
        data_summary = self.aggregate_patient_data(patient_id, date_range=date_range)
        
        # Group data by discipline
        discipline_data = {}
        for discipline in data_summary.disciplines_involved:
            discipline_notes = [note for note in data_summary.treatment_notes if note.get('profession') == discipline]
            discipline_measures = [measure for measure in data_summary.outcome_measures if measure.get('profession') == discipline]
            discipline_assessments = [assessment for assessment in data_summary.assessments if assessment.get('profession') == discipline]
            
            discipline_data[discipline] = {
                'treatment_sessions': len(discipline_notes),
                'latest_session': discipline_notes[0]['appointment_date'] if discipline_notes else None,
                'outcome_measures_count': len(discipline_measures),
                'assessments_count': len(discipline_assessments),
                'key_findings': self._extract_key_findings(discipline_notes, discipline_measures, discipline_assessments)
            }
        
        return {
            'patient_id': patient_id,
            'disciplines_involved': data_summary.disciplines_involved,
            'total_sessions': len(data_summary.treatment_notes),
            'date_range': data_summary.date_range,
            'discipline_breakdown': discipline_data,
            'collaborative_indicators': self._identify_collaborative_elements(data_summary)
        }
    
    def _extract_key_findings(self, notes: List[Dict], measures: List[Dict], assessments: List[Dict]) -> List[str]:
        """Extract key findings from discipline data"""
        findings = []
        
        # Extract from recent notes
        if notes:
            latest_note = notes[0]
            if latest_note.get('objective_findings'):
                findings.append(f"Latest findings: {latest_note['objective_findings'][:100]}...")
        
        # Extract from outcome measures
        if measures:
            recent_measures = measures[:3]  # Last 3 measures
            for measure in recent_measures:
                if measure.get('interpretation'):
                    findings.append(f"{measure['measure_name']}: {measure['interpretation']}")
        
        return findings[:5]  # Limit to 5 key findings
    
    def _identify_collaborative_elements(self, data_summary: PatientDataSummary) -> Dict[str, Any]:
        """Identify elements indicating collaborative care"""
        collaborative_elements = {
            'multi_disciplinary': len(data_summary.disciplines_involved) > 1,
            'concurrent_care': False,
            'shared_goals': False,
            'communication_indicators': []
        }
        
        # Check for concurrent care (treatments within same time periods)
        if len(data_summary.disciplines_involved) > 1:
            # Group notes by date to find concurrent care
            date_disciplines = {}
            for note in data_summary.treatment_notes:
                date = note.get('appointment_date')
                if date:
                    if date not in date_disciplines:
                        date_disciplines[date] = set()
                    date_disciplines[date].add(note.get('profession'))
            
            # Check for overlapping care periods
            concurrent_dates = [date for date, disciplines in date_disciplines.items() if len(disciplines) > 1]
            collaborative_elements['concurrent_care'] = len(concurrent_dates) > 0
            collaborative_elements['concurrent_care_dates'] = len(concurrent_dates)
        
        return collaborative_elements


# Global instance
data_aggregator = DataAggregationService()


# Convenience functions
def get_patient_data_summary(patient_id: str, disciplines: Optional[List[str]] = None,
                           date_range: Optional[tuple] = None, include_billing: bool = False) -> PatientDataSummary:
    """Get comprehensive patient data summary"""
    return data_aggregator.aggregate_patient_data(patient_id, disciplines, date_range, include_billing)


def get_cross_disciplinary_summary(patient_id: str, date_range: Optional[tuple] = None) -> Dict[str, Any]:
    """Get cross-disciplinary care summary"""
    return data_aggregator.get_cross_disciplinary_summary(patient_id, date_range)