"""
Comprehensive input validation models for HadadaHealth
Implements data validation, sanitization, and security checks for all user inputs
"""
import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator


def sanitize_string(value: str) -> str:
    """Sanitize string input to prevent injection attacks"""
    if not isinstance(value, str):
        return str(value)
    
    # Remove HTML tags and script elements
    value = re.sub(r'<[^>]*>', '', value)
    
    # Remove potentially dangerous characters
    value = re.sub(r'[<>"\']', '', value)
    
    # Normalize whitespace
    value = ' '.join(value.split())
    
    return value.strip()


def validate_sa_id_number(id_number: str) -> bool:
    """Validate South African ID number format and checksum"""
    if not id_number or len(id_number) != 13:
        return False
    
    if not id_number.isdigit():
        return False
    
    # Check date validity (first 6 digits: YYMMDD)
    try:
        year = int(id_number[:2])
        month = int(id_number[2:4])
        day = int(id_number[4:6])
        
        # Assume 1900s for years 30-99, 2000s for years 00-29
        full_year = 1900 + year if year >= 30 else 2000 + year
        
        date(full_year, month, day)
    except ValueError:
        return False
    
    # Luhn algorithm checksum validation
    digits = [int(d) for d in id_number]
    checksum = 0
    
    for i in range(12):
        if i % 2 == 0:
            checksum += digits[i]
        else:
            doubled = digits[i] * 2
            checksum += doubled // 10 + doubled % 10
    
    return (10 - (checksum % 10)) % 10 == digits[12]


def validate_sa_phone_number(phone: str) -> bool:
    """Validate South African phone number formats"""
    if not phone:
        return True  # Optional field
    
    # Remove spaces, dashes, and brackets
    clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Check various SA phone formats
    patterns = [
        r'^0[1-9]\d{8}$',      # 0XX XXX XXXX (10 digits)
        r'^\+27[1-9]\d{8}$',   # +27XX XXX XXXX
        r'^27[1-9]\d{8}$',     # 27XX XXX XXXX
        r'^0[8-9]\d{8}$',      # Mobile: 08X/09X
    ]
    
    return any(re.match(pattern, clean_phone) for pattern in patterns)


def validate_sa_postal_code(postal_code: str) -> bool:
    """Validate South African postal code (4 digits)"""
    if not postal_code:
        return False
    return len(postal_code) == 4 and postal_code.isdigit()


class PatientCreateModel(BaseModel):
    """Validated patient creation model with comprehensive field validation"""
    
    model_config = {"extra": "ignore"}  # Ignore extra fields instead of erroring
    
    # Personal Information
    title: Optional[str] = Field(None, max_length=10, description="Title (Mr., Mrs., Dr., etc.)")
    first_name: str = Field(..., min_length=1, max_length=50, description="Patient's first name")
    surname: str = Field(..., min_length=1, max_length=50, description="Patient's surname")
    preferred_name: Optional[str] = Field(None, max_length=50, description="Patient's preferred name")
    
    date_of_birth: Optional[str] = Field(None, description="Date of birth in YYYY-MM-DD format")
    gender: Optional[str] = Field(None, max_length=50, description="Patient's gender")
    id_number: Optional[str] = Field(None, min_length=13, max_length=13, description="South African ID number")
    
    # Contact Information
    email: Optional[EmailStr] = Field(None, description="Valid email address")
    contact_number: Optional[str] = Field(None, max_length=20, description="Primary contact number")
    phone_home: Optional[str] = Field(None, max_length=20, description="Home phone number")
    phone_work: Optional[str] = Field(None, max_length=20, description="Work phone number")
    phone_cell: Optional[str] = Field(None, max_length=20, description="Mobile phone number")
    clinic: Optional[str] = Field(None, max_length=100, description="Clinic name")
    
    # Address Information
    address_line1: Optional[str] = Field(None, max_length=100, description="Street address line 1")
    address_line2: Optional[str] = Field(None, max_length=100, description="Street address line 2")
    town: Optional[str] = Field(None, max_length=50, description="City/Town")
    postal_code: Optional[str] = Field(None, description="4-digit postal code")
    country: str = Field(default="South Africa", max_length=50, description="Country")
    
    # Account/Billing Information
    account_responsible: Optional[str] = Field(None, max_length=50, description="Who is responsible for the account")
    account_name: Optional[str] = Field(None, max_length=100, description="Account holder name")
    account_id_number: Optional[str] = Field(None, max_length=13, description="Account holder ID number")
    account_address: Optional[str] = Field(None, max_length=200, description="Account holder address")
    account_phone: Optional[str] = Field(None, max_length=20, description="Account holder phone")
    account_email: Optional[EmailStr] = Field(None, description="Account holder email")
    
    # Funding and Medical Aid Information
    funding_option: Optional[str] = Field(None, max_length=50, description="Funding option")
    main_member_name: Optional[str] = Field(None, max_length=100, description="Main member name")
    medical_aid_name: Optional[str] = Field(None, max_length=100, description="Medical aid scheme name")
    medical_aid_other: Optional[str] = Field(None, max_length=100, description="Other medical aid details")
    plan_name: Optional[str] = Field(None, max_length=50, description="Medical aid plan name")
    medical_aid_number: Optional[str] = Field(None, max_length=20, description="Medical aid member number")
    dependent_number: Optional[str] = Field(None, max_length=10, description="Dependent number")
    alternative_funding_source: Optional[str] = Field(None, max_length=100, description="Alternative funding source")
    alternative_funding_other: Optional[str] = Field(None, max_length=100, description="Other funding details")
    claim_number: Optional[str] = Field(None, max_length=50, description="Claim number")
    case_manager: Optional[str] = Field(None, max_length=100, description="Case manager name")
    
    # Emergency Contact
    emergency_contact_name: Optional[str] = Field(None, max_length=100, description="Emergency contact name")
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50, description="Relationship to patient")
    emergency_contact_phone: Optional[str] = Field(None, max_length=20, description="Emergency contact phone")
    
    # Consent and Additional Information
    patient_important_info: Optional[str] = Field(None, max_length=1000, description="Important patient information")
    consent_treatment: Optional[bool] = Field(None, description="Consent for treatment")
    consent_photography: Optional[bool] = Field(None, description="Consent for photography")
    consent_data: Optional[bool] = Field(None, description="Consent for data processing")
    consent_communication: Optional[bool] = Field(None, description="Consent for communication")
    consent_billing: Optional[bool] = Field(None, description="Consent for billing")
    consent_terms: Optional[bool] = Field(None, description="Consent to terms and conditions")
    
    # Signature Information
    signature_identity: Optional[str] = Field(None, max_length=100, description="Signature identity")
    signature_name: Optional[str] = Field(None, max_length=100, description="Signature name")
    signature_relationship: Optional[str] = Field(None, max_length=50, description="Signature relationship")
    signature_data: Optional[str] = Field(None, description="Signature data")
    
    @field_validator('title', 'first_name', 'surname', 'preferred_name', 'emergency_contact_name', 'main_member_name', 'account_name', 'case_manager', 'signature_name')
    @classmethod
    def sanitize_names(cls, v):
        if v:
            sanitized = sanitize_string(v)
            if not sanitized:
                raise ValueError('Name cannot be empty after sanitization')
            # Names should only contain letters, spaces, hyphens, and apostrophes
            if not re.match(r"^[a-zA-Z\s\-'.]+$", sanitized):
                raise ValueError('Name contains invalid characters')
            return sanitized
        return v
    
    @field_validator('id_number', 'account_id_number')
    @classmethod
    def validate_id_number(cls, v):
        if v and not validate_sa_id_number(v):
            raise ValueError('Invalid South African ID number format or checksum')
        return v
    
    @field_validator('date_of_birth')
    @classmethod
    def validate_date_of_birth(cls, v):
        if v is None:
            return v
        try:
            birth_date = datetime.strptime(v, '%Y-%m-%d').date()
            # Check if date is not in the future
            if birth_date > date.today():
                raise ValueError('Date of birth cannot be in the future')
            # Check if person is not older than 150 years
            if date.today().year - birth_date.year > 150:
                raise ValueError('Invalid date of birth - person would be over 150 years old')
            return v
        except ValueError as e:
            if 'does not match format' in str(e):
                raise ValueError('Date must be in YYYY-MM-DD format')
            raise e
    
    @field_validator('contact_number', 'phone_home', 'phone_work', 'phone_cell', 'emergency_contact_phone', 'account_phone')
    @classmethod
    def validate_phone_numbers(cls, v):
        if v and not validate_sa_phone_number(v):
            raise ValueError('Invalid South African phone number format')
        return v
    
    @field_validator('postal_code')
    @classmethod
    def validate_postal_code(cls, v):
        if v and not validate_sa_postal_code(v):
            raise ValueError('Postal code must be 4 digits')
        return v
    
    @field_validator('address_line1', 'address_line2', 'town', 'patient_important_info', 'clinic', 'account_address', 'funding_option', 'medical_aid_other', 'alternative_funding_source', 'alternative_funding_other', 'claim_number', 'signature_identity', 'signature_relationship')
    @classmethod
    def sanitize_text_fields(cls, v):
        if v:
            sanitized = sanitize_string(v)
            # Don't require non-empty after sanitization for optional fields
            return sanitized
        return v
    
    @field_validator('medical_aid_number')
    @classmethod
    def validate_medical_aid_number(cls, v):
        if v:
            # Remove spaces and dashes
            clean_number = re.sub(r'[\s\-]', '', v)
            if not re.match(r'^[A-Z0-9]{6,20}$', clean_number):
                raise ValueError('Medical aid number should be 6-20 alphanumeric characters')
            return clean_number
        return v
    
    @field_validator('medical_aid_name', 'plan_name')
    @classmethod
    def sanitize_medical_fields(cls, v):
        if v:
            return sanitize_string(v)
        return v
    
    @field_validator('gender')
    @classmethod
    def normalize_gender(cls, v):
        """Normalize gender values to handle different frontend formats"""
        if not v:
            return v
        
        # Convert to lowercase for comparison
        gender_lower = str(v).lower().strip()
        
        # Map common variations to standard values
        gender_mappings = {
            'male': 'Male',
            'm': 'Male',
            'man': 'Male',
            'boy': 'Male',
            'female': 'Female', 
            'f': 'Female',
            'woman': 'Female',
            'girl': 'Female',
            'other': 'Other',
            'non-binary': 'Other',
            'nonbinary': 'Other',
            'prefer not to say': 'Prefer not to say',
            'prefer_not_to_say': 'Prefer not to say',
            'no answer': 'Prefer not to say',
            'decline': 'Prefer not to say',
            '': None,
            'null': None,
            'none': None,
            'n/a': None
        }
        
        # Return mapped value or original if no mapping found
        normalized = gender_mappings.get(gender_lower, v)
        
        # Sanitize if it's a string
        if normalized:
            normalized = sanitize_string(str(normalized))
        
        return normalized
    
    @model_validator(mode="before")
    @classmethod
    def handle_business_logic(cls, values):
        """Handle business logic for auto-completion and conditional fields"""
        
        # Get funding option to determine what fields are needed
        funding_option = values.get('funding_option', '').lower() if values.get('funding_option') else ''
        
        # Handle account responsibility logic
        account_responsible = values.get('account_responsible', '').lower() if values.get('account_responsible') else ''
        
        # If patient is responsible for account, copy patient details to account fields
        if account_responsible == 'patient' or account_responsible == 'self':
            # Copy patient details to account fields
            if not values.get('account_name') and values.get('first_name') and values.get('surname'):
                values['account_name'] = f"{values.get('first_name', '')} {values.get('surname', '')}".strip()
            
            if not values.get('account_id_number') and values.get('id_number'):
                values['account_id_number'] = values.get('id_number')
            
            if not values.get('account_email') and values.get('email'):
                values['account_email'] = values.get('email')
            
            if not values.get('account_phone') and values.get('contact_number'):
                values['account_phone'] = values.get('contact_number')
            
            # Build address from patient address
            if not values.get('account_address'):
                address_parts = []
                if values.get('address_line1'):
                    address_parts.append(values.get('address_line1'))
                if values.get('address_line2'):
                    address_parts.append(values.get('address_line2'))
                if values.get('town'):
                    address_parts.append(values.get('town'))
                if values.get('postal_code'):
                    address_parts.append(values.get('postal_code'))
                if address_parts:
                    values['account_address'] = ', '.join(address_parts)
        
        # Handle private payment - clear medical aid fields
        if funding_option in ['private', 'self-pay', 'cash', 'private pay']:
            # Clear medical aid related fields for private patients
            medical_aid_fields = [
                'medical_aid_name', 'medical_aid_other', 'plan_name', 
                'medical_aid_number', 'dependent_number', 'main_member_name'
            ]
            for field in medical_aid_fields:
                if values.get(field) in ['', 'N/A', 'None', 'null']:
                    values[field] = None
        
        # Handle alternative funding - clear medical aid fields but keep alternative funding fields
        elif funding_option in ['alternative', 'alternative funding', 'other']:
            # Clear medical aid fields
            medical_aid_fields = [
                'medical_aid_name', 'medical_aid_other', 'plan_name', 
                'medical_aid_number', 'dependent_number', 'main_member_name'
            ]
            for field in medical_aid_fields:
                if values.get(field) in ['', 'N/A', 'None', 'null']:
                    values[field] = None
            
            # Keep alternative funding fields as they are needed
        
        # Clean up empty string values - convert to None for optional fields
        optional_email_fields = ['email', 'account_email']
        for field in optional_email_fields:
            if values.get(field) in ['', 'N/A', 'None', 'null', ' ']:
                values[field] = None
        
        # Clean up other empty string values
        text_fields = [
            'title', 'preferred_name', 'contact_number', 'phone_home', 'phone_work', 
            'phone_cell', 'clinic', 'address_line1', 'address_line2', 'town', 
            'postal_code', 'account_name', 'account_id_number', 'account_address', 
            'account_phone', 'funding_option', 'main_member_name', 'medical_aid_name',
            'medical_aid_other', 'plan_name', 'medical_aid_number', 'dependent_number',
            'alternative_funding_source', 'alternative_funding_other', 'claim_number',
            'case_manager', 'emergency_contact_name', 'emergency_contact_relationship',
            'emergency_contact_phone', 'patient_important_info', 'signature_identity',
            'signature_name', 'signature_relationship'
        ]
        
        for field in text_fields:
            if values.get(field) in ['', 'N/A', 'None', 'null', ' ']:
                values[field] = None
        
        return values


