# Medical Intake Form OCR Implementation Plan

## Executive Summary
Template-based OCR pipeline for standardized hospital intake forms using OpenCV + Tesseract (offline-first) with AWS Textract fallback for low-confidence scenarios. POPIA-compliant with audit logging and user confirmation workflow.

---

## 1. Architecture & Data Flow

### System Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React/JS)                       │
├─────────────────────────────────────────────────────────────────┤
│                     FastAPI Application Layer                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐    │
│  │   Endpoints  │  │  Validation  │  │   Audit Logger    │    │
│  └──────────────┘  └──────────────┘  └───────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│                        OCR Pipeline Core                         │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐    │
│  │ Preprocessor │→ │ OCR Engine   │→ │  Postprocessor    │    │
│  │   (OpenCV)   │  │  (Tesseract) │  │   (Validation)    │    │
│  └──────────────┘  └──────────────┘  └───────────────────┘    │
│                              ↓                                   │
│                    ┌───────────────────┐                        │
│                    │ Confidence Check  │                        │
│                    └───────────────────┘                        │
│                         ↓         ↓                             │
│                    [Pass]      [Fail]                           │
│                       ↓           ↓                             │
│                  Return JSON  ┌─────────────┐                   │
│                              │ AWS Textract │                   │
│                              └─────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow Sequence
1. **Upload**: User submits image via multipart/form-data
2. **Validation**: File type/size checks
3. **Preprocessing**: Image enhancement & alignment
4. **Template Mapping**: Apply bounding box template
5. **OCR Extraction**: Process each field region
6. **Confidence Scoring**: Calculate per-field confidence
7. **Fallback Decision**: If confidence < threshold → Textract
8. **Postprocessing**: Normalize & validate fields
9. **Audit Log**: Record extraction event
10. **Response**: Return JSON with fields + confidence
11. **UI Confirmation**: User reviews & confirms
12. **Persistence**: Save to patient record

---

## 2. Project Structure

```
hadada_health/
├── form_ocr/
│   ├── __init__.py
│   ├── config.py                 # Settings & env vars
│   ├── models.py                 # Pydantic models
│   ├── template.py               # Template management
│   ├── preprocessor.py           # OpenCV operations
│   ├── ocr_engine.py            # Tesseract wrapper
│   ├── textract_client.py       # AWS Textract fallback
│   ├── postprocessor.py         # Field validation
│   ├── validators.py            # SA ID, email, phone validators
│   ├── audit.py                 # Audit logging
│   ├── exceptions.py            # Custom exceptions
│   └── utils.py                 # Helper functions
├── api/
│   └── ocr_endpoints.py         # FastAPI routes
├── templates/
│   └── intake_form_v1.yaml      # Template definition
├── tests/
│   ├── test_preprocessor.py
│   ├── test_ocr_engine.py
│   ├── test_validators.py
│   ├── test_integration.py
│   └── fixtures/
│       └── test_images/
├── scripts/
│   ├── calibrate_template.py    # Draw boxes for calibration
│   └── batch_ocr.py            # Batch processing CLI
├── static/
│   └── ocr/
│       └── confirm.html         # Confirmation UI
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

---

## 3. Dependencies & Requirements

### requirements.txt
```txt
# Core dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
python-dotenv==1.0.0

# Image processing
opencv-python==4.8.1.78
Pillow==10.1.0
numpy==1.24.3

# OCR
pytesseract==0.3.10

# AWS (optional)
boto3==1.29.7

# Utilities
pyyaml==6.0.1
python-jose[cryptography]==3.3.0
httpx==0.25.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0

# Development
black==23.11.0
mypy==1.7.0
```

---

## 4. Template Specification

### templates/intake_form_v1.yaml
```yaml
# Hospital Intake Form Template v1.0
# Coordinates based on A4 scanned at 300 DPI (2480x3508 pixels)

metadata:
  version: "1.0"
  page_width: 2480
  page_height: 3508
  dpi: 300
  form_revision: "2024-01"

fields:
  patient_name:
    label: "Patient Name"
    type: "text"
    bbox: {x: 450, y: 520, w: 800, h: 60}
    whitelist: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz '-"
    
  sa_id:
    label: "SA ID Number"
    type: "numeric"
    bbox: {x: 450, y: 620, w: 400, h: 60}
    whitelist: "0123456789"
    validation: "sa_id"
    
  date_of_birth:
    label: "Date of Birth"
    type: "date"
    bbox: {x: 450, y: 720, w: 300, h: 60}
    format: "dd.mm.yyyy"
    
  email:
    label: "Email Address"
    type: "email"
    bbox: {x: 450, y: 820, w: 600, h: 60}
    
  cell_number:
    label: "Cell Number"
    type: "phone"
    bbox: {x: 450, y: 920, w: 400, h: 60}
    whitelist: "0123456789+-() "
    
  admission_date:
    label: "Admission Date"
    type: "date"
    bbox: {x: 1500, y: 520, w: 300, h: 60}
    format: "dd/mm/yyyy"
    
  medical_aid:
    label: "Medical Aid"
    type: "text"
    bbox: {x: 450, y: 1120, w: 600, h: 60}
    
  member_number:
    label: "Member Number"
    type: "alphanumeric"
    bbox: {x: 450, y: 1220, w: 500, h: 60}
    whitelist: "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-"
    
  emergency_contact:
    label: "Emergency Contact Person"
    type: "text"
    bbox: {x: 450, y: 1420, w: 700, h: 60}
    
  referring_doctor:
    label: "Referring Doctor"
    type: "text"
    bbox: {x: 450, y: 1620, w: 700, h: 60}
    prefix: "Dr."

confidence_thresholds:
  minimum_field: 70
  minimum_overall: 75
  fallback_trigger: 60
```

---

## 5. Preprocessing Pipeline

### preprocessor.py
```python
import cv2
import numpy as np
from typing import Tuple, Optional

