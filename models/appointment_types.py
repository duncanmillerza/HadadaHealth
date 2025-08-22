"""
AppointmentType and PracticeAppointmentType models for HadadaHealth

Provides hierarchical appointment type management with practice-specific customizations.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from modules.database import execute_query, execute_many


class AppointmentType(BaseModel):
    """
    Model for hierarchical appointment types with self-referential parent/child relationships
    
    Supports multi-level categorization like:
    - Patient
      - New Assessment  
      - Follow-up
      - Treatment
    - Meeting
      - MDT Meeting
      - Family Meeting
    - Admin
      - Travel
    """
    
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100, description="Appointment type name")
    parent_id: Optional[int] = Field(None, description="Parent appointment type ID for hierarchy")
    practice_id: Optional[int] = Field(None, description="Practice ID (null for global types)")
    color: str = Field(default="#2D6356", description="Color hex code for UI display")
    duration: int = Field(default=30, ge=5, le=480, description="Default duration in minutes")
    description: Optional[str] = Field(None, max_length=500, description="Description of appointment type")
    is_active: bool = Field(default=True, description="Whether appointment type is active")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @field_validator('color')
    @classmethod
    def validate_color(cls, v: str) -> str:
        """Validate hex color format"""
        if not v.startswith('#') or len(v) != 7:
            raise ValueError('Color must be in hex format (#RRGGBB)')
        
        try:
            int(v[1:], 16)
        except ValueError:
            raise ValueError('Color must be valid hex format (#RRGGBB)')
        
        return v.upper()
    
    @field_validator('name')
    @classmethod  
    def validate_name(cls, v: str) -> str:
        """Validate and sanitize appointment type name"""
        name = v.strip()
        if not name:
            raise ValueError('Appointment type name cannot be empty')
        
        # Remove potentially dangerous characters but allow common punctuation
        import re
        if not re.match(r'^[a-zA-Z0-9\s\-_.()]+$', name):
            raise ValueError('Appointment type name contains invalid characters')
        
        return name
    
    @classmethod
    def create(cls, name: str, parent_id: Optional[int] = None, practice_id: Optional[int] = None,
               color: str = "#2D6356", duration: int = 30, description: Optional[str] = None) -> "AppointmentType":
        """
        Create a new appointment type
        
        Args:
            name: Appointment type name
            parent_id: Parent appointment type ID for hierarchy
            practice_id: Practice ID (null for global types)
            color: Color hex code
            duration: Default duration in minutes  
            description: Description of appointment type
            
        Returns:
            Created AppointmentType instance
            
        Raises:
            ValueError: If validation fails or duplicate name exists
        """
        # Validate input
        appointment_type = cls(
            name=name, parent_id=parent_id, practice_id=practice_id,
            color=color, duration=duration, description=description
        )
        
        # Check for duplicate names within same practice/parent
        # Handle NULL parent_id comparison correctly
        if parent_id is None:
            existing = execute_query("""
                SELECT id FROM appointment_types 
                WHERE name = ? AND practice_id = ? AND parent_id IS NULL
            """, (name, practice_id), fetch='one')
        else:
            existing = execute_query("""
                SELECT id FROM appointment_types 
                WHERE name = ? AND practice_id = ? AND parent_id = ?
            """, (name, practice_id, parent_id), fetch='one')
        
        if existing:
            raise ValueError(f"Appointment type '{name}' already exists in this context")
        
        # Insert into database
        from modules.database import get_db_connection
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO appointment_types (name, parent_id, practice_id, color, duration, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, parent_id, practice_id, color, duration, description))
            
            appointment_type_id = cursor.lastrowid
            conn.commit()
            
            # Get the created record
            created = execute_query("""
                SELECT * FROM appointment_types WHERE id = ?
            """, (appointment_type_id,), fetch='one')
        finally:
            conn.close()
        
        return cls.from_db_row(created)
    
    @classmethod
    def get_by_id(cls, appointment_type_id: int) -> Optional["AppointmentType"]:
        """
        Get appointment type by ID
        
        Args:
            appointment_type_id: Appointment type ID
            
        Returns:
            AppointmentType instance or None if not found
        """
        row = execute_query("""
            SELECT * FROM appointment_types WHERE id = ?
        """, (appointment_type_id,), fetch='one')
        
        return cls.from_db_row(row) if row else None
    
    @classmethod
    def get_by_practice(cls, practice_id: Optional[int] = None, include_global: bool = True,
                       active_only: bool = True) -> List["AppointmentType"]:
        """
        Get appointment types for a practice
        
        Args:
            practice_id: Practice ID (None for global types only)
            include_global: Whether to include global types (practice_id=null)
            active_only: Whether to return only active appointment types
            
        Returns:
            List of AppointmentType instances
        """
        conditions = []
        params = []
        
        if practice_id is not None and include_global:
            conditions.append("(practice_id = ? OR practice_id IS NULL)")
            params.append(practice_id)
        elif practice_id is not None:
            conditions.append("practice_id = ?")
            params.append(practice_id)
        else:
            conditions.append("practice_id IS NULL")
        
        if active_only:
            conditions.append("is_active = 1")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        rows = execute_query(f"""
            SELECT * FROM appointment_types 
            WHERE {where_clause}
            ORDER BY name
        """, tuple(params), fetch='all')
        
        return [cls.from_db_row(row) for row in rows]
    
    @classmethod
    def get_hierarchical(cls, practice_id: Optional[int] = None, 
                        active_only: bool = True) -> Dict[str, Any]:
        """
        Get appointment types organized in hierarchical structure
        
        Args:
            practice_id: Practice ID
            active_only: Whether to return only active types
            
        Returns:
            Dictionary with hierarchical structure of appointment types
        """
        types = cls.get_by_practice(practice_id, include_global=True, active_only=active_only)
        
        # Organize into hierarchy
        hierarchy = {}
        type_map = {t.id: t for t in types}
        
        for appointment_type in types:
            if appointment_type.parent_id is None:
                # Root level appointment type
                if appointment_type.id not in hierarchy:
                    hierarchy[appointment_type.id] = {
                        'appointment_type': appointment_type,
                        'children': {}
                    }
            else:
                # Child appointment type
                parent_id = appointment_type.parent_id
                
                # Ensure parent exists in hierarchy
                if parent_id not in hierarchy:
                    parent = type_map.get(parent_id)
                    if parent:
                        hierarchy[parent_id] = {
                            'appointment_type': parent,
                            'children': {}
                        }
                
                # Add child to parent
                if parent_id in hierarchy:
                    hierarchy[parent_id]['children'][appointment_type.id] = {
                        'appointment_type': appointment_type,
                        'children': {}
                    }
        
        return hierarchy
    
    def get_children(self) -> List["AppointmentType"]:
        """
        Get direct children of this appointment type
        
        Returns:
            List of child AppointmentType instances
        """
        if self.id is None:
            return []
        
        rows = execute_query("""
            SELECT * FROM appointment_types 
            WHERE parent_id = ? AND is_active = 1
            ORDER BY name
        """, (self.id,), fetch='all')
        
        return [AppointmentType.from_db_row(row) for row in rows]
    
    def get_parent(self) -> Optional["AppointmentType"]:
        """
        Get parent appointment type
        
        Returns:
            Parent AppointmentType instance or None if no parent
        """
        if self.parent_id is None:
            return None
        
        return AppointmentType.get_by_id(self.parent_id)
    
    def get_ancestors(self) -> List["AppointmentType"]:
        """
        Get all ancestors of this appointment type (parent, grandparent, etc.)
        
        Returns:
            List of ancestor AppointmentType instances ordered from immediate parent to root
        """
        ancestors = []
        current_parent = self.get_parent()
        
        while current_parent:
            ancestors.append(current_parent)
            current_parent = current_parent.get_parent()
        
        return ancestors
    
    def get_full_path(self) -> str:
        """
        Get full hierarchical path of this appointment type
        
        Returns:
            String path like "Patient > Assessment > New Assessment"
        """
        ancestors = self.get_ancestors()
        ancestors.reverse()  # Start from root
        
        path_parts = [a.name for a in ancestors] + [self.name]
        return " > ".join(path_parts)
    
    def update(self, **kwargs) -> "AppointmentType":
        """
        Update appointment type fields
        
        Args:
            **kwargs: Fields to update
            
        Returns:
            Updated AppointmentType instance
        """
        if self.id is None:
            raise ValueError("Cannot update appointment type without ID")
        
        # Validate allowed fields
        allowed_fields = {'name', 'parent_id', 'color', 'duration', 'description', 'is_active'}
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not update_fields:
            return self
        
        # Build update query
        set_clauses = [f"{field} = ?" for field in update_fields.keys()]
        values = list(update_fields.values()) + [self.id]
        
        execute_query(f"""
            UPDATE appointment_types 
            SET {', '.join(set_clauses)}
            WHERE id = ?
        """, tuple(values))
        
        # Return updated instance
        return AppointmentType.get_by_id(self.id)
    
    def delete(self) -> bool:
        """
        Delete appointment type (soft delete by setting is_active = False)
        
        Returns:
            True if deleted successfully, False otherwise
        """
        if self.id is None:
            return False
        
        # Check if has children
        children = self.get_children()
        if children:
            raise ValueError("Cannot delete appointment type with active children")
        
        # Soft delete
        execute_query("""
            UPDATE appointment_types SET is_active = 0 WHERE id = ?
        """, (self.id,))
        
        return True
    
    @classmethod
    def from_db_row(cls, row) -> "AppointmentType":
        """
        Create AppointmentType instance from database row
        
        Args:
            row: Database row (sqlite3.Row)
            
        Returns:
            AppointmentType instance
        """
        return cls(
            id=row['id'],
            name=row['name'],
            parent_id=row['parent_id'],
            practice_id=row['practice_id'],
            color=row['color'],
            duration=row['duration'],
            description=row['description'],
            is_active=bool(row['is_active']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )


class PracticeAppointmentType(BaseModel):
    """
    Model for practice-specific appointment type customizations
    
    Allows practices to customize appointment types with:
    - Custom default duration
    - Default billing codes  
    - Default notes/templates
    - Enable/disable specific types
    - Sort order for UI
    """
    
    id: Optional[int] = None
    practice_id: int = Field(..., description="Practice ID")
    appointment_type_id: int = Field(..., description="Appointment type ID")
    default_duration: Optional[int] = Field(None, ge=5, le=480, description="Custom default duration in minutes")
    default_billing_code: Optional[str] = Field(None, max_length=20, description="Default billing code")
    default_notes: Optional[str] = Field(None, max_length=1000, description="Default notes template")
    is_enabled: bool = Field(default=True, description="Whether this appointment type is enabled for the practice")
    sort_order: int = Field(default=0, description="Sort order for UI display")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @field_validator('default_billing_code')
    @classmethod
    def validate_billing_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate billing code format"""
        if v is None:
            return v
        
        # Billing codes should be alphanumeric with dashes allowed
        import re
        if not re.match(r'^[A-Z0-9\-]+$', v.upper()):
            raise ValueError('Billing code should contain only letters, numbers, and dashes')
        
        return v.upper()
    
    @classmethod
    def create(cls, practice_id: int, appointment_type_id: int, 
               default_duration: Optional[int] = None, default_billing_code: Optional[str] = None,
               default_notes: Optional[str] = None, is_enabled: bool = True,
               sort_order: int = 0) -> "PracticeAppointmentType":
        """
        Create practice-specific appointment type customization
        
        Args:
            practice_id: Practice ID
            appointment_type_id: Appointment type ID
            default_duration: Custom default duration
            default_billing_code: Default billing code
            default_notes: Default notes template
            is_enabled: Whether enabled for practice
            sort_order: Sort order for UI
            
        Returns:
            Created PracticeAppointmentType instance
            
        Raises:
            ValueError: If validation fails or duplicate exists
        """
        # Validate input
        practice_type = cls(
            practice_id=practice_id,
            appointment_type_id=appointment_type_id,
            default_duration=default_duration,
            default_billing_code=default_billing_code,
            default_notes=default_notes,
            is_enabled=is_enabled,
            sort_order=sort_order
        )
        
        # Check for duplicate
        existing = execute_query("""
            SELECT id FROM practice_appointment_types 
            WHERE practice_id = ? AND appointment_type_id = ?
        """, (practice_id, appointment_type_id), fetch='one')
        
        if existing:
            raise ValueError(f"Practice customization already exists for this appointment type")
        
        # Verify appointment type exists
        appointment_type = AppointmentType.get_by_id(appointment_type_id)
        if not appointment_type:
            raise ValueError(f"Appointment type {appointment_type_id} does not exist")
        
        # Insert into database
        from modules.database import get_db_connection
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO practice_appointment_types 
                (practice_id, appointment_type_id, default_duration, default_billing_code, 
                 default_notes, is_enabled, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (practice_id, appointment_type_id, default_duration, default_billing_code,
                  default_notes, is_enabled, sort_order))
            
            practice_type_id = cursor.lastrowid
            conn.commit()
            
            # Get the created record
            created = execute_query("""
                SELECT * FROM practice_appointment_types WHERE id = ?
            """, (practice_type_id,), fetch='one')
        finally:
            conn.close()
        
        return cls.from_db_row(created)
    
    @classmethod
    def get_by_id(cls, practice_type_id: int) -> Optional["PracticeAppointmentType"]:
        """
        Get practice appointment type by ID
        
        Args:
            practice_type_id: Practice appointment type ID
            
        Returns:
            PracticeAppointmentType instance or None if not found
        """
        row = execute_query("""
            SELECT * FROM practice_appointment_types WHERE id = ?
        """, (practice_type_id,), fetch='one')
        
        return cls.from_db_row(row) if row else None
    
    @classmethod
    def get_by_practice(cls, practice_id: int, enabled_only: bool = True) -> List["PracticeAppointmentType"]:
        """
        Get all practice appointment type customizations for a practice
        
        Args:
            practice_id: Practice ID
            enabled_only: Whether to return only enabled customizations
            
        Returns:
            List of PracticeAppointmentType instances
        """
        conditions = ["practice_id = ?"]
        params = [practice_id]
        
        if enabled_only:
            conditions.append("is_enabled = 1")
        
        where_clause = " AND ".join(conditions)
        
        rows = execute_query(f"""
            SELECT * FROM practice_appointment_types 
            WHERE {where_clause}
            ORDER BY sort_order, id
        """, tuple(params), fetch='all')
        
        return [cls.from_db_row(row) for row in rows]
    
    @classmethod
    def get_by_appointment_type(cls, appointment_type_id: int) -> List["PracticeAppointmentType"]:
        """
        Get all practice customizations for a specific appointment type
        
        Args:
            appointment_type_id: Appointment type ID
            
        Returns:
            List of PracticeAppointmentType instances
        """
        rows = execute_query("""
            SELECT * FROM practice_appointment_types 
            WHERE appointment_type_id = ?
            ORDER BY practice_id
        """, (appointment_type_id,), fetch='all')
        
        return [cls.from_db_row(row) for row in rows]
    
    @classmethod
    def get_for_practice_and_type(cls, practice_id: int, 
                                 appointment_type_id: int) -> Optional["PracticeAppointmentType"]:
        """
        Get specific practice customization for an appointment type
        
        Args:
            practice_id: Practice ID
            appointment_type_id: Appointment type ID
            
        Returns:
            PracticeAppointmentType instance or None if not found
        """
        row = execute_query("""
            SELECT * FROM practice_appointment_types 
            WHERE practice_id = ? AND appointment_type_id = ?
        """, (practice_id, appointment_type_id), fetch='one')
        
        return cls.from_db_row(row) if row else None
    
    def get_appointment_type(self) -> Optional[AppointmentType]:
        """
        Get the associated appointment type
        
        Returns:
            AppointmentType instance or None if not found
        """
        return AppointmentType.get_by_id(self.appointment_type_id)
    
    def get_effective_duration(self) -> int:
        """
        Get effective duration (custom duration or appointment type default)
        
        Returns:
            Effective duration in minutes
        """
        if self.default_duration is not None:
            return self.default_duration
        
        appointment_type = self.get_appointment_type()
        return appointment_type.duration if appointment_type else 30
    
    def update(self, **kwargs) -> "PracticeAppointmentType":
        """
        Update practice appointment type customization
        
        Args:
            **kwargs: Fields to update
            
        Returns:
            Updated PracticeAppointmentType instance
        """
        if self.id is None:
            raise ValueError("Cannot update practice appointment type without ID")
        
        # Validate allowed fields
        allowed_fields = {
            'default_duration', 'default_billing_code', 'default_notes', 
            'is_enabled', 'sort_order'
        }
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not update_fields:
            return self
        
        # Build update query
        set_clauses = [f"{field} = ?" for field in update_fields.keys()]
        values = list(update_fields.values()) + [self.id]
        
        execute_query(f"""
            UPDATE practice_appointment_types 
            SET {', '.join(set_clauses)}
            WHERE id = ?
        """, tuple(values))
        
        # Return updated instance
        return PracticeAppointmentType.get_by_id(self.id)
    
    def delete(self) -> bool:
        """
        Delete practice appointment type customization
        
        Returns:
            True if deleted successfully, False otherwise
        """
        if self.id is None:
            return False
        
        execute_query("""
            DELETE FROM practice_appointment_types WHERE id = ?
        """, (self.id,))
        
        return True
    
    @classmethod
    def from_db_row(cls, row) -> "PracticeAppointmentType":
        """
        Create PracticeAppointmentType instance from database row
        
        Args:
            row: Database row (sqlite3.Row)
            
        Returns:
            PracticeAppointmentType instance
        """
        return cls(
            id=row['id'],
            practice_id=row['practice_id'],
            appointment_type_id=row['appointment_type_id'],
            default_duration=row['default_duration'],
            default_billing_code=row['default_billing_code'],
            default_notes=row['default_notes'],
            is_enabled=bool(row['is_enabled']),
            sort_order=row['sort_order'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )