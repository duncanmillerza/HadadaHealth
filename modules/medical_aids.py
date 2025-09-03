"""
Medical aids management functions for HadadaHealth
"""
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, UploadFile
from pydantic import BaseModel
import pandas as pd
import json
from .database import get_db_connection, execute_query
import sqlite3


class MedicalAid(BaseModel):
    """Medical Aid model"""
    name: str
    website: Optional[str] = None
    claims_email: Optional[str] = None
    plans: Optional[List[str]] = None
    claim_tips: Optional[str] = None
    administrator: Optional[str] = None


def get_all_medical_aids() -> List[str]:
    """
    Get all medical aid names
    
    Returns:
        List of medical aid names
    """
    query = "SELECT name FROM medical_aids ORDER BY name ASC"
    results = execute_query(query, fetch='all')
    return [row[0] for row in results] if results else []


def get_all_medical_aids_full() -> List[Dict[str, Any]]:
    """
    Get all medical aids with full details
    
    Returns:
        List of medical aid dictionaries with full information
    """
    query = """
        SELECT name, website, claims_email, plans, claim_tips, administrator
        FROM medical_aids ORDER BY name ASC
    """
    results = execute_query(query, fetch='all')
    
    medical_aids = []
    for row in results:
        medical_aid = dict(row)
        # Parse plans JSON if it exists
        if medical_aid.get('plans'):
            try:
                medical_aid['plans'] = json.loads(medical_aid['plans'])
            except (json.JSONDecodeError, TypeError):
                medical_aid['plans'] = []
        else:
            medical_aid['plans'] = []
        medical_aids.append(medical_aid)
    
    return medical_aids


def create_medical_aid(aid: MedicalAid) -> Dict[str, str]:
    """
    Create a new medical aid
    
    Args:
        aid: MedicalAid object with medical aid details
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If medical aid already exists or creation fails
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO medical_aids (name, website, claims_email, plans, claim_tips, administrator)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            aid.name,
            aid.website,
            aid.claims_email,
            json.dumps(aid.plans) if aid.plans else None,
            aid.claim_tips,
            aid.administrator
        ))
        conn.commit()
        return {"detail": "Medical aid added"}
        
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Medical aid already exists")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create medical aid: {str(e)}")
    finally:
        conn.close()


def update_medical_aid(old_name: str, aid: MedicalAid) -> Dict[str, str]:
    """
    Update an existing medical aid
    
    Args:
        old_name: Current name of the medical aid
        aid: MedicalAid object with updated details
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If medical aid not found or update fails
    """
    conn = get_db_connection()
    try:
        # Check if medical aid exists
        existing = conn.execute("SELECT 1 FROM medical_aids WHERE name = ?", (old_name,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Medical aid not found")
            
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE medical_aids
            SET name = ?, website = ?, claims_email = ?, plans = ?, claim_tips = ?, administrator = ?
            WHERE name = ?
        """, (
            aid.name,
            aid.website,
            aid.claims_email,
            json.dumps(aid.plans) if aid.plans else None,
            aid.claim_tips,
            aid.administrator,
            old_name
        ))
        conn.commit()
        return {"detail": "Medical aid updated"}
        
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="New name already exists")
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update medical aid: {str(e)}")
    finally:
        conn.close()