class FormPreprocessor:
    def __init__(self, config: dict):
        self.config = config
        
    def process(self, image: np.ndarray) -> np.ndarray:
        """Full preprocessing pipeline"""
        # 1. Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 2. Noise reduction
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # 3. Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            denoised, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        # 4. Deskew
        deskewed = self.deskew(thresh)
        
        # 5. Perspective correction
        corrected = self.perspective_correction(deskewed)
        
        # 6. Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        morph = cv2.morphologyEx(corrected, cv2.MORPH_CLOSE, kernel)
        
        return morph
    
    def deskew(self, image: np.ndarray) -> np.ndarray:
        """Deskew using Hough transform"""
        edges = cv2.Canny(image, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
        
        if lines is not None:
            angles = []
            for rho, theta in lines[:10, 0]:
                angle = (theta * 180 / np.pi) - 90
                if -45 <= angle <= 45:
                    angles.append(angle)
            
            if angles:
                median_angle = np.median(angles)
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                return cv2.warpAffine(image, M, (w, h), 
                                     flags=cv2.INTER_CUBIC,
                                     borderMode=cv2.BORDER_REPLICATE)
        return image
    
    def perspective_correction(self, image: np.ndarray) -> np.ndarray:
        """4-point perspective transform"""
        # Find corners using contour detection
        contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, 
                                       cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            peri = cv2.arcLength(largest, True)
            approx = cv2.approxPolyDP(largest, 0.02 * peri, True)
            
            if len(approx) == 4:
                pts = approx.reshape(4, 2)
                rect = self.order_points(pts)
                (tl, tr, br, bl) = rect
                
                widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
                widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
                maxWidth = max(int(widthA), int(widthB))
                
                heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
                heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
                maxHeight = max(int(heightA), int(heightB))
                
                dst = np.array([
                    [0, 0],
                    [maxWidth - 1, 0],
                    [maxWidth - 1, maxHeight - 1],
                    [0, maxHeight - 1]], dtype="float32")
                
                M = cv2.getPerspectiveTransform(rect, dst)
                return cv2.warpPerspective(image, M, (maxWidth, maxHeight))
        
        return image
```

---

## 6. OCR Strategy

### ocr_engine.py
```python
import pytesseract
from PIL import Image
import numpy as np
from typing import Dict, Tuple

class TesseractEngine:
    def __init__(self, config: dict):
        self.config = config
        self.psm_modes = {
            'single_line': 7,     # Single text line
            'single_word': 8,     # Single word
            'single_block': 6,    # Uniform block of text
            'sparse': 11          # Sparse text
        }
        
    def extract_field(self, image: np.ndarray, field_config: dict) -> Tuple[str, float]:
        """Extract text from field region with confidence"""
        # Crop to field bbox
        x, y, w, h = field_config['bbox'].values()
        roi = image[y:y+h, x:x+w]
        
        # Determine PSM mode based on field type
        if field_config['type'] == 'numeric':
            psm = self.psm_modes['single_line']
            config = f'--psm {psm} -c tessedit_char_whitelist=0123456789'
        elif field_config['type'] == 'date':
            psm = self.psm_modes['single_line']
            config = f'--psm {psm} -c tessedit_char_whitelist=0123456789./-'
        elif field_config.get('whitelist'):
            psm = self.psm_modes['single_line']
            whitelist = field_config['whitelist']
            config = f'--psm {psm} -c tessedit_char_whitelist={whitelist}'
        else:
            psm = self.psm_modes['single_block']
            config = f'--psm {psm} --oem 3'
        
        # Run OCR with confidence
        data = pytesseract.image_to_data(roi, config=config, 
                                         output_type=pytesseract.Output.DICT)
        
        # Extract text and calculate confidence
        text_parts = []
        confidences = []
        
        for i, conf in enumerate(data['conf']):
            if int(conf) > 0:
                text_parts.append(data['text'][i])
                confidences.append(int(conf))
        
        text = ' '.join(text_parts).strip()
        avg_confidence = np.mean(confidences) if confidences else 0
        
        return text, avg_confidence
    
    def process_form(self, image: np.ndarray, template: dict) -> Dict:
        """Process entire form using template"""
        results = {}
        total_confidence = []
        
        for field_name, field_config in template['fields'].items():
            text, confidence = self.extract_field(image, field_config)
            results[field_name] = {
                'raw_value': text,
                'confidence': confidence,
                'field_type': field_config['type']
            }
            total_confidence.append(confidence)
        
        results['overall_confidence'] = np.mean(total_confidence)
        return results
```

---

## 7. Postprocessing & Validation

### validators.py
```python
import re
from datetime import datetime
from typing import Optional, Tuple

class FieldValidator:
    @staticmethod
    def validate_sa_id(id_number: str) -> Tuple[bool, Optional[str]]:
        """Validate South African ID with Luhn check"""
        # Remove spaces and validate length
        id_clean = re.sub(r'\D', '', id_number)
        if len(id_clean) != 13:
            return False, "ID must be 13 digits"
        
        # Luhn algorithm
        total = 0
        for i in range(12):
            digit = int(id_clean[i])
            if i % 2 == 0:
                total += digit
            else:
                double = digit * 2
                total += double if double < 10 else double - 9
        
        check_digit = (10 - (total % 10)) % 10
        if check_digit != int(id_clean[12]):
            return False, "Invalid ID checksum"
        
        # Extract DOB
        year = int(id_clean[0:2])
        month = int(id_clean[2:4])
        day = int(id_clean[4:6])
        
        # Determine century
        current_year = datetime.now().year % 100
        if year <= current_year:
            year += 2000
        else:
            year += 1900
        
        try:
            dob = datetime(year, month, day)
            return True, dob.isoformat()[:10]
        except ValueError:
            return False, "Invalid date in ID"
    
    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
        """Normalize South African phone numbers"""
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone)
        
        # Handle different formats
        if len(digits) == 10 and digits[0] == '0':
            # Local format: 0XX XXX XXXX
            normalized = f"+27{digits[1:]}"
            return True, normalized
        elif len(digits) == 11 and digits[:2] == '27':
            # Country code without +
            normalized = f"+{digits}"
            return True, normalized
        elif len(digits) == 9:
            # Missing leading 0
            normalized = f"+27{digits}"
            return True, normalized
        else:
            return False, "Invalid phone format"
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str]]:
        """Validate email with regex"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        email_clean = email.strip().lower()
        if re.match(pattern, email_clean):
            return True, email_clean
        return False, "Invalid email format"
    
    @staticmethod
    def validate_date(date_str: str, format_hint: str = "dd.mm.yyyy") -> Tuple[bool, Optional[str]]:
        """Parse and validate dates"""
        # Try multiple formats
        formats = [
            ('%d.%m.%Y', 'dd.mm.yyyy'),
            ('%d/%m/%Y', 'dd/mm/yyyy'),
            ('%d-%m-%Y', 'dd-mm-yyyy'),
            ('%Y-%m-%d', 'yyyy-mm-dd')
        ]
        
        for fmt, hint in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                # Sanity check
                if 1900 < dt.year < 2100:
                    return True, dt.isoformat()[:10]
            except ValueError:
                continue
        
        return False, "Invalid date format"
    
    @staticmethod
    def validate_member_number(member_no: str) -> Tuple[bool, Optional[str]]:
        """Clean and validate medical aid member number"""
        # Keep only alphanumeric and hyphens
        cleaned = re.sub(r'[^A-Z0-9-]', '', member_no.upper())
        
        # Length check (typical range)
        if 5 <= len(cleaned) <= 20:
            return True, cleaned
        return False, "Invalid member number length"
```

### postprocessor.py
```python
from typing import Dict
from .validators import FieldValidator

class FormPostprocessor:
    def __init__(self):
        self.validator = FieldValidator()
        
    def process_results(self, ocr_results: Dict, template: Dict) -> Dict:
        """Validate and normalize all fields"""
        processed = {}
        warnings = []
        
        for field_name, field_data in ocr_results.items():
            if field_name == 'overall_confidence':
                processed[field_name] = field_data
                continue
                
            raw_value = field_data['raw_value']
            confidence = field_data['confidence']
            field_config = template['fields'].get(field_name, {})
            
            # Apply validation based on field type
            validation_type = field_config.get('validation', field_config.get('type'))
            
            if validation_type == 'sa_id':
                valid, normalized = self.validator.validate_sa_id(raw_value)
            elif validation_type == 'phone':
                valid, normalized = self.validator.validate_phone(raw_value)
            elif validation_type == 'email':
                valid, normalized = self.validator.validate_email(raw_value)
            elif validation_type == 'date':
                format_hint = field_config.get('format', 'dd.mm.yyyy')
                valid, normalized = self.validator.validate_date(raw_value, format_hint)
            elif field_name == 'member_number':
                valid, normalized = self.validator.validate_member_number(raw_value)
            else:
                valid, normalized = True, raw_value.strip()
            
            processed[field_name] = {
                'value': normalized if valid else raw_value,
                'raw_value': raw_value,
                'confidence': confidence,
                'valid': valid,
                'normalized_value': normalized if valid else None
            }
            
            if not valid:
                warnings.append(f"{field_name}: {normalized or 'Validation failed'}")
        
        processed['warnings'] = warnings
        return processed
```

---

## 8. AWS Textract Fallback

### textract_client.py
```python
import boto3
import os
from typing import Dict, Optional
import json

class TextractClient:
    def __init__(self):
        self.enabled = os.getenv('ENABLE_TEXTRACT', 'false').lower() == 'true'
        if self.enabled:
            self.client = boto3.client(
                'textract',
                region_name=os.getenv('AWS_REGION', 'eu-west-1'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
    
    def extract_form(self, image_bytes: bytes) -> Optional[Dict]:
        """Extract form using AWS Textract"""
        if not self.enabled:
            return None
        
        try:
            response = self.client.analyze_document(
                Document={'Bytes': image_bytes},
                FeatureTypes=['FORMS', 'TABLES']
            )
            
            # Parse Textract response
            form_data = {}
            for block in response['Blocks']:
                if block['BlockType'] == 'KEY_VALUE_SET':
                    if 'KEY' in block['EntityTypes']:
                        key = self.get_text(block, response['Blocks'])
                        value_block = self.get_value_block(block, response['Blocks'])
                        if value_block:
                            value = self.get_text(value_block, response['Blocks'])
                            # Map to our field names
                            mapped_key = self.map_field_name(key)
                            if mapped_key:
                                form_data[mapped_key] = {
                                    'value': value,
                                    'confidence': block.get('Confidence', 0)
                                }
            
            return form_data
            
        except Exception as e:
            print(f"Textract error: {e}")
            return None
    
    def map_field_name(self, textract_key: str) -> Optional[str]:
        """Map Textract field names to our template"""
        mapping = {
            'patient name': 'patient_name',
            'id number': 'sa_id',
            'date of birth': 'date_of_birth',
            'email': 'email',
            'cell': 'cell_number',
            'admission date': 'admission_date',
            'medical aid': 'medical_aid',
            'member number': 'member_number',
            'emergency contact': 'emergency_contact',
            'referring doctor': 'referring_doctor'
        }
        
        key_lower = textract_key.lower().strip()
        for pattern, field in mapping.items():
            if pattern in key_lower:
                return field
        return None
    
    def get_text(self, block: Dict, blocks: list) -> str:
        """Extract text from block relationships"""
        text = ''
        if 'Relationships' in block:
            for relationship in block['Relationships']:
                if relationship['Type'] == 'CHILD':
                    for child_id in relationship['Ids']:
                        child = next((b for b in blocks if b['Id'] == child_id), None)
                        if child and child['BlockType'] == 'WORD':
                            text += child.get('Text', '') + ' '
        return text.strip()
```

---

## 9. FastAPI Endpoints

### api/ocr_endpoints.py
```python
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict
import numpy as np
from PIL import Image
import io
import json
from ..form_ocr import (
    FormPreprocessor, TesseractEngine, 
    FormPostprocessor, TextractClient,
    AuditLogger, load_template
)

router = APIRouter(prefix="/ocr", tags=["OCR"])
security = HTTPBearer()

@router.post("/extract")
async def extract_form(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Extract fields from uploaded form image"""
    # Validate file
    if file.content_type not in ['image/jpeg', 'image/png', 'image/tiff']:
        raise HTTPException(400, "Invalid image format")
    
    if file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(400, "File too large")
    
    try:
        # Load image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        img_array = np.array(image)
        
        # Load template
        template = load_template('intake_form_v1.yaml')
        
        # Preprocess
        preprocessor = FormPreprocessor({})
        processed_img = preprocessor.process(img_array)
        
        # OCR
        ocr_engine = TesseractEngine({})
        ocr_results = ocr_engine.process_form(processed_img, template)
        
        # Check confidence for fallback
        if ocr_results['overall_confidence'] < template['confidence_thresholds']['fallback_trigger']:
            textract = TextractClient()
            textract_results = textract.extract_form(contents)
            if textract_results:
                # Merge results, preferring higher confidence
                for field, data in textract_results.items():
                    if field in ocr_results:
                        if data['confidence'] > ocr_results[field]['confidence']:
                            ocr_results[field] = data
        
        # Postprocess
        postprocessor = FormPostprocessor()
        final_results = postprocessor.process_results(ocr_results, template)
        
        # Audit log (without PII)
        audit = AuditLogger()
        audit.log_extraction(
            user_id=credentials.credentials,
            confidence=final_results['overall_confidence'],
            field_count=len(final_results) - 2  # Exclude meta fields
        )
        
        return {
            "success": True,
            "data": final_results,
            "template_version": template['metadata']['version']
        }
        
    except Exception as e:
        raise HTTPException(500, f"Processing error: {str(e)}")