class PatientUpdateModel(BaseModel):
    """Validated patient update model - all fields optional"""
    
    model_config = {"extra": "ignore"}  # Ignore extra fields instead of erroring
    
    title: Optional[str] = Field(None, max_length=10)
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    surname: Optional[str] = Field(None, min_length=1, max_length=50)
    preferred_name: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[str] = None
    gender: Optional[str] = Field(None, max_length=50)
    id_number: Optional[str] = Field(None, min_length=13, max_length=13)
    email: Optional[EmailStr] = None
    contact_number: Optional[str] = Field(None, max_length=20)
    phone_home: Optional[str] = Field(None, max_length=20)
    phone_work: Optional[str] = Field(None, max_length=20)
    phone_cell: Optional[str] = Field(None, max_length=20)
    clinic: Optional[str] = Field(None, max_length=100)
    address_line1: Optional[str] = Field(None, min_length=1, max_length=100)
    address_line2: Optional[str] = Field(None, max_length=100)
    town: Optional[str] = Field(None, min_length=1, max_length=50)
    postal_code: Optional[str] = None
    country: Optional[str] = Field(None, max_length=50)
    account_responsible: Optional[str] = Field(None, max_length=50)
    account_name: Optional[str] = Field(None, max_length=100)
    account_id_number: Optional[str] = Field(None, max_length=13)
    account_address: Optional[str] = Field(None, max_length=200)
    account_phone: Optional[str] = Field(None, max_length=20)
    account_email: Optional[EmailStr] = None
    funding_option: Optional[str] = Field(None, max_length=50)
    main_member_name: Optional[str] = Field(None, max_length=100)
    medical_aid_name: Optional[str] = Field(None, max_length=100)
    medical_aid_other: Optional[str] = Field(None, max_length=100)
    plan_name: Optional[str] = Field(None, max_length=50)
    medical_aid_number: Optional[str] = Field(None, max_length=20)
    dependent_number: Optional[str] = Field(None, max_length=10)
    alternative_funding_source: Optional[str] = Field(None, max_length=100)
    alternative_funding_other: Optional[str] = Field(None, max_length=100)
    claim_number: Optional[str] = Field(None, max_length=50)
    case_manager: Optional[str] = Field(None, max_length=100)
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    patient_important_info: Optional[str] = Field(None, max_length=1000)
    consent_treatment: Optional[bool] = None
    consent_photography: Optional[bool] = None
    consent_data: Optional[bool] = None
    consent_communication: Optional[bool] = None
    consent_billing: Optional[bool] = None
    consent_terms: Optional[bool] = None
    signature_identity: Optional[str] = Field(None, max_length=100)
    signature_name: Optional[str] = Field(None, max_length=100)
    signature_relationship: Optional[str] = Field(None, max_length=50)
    signature_data: Optional[str] = None
    
    # Apply same validators as create model
    @field_validator('title', 'first_name', 'surname', 'preferred_name', 'emergency_contact_name', 'main_member_name', 'account_name', 'case_manager', 'signature_name')
    @classmethod
    def sanitize_names(cls, v):
        return PatientCreateModel.sanitize_names(v)
    
    @field_validator('id_number', 'account_id_number')
    @classmethod
    def validate_id_number(cls, v):
        return PatientCreateModel.validate_id_number(v)
    
    @field_validator('date_of_birth')
    @classmethod
    def validate_date_of_birth(cls, v):
        return PatientCreateModel.validate_date_of_birth(v)
    
    @field_validator('contact_number', 'phone_home', 'phone_work', 'phone_cell', 'emergency_contact_phone', 'account_phone')
    @classmethod
    def validate_phone_numbers(cls, v):
        return PatientCreateModel.validate_phone_numbers(v)
    
    @field_validator('postal_code')
    @classmethod
    def validate_postal_code(cls, v):
        return PatientCreateModel.validate_postal_code(v)
    
    @field_validator('address_line1', 'address_line2', 'town', 'patient_important_info', 'clinic', 'account_address', 'funding_option', 'medical_aid_other', 'alternative_funding_source', 'alternative_funding_other', 'claim_number', 'signature_identity', 'signature_relationship')
    @classmethod
    def sanitize_text_fields(cls, v):
        return PatientCreateModel.sanitize_text_fields(v)
    
    @field_validator('medical_aid_number')
    @classmethod
    def validate_medical_aid_number(cls, v):
        return PatientCreateModel.validate_medical_aid_number(v)
    
    @field_validator('medical_aid_name', 'plan_name')
    @classmethod
    def sanitize_medical_fields(cls, v):
        return PatientCreateModel.sanitize_medical_fields(v)
    
    @field_validator('gender')
    @classmethod
    def normalize_gender(cls, v):
        return PatientCreateModel.normalize_gender(v)


