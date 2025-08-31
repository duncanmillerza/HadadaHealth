"""
AI Content Generation Module for HadadaHealth

Provides AI-powered content generation for clinical reports including
medical history, treatment summaries, and outcome assessments.
"""
import json
import logging
import os
import hashlib
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
from fastapi import HTTPException

from modules.database import (
    get_db_connection, execute_query, cache_ai_content, 
    get_cached_ai_content, create_report_notification
)


class AIContentGenerator:
    """AI content generation service using OpenRouter API"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.default_model = "mistralai/mistral-nemo:free"
        self.timeout = 30.0
        
        if not self.api_key:
            logging.error("SECURITY ALERT: OpenRouter API key not configured")
    
    async def generate_medical_history(self, patient_id: str, disciplines: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate AI-powered medical history from treatment notes
        
        Args:
            patient_id: Patient identifier
            disciplines: Optional list of disciplines to include
        
        Returns:
            Dictionary with generated content and metadata
        """
        # Check cache first
        cached_content = get_cached_ai_content(patient_id, "medical_history")
        if cached_content:
            logging.info(f"AI CACHE HIT: Medical history for patient {patient_id}")
            return {
                'content': cached_content['content'],
                'source': 'cache',
                'generated_at': cached_content['generated_at'],
                'usage_count': cached_content['usage_count']
            }
        
        # Gather source data
        source_data = self._get_treatment_notes_data(patient_id, disciplines)
        if not source_data:
            raise HTTPException(status_code=404, detail="No treatment data found for medical history generation")
        
        # Generate content
        prompt = self._build_medical_history_prompt(source_data)
        ai_response = await self._call_openrouter_api(prompt, "medical_history")
        
        # Cache the generated content
        cache_id = cache_ai_content(
            patient_id=patient_id,
            content_type="medical_history",
            content=ai_response['content'],
            discipline=None if not disciplines or len(disciplines) > 1 else disciplines[0],
            expires_days=7
        )
        
        # Create audit trail
        await self._create_ai_audit_log(patient_id, "medical_history", ai_response, cache_id)
        
        return {
            'content': ai_response['content'],
            'source': 'ai_generated',
            'generated_at': datetime.now().isoformat(),
            'tokens_used': ai_response.get('tokens_used', 0),
            'cache_id': cache_id
        }
    
    async def generate_treatment_summary(self, patient_id: str, disciplines: Optional[List[str]] = None,
                                       date_range: Optional[tuple] = None) -> Dict[str, Any]:
        """
        Generate AI-powered treatment summary
        
        Args:
            patient_id: Patient identifier
            disciplines: Optional list of disciplines to include
            date_range: Optional tuple of (start_date, end_date)
        
        Returns:
            Dictionary with generated content and metadata
        """
        # Check cache (with date range consideration)
        cache_key_suffix = f"_{date_range[0]}_{date_range[1]}" if date_range else ""
        cached_content = get_cached_ai_content(patient_id, f"treatment_summary{cache_key_suffix}")
        
        if cached_content:
            logging.info(f"AI CACHE HIT: Treatment summary for patient {patient_id}")
            return {
                'content': cached_content['content'],
                'source': 'cache',
                'generated_at': cached_content['generated_at'],
                'usage_count': cached_content['usage_count']
            }
        
        # Gather source data
        source_data = self._get_treatment_summary_data(patient_id, disciplines, date_range)
        if not source_data:
            raise HTTPException(status_code=404, detail="No treatment data found for summary generation")
        
        # Generate content
        prompt = self._build_treatment_summary_prompt(source_data, date_range)
        ai_response = await self._call_openrouter_api(prompt, "treatment_summary")
        
        # Cache the generated content
        cache_id = cache_ai_content(
            patient_id=patient_id,
            content_type=f"treatment_summary{cache_key_suffix}",
            content=ai_response['content'],
            discipline=None if not disciplines or len(disciplines) > 1 else disciplines[0],
            expires_days=7
        )
        
        # Create audit trail
        await self._create_ai_audit_log(patient_id, "treatment_summary", ai_response, cache_id)
        
        return {
            'content': ai_response['content'],
            'source': 'ai_generated',
            'generated_at': datetime.now().isoformat(),
            'tokens_used': ai_response.get('tokens_used', 0),
            'cache_id': cache_id
        }
    
    async def generate_outcome_summary(self, patient_id: str, disciplines: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate AI-powered outcome measures summary
        
        Args:
            patient_id: Patient identifier
            disciplines: Optional list of disciplines to include
        
        Returns:
            Dictionary with generated content and metadata
        """
        # Check cache first
        cached_content = get_cached_ai_content(patient_id, "outcome_summary")
        if cached_content:
            logging.info(f"AI CACHE HIT: Outcome summary for patient {patient_id}")
            return {
                'content': cached_content['content'],
                'source': 'cache',
                'generated_at': cached_content['generated_at'],
                'usage_count': cached_content['usage_count']
            }
        
        # Gather outcome measures data
        source_data = self._get_outcome_measures_data(patient_id, disciplines)
        if not source_data:
            raise HTTPException(status_code=404, detail="No outcome measures found for summary generation")
        
        # Generate content
        prompt = self._build_outcome_summary_prompt(source_data)
        ai_response = await self._call_openrouter_api(prompt, "outcome_summary")
        
        # Cache the generated content
        cache_id = cache_ai_content(
            patient_id=patient_id,
            content_type="outcome_summary",
            content=ai_response['content'],
            discipline=None if not disciplines or len(disciplines) > 1 else disciplines[0],
            expires_days=7
        )
        
        # Create audit trail
        await self._create_ai_audit_log(patient_id, "outcome_summary", ai_response, cache_id)
        
        return {
            'content': ai_response['content'],
            'source': 'ai_generated',
            'generated_at': datetime.now().isoformat(),
            'tokens_used': ai_response.get('tokens_used', 0),
            'cache_id': cache_id
        }
    
    def _get_treatment_notes_data(self, patient_id: str, disciplines: Optional[List[str]] = None) -> List[Dict]:
        """Get treatment notes data for AI processing"""
        base_query = """
        SELECT appointment_date, start_time, profession, therapist_name,
               subjective_findings, objective_findings, treatment, plan, duration
        FROM treatment_notes
        WHERE patient_id = ?
        """
        params = [patient_id]
        
        if disciplines:
            placeholders = ', '.join(['?' for _ in disciplines])
            base_query += f" AND profession IN ({placeholders})"
            params.extend(disciplines)
        
        base_query += " ORDER BY appointment_date ASC, start_time ASC"
        
        try:
            results = execute_query(base_query, tuple(params), fetch='all')
            if not results:
                return []
            
            return [
                {
                    "date": row[0] or "",
                    "time": row[1] or "",
                    "profession": row[2] or "",
                    "therapist": row[3] or "",
                    "subjective_findings": row[4] or "",
                    "objective_findings": row[5] or "",
                    "treatment": row[6] or "",
                    "plan": row[7] or "",
                    "duration_minutes": row[8] if len(row) > 8 and row[8] is not None else "",
                }
                for row in results
            ]
        except Exception as e:
            logging.warning(f"No treatment notes table or data available: {e}")
            return []
    
    def _get_treatment_summary_data(self, patient_id: str, disciplines: Optional[List[str]] = None,
                                   date_range: Optional[tuple] = None) -> List[Dict]:
        """Get treatment data for summary generation"""
        # This would be similar to treatment notes but potentially include more data
        # For now, use the same function with date filtering
        data = self._get_treatment_notes_data(patient_id, disciplines)
        
        if date_range and data:
            start_date, end_date = date_range
            filtered_data = []
            for item in data:
                if start_date <= item['date'] <= end_date:
                    filtered_data.append(item)
            return filtered_data
        
        return data
    
    def _get_outcome_measures_data(self, patient_id: str, disciplines: Optional[List[str]] = None) -> List[Dict]:
        """Get outcome measures data for AI processing"""
        # This is a placeholder - would need to integrate with actual outcome measures data
        try:
            base_query = """
            SELECT measure_name, score, date_recorded, notes, profession
            FROM outcome_measures
            WHERE patient_id = ?
            """
            params = [patient_id]
            
            if disciplines:
                placeholders = ', '.join(['?' for _ in disciplines])
                base_query += f" AND profession IN ({placeholders})"
                params.extend(disciplines)
            
            base_query += " ORDER BY date_recorded DESC"
            
            results = execute_query(base_query, tuple(params), fetch='all')
            if not results:
                return []
            
            return [
                {
                    "measure_name": row[0],
                    "score": row[1],
                    "date_recorded": row[2],
                    "notes": row[3] or "",
                    "profession": row[4] or ""
                }
                for row in results
            ]
        except Exception as e:
            logging.warning(f"No outcome measures table or data available: {e}")
            return []
    
    def _build_medical_history_prompt(self, source_data: List[Dict]) -> str:
        """Build prompt for medical history generation"""
        combined_notes = "\n\n".join([
            f"Session on {note['date']} at {note['time']} with {note['therapist']} ({note['profession']}) — Duration: {note['duration_minutes']} minutes\n"
            f"Subjective: {note['subjective_findings']}\n"
            f"Objective: {note['objective_findings']}\n"
            f"Treatment: {note['treatment']}\n"
            f"Plan: {note['plan']}"
            for note in source_data
        ])
        
        return (
            f"Please extract the medical history and level of function from the following clinical notes:\n\n"
            f"{combined_notes}\n\n"
            f"Instructions:\n"
            f"- Never make anything up, only use the information provided\n"
            f"- If there is not enough information, say 'No information available'\n"
            f"- Use HTML strong tags for headings\n"
            f"- Focus on medical history, presenting conditions, and functional status\n"
            f"- Organize information chronologically where relevant"
        )
    
    def _build_treatment_summary_prompt(self, source_data: List[Dict], date_range: Optional[tuple] = None) -> str:
        """Build prompt for treatment summary generation"""
        combined_notes = "\n\n".join([
            f"Session on {note['date']} at {note['time']} with {note['therapist']} ({note['profession']}) — Duration: {note['duration_minutes']} minutes\n"
            f"Subjective: {note['subjective_findings']}\n"
            f"Objective: {note['objective_findings']}\n"
            f"Treatment: {note['treatment']}\n"
            f"Plan: {note['plan']}"
            for note in source_data
        ])
        
        date_context = ""
        if date_range:
            date_context = f"Focus on the treatment period from {date_range[0]} to {date_range[1]}.\n"
        
        return (
            f"Please create a comprehensive treatment summary from the following clinical notes:\n\n"
            f"{combined_notes}\n\n"
            f"Instructions:\n"
            f"{date_context}"
            f"- Summarize the overall treatment approach and interventions\n"
            f"- Highlight patient progress and outcomes\n"
            f"- Include key objective findings and improvements\n"
            f"- Never make anything up, only use the information provided\n"
            f"- Use HTML strong tags for headings\n"
            f"- Organize by discipline if multiple disciplines involved"
        )
    
    def _build_outcome_summary_prompt(self, source_data: List[Dict]) -> str:
        """Build prompt for outcome measures summary"""
        measures_text = "\n".join([
            f"{measure['measure_name']}: {measure['score']} (recorded {measure['date_recorded']}) - {measure['notes']}"
            for measure in source_data
        ])
        
        return (
            f"Please analyze and summarize the following outcome measures:\n\n"
            f"{measures_text}\n\n"
            f"Instructions:\n"
            f"- Provide clinical interpretation of scores and trends\n"
            f"- Highlight significant changes or improvements\n"
            f"- Note any concerning patterns\n"
            f"- Never make anything up, only use the information provided\n"
            f"- Use HTML strong tags for headings\n"
            f"- Focus on functional implications of the measurements"
        )
    
    async def _call_openrouter_api(self, prompt: str, content_type: str) -> Dict[str, Any]:
        """Make API call to OpenRouter"""
        if not self.api_key:
            raise HTTPException(status_code=500, detail="AI service not available - API key not configured")
        
        # Security and monitoring
        api_start_time = datetime.now()
        input_length = len(prompt)
        
        logging.info(f"AI API CALL: {content_type} generation, input length: {input_length} chars")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://hadadahealth.com",
            "X-Title": "HadadaHealth Medical AI"
        }
        
        body = {
            "model": self.default_model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant summarizing clinical information for healthcare professionals. Always follow medical documentation standards and never fabricate information."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1500,  # Increased for more detailed summaries
            "temperature": 0.3   # Low temperature for consistent medical content
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.base_url, headers=headers, json=body)
                response.raise_for_status()
                
                response_data = response.json()
                content = response_data["choices"][0]["message"]["content"]
                
                # API Usage monitoring
                api_end_time = datetime.now()
                duration = (api_end_time - api_start_time).total_seconds()
                
                # Extract usage statistics
                usage_info = response_data.get("usage", {})
                total_tokens = usage_info.get("total_tokens", 0)
                
                logging.info(f"AI API SUCCESS: {content_type} generation completed - "
                           f"Duration: {duration:.2f}s, Tokens: {total_tokens}")
                
                return {
                    'content': content,
                    'tokens_used': total_tokens,
                    'duration': duration,
                    'usage_info': usage_info
                }
                
        except httpx.HTTPError as e:
            logging.error(f"AI API ERROR: {content_type} generation failed - {str(e)}")
            raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")
        except Exception as e:
            logging.error(f"AI SYSTEM ERROR: {content_type} generation crashed - {str(e)}")
            raise HTTPException(status_code=500, detail="AI service temporarily unavailable")
    
    async def _create_ai_audit_log(self, patient_id: str, content_type: str, 
                                  ai_response: Dict, cache_id: int) -> None:
        """Create comprehensive audit log for AI-generated content"""
        try:
            audit_data = {
                'timestamp': datetime.now().isoformat(),
                'patient_id': patient_id,
                'content_type': content_type,
                'ai_model': self.default_model,
                'tokens_used': ai_response.get('tokens_used', 0),
                'duration': ai_response.get('duration', 0),
                'cache_id': cache_id,
                'content_length': len(ai_response['content'])
            }
            
            # Log to file for POPIA compliance
            audit_log_path = "logs/ai_audit.log"
            os.makedirs(os.path.dirname(audit_log_path), exist_ok=True)
            
            with open(audit_log_path, 'a') as f:
                f.write(json.dumps(audit_data) + '\n')
            
            logging.info(f"AI AUDIT: Content generated for patient {patient_id}, type {content_type}")
            
        except Exception as e:
            logging.error(f"AI AUDIT ERROR: Failed to create audit log - {str(e)}")
    
    def clear_patient_cache(self, patient_id: str, content_type: Optional[str] = None) -> int:
        """Clear AI cache for a patient (force regeneration)"""
        try:
            if content_type:
                affected_rows = execute_query(
                    "UPDATE ai_content_cache SET is_valid = 0 WHERE patient_id = ? AND content_type = ?",
                    (patient_id, content_type)
                )
            else:
                affected_rows = execute_query(
                    "UPDATE ai_content_cache SET is_valid = 0 WHERE patient_id = ?",
                    (patient_id,)
                )
            
            logging.info(f"AI CACHE CLEARED: Patient {patient_id}, type {content_type or 'all'}")
            return affected_rows or 0
            
        except Exception as e:
            logging.error(f"AI CACHE CLEAR ERROR: {str(e)}")
            return 0


# Global instance
ai_generator = AIContentGenerator()


# Convenience functions for easy import
async def generate_medical_history(patient_id: str, disciplines: Optional[List[str]] = None) -> Dict[str, Any]:
    """Generate medical history for a patient"""
    return await ai_generator.generate_medical_history(patient_id, disciplines)


async def generate_treatment_summary(patient_id: str, disciplines: Optional[List[str]] = None,
                                   date_range: Optional[tuple] = None) -> Dict[str, Any]:
    """Generate treatment summary for a patient"""
    return await ai_generator.generate_treatment_summary(patient_id, disciplines, date_range)


async def generate_outcome_summary(patient_id: str, disciplines: Optional[List[str]] = None) -> Dict[str, Any]:
    """Generate outcome measures summary for a patient"""
    return await ai_generator.generate_outcome_summary(patient_id, disciplines)


def clear_ai_cache(patient_id: str, content_type: Optional[str] = None) -> int:
    """Clear AI cache for a patient"""
    return ai_generator.clear_patient_cache(patient_id, content_type)