@router.get("/template")
async def get_template(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current template configuration"""
    template = load_template('intake_form_v1.yaml')
    return {
        "success": True,
        "template": template
    }

@router.post("/template")
async def update_template(
    template_data: Dict,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update template (admin only)"""
    # Check admin role
    if not is_admin(credentials.credentials):
        raise HTTPException(403, "Admin access required")
    
    try:
        # Validate template structure
        required_keys = ['metadata', 'fields', 'confidence_thresholds']
        if not all(k in template_data for k in required_keys):
            raise HTTPException(400, "Invalid template structure")
        
        # Save new template
        save_template('intake_form_v1.yaml', template_data)
        
        return {"success": True, "message": "Template updated"}
        
    except Exception as e:
        raise HTTPException(500, f"Update failed: {str(e)}")
```

---

## 10. Security & Compliance

### config.py
```python
import os
from pydantic import BaseSettings

class OCRSettings(BaseSettings):
    # Core settings
    enable_cloud_fallback: bool = False
    max_file_size_mb: int = 10
    allowed_formats: list = ['image/jpeg', 'image/png', 'image/tiff']
    
    # Confidence thresholds
    min_field_confidence: int = 70
    min_overall_confidence: int = 75
    fallback_trigger_confidence: int = 60
    
    # Security
    enable_pii_logging: bool = False
    temp_file_retention_hours: int = 1
    audit_log_path: str = '/var/log/ocr_audit.log'
    
    # AWS Textract (optional)
    enable_textract: bool = False
    aws_region: str = 'eu-west-1'
    aws_access_key_id: str = ''
    aws_secret_access_key: str = ''
    
    class Config:
        env_file = '.env'
```

### audit.py
```python
import json
import hashlib
from datetime import datetime
from typing import Dict, Optional

class AuditLogger:
    def __init__(self, log_path: str = '/var/log/ocr_audit.log'):
        self.log_path = log_path
    
    def log_extraction(self, user_id: str, confidence: float, 
                      field_count: int, success: bool = True):
        """Log extraction event without PII"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'form_extraction',
            'user_id': self.hash_user_id(user_id),
            'confidence': round(confidence, 2),
            'field_count': field_count,
            'success': success,
            'ip_address': self.get_client_ip()  # From request context
        }
        
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(event) + '\n')
    
    def hash_user_id(self, user_id: str) -> str:
        """Hash user ID for privacy"""
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]
    
    def log_access_denied(self, user_id: str, reason: str):
        """Log unauthorized access attempts"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'access_denied',
            'user_id': self.hash_user_id(user_id),
            'reason': reason
        }
        
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(event) + '\n')
```

---

## 11. Testing Plan

### test_integration.py
```python
import pytest
from pathlib import Path
import json
from ..form_ocr import FormPreprocessor, TesseractEngine, FormPostprocessor