class TreatmentNoteModel(BaseModel):
    """Validated treatment note model for medical records"""
    
    appointment_id: str = Field(..., min_length=1, max_length=50, description="Appointment reference ID")
    patient_id: str = Field(..., min_length=1, max_length=50, description="Patient reference ID")
    therapist_id: int = Field(..., gt=0, description="Therapist ID")
    therapist_name: str = Field(..., min_length=1, max_length=100, description="Therapist name")
    profession: str = Field(..., min_length=1, max_length=50, description="Therapist profession")
    
    appointment_date: str = Field(..., description="Appointment date in YYYY-MM-DD format")
    start_time: str = Field(..., description="Appointment start time in HH:MM format")
    duration: Optional[int] = Field(None, ge=15, le=480, description="Duration in minutes (15-480)")
    
    # Medical content fields
    subjective_findings: str = Field(..., min_length=1, max_length=2000, description="Patient's subjective report")
    objective_findings: str = Field(..., min_length=1, max_length=2000, description="Therapist's objective findings")
    treatment: str = Field(..., min_length=1, max_length=2000, description="Treatment provided")
    plan: str = Field(..., min_length=1, max_length=2000, description="Treatment plan")
    
    # Optional fields
    note_to_patient: Optional[str] = Field(None, max_length=1000, description="Note to patient")
    alert_comment: Optional[str] = Field(None, max_length=500, description="Alert comment")
    alert_resolved: Optional[bool] = Field(None, description="Whether alert is resolved")
    
    @field_validator('appointment_date')
    @classmethod
    def validate_appointment_date(cls, v):
        try:
            appointment_date = datetime.strptime(v, '%Y-%m-%d').date()
            # Allow appointments up to 1 year in the past and 1 year in the future
            today = date.today()
            if appointment_date < date(today.year - 1, today.month, today.day):
                raise ValueError('Appointment date cannot be more than 1 year in the past')
            if appointment_date > date(today.year + 1, today.month, today.day):
                raise ValueError('Appointment date cannot be more than 1 year in the future')
            return v
        except ValueError as e:
            if 'does not match format' in str(e):
                raise ValueError('Date must be in YYYY-MM-DD format')
            raise e
    
    @field_validator('start_time')
    @classmethod
    def validate_start_time(cls, v):
        try:
            time_obj = datetime.strptime(v, '%H:%M').time()
            # Business hours validation (6 AM to 10 PM)
            if time_obj < datetime.strptime('06:00', '%H:%M').time():
                raise ValueError('Appointment time cannot be before 6:00 AM')
            if time_obj > datetime.strptime('22:00', '%H:%M').time():
                raise ValueError('Appointment time cannot be after 10:00 PM')
            return v
        except ValueError as e:
            if 'does not match format' in str(e):
                raise ValueError('Time must be in HH:MM format')
            raise e
    
    @field_validator('subjective_findings', 'objective_findings', 'treatment', 'plan', 'note_to_patient', 'alert_comment')
    @classmethod
    def sanitize_medical_text(cls, v):
        if v:
            sanitized = sanitize_string(v)
            if not sanitized and v:  # Only raise error if original had content
                raise ValueError('Text field cannot be empty after sanitization')
            return sanitized
        return v
    
    @field_validator('therapist_name')
    @classmethod
    def validate_therapist_name(cls, v):
        sanitized = sanitize_string(v)
        if not re.match(r"^[a-zA-Z\s\-'.]+$", sanitized):
            raise ValueError('Therapist name contains invalid characters')
        return sanitized
    
    @field_validator('profession')
    @classmethod
    def validate_profession(cls, v):
        valid_professions = [
            'Physiotherapy', 'Occupational Therapy', 'Speech Therapy', 
            'Psychology', 'Dietetics', 'Social Work', 'Nursing',
            'Biokinetics', 'Podiatry', 'Audiology'
        ]
        if v not in valid_professions:
            raise ValueError(f'Profession must be one of: {", ".join(valid_professions)}')
        return v


class BillingAmountModel(BaseModel):
    """Validated billing amount with financial validation"""
    
    amount: Decimal = Field(..., ge=0, le=50000, decimal_places=2, description="Amount in Rands")
    currency: str = Field(default="ZAR", description="Currency code")
    description: Optional[str] = Field(None, max_length=200, description="Description of charge")
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        try:
            # Ensure it's a valid decimal with max 2 decimal places
            if v < 0:
                raise ValueError('Amount cannot be negative')
            if v > Decimal('50000.00'):
                raise ValueError('Amount cannot exceed R50,000')
            
            # Check decimal places
            if v.as_tuple().exponent < -2:
                raise ValueError('Amount cannot have more than 2 decimal places')
            
            return v
        except (ValueError, InvalidOperation):
            raise ValueError('Invalid amount format')
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        valid_currencies = ['ZAR', 'USD', 'EUR', 'GBP']
        if v not in valid_currencies:
            raise ValueError(f'Currency must be one of: {", ".join(valid_currencies)}')
        return v
    
    @field_validator('description')
    @classmethod
    def sanitize_description(cls, v):
        if v:
            return sanitize_string(v)
        return v


class BillingSessionModel(BaseModel):
    """Validated billing session model"""
    
    patient_id: str = Field(..., min_length=1, max_length=50, description="Patient ID")
    therapist_id: int = Field(..., gt=0, description="Therapist ID")
    appointment_id: str = Field(..., min_length=1, max_length=50, description="Appointment ID")
    
    date_of_service: str = Field(..., description="Date of service in YYYY-MM-DD format")
    invoice_number: Optional[str] = Field(None, max_length=50, description="Invoice number")
    
    total_amount: Decimal = Field(..., ge=0, le=50000, decimal_places=2, description="Total amount")
    amount_paid: Optional[Decimal] = Field(None, ge=0, le=50000, decimal_places=2, description="Amount paid")
    
    notes: Optional[str] = Field(None, max_length=1000, description="Billing notes")
    status: Literal["Draft", "Sent", "Paid", "Overdue", "Cancelled"] = Field(default="Draft")
    
    @field_validator('date_of_service')
    @classmethod
    def validate_service_date(cls, v):
        try:
            service_date = datetime.strptime(v, '%Y-%m-%d').date()
            # Service date should not be in the future
            if service_date > date.today():
                raise ValueError('Service date cannot be in the future')
            # Service date should not be more than 2 years old
            if date.today().year - service_date.year > 2:
                raise ValueError('Service date cannot be more than 2 years old')
            return v
        except ValueError as e:
            if 'does not match format' in str(e):
                raise ValueError('Date must be in YYYY-MM-DD format')
            raise e
    
    @field_validator('total_amount', 'amount_paid')
    @classmethod
    def validate_amounts(cls, v):
        if v is not None:
            if v < 0:
                raise ValueError('Amount cannot be negative')
            if v > Decimal('50000.00'):
                raise ValueError('Amount cannot exceed R50,000')
            if v.as_tuple().exponent < -2:
                raise ValueError('Amount cannot have more than 2 decimal places')
        return v
    
    @field_validator('notes')
    @classmethod
    def sanitize_notes(cls, v):
        if v:
            return sanitize_string(v)
        return v
    
    @field_validator('invoice_number')
    @classmethod
    def validate_invoice_number(cls, v):
        if v:
            # Invoice number should be alphanumeric with dashes/slashes allowed
            if not re.match(r'^[A-Z0-9\-/]+$', v.upper()):
                raise ValueError('Invoice number should contain only letters, numbers, dashes, and slashes')
            return v.upper()
        return v
    
    @model_validator(mode="before")
    @classmethod
    def validate_payment_amount(cls, values):
        total = values.get('total_amount')
        paid = values.get('amount_paid')
        
        if total is not None and paid is not None:
            if paid > total:
                raise ValueError('Amount paid cannot exceed total amount')
        
        return values


class AlertResolutionModel(BaseModel):
    """Model for resolving patient alerts"""
    
    resolved: bool = Field(..., description="Whether the alert is resolved")
    resolution_notes: Optional[str] = Field(None, max_length=500, description="Resolution notes")
    
    @field_validator('resolution_notes')
    @classmethod
    def sanitize_resolution_notes(cls, v):
        if v:
            return sanitize_string(v)
        return v


class BillingEntryModel(BaseModel):
    """Individual billing entry validation"""
    
    code_id: str = Field(..., min_length=1, max_length=20, description="Billing code ID")
    description: str = Field(..., min_length=1, max_length=200, description="Service description")
    quantity: int = Field(..., ge=1, le=100, description="Quantity of services")
    rate: Decimal = Field(..., ge=0, le=5000, decimal_places=2, description="Rate per unit")
    total: Decimal = Field(..., ge=0, le=50000, decimal_places=2, description="Total amount")
    
    @field_validator('description')
    @classmethod
    def sanitize_description(cls, v):
        return sanitize_string(v)
    
    @field_validator('code_id')
    @classmethod
    def validate_code_id(cls, v):
        # Billing codes should be alphanumeric
        if not re.match(r'^[A-Z0-9\-]+$', v.upper()):
            raise ValueError('Billing code should contain only letters, numbers, and dashes')
        return v.upper()
    
    @model_validator(mode="before")
    @classmethod
    def validate_total(cls, values):
        quantity = values.get('quantity')
        rate = values.get('rate')
        total = values.get('total')
        
        if quantity and rate and total:
            expected_total = Decimal(str(quantity)) * rate
            if abs(total - expected_total) > Decimal('0.01'):  # Allow for small rounding differences
                raise ValueError(f'Total {total} does not match quantity {quantity} × rate {rate} = {expected_total}')
        
        return values


class BillingSubmissionModel(BaseModel):
    """Model for billing submission with session and entries"""
    
    session: BillingSessionModel
    entries: List[BillingEntryModel] = Field(..., min_items=1, max_items=50, description="Billing entries")
    
    @model_validator(mode="before")
    @classmethod
    def validate_entries_total(cls, values):
        entries = values.get('entries', [])
        session = values.get('session')
        
        if entries and session and hasattr(session, 'total_amount'):
            # Calculate total from entries
            calculated_total = sum(entry.total for entry in entries)
            if abs(session.total_amount - calculated_total) > Decimal('0.01'):
                raise ValueError(f'Session total {session.total_amount} does not match entries total {calculated_total}')
        
        return values


class UserUpdateModel(BaseModel):
    """Model for updating user accounts"""
    
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Full name")
    role: Optional[Literal["admin", "therapist", "assistant"]] = Field(None, description="User role")
    is_active: Optional[bool] = Field(None, description="Account active status")
    therapist_id: Optional[int] = Field(None, gt=0, description="Associated therapist ID")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if v:
            # Username should be alphanumeric with underscores/hyphens allowed
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
            return v.lower()
        return v
    
    @field_validator('full_name')
    @classmethod
    def sanitize_full_name(cls, v):
        if v:
            sanitized = sanitize_string(v)
            if not re.match(r"^[a-zA-Z\s\-'.]+$", sanitized):
                raise ValueError('Full name contains invalid characters')
            return sanitized
        return v


class TherapistUpdateModel(BaseModel):
    """Model for updating therapist information"""
    
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    surname: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    profession_id: Optional[int] = Field(None, gt=0)
    registration_number: Optional[str] = Field(None, min_length=1, max_length=50)
    clinic_id: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None
    
    @field_validator('first_name', 'surname')
    @classmethod
    def sanitize_names(cls, v):
        if v:
            sanitized = sanitize_string(v)
            if not re.match(r"^[a-zA-Z\s\-']+$", sanitized):
                raise ValueError('Name contains invalid characters')
            return sanitized
        return v
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v and not validate_sa_phone_number(v):
            raise ValueError('Invalid South African phone number format')
        return v
    
    @field_validator('registration_number')
    @classmethod
    def validate_registration_number(cls, v):
        if v:
            # Registration numbers should be alphanumeric with forward slashes allowed
            if not re.match(r'^[A-Z0-9/]+$', v.upper()):
                raise ValueError('Registration number should contain only letters, numbers, and forward slashes')
            return v.upper()
        return v


class SettingsUpdateModel(BaseModel):
    """Model for updating system settings"""
    
    practice_name: Optional[str] = Field(None, min_length=1, max_length=200)
    practice_address: Optional[str] = Field(None, min_length=1, max_length=300)
    practice_phone: Optional[str] = Field(None, max_length=20)
    practice_email: Optional[EmailStr] = None
    banking_details: Optional[str] = Field(None, max_length=500)
    default_session_duration: Optional[int] = Field(None, ge=15, le=480)
    currency: Optional[str] = Field(None, max_length=3)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=1, decimal_places=4)
    
    @field_validator('practice_name', 'practice_address', 'banking_details')
    @classmethod
    def sanitize_text_fields(cls, v):
        if v:
            return sanitize_string(v)
        return v
    
    @field_validator('practice_phone')
    @classmethod
    def validate_practice_phone(cls, v):
        if v and not validate_sa_phone_number(v):
            raise ValueError('Invalid South African phone number format')
        return v
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        if v:
            valid_currencies = ['ZAR', 'USD', 'EUR', 'GBP']
            if v.upper() not in valid_currencies:
                raise ValueError(f'Currency must be one of: {", ".join(valid_currencies)}')
            return v.upper()
        return v


class ProfessionUpdateModel(BaseModel):
    """Model for updating profession information"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Profession name")
    description: Optional[str] = Field(None, max_length=500, description="Profession description")
    billing_code_prefix: Optional[str] = Field(None, max_length=10, description="Billing code prefix")
    is_active: Optional[bool] = None
    
    @field_validator('name')
    @classmethod
    def sanitize_name(cls, v):
        if v:
            sanitized = sanitize_string(v)
            if not sanitized:
                raise ValueError('Profession name cannot be empty after sanitization')
            return sanitized
        return v
    
    @field_validator('description')
    @classmethod
    def sanitize_description(cls, v):
        if v:
            return sanitize_string(v)
        return v
    
    @field_validator('billing_code_prefix')
    @classmethod
    def validate_billing_prefix(cls, v):
        if v:
            # Billing prefix should be uppercase letters/numbers
            if not re.match(r'^[A-Z0-9]+$', v.upper()):
                raise ValueError('Billing code prefix should contain only letters and numbers')
            return v.upper()
        return v


class ClinicUpdateModel(BaseModel):
    """Model for updating clinic information"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Clinic name")
    address: Optional[str] = Field(None, min_length=1, max_length=300, description="Clinic address")
    phone: Optional[str] = Field(None, max_length=20, description="Clinic phone")
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    
    @field_validator('name', 'address')
    @classmethod
    def sanitize_text_fields(cls, v):
        if v:
            sanitized = sanitize_string(v)
            if not sanitized:
                raise ValueError('Field cannot be empty after sanitization')
            return sanitized
        return v
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v and not validate_sa_phone_number(v):
            raise ValueError('Invalid South African phone number format')
        return v


class BillingCodeUpdateModel(BaseModel):
    """Model for updating billing codes"""
    
    code: Optional[str] = Field(None, min_length=1, max_length=20, description="Billing code")
    description: Optional[str] = Field(None, min_length=1, max_length=200, description="Code description")
    rate: Optional[Decimal] = Field(None, ge=0, le=5000, decimal_places=2, description="Default rate")
    profession_id: Optional[int] = Field(None, gt=0, description="Associated profession ID")
    is_active: Optional[bool] = None
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        if v:
            # Billing codes should be alphanumeric with dashes allowed
            if not re.match(r'^[A-Z0-9\-]+$', v.upper()):
                raise ValueError('Billing code should contain only letters, numbers, and dashes')
            return v.upper()
        return v
    
    @field_validator('description')
    @classmethod
    def sanitize_description(cls, v):
        if v:
            return sanitize_string(v)
        return v


class InvoiceDataModel(BaseModel):
    """Model for invoice data within invoice creation"""
    
    id: Optional[str] = Field(None, max_length=50, description="Invoice ID")
    patient_id: str = Field(..., min_length=1, max_length=50, description="Patient ID")
    therapist_id: int = Field(..., gt=0, description="Therapist ID")
    invoice_date: str = Field(..., description="Invoice date in YYYY-MM-DD format")
    due_date: Optional[str] = Field(None, description="Due date in YYYY-MM-DD format")
    status: Optional[Literal["Draft", "Sent", "Paid", "Overdue", "Cancelled"]] = Field(default="Draft")
    notes: Optional[str] = Field(None, max_length=1000, description="Invoice notes")
    total_amount: Optional[Decimal] = Field(None, ge=0, le=50000, decimal_places=2)
    
    @field_validator('invoice_date', 'due_date')
    @classmethod
    def validate_dates(cls, v):
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d').date()
                return v
            except ValueError:
                raise ValueError('Date must be in YYYY-MM-DD format')
        return v
    
    @field_validator('notes')
    @classmethod
    def sanitize_notes(cls, v):
        if v:
            return sanitize_string(v)
        return v


class InvoiceCreateModel(BaseModel):
    """Model for creating new invoices with billing entries"""
    
    invoice: InvoiceDataModel
    entry_ids: List[int] = Field(..., min_items=1, max_items=100, description="Billing entry IDs")
    
    @field_validator('entry_ids')
    @classmethod
    def validate_entry_ids(cls, v):
        # Check for duplicates
        if len(v) != len(set(v)):
            raise ValueError('Duplicate entry IDs are not allowed')
        
        # All IDs should be positive integers
        for entry_id in v:
            if entry_id <= 0:
                raise ValueError('All entry IDs must be positive integers')
        
        return v


class InvoiceUpdateModel(BaseModel):
    """Model for updating existing invoices"""
    
    due_date: Optional[str] = Field(None, description="Due date in YYYY-MM-DD format")
    status: Optional[Literal["Draft", "Sent", "Paid", "Overdue", "Cancelled"]] = None
    amount_paid: Optional[Decimal] = Field(None, ge=0, le=50000, decimal_places=2)
    payment_date: Optional[str] = Field(None, description="Payment date in YYYY-MM-DD format")
    notes: Optional[str] = Field(None, max_length=1000)
    
    @field_validator('due_date', 'payment_date')
    @classmethod
    def validate_dates(cls, v):
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d').date()
                return v
            except ValueError:
                raise ValueError('Date must be in YYYY-MM-DD format')
        return v
    
    @field_validator('notes')
    @classmethod
    def sanitize_notes(cls, v):
        if v:
            return sanitize_string(v)
        return v