def delete_medical_aid(name: str) -> Dict[str, str]:
    """
    Delete a medical aid
    
    Args:
        name: Name of the medical aid to delete
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If medical aid not found or deletion fails
    """
    conn = get_db_connection()
    try:
        # Check if medical aid exists
        existing = conn.execute("SELECT 1 FROM medical_aids WHERE name = ?", (name,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Medical aid not found")
            
        cursor = conn.cursor()
        cursor.execute("DELETE FROM medical_aids WHERE name = ?", (name,))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Medical aid not found")
            
        return {"detail": "Medical aid deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete medical aid: {str(e)}")
    finally:
        conn.close()


def get_medical_aid_plans(medical_aid_name: str) -> List[str]:
    """
    Get plans for a specific medical aid
    
    Args:
        medical_aid_name: Name of the medical aid
        
    Returns:
        List of plan names for the medical aid
    """
    query = "SELECT plans FROM medical_aids WHERE name = ?"
    result = execute_query(query, (medical_aid_name,), fetch='one')
    
    if not result or result[0] is None:
        return []
        
    try:
        plans = json.loads(result[0])
        return plans if isinstance(plans, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def get_medical_aid_by_name(name: str) -> Optional[Dict[str, Any]]:
    """
    Get a medical aid by name
    
    Args:
        name: Name of the medical aid
        
    Returns:
        Medical aid dictionary or None if not found
    """
    query = """
        SELECT name, website, claims_email, plans, claim_tips, administrator
        FROM medical_aids WHERE name = ?
    """
    result = execute_query(query, (name,), fetch='one')
    
    if result:
        medical_aid = dict(result)
        # Parse plans JSON if it exists
        if medical_aid.get('plans'):
            try:
                medical_aid['plans'] = json.loads(medical_aid['plans'])
            except (json.JSONDecodeError, TypeError):
                medical_aid['plans'] = []
        else:
            medical_aid['plans'] = []
        return medical_aid
    
    return None


def import_medical_aids_from_excel(file: UploadFile) -> Dict[str, Any]:
    """
    Import medical aids from Excel file
    
    Args:
        file: The uploaded Excel file
        
    Returns:
        Import results summary
        
    Raises:
        HTTPException: If import fails
    """
    try:
        # Read Excel file
        df = pd.read_excel(file.file)
        
        # Validate required columns
        required_columns = ['name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        imported_count = 0
        errors = []
        
        conn = get_db_connection()
        try:
            for index, row in df.iterrows():
                try:
                    # Convert row to dict and handle NaN values
                    aid_data = row.to_dict()
                    aid_data = {k: (v if pd.notna(v) else None) for k, v in aid_data.items()}
                    
                    # Handle plans if present
                    if aid_data.get('plans') and aid_data['plans']:
                        if isinstance(aid_data['plans'], str):
                            # Convert comma-separated string to list
                            plans = [p.strip() for p in str(aid_data['plans']).split(",") if p.strip()]
                            aid_data['plans'] = plans
                    
                    # Clean up the data for MedicalAid model
                    cleaned_data = {
                        'name': aid_data.get('name', ''),
                        'website': aid_data.get('website'),
                        'claims_email': aid_data.get('claims_email'),
                        'plans': aid_data.get('plans'),
                        'claim_tips': aid_data.get('claim_tips'),
                        'administrator': aid_data.get('administrator')
                    }
                    
                    # Create MedicalAid object and save
                    medical_aid = MedicalAid(**cleaned_data)
                    
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO medical_aids (name, website, claims_email, plans, claim_tips, administrator)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        medical_aid.name,
                        medical_aid.website,
                        medical_aid.claims_email,
                        json.dumps(medical_aid.plans) if medical_aid.plans else None,
                        medical_aid.claim_tips,
                        medical_aid.administrator
                    ))
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
            
            conn.commit()
            
        finally:
            conn.close()
        
        return {
            "imported_count": imported_count,
            "total_rows": len(df),
            "errors": errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process Excel file: {str(e)}")


def search_medical_aids(search_term: str) -> List[Dict[str, Any]]:
    """
    Search medical aids by name, administrator, or claims email
    
    Args:
        search_term: The search term
        
    Returns:
        List of matching medical aid dictionaries
    """
    search_pattern = f"%{search_term}%"
    query = """
        SELECT name, website, claims_email, plans, claim_tips, administrator
        FROM medical_aids
        WHERE 
            name LIKE ? OR 
            administrator LIKE ? OR
            claims_email LIKE ?
        ORDER BY name
    """
    
    params = [search_pattern] * 3
    results = execute_query(query, tuple(params), fetch='all')
    
    medical_aids = []
    for row in results:
        medical_aid = dict(row)
        # Parse plans JSON if it exists
        if medical_aid.get('plans'):
            try:
                medical_aid['plans'] = json.loads(medical_aid['plans'])
            except (json.JSONDecodeError, TypeError):
                medical_aid['plans'] = []
        else:
            medical_aid['plans'] = []
        medical_aids.append(medical_aid)
    
    return medical_aids


def get_medical_aids_statistics() -> Dict[str, Any]:
    """
    Get statistics about medical aids
    
    Returns:
        Statistics dictionary
    """
    conn = get_db_connection()
    try:
        stats = {}
        
        # Total medical aids
        total_result = conn.execute("SELECT COUNT(*) FROM medical_aids").fetchone()
        stats['total_medical_aids'] = total_result[0] if total_result else 0
        
        # Medical aids with plans
        plans_result = conn.execute(
            "SELECT COUNT(*) FROM medical_aids WHERE plans IS NOT NULL AND plans != '[]'"
        ).fetchone()
        stats['medical_aids_with_plans'] = plans_result[0] if plans_result else 0
        
        # Medical aids with administrators
        admin_result = conn.execute(
            "SELECT COUNT(*) FROM medical_aids WHERE administrator IS NOT NULL AND administrator != ''"
        ).fetchone()
        stats['medical_aids_with_administrators'] = admin_result[0] if admin_result else 0
        
        # Medical aids with claims email
        email_result = conn.execute(
            "SELECT COUNT(*) FROM medical_aids WHERE claims_email IS NOT NULL AND claims_email != ''"
        ).fetchone()
        stats['medical_aids_with_claims_email'] = email_result[0] if email_result else 0
        
        return stats
        
    finally:
        conn.close()