class TestOCRPipeline:
    @pytest.fixture
    def golden_images(self):
        """Load test images with ground truth"""
        test_dir = Path('tests/fixtures/test_images')
        images = []
        for img_path in test_dir.glob('*.jpg'):
            truth_path = img_path.with_suffix('.json')
            if truth_path.exists():
                with open(truth_path) as f:
                    truth = json.load(f)
                images.append((img_path, truth))
        return images
    
    def test_field_accuracy(self, golden_images):
        """Test field-level extraction accuracy"""
        results = []
        
        for img_path, ground_truth in golden_images:
            # Process image
            extracted = self.process_image(img_path)
            
            # Calculate metrics
            for field, expected in ground_truth.items():
                actual = extracted.get(field, {}).get('value', '')
                match = actual.lower() == expected.lower()
                confidence = extracted.get(field, {}).get('confidence', 0)
                
                results.append({
                    'field': field,
                    'match': match,
                    'confidence': confidence,
                    'expected': expected,
                    'actual': actual
                })
        
        # Calculate aggregate metrics
        by_field = {}
        for r in results:
            field = r['field']
            if field not in by_field:
                by_field[field] = {'correct': 0, 'total': 0, 'conf': []}
            
            by_field[field]['total'] += 1
            if r['match']:
                by_field[field]['correct'] += 1
            by_field[field]['conf'].append(r['confidence'])
        
        # Report
        for field, stats in by_field.items():
            precision = stats['correct'] / stats['total']
            avg_conf = sum(stats['conf']) / len(stats['conf'])
            print(f"{field}: Precision={precision:.2%}, Avg Conf={avg_conf:.1f}")
            
            # Assert minimum accuracy
            assert precision >= 0.85, f"{field} accuracy below threshold"
    
    def test_edge_cases(self):
        """Test handling of problematic images"""
        test_cases = [
            ('skewed_form.jpg', 'Should handle 15° rotation'),
            ('low_contrast.jpg', 'Should enhance faded text'),
            ('glare_spot.jpg', 'Should handle partial glare'),
            ('crumpled.jpg', 'Should handle minor wrinkles')
        ]
        
        for image_file, description in test_cases:
            result = self.process_image(f'tests/fixtures/edge_cases/{image_file}')
            assert result['overall_confidence'] > 60, f"Failed: {description}"
```

---

## 12. Deployment Configuration

### Dockerfile
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-afr \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p /app/logs /app/temp

# Set permissions
RUN chmod 755 /app/scripts/*.py

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### .env.example
```env
# Application
ENV=production
DEBUG=false

# OCR Settings
ENABLE_CLOUD_FALLBACK=false
MIN_FIELD_CONFIDENCE=70
MIN_OVERALL_CONFIDENCE=75
FALLBACK_TRIGGER_CONFIDENCE=60

# Security
ENABLE_PII_LOGGING=false
TEMP_FILE_RETENTION_HOURS=1
SECRET_KEY=your-secret-key-here

# AWS Textract (optional)
ENABLE_TEXTRACT=false
AWS_REGION=eu-west-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# Resource Limits
MAX_FILE_SIZE_MB=10
REQUEST_TIMEOUT_SECONDS=30
```

---

## 13. Developer Scripts

### scripts/calibrate_template.py
```python
#!/usr/bin/env python3
"""
Template calibration tool - draws bounding boxes on form image
Usage: python calibrate_template.py input.jpg output.jpg
"""

import cv2
import yaml
import sys
from pathlib import Path

def draw_template_boxes(image_path: str, output_path: str, template_path: str):
    # Load image and template
    img = cv2.imread(image_path)
    with open(template_path) as f:
        template = yaml.safe_load(f)
    
    # Draw boxes
    for field_name, field_config in template['fields'].items():
        bbox = field_config['bbox']
        x, y, w, h = bbox['x'], bbox['y'], bbox['w'], bbox['h']
        
        # Draw rectangle
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Add label
        cv2.putText(img, field_name, (x, y - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # Save output
    cv2.imwrite(output_path, img)
    print(f"Template overlay saved to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: calibrate_template.py <input.jpg> <output.jpg>")
        sys.exit(1)
    
    draw_template_boxes(sys.argv[1], sys.argv[2], 'templates/intake_form_v1.yaml')
```

### scripts/batch_ocr.py
```python
#!/usr/bin/env python3
"""
Batch OCR processing for QA
Usage: python batch_ocr.py <input_dir> <output.csv>
"""

import csv
import sys
from pathlib import Path
from ..form_ocr import process_form_image

def batch_process(input_dir: str, output_csv: str):
    input_path = Path(input_dir)
    
    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'filename', 'patient_name', 'sa_id', 'email', 
            'confidence', 'warnings', 'processing_time'
        ])
        writer.writeheader()
        
        for img_file in input_path.glob('*.jpg'):
            print(f"Processing {img_file.name}...")
            
            try:
                result = process_form_image(str(img_file))
                
                writer.writerow({
                    'filename': img_file.name,
                    'patient_name': result.get('patient_name', {}).get('value', ''),
                    'sa_id': result.get('sa_id', {}).get('value', ''),
                    'email': result.get('email', {}).get('value', ''),
                    'confidence': result.get('overall_confidence', 0),
                    'warnings': '; '.join(result.get('warnings', [])),
                    'processing_time': result.get('processing_time', 0)
                })
            except Exception as e:
                print(f"Error processing {img_file.name}: {e}")
    
    print(f"Results saved to {output_csv}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: batch_ocr.py <input_dir> <output.csv>")
        sys.exit(1)
    
    batch_process(sys.argv[1], sys.argv[2])
```

---

## 14. Frontend Integration Contract

### JSON Response Format
```json
{
  "success": true,
  "data": {
    "patient_name": {
      "value": "John Smith",
      "raw_value": "JOHN SMITH",
      "normalized_value": "John Smith",
      "confidence": 92.5,
      "valid": true
    },
    "sa_id": {
      "value": "8501015800085",
      "raw_value": "850101 5800 08 5",
      "normalized_value": "8501015800085",
      "confidence": 88.3,
      "valid": true
    },
    "date_of_birth": {
      "value": "1985-01-01",
      "raw_value": "01.01.1985",
      "normalized_value": "1985-01-01",
      "confidence": 95.0,
      "valid": true
    },
    "email": {
      "value": "john.smith@email.com",
      "raw_value": "JOHN.SMITH@EMAIL.COM",
      "normalized_value": "john.smith@email.com",
      "confidence": 90.1,
      "valid": true
    },
    "cell_number": {
      "value": "+27821234567",
      "raw_value": "082 123 4567",
      "normalized_value": "+27821234567",
      "confidence": 87.5,
      "valid": true
    },
    "overall_confidence": 89.7,
    "warnings": []
  },
  "template_version": "1.0"
}
```

### Frontend UX Checklist
```markdown
## Confirmation Screen Requirements

### Display
- [ ] Show extracted fields in editable form
- [ ] Color-code confidence levels (green >85%, yellow 70-85%, red <70%)
- [ ] Highlight fields with warnings
- [ ] Show original image thumbnail with zoom capability

