"""
AppointmentType API Controllers for HadadaHealth

Provides RESTful API endpoints for managing appointment types with hierarchical structure
and practice-specific customizations.
"""
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, Query, Path
from pydantic import BaseModel, Field

from models.appointment_types import AppointmentType, PracticeAppointmentType


class AppointmentTypeResponse(BaseModel):
    """Response model for appointment type data"""
    id: int
    name: str
    parent_id: Optional[int] = None
    practice_id: Optional[int] = None
    color: str
    duration: int
    description: Optional[str] = None
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AppointmentTypeCreateRequest(BaseModel):
    """Request model for creating appointment types"""
    name: str = Field(..., min_length=1, max_length=100, description="Appointment type name")
    parent_id: Optional[int] = Field(None, description="Parent appointment type ID for hierarchy")
    practice_id: Optional[int] = Field(None, description="Practice ID (null for global types)")
    color: str = Field(default="#2D6356", description="Color hex code for UI display")
    duration: int = Field(default=30, ge=5, le=480, description="Default duration in minutes")
    description: Optional[str] = Field(None, max_length=500, description="Description of appointment type")


class AppointmentTypeUpdateRequest(BaseModel):
    """Request model for updating appointment types"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Appointment type name")
    parent_id: Optional[int] = Field(None, description="Parent appointment type ID for hierarchy")
    color: Optional[str] = Field(None, description="Color hex code for UI display")
    duration: Optional[int] = Field(None, ge=5, le=480, description="Default duration in minutes")
    description: Optional[str] = Field(None, max_length=500, description="Description of appointment type")
    is_active: Optional[bool] = Field(None, description="Whether appointment type is active")


class HierarchicalAppointmentTypeResponse(BaseModel):
    """Response model for hierarchical appointment type structure"""
    appointment_type: AppointmentTypeResponse
    children: Dict[int, "HierarchicalAppointmentTypeResponse"]


class AppointmentTypeController:
    """Controller for AppointmentType CRUD operations"""
    
    @staticmethod
    def index(
        hierarchical: bool = Query(False, description="Return hierarchical structure"),
        practice_id: Optional[int] = Query(None, description="Filter by practice ID"),
        active_only: bool = Query(True, description="Return only active appointment types"),
        parent_only: bool = Query(False, description="Return only parent (root level) types"),
        include_global: bool = Query(True, description="Include global appointment types")
    ) -> List[AppointmentTypeResponse] | Dict[str, Any]:
        """
        Get list of appointment types with optional filtering and hierarchical structure
        
        Returns:
            List of appointment types or hierarchical structure based on parameters
        """
        try:
            if hierarchical:
                # Return hierarchical structure
                hierarchy = AppointmentType.get_hierarchical(
                    practice_id=practice_id, 
                    active_only=active_only
                )
                
                # Convert to response format
                response_hierarchy = {}
                for parent_id, data in hierarchy.items():
                    parent_type = data['appointment_type']
                    children = data['children']
                    
                    response_hierarchy[str(parent_id)] = {
                        "appointment_type": AppointmentTypeController._to_response_model(parent_type),
                        "children": AppointmentTypeController._convert_children_to_response(children)
                    }
                
                return response_hierarchy
            else:
                # Return flat list
                if parent_only:
                    # Get only parent types (parent_id is None)
                    appointment_types = []
                    all_types = AppointmentType.get_by_practice(
                        practice_id=practice_id, 
                        include_global=include_global, 
                        active_only=active_only
                    )
                    appointment_types = [at for at in all_types if at.parent_id is None]
                else:
                    appointment_types = AppointmentType.get_by_practice(
                        practice_id=practice_id, 
                        include_global=include_global, 
                        active_only=active_only
                    )
                
                return [AppointmentTypeController._to_response_model(at) for at in appointment_types]
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch appointment types: {str(e)}")
    
    @staticmethod
    def show(appointment_type_id: int = Path(..., description="Appointment type ID")) -> AppointmentTypeResponse:
        """
        Get a specific appointment type by ID
        
        Args:
            appointment_type_id: ID of the appointment type to retrieve
            
        Returns:
            AppointmentType data
            
        Raises:
            HTTPException: 404 if appointment type not found
        """
        try:
            appointment_type = AppointmentType.get_by_id(appointment_type_id)
            
            if not appointment_type:
                raise HTTPException(status_code=404, detail="Appointment type not found")
            
            return AppointmentTypeController._to_response_model(appointment_type)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch appointment type: {str(e)}")
    
    @staticmethod
    def store(request: AppointmentTypeCreateRequest) -> AppointmentTypeResponse:
        """
        Create a new appointment type
        
        Args:
            request: Appointment type creation data
            
        Returns:
            Created appointment type data
            
        Raises:
            HTTPException: 422 for validation errors, 500 for server errors
        """
        try:
            appointment_type = AppointmentType.create(
                name=request.name,
                parent_id=request.parent_id,
                practice_id=request.practice_id,
                color=request.color,
                duration=request.duration,
                description=request.description
            )
            
            return AppointmentTypeController._to_response_model(appointment_type)
            
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create appointment type: {str(e)}")
    
    @staticmethod
    def update(
        appointment_type_id: int = Path(..., description="Appointment type ID"),
        request: AppointmentTypeUpdateRequest = None
    ) -> AppointmentTypeResponse:
        """
        Update an existing appointment type
        
        Args:
            appointment_type_id: ID of the appointment type to update
            request: Update data
            
        Returns:
            Updated appointment type data
            
        Raises:
            HTTPException: 404 if not found, 422 for validation errors, 500 for server errors
        """
        try:
            appointment_type = AppointmentType.get_by_id(appointment_type_id)
            
            if not appointment_type:
                raise HTTPException(status_code=404, detail="Appointment type not found")
            
            # Build update data from non-None fields
            update_data = {}
            if request.name is not None:
                update_data['name'] = request.name
            if request.parent_id is not None:
                update_data['parent_id'] = request.parent_id
            if request.color is not None:
                update_data['color'] = request.color
            if request.duration is not None:
                update_data['duration'] = request.duration
            if request.description is not None:
                update_data['description'] = request.description
            if request.is_active is not None:
                update_data['is_active'] = request.is_active
            
            if update_data:
                appointment_type = appointment_type.update(**update_data)
            
            return AppointmentTypeController._to_response_model(appointment_type)
            
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update appointment type: {str(e)}")
    
    @staticmethod
    def destroy(appointment_type_id: int = Path(..., description="Appointment type ID")) -> None:
        """
        Delete (soft delete) an appointment type
        
        Args:
            appointment_type_id: ID of the appointment type to delete
            
        Raises:
            HTTPException: 404 if not found, 422 for validation errors, 500 for server errors
        """
        try:
            appointment_type = AppointmentType.get_by_id(appointment_type_id)
            
            if not appointment_type:
                raise HTTPException(status_code=404, detail="Appointment type not found")
            
            success = appointment_type.delete()
            
            if not success:
                raise HTTPException(status_code=422, detail="Failed to delete appointment type")
                
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete appointment type: {str(e)}")
    
    @staticmethod
    def get_by_practice(
        practice_id: int = Path(..., description="Practice ID"),
        active_only: bool = Query(True, description="Return only active appointment types"),
        include_global: bool = Query(True, description="Include global appointment types")
    ) -> List[AppointmentTypeResponse]:
        """
        Get appointment types for a specific practice
        
        Args:
            practice_id: Practice ID to filter by
            active_only: Whether to return only active types
            include_global: Whether to include global types
            
        Returns:
            List of appointment types for the practice
        """
        try:
            appointment_types = AppointmentType.get_by_practice(
                practice_id=practice_id,
                include_global=include_global,
                active_only=active_only
            )
            
            return [AppointmentTypeController._to_response_model(at) for at in appointment_types]
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch practice appointment types: {str(e)}")
    
    @staticmethod
    def _to_response_model(appointment_type: AppointmentType) -> AppointmentTypeResponse:
        """Convert AppointmentType model to response format"""
        return AppointmentTypeResponse(
            id=appointment_type.id,
            name=appointment_type.name,
            parent_id=appointment_type.parent_id,
            practice_id=appointment_type.practice_id,
            color=appointment_type.color,
            duration=appointment_type.duration,
            description=appointment_type.description,
            is_active=appointment_type.is_active,
            created_at=appointment_type.created_at.isoformat() if appointment_type.created_at else None,
            updated_at=appointment_type.updated_at.isoformat() if appointment_type.updated_at else None
        )
    
    @staticmethod
    def _convert_children_to_response(children: Dict[int, Dict]) -> Dict[str, Dict]:
        """Convert children dictionary to response format recursively"""
        response_children = {}
        
        for child_id, child_data in children.items():
            child_type = child_data['appointment_type']
            grandchildren = child_data['children']
            
            response_children[str(child_id)] = {
                "appointment_type": AppointmentTypeController._to_response_model(child_type),
                "children": AppointmentTypeController._convert_children_to_response(grandchildren)
            }
        
        return response_children


class PracticeAppointmentTypeResponse(BaseModel):
    """Response model for practice appointment type customizations"""
    id: int
    practice_id: int
    appointment_type_id: int
    default_duration: Optional[int] = None
    default_billing_code: Optional[str] = None
    default_notes: Optional[str] = None
    is_enabled: bool
    sort_order: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    # Include appointment type details for convenience
    appointment_type: Optional[AppointmentTypeResponse] = None


class PracticeAppointmentTypeCreateRequest(BaseModel):
    """Request model for creating practice appointment type customizations"""
    appointment_type_id: int = Field(..., description="Appointment type ID")
    default_duration: Optional[int] = Field(None, ge=5, le=480, description="Custom default duration")
    default_billing_code: Optional[str] = Field(None, max_length=20, description="Default billing code")
    default_notes: Optional[str] = Field(None, max_length=1000, description="Default notes template")
    is_enabled: bool = Field(default=True, description="Whether enabled for practice")
    sort_order: int = Field(default=0, description="Sort order for UI")


class PracticeAppointmentTypeUpdateRequest(BaseModel):
    """Request model for updating practice appointment type customizations"""
    default_duration: Optional[int] = Field(None, ge=5, le=480, description="Custom default duration")
    default_billing_code: Optional[str] = Field(None, max_length=20, description="Default billing code")
    default_notes: Optional[str] = Field(None, max_length=1000, description="Default notes template")
    is_enabled: Optional[bool] = Field(None, description="Whether enabled for practice")
    sort_order: Optional[int] = Field(None, description="Sort order for UI")


class EffectiveAppointmentTypeResponse(BaseModel):
    """Response model for appointment types with effective settings"""
    id: int
    name: str
    parent_id: Optional[int] = None
    practice_id: Optional[int] = None
    color: str
    duration: int  # Base duration
    description: Optional[str] = None
    is_active: bool
    # Effective settings (from customization if exists, else defaults)
    effective_duration: int
    default_billing_code: Optional[str] = None
    default_notes: Optional[str] = None
    is_enabled: bool
    sort_order: int
    has_customization: bool


class PracticeAppointmentTypeController:
    """Controller for PracticeAppointmentType CRUD operations"""
    
    @staticmethod
    def index(
        practice_id: int = Path(..., description="Practice ID"),
        enabled_only: bool = Query(True, description="Return only enabled customizations")
    ) -> List[PracticeAppointmentTypeResponse]:
        """
        Get practice appointment type customizations
        
        Args:
            practice_id: Practice ID
            enabled_only: Whether to return only enabled customizations
            
        Returns:
            List of practice appointment type customizations
        """
        try:
            customizations = PracticeAppointmentType.get_by_practice(
                practice_id=practice_id,
                enabled_only=enabled_only
            )
            
            response_list = []
            for customization in customizations:
                response = PracticeAppointmentTypeController._to_response_model(customization)
                
                # Include appointment type details
                appointment_type = customization.get_appointment_type()
                if appointment_type:
                    response.appointment_type = AppointmentTypeController._to_response_model(appointment_type)
                
                response_list.append(response)
            
            return response_list
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch practice customizations: {str(e)}")
    
    @staticmethod
    def show(
        practice_id: int = Path(..., description="Practice ID"),
        customization_id: int = Path(..., description="Customization ID")
    ) -> PracticeAppointmentTypeResponse:
        """
        Get a specific practice appointment type customization
        
        Args:
            practice_id: Practice ID
            customization_id: Customization ID
            
        Returns:
            Practice appointment type customization data
            
        Raises:
            HTTPException: 404 if customization not found
        """
        try:
            customization = PracticeAppointmentType.get_by_id(customization_id)
            
            if not customization or customization.practice_id != practice_id:
                raise HTTPException(status_code=404, detail="Practice customization not found")
            
            response = PracticeAppointmentTypeController._to_response_model(customization)
            
            # Include appointment type details
            appointment_type = customization.get_appointment_type()
            if appointment_type:
                response.appointment_type = AppointmentTypeController._to_response_model(appointment_type)
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch customization: {str(e)}")
    
    @staticmethod
    def store(
        practice_id: int = Path(..., description="Practice ID"),
        request: PracticeAppointmentTypeCreateRequest = None
    ) -> PracticeAppointmentTypeResponse:
        """
        Create a new practice appointment type customization
        
        Args:
            practice_id: Practice ID
            request: Customization creation data
            
        Returns:
            Created customization data
            
        Raises:
            HTTPException: 422 for validation errors, 500 for server errors
        """
        try:
            customization = PracticeAppointmentType.create(
                practice_id=practice_id,
                appointment_type_id=request.appointment_type_id,
                default_duration=request.default_duration,
                default_billing_code=request.default_billing_code,
                default_notes=request.default_notes,
                is_enabled=request.is_enabled,
                sort_order=request.sort_order
            )
            
            response = PracticeAppointmentTypeController._to_response_model(customization)
            
            # Include appointment type details
            appointment_type = customization.get_appointment_type()
            if appointment_type:
                response.appointment_type = AppointmentTypeController._to_response_model(appointment_type)
            
            return response
            
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create customization: {str(e)}")
    
    @staticmethod
    def update(
        practice_id: int = Path(..., description="Practice ID"),
        customization_id: int = Path(..., description="Customization ID"),
        request: PracticeAppointmentTypeUpdateRequest = None
    ) -> PracticeAppointmentTypeResponse:
        """
        Update a practice appointment type customization
        
        Args:
            practice_id: Practice ID
            customization_id: Customization ID
            request: Update data
            
        Returns:
            Updated customization data
            
        Raises:
            HTTPException: 404 if not found, 422 for validation errors, 500 for server errors
        """
        try:
            customization = PracticeAppointmentType.get_by_id(customization_id)
            
            if not customization or customization.practice_id != practice_id:
                raise HTTPException(status_code=404, detail="Practice customization not found")
            
            # Build update data from non-None fields
            update_data = {}
            if request.default_duration is not None:
                update_data['default_duration'] = request.default_duration
            if request.default_billing_code is not None:
                update_data['default_billing_code'] = request.default_billing_code
            if request.default_notes is not None:
                update_data['default_notes'] = request.default_notes
            if request.is_enabled is not None:
                update_data['is_enabled'] = request.is_enabled
            if request.sort_order is not None:
                update_data['sort_order'] = request.sort_order
            
            if update_data:
                customization = customization.update(**update_data)
            
            response = PracticeAppointmentTypeController._to_response_model(customization)
            
            # Include appointment type details
            appointment_type = customization.get_appointment_type()
            if appointment_type:
                response.appointment_type = AppointmentTypeController._to_response_model(appointment_type)
            
            return response
            
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update customization: {str(e)}")
    
    @staticmethod
    def destroy(
        practice_id: int = Path(..., description="Practice ID"),
        customization_id: int = Path(..., description="Customization ID")
    ) -> None:
        """
        Delete a practice appointment type customization
        
        Args:
            practice_id: Practice ID
            customization_id: Customization ID
            
        Raises:
            HTTPException: 404 if not found, 500 for server errors
        """
        try:
            customization = PracticeAppointmentType.get_by_id(customization_id)
            
            if not customization or customization.practice_id != practice_id:
                raise HTTPException(status_code=404, detail="Practice customization not found")
            
            success = customization.delete()
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to delete customization")
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete customization: {str(e)}")
    
    @staticmethod
    def get_effective_types(
        practice_id: int = Path(..., description="Practice ID"),
        active_only: bool = Query(True, description="Return only active appointment types"),
        enabled_only: bool = Query(True, description="Return only enabled types for practice")
    ) -> List[EffectiveAppointmentTypeResponse]:
        """
        Get appointment types with effective settings (merged with customizations)
        
        Args:
            practice_id: Practice ID
            active_only: Whether to return only active appointment types
            enabled_only: Whether to return only enabled types for practice
            
        Returns:
            List of appointment types with effective settings
        """
        try:
            # Get all appointment types for the practice
            appointment_types = AppointmentType.get_by_practice(
                practice_id=practice_id,
                include_global=True,
                active_only=active_only
            )
            
            # Get all customizations for the practice
            customizations = PracticeAppointmentType.get_by_practice(
                practice_id=practice_id,
                enabled_only=enabled_only
            )
            
            # Create lookup for customizations by appointment_type_id
            customizations_map = {c.appointment_type_id: c for c in customizations}
            
            effective_types = []
            
            for appointment_type in appointment_types:
                customization = customizations_map.get(appointment_type.id)
                
                # Skip if enabled_only=True and no customization exists (default disabled)
                if enabled_only and customization is None:
                    continue
                
                # Skip if customization exists but is disabled
                if customization and not customization.is_enabled:
                    continue
                
                effective_type = EffectiveAppointmentTypeResponse(
                    id=appointment_type.id,
                    name=appointment_type.name,
                    parent_id=appointment_type.parent_id,
                    practice_id=appointment_type.practice_id,
                    color=appointment_type.color,
                    duration=appointment_type.duration,
                    description=appointment_type.description,
                    is_active=appointment_type.is_active,
                    
                    # Effective settings
                    effective_duration=customization.get_effective_duration() if customization else appointment_type.duration,
                    default_billing_code=customization.default_billing_code if customization else None,
                    default_notes=customization.default_notes if customization else None,
                    is_enabled=customization.is_enabled if customization else True,
                    sort_order=customization.sort_order if customization else 0,
                    has_customization=customization is not None
                )
                
                effective_types.append(effective_type)
            
            # Sort by sort_order, then by name
            effective_types.sort(key=lambda x: (x.sort_order, x.name))
            
            return effective_types
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch effective types: {str(e)}")
    
    @staticmethod
    def _to_response_model(customization: PracticeAppointmentType) -> PracticeAppointmentTypeResponse:
        """Convert PracticeAppointmentType model to response format"""
        return PracticeAppointmentTypeResponse(
            id=customization.id,
            practice_id=customization.practice_id,
            appointment_type_id=customization.appointment_type_id,
            default_duration=customization.default_duration,
            default_billing_code=customization.default_billing_code,
            default_notes=customization.default_notes,
            is_enabled=customization.is_enabled,
            sort_order=customization.sort_order,
            created_at=customization.created_at.isoformat() if customization.created_at else None,
            updated_at=customization.updated_at.isoformat() if customization.updated_at else None
        )