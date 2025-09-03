"""
Outcome Measures module for HadadaHealth
Handles outcome measure data storage, calculations, and validation
"""
import sqlite3
import json
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

from modules.database import get_db_connection, execute_query, execute_many, table_exists


def initialize_outcome_measures_schema():
    """Initialize the outcome measures database schema"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Create domains table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS outcome_domains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(50) NOT NULL,
                display_order INTEGER DEFAULT 1
            )
        """)
        
        # Create measures table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS outcome_measures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain_id INTEGER REFERENCES outcome_domains(id),
                name VARCHAR(100) NOT NULL,
                abbreviation VARCHAR(10) NOT NULL,
                type VARCHAR(20) NOT NULL, -- 'multi_item', 'single_score', 'timed', 'distance'
                total_items INTEGER,
                max_score INTEGER,
                unit VARCHAR(20),
                allows_individual_items BOOLEAN DEFAULT TRUE,
                calculation_type VARCHAR(20), -- 'sum', 'average', 'time_to_speed', 'distance'
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create outcome entries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS outcome_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                treatment_note_id INTEGER REFERENCES treatment_notes(id),
                measure_id INTEGER REFERENCES outcome_measures(id),
                entry_method VARCHAR(20) NOT NULL, -- 'individual_items', 'total_only'
                total_score DECIMAL(10,2),
                calculated_result VARCHAR(100),
                assistive_device TEXT,
                additional_notes TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER REFERENCES users(id)
            )
        """)
        
        # Create item scores table for multi-item measures
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS outcome_item_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER REFERENCES outcome_entries(id),
                item_number INTEGER NOT NULL,
                score INTEGER NOT NULL,
                max_possible INTEGER NOT NULL
            )
        """)
        
        # Create raw data table for timed/distance measures
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS outcome_raw_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER REFERENCES outcome_entries(id),
                data_type VARCHAR(50) NOT NULL, -- 'time_seconds', 'distance_meters', 'trial_1_time', etc.
                value DECIMAL(10,3) NOT NULL,
                unit VARCHAR(20) NOT NULL
            )
        """)
        
        conn.commit()
        
        # Insert default data if tables are empty
        _insert_default_data(cursor)
        conn.commit()
        
    finally:
        conn.close()


def _insert_default_data(cursor):
    """Insert default domains and measures"""
    
    # Check if domains exist
    cursor.execute("SELECT COUNT(*) FROM outcome_domains")
    if cursor.fetchone()[0] == 0:
        # Insert domains
        domains = [
            ('Balance', 1),
            ('Mobility', 2),
            ('Function', 3)
        ]
        cursor.executemany(
            "INSERT INTO outcome_domains (name, display_order) VALUES (?, ?)",
            domains
        )
    
    # Check if measures exist
    cursor.execute("SELECT COUNT(*) FROM outcome_measures")
    if cursor.fetchone()[0] == 0:
        # Get domain IDs
        cursor.execute("SELECT id, name FROM outcome_domains")
        domain_map = {name: id for id, name in cursor.fetchall()}
        
        # Insert measures
        measures = [
            (domain_map['Balance'], 'Berg Balance Scale', 'BBS', 'multi_item', 14, 56, 'points', True, 'sum'),
            (domain_map['Balance'], 'Activities-Specific Balance Confidence Scale', 'ABC', 'multi_item', 16, 100, 'percentage', True, 'average'),
            (domain_map['Mobility'], '10 Meter Walk Test', '10mWT', 'timed', None, None, 'm/s', False, 'time_to_speed'),
            (domain_map['Function'], 'Five Times Sit-to-Stand', '5TSTS', 'timed', None, None, 'seconds', False, 'time_only'),
            (domain_map['Mobility'], 'Functional Gait Assessment', 'FGA', 'multi_item', 10, 30, 'points', True, 'sum'),
            (domain_map['Function'], 'Six Minute Walk Test', '6MWT', 'distance', None, None, 'meters', False, 'distance_only')
        ]
        
        cursor.executemany("""
            INSERT INTO outcome_measures 
            (domain_id, name, abbreviation, type, total_items, max_score, unit, allows_individual_items, calculation_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, measures)


class OutcomeMeasureCalculator:
    """Handles calculations for different outcome measures"""
    
    @staticmethod
    def calculate_berg_balance_scale(items_scores: List[int]) -> Dict[str, Any]:
        """BBS: Sum of 14 items (0-4 each) = 0-56 total"""
        if len(items_scores) != 14:
            raise ValueError("BBS requires exactly 14 item scores")
        
        total = sum(items_scores)
        if not 0 <= total <= 56:
            raise ValueError("BBS total must be 0-56")
            
        return {
            'total_score': total,
            'max_score': 56,
            'percentage': round((total / 56) * 100, 1),
            'interpretation': _get_bbs_interpretation(total),
            'calculated_result': f"{total}/56 ({_get_bbs_interpretation(total)})"
        }
    
    @staticmethod
    def calculate_abc_scale(items_scores: List[float]) -> Dict[str, Any]:
        """ABC: Average of 16 items (0-100% each) = 0-100% average"""
        if len(items_scores) != 16:
            raise ValueError("ABC requires exactly 16 item scores")
        
        average = sum(items_scores) / 16
        average = float(Decimal(str(average)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))
        
        return {
            'total_score': average,
            'max_score': 100,
            'unit': 'percentage',
            'interpretation': _get_abc_interpretation(average),
            'calculated_result': f"{average}% ({_get_abc_interpretation(average)})"
        }
    
    @staticmethod
    def calculate_10mwt(comfortable_times: List[float], fast_times: List[float] = None) -> Dict[str, Any]:
        """10mWT: 6 meters ÷ average time = speed in m/s"""
        results = {}
        
        if comfortable_times and all(t > 0 for t in comfortable_times):
            avg_time = sum(comfortable_times) / len(comfortable_times)
            speed = 6.0 / avg_time
            speed = float(Decimal(str(speed)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            
            results['comfortable'] = {
                'average_time': round(avg_time, 2),
                'speed_ms': speed,
                'interpretation': _get_10mwt_interpretation(speed, 'comfortable')
            }
        
        if fast_times and all(t > 0 for t in fast_times):
            avg_time = sum(fast_times) / len(fast_times)
            speed = 6.0 / avg_time
            speed = float(Decimal(str(speed)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            
            results['fast'] = {
                'average_time': round(avg_time, 2),
                'speed_ms': speed,
                'interpretation': _get_10mwt_interpretation(speed, 'fast')
            }
        
        # Format result string
        result_parts = []
        if 'comfortable' in results:
            result_parts.append(f"Comfortable: {results['comfortable']['speed_ms']} m/s")
        if 'fast' in results:
            result_parts.append(f"Fast: {results['fast']['speed_ms']} m/s")
        
        results['calculated_result'] = " | ".join(result_parts)
        return results
    
    @staticmethod
    def calculate_5tsts(time_seconds: float) -> Dict[str, Any]:
        """5TSTS: Time to complete 5 sit-to-stands"""
        if time_seconds <= 0:
            raise ValueError("Time must be positive")
        
        return {
            'time_seconds': round(time_seconds, 1),
            'interpretation': _get_5tsts_interpretation(time_seconds),
            'calculated_result': f"{round(time_seconds, 1)}s ({_get_5tsts_interpretation(time_seconds)})"
        }
    
    @staticmethod
    def calculate_fga(items_scores: List[int]) -> Dict[str, Any]:
        """FGA: Sum of 10 items (0-3 each) = 0-30 total"""
        if len(items_scores) != 10:
            raise ValueError("FGA requires exactly 10 item scores")
        
        total = sum(items_scores)
        if not 0 <= total <= 30:
            raise ValueError("FGA total must be 0-30")
        
        return {
            'total_score': total,
            'max_score': 30,
            'percentage': round((total / 30) * 100, 1),
            'interpretation': _get_fga_interpretation(total),
            'calculated_result': f"{total}/30 ({_get_fga_interpretation(total)})"
        }
    
    @staticmethod
    def calculate_6mwt(distance_meters: float, actual_time_minutes: float = 6.0) -> Dict[str, Any]:
        """6MWT: Total distance walked in meters"""
        if distance_meters < 0:
            raise ValueError("Distance must be non-negative")
        
        return {
            'distance_meters': distance_meters,
            'actual_time_minutes': actual_time_minutes,
            'meters_per_minute': round(distance_meters / actual_time_minutes, 1) if actual_time_minutes > 0 else 0,
            'interpretation': _get_6mwt_interpretation(distance_meters),
            'calculated_result': f"{distance_meters}m ({_get_6mwt_interpretation(distance_meters)})"
        }


# Interpretation helper functions
def _get_bbs_interpretation(score: int) -> str:
    if score >= 45:
        return "Low fall risk"
    elif score >= 36:
        return "Medium fall risk"
    else:
        return "High fall risk"


def _get_abc_interpretation(score: float) -> str:
    if score >= 80:
        return "High level of physical functioning"
    elif score >= 50:
        return "Moderate level of physical functioning"
    else:
        return "Low level of physical functioning"


def _get_10mwt_interpretation(speed: float, test_type: str) -> str:
    if test_type == 'comfortable':
        if speed >= 1.0:
            return "Community ambulator"
        elif speed >= 0.4:
            return "Limited community ambulator"
        else:
            return "Household ambulator"
    return f"Fast walking speed: {speed} m/s"


def _get_5tsts_interpretation(time: float) -> str:
    if time <= 11:
        return "Normal function"
    elif time <= 13.6:
        return "Mostly normal function"
    else:
        return "Below normal function"


def _get_fga_interpretation(score: int) -> str:
    if score >= 23:
        return "Low fall risk"
    elif score >= 19:
        return "Medium fall risk"
    else:
        return "High fall risk"


def _get_6mwt_interpretation(distance: float) -> str:
    if distance >= 400:
        return "Good functional capacity"
    elif distance >= 300:
        return "Moderate functional capacity"
    else:
        return "Limited functional capacity"


class OutcomeMeasureValidator:
    """Validates outcome measure entries"""
    
    VALIDATION_RULES = {
        'BBS': {
            'item_range': (0, 4),
            'total_items': 14,
            'total_range': (0, 56)
        },
        'ABC': {
            'item_range': (0, 100),
            'total_items': 16,
            'total_range': (0, 100)
        },
        '10mWT': {
            'time_range': (1.0, 60.0),
            'speed_range': (0.1, 6.0)
        },
        '5TSTS': {
            'time_range': (3.0, 120.0)
        },
        'FGA': {
            'item_range': (0, 3),
            'total_items': 10,
            'total_range': (0, 30)
        },
        '6MWT': {
            'distance_range': (0, 1000),
            'time_range': (0.5, 6.0)
        }
    }
    
    @classmethod
    def validate_entry(cls, measure_abbrev: str, data: Dict[str, Any]) -> List[str]:
        """Validate an outcome measure entry"""
        rules = cls.VALIDATION_RULES.get(measure_abbrev)
        if not rules:
            return [f"Unknown measure: {measure_abbrev}"]
        
        errors = []
        
        if measure_abbrev in ['BBS', 'ABC', 'FGA']:
            errors.extend(cls._validate_multi_item(measure_abbrev, data, rules))
        elif measure_abbrev in ['10mWT', '5TSTS']:
            errors.extend(cls._validate_timed(measure_abbrev, data, rules))
        elif measure_abbrev == '6MWT':
            errors.extend(cls._validate_distance(data, rules))
        
        return errors
    
    @classmethod
    def _validate_multi_item(cls, measure: str, data: Dict, rules: Dict) -> List[str]:
        errors = []
        
        if 'individual_items' in data:
            items = data['individual_items']
            if len(items) != rules['total_items']:
                errors.append(f"{measure} requires {rules['total_items']} items")
            
            for i, score in enumerate(items, 1):
                if not (rules['item_range'][0] <= score <= rules['item_range'][1]):
                    errors.append(f"Item {i} must be {rules['item_range'][0]}-{rules['item_range'][1]}")
        
        elif 'total_score' in data:
            total = data['total_score']
            if not (rules['total_range'][0] <= total <= rules['total_range'][1]):
                errors.append(f"Total score must be {rules['total_range'][0]}-{rules['total_range'][1]}")
        
        return errors
    
    @classmethod
    def _validate_timed(cls, measure: str, data: Dict, rules: Dict) -> List[str]:
        errors = []
        
        if measure == '10mWT':
            for trial_type in ['comfortable_trials', 'fast_trials']:
                if trial_type in data and data[trial_type]:
                    for i, time_val in enumerate(data[trial_type], 1):
                        if not (rules['time_range'][0] <= time_val <= rules['time_range'][1]):
                            errors.append(f"{trial_type.replace('_', ' ').title()} trial {i}: {rules['time_range'][0]}-{rules['time_range'][1]} seconds")
        
        elif measure == '5TSTS':
            if 'time_seconds' in data:
                time_val = data['time_seconds']
                if not (rules['time_range'][0] <= time_val <= rules['time_range'][1]):
                    errors.append(f"Time must be {rules['time_range'][0]}-{rules['time_range'][1]} seconds")
        
        return errors
    
    @classmethod
    def _validate_distance(cls, data: Dict, rules: Dict) -> List[str]:
        errors = []
        
        if 'distance_meters' in data:
            distance = data['distance_meters']
            if not (rules['distance_range'][0] <= distance <= rules['distance_range'][1]):
                errors.append(f"Distance must be {rules['distance_range'][0]}-{rules['distance_range'][1]} meters")
        
        return errors


# Data access functions
def get_all_domains() -> List[Dict[str, Any]]:
    """Get all outcome domains"""
    query = "SELECT * FROM outcome_domains ORDER BY display_order"
    result = execute_query(query, fetch='all')
    return [dict(row) for row in result] if result else []


def get_measures_by_domain(domain_id: int) -> List[Dict[str, Any]]:
    """Get measures for a specific domain"""
    query = """
        SELECT * FROM outcome_measures 
        WHERE domain_id = ? 
        ORDER BY name
    """
    result = execute_query(query, (domain_id,), fetch='all')
    return [dict(row) for row in result] if result else []


def get_measure_by_id(measure_id: int) -> Optional[Dict[str, Any]]:
    """Get measure by ID"""
    query = "SELECT * FROM outcome_measures WHERE id = ?"
    result = execute_query(query, (measure_id,), fetch='one')
    return dict(result) if result else None


def create_outcome_entry(appointment_id: str, measure_id: int, entry_data: Dict[str, Any], user_id: int) -> int:
    """Create a new outcome entry"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Insert main entry
        cursor.execute("""
            INSERT INTO outcome_entries 
            (appointment_id, measure_id, entry_method, total_score, calculated_result, 
             assistive_device, additional_notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            appointment_id, measure_id, entry_data.get('entry_method'),
            entry_data.get('total_score'), entry_data.get('calculated_result'),
            entry_data.get('assistive_device'), entry_data.get('additional_notes'),
            user_id
        ))
        
        entry_id = cursor.lastrowid
        
        # Insert item scores if provided
        if entry_data.get('individual_items'):
            item_scores = []
            max_score = entry_data.get('max_item_score', 4)  # Default for most measures
            for i, score in enumerate(entry_data['individual_items'], 1):
                item_scores.append((entry_id, i, score, max_score))
            
            cursor.executemany("""
                INSERT INTO outcome_item_scores (entry_id, item_number, score, max_possible)
                VALUES (?, ?, ?, ?)
            """, item_scores)
        
        # Insert raw data if provided
        if entry_data.get('raw_data'):
            raw_data_entries = []
            for data_type, values in entry_data['raw_data'].items():
                if isinstance(values, list):
                    for i, value in enumerate(values):
                        raw_data_entries.append((entry_id, f"{data_type}_trial_{i+1}", value, entry_data.get('unit', 'seconds')))
                else:
                    raw_data_entries.append((entry_id, data_type, values, entry_data.get('unit', 'seconds')))
            
            cursor.executemany("""
                INSERT INTO outcome_raw_data (entry_id, data_type, value, unit)
                VALUES (?, ?, ?, ?)
            """, raw_data_entries)
        
        conn.commit()
        return entry_id
        
    finally:
        conn.close()


def get_outcome_entries_for_treatment_note(appointment_id: str) -> List[Dict[str, Any]]:
    """Get all outcome entries for a treatment note"""
    query = """
        SELECT 
            oe.*,
            om.name as measure_name,
            om.abbreviation as measure_abbreviation,
            od.name as domain_name
        FROM outcome_entries oe
        JOIN outcome_measures om ON oe.measure_id = om.id
        JOIN outcome_domains od ON om.domain_id = od.id
        WHERE oe.appointment_id = ?
        ORDER BY oe.timestamp
    """
    result = execute_query(query, (appointment_id,), fetch='all')
    return [dict(row) for row in result] if result else []


def get_outcome_entry_by_id(entry_id: int) -> Optional[Dict[str, Any]]:
    """Get detailed outcome entry by ID including item scores and raw data"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get main entry
        cursor.execute("""
            SELECT 
                oe.*,
                om.name as measure_name,
                om.abbreviation as measure_abbreviation,
                om.type as measure_type,
                om.total_items,
                om.max_score,
                od.name as domain_name
            FROM outcome_entries oe
            JOIN outcome_measures om ON oe.measure_id = om.id
            JOIN outcome_domains od ON om.domain_id = od.id
            WHERE oe.id = ?
        """, (entry_id,))
        
        entry = cursor.fetchone()
        if not entry:
            return None
        
        entry = dict(entry)
        
        # Get item scores if they exist
        cursor.execute("""
            SELECT item_number, score, max_possible 
            FROM outcome_item_scores 
            WHERE entry_id = ? 
            ORDER BY item_number
        """, (entry_id,))
        
        item_scores = cursor.fetchall()
        if item_scores:
            entry['individual_items'] = [row[1] for row in item_scores]
        
        # Get raw data if it exists
        cursor.execute("""
            SELECT data_type, value, unit 
            FROM outcome_raw_data 
            WHERE entry_id = ?
            ORDER BY data_type
        """, (entry_id,))
        
        raw_data = cursor.fetchall()
        if raw_data:
            entry['raw_data'] = {}
            for data_type, value, unit in raw_data:
                if data_type not in entry['raw_data']:
                    entry['raw_data'][data_type] = []
                entry['raw_data'][data_type].append(value)
        
        return entry
        
    finally:
        conn.close()


def update_outcome_entry(entry_id: int, entry_data: Dict[str, Any]) -> bool:
    """Update an existing outcome entry"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Update main entry
        cursor.execute("""
            UPDATE outcome_entries 
            SET entry_method = ?, total_score = ?, calculated_result = ?,
                assistive_device = ?, additional_notes = ?, timestamp = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            entry_data.get('entry_method'), entry_data.get('total_score'),
            entry_data.get('calculated_result'), entry_data.get('assistive_device'),
            entry_data.get('additional_notes'), entry_id
        ))
        
        # Delete existing related data
        cursor.execute("DELETE FROM outcome_item_scores WHERE entry_id = ?", (entry_id,))
        cursor.execute("DELETE FROM outcome_raw_data WHERE entry_id = ?", (entry_id,))
        
        # Insert new item scores if provided
        if entry_data.get('individual_items'):
            item_scores = []
            max_score = entry_data.get('max_item_score', 4)
            for i, score in enumerate(entry_data['individual_items'], 1):
                item_scores.append((entry_id, i, score, max_score))
            
            cursor.executemany("""
                INSERT INTO outcome_item_scores (entry_id, item_number, score, max_possible)
                VALUES (?, ?, ?, ?)
            """, item_scores)
        
        # Insert new raw data if provided
        if entry_data.get('raw_data'):
            raw_data_entries = []
            for data_type, values in entry_data['raw_data'].items():
                if isinstance(values, list):
                    for i, value in enumerate(values):
                        raw_data_entries.append((entry_id, f"{data_type}_trial_{i+1}", value, entry_data.get('unit', 'seconds')))
                else:
                    raw_data_entries.append((entry_id, data_type, values, entry_data.get('unit', 'seconds')))
            
            cursor.executemany("""
                INSERT INTO outcome_raw_data (entry_id, data_type, value, unit)
                VALUES (?, ?, ?, ?)
            """, raw_data_entries)
        
        conn.commit()
        return cursor.rowcount > 0
        
    finally:
        conn.close()


def delete_outcome_entry(entry_id: int) -> bool:
    """Delete an outcome entry and all related data"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Delete related data first
        cursor.execute("DELETE FROM outcome_item_scores WHERE entry_id = ?", (entry_id,))
        cursor.execute("DELETE FROM outcome_raw_data WHERE entry_id = ?", (entry_id,))
        
        # Delete main entry
        cursor.execute("DELETE FROM outcome_entries WHERE id = ?", (entry_id,))
        
        conn.commit()
        return cursor.rowcount > 0
        
    finally:
        conn.close()


# Initialize schema when module is imported
# if not table_exists('outcome_domains'):
#     initialize_outcome_measures_schema()