### Interaction
- [ ] Allow manual correction of any field
- [ ] Validation on blur for corrected fields
- [ ] Bulk accept/reject buttons
- [ ] Individual field accept/reject toggles

### Feedback
- [ ] Show processing spinner during extraction
- [ ] Display success/error toast notifications
- [ ] Confirmation dialog before final save
- [ ] Option to re-scan if quality too low

### Accessibility
- [ ] Keyboard navigation between fields
- [ ] Screen reader descriptions for confidence levels
- [ ] High contrast mode support
- [ ] Touch-friendly buttons (min 44px)
```

---

## 15. Implementation Roadmap

### Week 1: Foundation & Infrastructure
| Task | Owner | Duration | Acceptance Criteria |
|------|-------|----------|-------------------|
| Setup project structure | Backend Lead | 1 day | Directory structure created, dependencies installed |
| Implement preprocessing pipeline | CV Engineer | 2 days | All preprocessing functions tested with sample images |
| Create template system | Backend Dev | 1 day | YAML template loading/parsing working |
| Setup Tesseract integration | Backend Dev | 2 days | Basic OCR extraction functioning |
| Implement validators | Backend Dev | 1 day | All field validators unit tested |

### Week 2: Integration & Enhancement
| Task | Owner | Duration | Acceptance Criteria |
|------|-------|----------|-------------------|
| Integrate full pipeline | Backend Lead | 2 days | End-to-end extraction working |
| Add Textract fallback | Cloud Engineer | 2 days | AWS integration tested (or stubbed) |
| Build FastAPI endpoints | Backend Dev | 1 day | All endpoints responding correctly |
| Create developer scripts | DevOps | 1 day | Calibration and batch tools working |
| Implement audit logging | Security Lead | 1 day | POPIA-compliant logging verified |
| Frontend integration | Frontend Dev | 2 days | Confirmation UI connected to API |
| Testing & QA | QA Team | 2 days | >85% field accuracy achieved |
| Deployment setup | DevOps | 1 day | Docker container running successfully |

---

## 16. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Form template changes | High | Medium | Version templates, detect layout changes, notify admin |
| Poor image quality | High | High | Preprocessing pipeline, user guidance, quality checks |
| Handwritten sections | Medium | Low | Flag for manual review, exclude from automation |
| Performance bottleneck | Medium | Medium | Async processing, caching, horizontal scaling |
| POPIA compliance violation | High | Low | Audit logs, encryption, access controls, data retention |
| Textract costs | Low | Medium | Confidence thresholds, daily limits, monitoring |
| Language variations | Medium | Low | Multi-language Tesseract models, field mapping |

---

## 17. Optional Enhancements

### Phase 2 Features
1. **Mobile Capture Optimization**
   - Client-side preview with guidelines
   - Auto-capture when aligned
   - Real-time quality feedback
   - Glare/shadow detection

2. **ML Field Extraction**
   - Train custom field detection model
   - Active learning from corrections
   - Confidence improvement over time

3. **Multi-Form Support**
   - Template library management
   - Auto-detect form type
   - Custom field mapping UI

4. **Advanced Analytics**
   - Field accuracy dashboards
   - Processing time metrics
   - Error pattern analysis
   - ROI calculations

5. **Integration Expansions**
   - HL7/FHIR export
   - Direct EHR integration
   - Webhook notifications
   - Batch import API

---

## Conclusion

This implementation plan provides a production-ready OCR pipeline optimized for South African medical forms with:
- **Offline-first processing** using OpenCV + Tesseract
- **Cloud fallback** via AWS Textract for difficult cases  
- **POPIA compliance** with audit trails and data protection
- **Comprehensive validation** including SA ID verification
- **Extensible architecture** for future enhancements

The modular design allows incremental development while maintaining high accuracy (>85% target) and performance suitable for clinical workflows.

### Success Metrics
- Field extraction accuracy: >85%
- Processing time: <3 seconds per form
- User correction rate: <15% of fields
- System availability: 99.5% uptime
- POPIA compliance: 100% audit coverage

### Next Steps
1. Review and approve implementation plan
2. Assign team members to Week 1 tasks
3. Setup development environment
4. Begin template calibration with sample forms
5. Schedule daily standups for progress tracking