class ReminderCreateModel(BaseModel):
    """Model for creating reminders"""
    
    title: str = Field(..., min_length=1, max_length=200, description="Reminder title")
    description: Optional[str] = Field(None, max_length=1000, description="Reminder description")
    due_date: str = Field(..., description="Due date in YYYY-MM-DD format")
    due_time: Optional[str] = Field(None, description="Due time in HH:MM format")
    priority: Literal["Low", "Medium", "High", "Critical"] = Field(default="Medium", description="Priority level")
    category: Optional[str] = Field(None, max_length=50, description="Reminder category")
    patient_id: Optional[str] = Field(None, max_length=50, description="Associated patient ID")
    therapist_id: Optional[int] = Field(None, gt=0, description="Associated therapist ID")
    
    @field_validator('title', 'description')
    @classmethod
    def sanitize_text_fields(cls, v):
        if v:
            sanitized = sanitize_string(v)
            if not sanitized and v:
                raise ValueError('Field cannot be empty after sanitization')
            return sanitized
        return v
    
    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d').date()
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
    
    @field_validator('due_time')
    @classmethod
    def validate_due_time(cls, v):
        if v:
            try:
                datetime.strptime(v, '%H:%M').time()
                return v
            except ValueError:
                raise ValueError('Time must be in HH:MM format')
        return v


class ReminderUpdateModel(BaseModel):
    """Model for updating reminders"""
    
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    due_date: Optional[str] = None
    due_time: Optional[str] = None
    priority: Optional[Literal["Low", "Medium", "High", "Critical"]] = None
    category: Optional[str] = Field(None, max_length=50)
    is_completed: Optional[bool] = None
    
    @field_validator('title', 'description')
    @classmethod
    def sanitize_text_fields(cls, v):
        return ReminderCreateModel.sanitize_text_fields(v)
    
    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v):
        return ReminderCreateModel.validate_due_date(v)
    
    @field_validator('due_time')
    @classmethod
    def validate_due_time(cls, v):
        return ReminderCreateModel.validate_due_time(v)
    
    
    


class UserPreferencesUpdateModel(BaseModel):
    """Model for updating user preferences"""
    
    theme: Optional[Literal["light", "dark", "auto"]] = None
    language: Optional[str] = Field(None, max_length=10, description="Language code")
    timezone: Optional[str] = Field(None, max_length=50, description="Timezone identifier")
    notifications_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None
    dashboard_layout: Optional[str] = Field(None, max_length=100)
    default_appointment_duration: Optional[int] = Field(None, ge=15, le=480, description="Minutes")
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        if v:
            # Common language codes
            valid_languages = ['en', 'af', 'zu', 'xh', 'st', 'tn', 'ss', 'ts', 've', 'nr', 'nso']
            if v.lower() not in valid_languages:
                raise ValueError(f'Language must be one of: {", ".join(valid_languages)}')
            return v.lower()
        return v
    
    @field_validator('dashboard_layout')
    @classmethod
    def sanitize_dashboard_layout(cls, v):
        if v:
            return sanitize_string(v)
        return v


class SystemConfigurationModel(BaseModel):
    """Model for system configuration updates"""
    
    maintenance_mode: Optional[bool] = None
    allow_patient_self_booking: Optional[bool] = None
    require_email_verification: Optional[bool] = None
    session_timeout_minutes: Optional[int] = Field(None, ge=5, le=1440, description="Session timeout in minutes")
    max_failed_login_attempts: Optional[int] = Field(None, ge=3, le=10)
    password_min_length: Optional[int] = Field(None, ge=6, le=50)
    backup_enabled: Optional[bool] = None
    backup_frequency_hours: Optional[int] = Field(None, ge=1, le=168, description="Hours between backups")
    log_level: Optional[Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]] = None
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        if v:
            return v.upper()
        return v


class SystemBackupModel(BaseModel):
    """Model for system backup data"""
    
    backup_name: str = Field(..., min_length=1, max_length=100, description="Backup name")
    backup_type: Literal["full", "incremental", "configuration"] = Field(..., description="Type of backup")
    include_patient_data: Optional[bool] = Field(default=True, description="Include patient data")
    include_financial_data: Optional[bool] = Field(default=True, description="Include billing data")
    include_system_settings: Optional[bool] = Field(default=True, description="Include settings")
    compression_enabled: Optional[bool] = Field(default=True, description="Enable compression")
    
    @field_validator('backup_name')
    @classmethod
    def sanitize_backup_name(cls, v):
        # Backup names should be safe for filesystem
        sanitized = re.sub(r'[^\w\-_.]', '_', v)
        if not sanitized:
            raise ValueError('Backup name cannot be empty after sanitization')
        return sanitized


class AppointmentBillingModel(BaseModel):
    """Model for appointment-specific billing submissions"""
    
    appointment_id: str = Field(..., min_length=1, max_length=50, description="Appointment ID")
    billing_entries: List[BillingEntryModel] = Field(..., min_items=1, max_items=50, description="Billing entries")
    notes: Optional[str] = Field(None, max_length=1000, description="Billing session notes")
    
    @field_validator('notes')
    @classmethod
    def sanitize_notes(cls, v):
        if v:
            return sanitize_string(v)
        return v