from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import List, Dict, Optional
import pytesseract
from PIL import Image
import pdfplumber
import io
import re
import logging
import uuid
from pathlib import Path
import os
import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=config.API_TITLE,
    description=config.API_DESCRIPTION,
    version=config.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# Ensure upload directory exists
config.UPLOAD_DIR.mkdir(exist_ok=True)

# In-memory data store (consider using a database for production)
health_records: List[Dict] = []
file_metadata: Dict[str, Dict] = {}

class HealthRecord:
    """Data model for health records with AI insights"""
    def __init__(self, name: str, value: float, unit: str, range_str: str, status: str, date: str, file_id: str):
        self.id = str(uuid.uuid4())
        self.name = name.strip()
        self.value = value
        self.unit = unit.strip() or "N/A"
        self.range = range_str
        self.status = status
        self.date = date
        self.file_id = file_id
        self.created_at = datetime.now().isoformat()
        
        # Add AI insights and severity
        self.severity = self._calculate_severity()
        self.ai_insight = self._generate_ai_insight()
    
    def _calculate_severity(self) -> str:
        """Calculate severity based on status and value deviation"""
        if self.status == "Normal":
            return "None"
        
        # Parse range if available
        if self.range != "N/A" and "-" in self.range:
            try:
                low, high = map(float, self.range.split("-"))
                range_width = high - low
                
                # Calculate deviation percentage
                if self.value < low:
                    deviation = (low - self.value) / range_width
                elif self.value > high:
                    deviation = (self.value - high) / range_width
                else:
                    return "None"
                
                # Classify severity based on deviation
                if deviation >= 0.5:
                    return "Severe"
                elif deviation >= 0.2:
                    return "Moderate"
                else:
                    return "Mild"
            except (ValueError, ZeroDivisionError):
                pass
        
        # Default classification based on status
        if self.status in ["High", "Low", "Abnormal"]:
            return "Moderate"
        elif self.status == "Needs Attention":
            return "Mild"
        
        return "None"
    
    def _generate_ai_insight(self) -> str:
        """Generate AI-powered insights based on health parameter"""
        parameter_lower = self.name.lower()
        
        # Common health parameters with insights
        insights = {
            "hemoglobin": {
                "normal": "Good oxygen-carrying capacity",
                "low": "May indicate anemia or blood loss",
                "high": "Could suggest dehydration or blood disorders"
            },
            "glucose": {
                "normal": "Blood sugar levels are well controlled",
                "low": "Risk of hypoglycemia - monitor closely",
                "high": "May indicate diabetes or prediabetes"
            },
            "cholesterol": {
                "normal": "Heart health appears good",
                "low": "Generally good, but very low levels need monitoring",
                "high": "Increased cardiovascular risk - consider lifestyle changes"
            },
            "blood pressure": {
                "normal": "Cardiovascular health is good",
                "low": "Monitor for dizziness or fainting",
                "high": "Hypertension risk - lifestyle and medication review needed"
            },
            "creatinine": {
                "normal": "Kidney function appears normal",
                "low": "Usually not concerning",
                "high": "May indicate kidney dysfunction"
            },
            "white blood cells": {
                "normal": "Immune system functioning well",
                "low": "Increased infection risk",
                "high": "May indicate infection or immune response"
            },
            "platelets": {
                "normal": "Blood clotting function normal",
                "low": "Increased bleeding risk",
                "high": "May indicate blood disorders"
            },
            "vitamin d": {
                "normal": "Bone health support is adequate",
                "low": "May affect bone health and immunity",
                "high": "Generally safe but monitor for toxicity"
            },
            "thyroid": {
                "normal": "Thyroid function is balanced",
                "low": "May indicate hypothyroidism",
                "high": "May indicate hyperthyroidism"
            }
        }
        
        # Find matching parameter
        for param, insight_dict in insights.items():
            if param in parameter_lower:
                if self.status == "Normal":
                    return insight_dict.get("normal", "Parameter is within normal range")
                elif self.status in ["Low", "Below Normal"]:
                    return insight_dict.get("low", "Below normal range - consider medical consultation")
                elif self.status in ["High", "Above Normal", "Needs Attention"]:
                    return insight_dict.get("high", "Above normal range - consider medical consultation")
        
        # Generic insights based on status
        if self.status == "Normal":
            return "Parameter is within healthy range"
        elif self.status in ["Low", "Below Normal"]:
            return "Below normal range - recommend follow-up"
        elif self.status in ["High", "Above Normal"]:
            return "Above normal range - may need attention"
        elif self.status == "Needs Attention":
            return "Parameter deviation detected - consult healthcare provider"
        
        return "Consult healthcare provider for interpretation"
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "range": self.range,
            "status": self.status,
            "severity": self.severity,
            "ai_insight": self.ai_insight,
            "date": self.date,
            "file_id": self.file_id,
            "created_at": self.created_at
        }

def validate_file(file: UploadFile) -> None:
    """Validate uploaded file"""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )
    
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_extension} not allowed. Supported types: {', '.join(config.ALLOWED_EXTENSIONS)}"
        )

def extract_health_data_from_text(text: str, file_id: str) -> List[HealthRecord]:
    """Extract health data from text using improved regex patterns with enhanced status detection"""
    if not text.strip():
        return []
    
    # Enhanced regex patterns for different health report formats
    patterns = [
        # Pattern 1: Name Value Unit Range (e.g., "Hemoglobin 12.5 g/dL 12.0-15.0")
        r"([A-Za-z\s]+?)\s+(\d+(?:\.\d+)?)\s*([a-zA-Z/%]+)?\s+(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)",
        
        # Pattern 2: Name Value Unit (Normal/Abnormal) (e.g., "Glucose 95 mg/dL Normal")
        r"([A-Za-z\s]+?)\s+(\d+(?:\.\d+)?)\s*([a-zA-Z/%]+)?\s+(Normal|Abnormal|High|Low|Elevated|Decreased)",
        
        # Pattern 3: Simple Name Value Unit (e.g., "Blood Pressure 120/80 mmHg")
        r"([A-Za-z\s]+?)\s+(\d+(?:\.\d+)?(?:/\d+)?)\s*([a-zA-Z/%]+)?",
        
        # Pattern 4: Name: Value Unit (e.g., "Cholesterol: 180 mg/dL")
        r"([A-Za-z\s]+):\s*(\d+(?:\.\d+)?)\s*([a-zA-Z/%]+)?",
        
        # Pattern 5: Name Value (Range) Unit (e.g., "Hemoglobin 12.5 (12.0-15.0) g/dL")
        r"([A-Za-z\s]+?)\s+(\d+(?:\.\d+)?)\s*\((\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\)\s*([a-zA-Z/%]+)?"
    ]
    
    results = []
    processed_lines = set()  # Avoid duplicates
    
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            line_start = text.rfind('\n', 0, match.start()) + 1
            line_end = text.find('\n', match.end())
            if line_end == -1:
                line_end = len(text)
            
            line = text[line_start:line_end].strip()
            if line in processed_lines:
                continue
            processed_lines.add(line)
            
            try:
                groups = match.groups()
                name = groups[0].strip()
                value_str = groups[1]
                
                # Skip if name is too short or contains only numbers
                if len(name) < 2 or name.isdigit():
                    continue
                
                # Clean up parameter names
                name = _clean_parameter_name(name)
                
                # Handle different value formats
                if '/' in value_str:  # Blood pressure format
                    value = float(value_str.split('/')[0])
                else:
                    value = float(value_str)
                
                # Extract unit, range, and status based on pattern
                unit, range_str, status = _extract_unit_range_status(groups, pattern)
                
                # Enhanced status determination
                if status == "Unknown" and range_str != "N/A":
                    status = _determine_status_from_range(value, range_str)
                
                # If still unknown, use parameter-specific rules
                if status == "Unknown":
                    status = _determine_status_by_parameter(name, value, unit)
                
                # Create health record
                record = HealthRecord(
                    name=name,
                    value=value,
                    unit=unit,
                    range_str=range_str,
                    status=status,
                    date=datetime.now().strftime("%Y-%m-%d"),
                    file_id=file_id
                )
                results.append(record)
                
            except (ValueError, TypeError, IndexError) as e:
                logger.warning(f"Failed to parse match: {match.groups()}, error: {e}")
                continue
    
    return results

def _clean_parameter_name(name: str) -> str:
    """Clean and standardize parameter names"""
    # Remove common prefixes and suffixes
    name = re.sub(r'^(serum|plasma|blood|total|free)\s+', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+(level|count|test|result)$', '', name, flags=re.IGNORECASE)
    
    # Standardize common parameter names
    standardized = {
        'hb': 'Hemoglobin',
        'hgb': 'Hemoglobin',
        'wbc': 'White Blood Cells',
        'rbc': 'Red Blood Cells',
        'plt': 'Platelets',
        'bp': 'Blood Pressure',
        'chol': 'Cholesterol',
        'hdl': 'HDL Cholesterol',
        'ldl': 'LDL Cholesterol',
        'trig': 'Triglycerides',
        'glu': 'Glucose',
        'cr': 'Creatinine',
        'bun': 'Blood Urea Nitrogen',
        'alt': 'ALT',
        'ast': 'AST',
        'tsh': 'TSH',
        't3': 'T3',
        't4': 'T4'
    }
    
    name_lower = name.lower().strip()
    for abbrev, full_name in standardized.items():
        if abbrev == name_lower:
            return full_name
    
    # Capitalize first letter of each word
    return ' '.join(word.capitalize() for word in name.split())

def _extract_unit_range_status(groups: tuple, pattern: str) -> tuple:
    """Extract unit, range, and status from regex groups"""
    unit = "N/A"
    range_str = "N/A"
    status = "Unknown"
    
    if len(groups) >= 3 and groups[2]:
        unit = groups[2].strip()
    
    # Check for explicit status in groups
    for group in groups[2:]:
        if group and group.strip().lower() in ['normal', 'abnormal', 'high', 'low', 'elevated', 'decreased']:
            status = group.strip().title()
            break
    
    # Check for range in groups
    if len(groups) >= 5:
        if groups[3] and groups[4]:
            try:
                low = float(groups[3])
                high = float(groups[4])
                range_str = f"{low}-{high}"
            except (ValueError, TypeError):
                pass
    
    return unit, range_str, status

def _determine_status_from_range(value: float, range_str: str) -> str:
    """Determine status based on value and range"""
    if range_str == "N/A" or "-" not in range_str:
        return "Unknown"
    
    try:
        low, high = map(float, range_str.split("-"))
        if low <= value <= high:
            return "Normal"
        elif value < low:
            return "Low"
        elif value > high:
            return "High"
    except (ValueError, TypeError):
        pass
    
    return "Unknown"

def _determine_status_by_parameter(name: str, value: float, unit: str) -> str:
    """Determine status using parameter-specific normal ranges"""
    name_lower = name.lower()
    
    # Common health parameter ranges (approximate)
    normal_ranges = {
        'hemoglobin': {'male': (13.5, 17.5), 'female': (12.0, 15.5), 'unit': 'g/dl'},
        'glucose': {'range': (70, 100), 'unit': 'mg/dl'},
        'cholesterol': {'range': (125, 200), 'unit': 'mg/dl'},
        'hdl cholesterol': {'male': (40, 60), 'female': (50, 60), 'unit': 'mg/dl'},
        'ldl cholesterol': {'range': (0, 100), 'unit': 'mg/dl'},
        'triglycerides': {'range': (0, 150), 'unit': 'mg/dl'},
        'creatinine': {'male': (0.7, 1.3), 'female': (0.6, 1.1), 'unit': 'mg/dl'},
        'blood urea nitrogen': {'range': (7, 20), 'unit': 'mg/dl'},
        'white blood cells': {'range': (4.5, 11.0), 'unit': 'k/ul'},
        'red blood cells': {'male': (4.7, 6.1), 'female': (4.2, 5.4), 'unit': 'm/ul'},
        'platelets': {'range': (150, 450), 'unit': 'k/ul'},
        'tsh': {'range': (0.4, 4.0), 'unit': 'miu/l'},
        'vitamin d': {'range': (30, 100), 'unit': 'ng/ml'},
        'blood pressure': {'systolic': (90, 120), 'diastolic': (60, 80), 'unit': 'mmhg'}
    }
    
    # Find matching parameter
    for param, ranges in normal_ranges.items():
        if param in name_lower:
            if 'range' in ranges:
                low, high = ranges['range']
                if low <= value <= high:
                    return "Normal"
                elif value < low:
                    return "Low"
                elif value > high:
                    return "High"
            # Handle gender-specific ranges (default to general range)
            elif 'male' in ranges and 'female' in ranges:
                # Use male range as default (could be improved with gender detection)
                low, high = ranges['male']
                if low <= value <= high:
                    return "Normal"
                elif value < low:
                    return "Low"
                elif value > high:
                    return "High"
            break
    
    return "Unknown"

def extract_text_from_pdf(contents: bytes) -> str:
    """Extract text from PDF file"""
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                    logger.info(f"Extracted text from PDF page {page_num + 1}")
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to process PDF file: {str(e)}"
        )
    return text

def extract_text_from_image(contents: bytes) -> str:
    """Extract text from image file using OCR"""
    text = ""
    try:
        image = Image.open(io.BytesIO(contents))
        
        # Preprocess image for better OCR results
        image = image.convert('RGB')
        
        # Use pytesseract with configuration for better medical text recognition
        text = pytesseract.image_to_string(image, config=config.TESSERACT_CONFIG)
        
        logger.info(f"Extracted text from image, length: {len(text)}")
    except Exception as e:
        logger.error(f"Error extracting text from image: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to process image file: {str(e)}"
        )
    return text

# API Routes
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Health Report Extractor API",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "records_count": len(health_records),
        "files_processed": len(file_metadata),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process health report files"""
    try:
        # Validate file
        validate_file(file)
        
        # Check file size
        contents = await file.read()
        if len(contents) > config.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {config.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Store file metadata
        file_metadata[file_id] = {
            "filename": file.filename,
            "size": len(contents),
            "upload_time": datetime.now().isoformat(),
            "content_type": file.content_type
        }
        
        logger.info(f"Processing file: {file.filename} (ID: {file_id}, Size: {len(contents)} bytes)")
        
        # Extract text based on file type
        text = ""
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension == '.pdf':
            text = extract_text_from_pdf(contents)
        else:  # Image files
            text = extract_text_from_image(contents)
        
        if not text.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No text could be extracted from the file"
            )
        
        # Extract health data
        extracted_records = extract_health_data_from_text(text, file_id)
        
        if not extracted_records:
            logger.warning(f"No health data found in file: {file.filename}")
            return {
                "message": "File processed successfully but no health data was found",
                "file_id": file_id,
                "data": [],
                "extracted_text_preview": text[:200] + "..." if len(text) > 200 else text
            }
        
        # Add to global records
        health_records.extend(extracted_records)
        
        # Convert to dictionaries for JSON response
        extracted_data = [record.to_dict() for record in extracted_records]
        
        logger.info(f"Successfully extracted {len(extracted_records)} health records from {file.filename}")
        
        return {
            "message": f"Successfully processed {file.filename}",
            "file_id": file_id,
            "records_extracted": len(extracted_records),
            "data": extracted_data,
            "total_records": len(health_records)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing file {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while processing the file: {str(e)}"
        )

@app.get("/records")
async def get_all_records():
    """Get all health records"""
    return {
        "records": [record.to_dict() for record in health_records],
        "total": len(health_records),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/records/{record_id}")
async def get_record(record_id: str):
    """Get a specific health record by ID"""
    for record in health_records:
        if record.id == record_id:
            return record.to_dict()
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Record with ID {record_id} not found"
    )

@app.delete("/records/{record_id}")
async def delete_record(record_id: str):
    """Delete a specific health record"""
    global health_records
    
    for i, record in enumerate(health_records):
        if record.id == record_id:
            deleted_record = health_records.pop(i)
            logger.info(f"Deleted record: {deleted_record.name} (ID: {record_id})")
            return {
                "message": f"Record '{deleted_record.name}' deleted successfully",
                "deleted_record": deleted_record.to_dict()
            }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Record with ID {record_id} not found"
    )

@app.delete("/records")
async def clear_all_records():
    """Clear all health records"""
    global health_records, file_metadata
    
    records_count = len(health_records)
    files_count = len(file_metadata)
    
    health_records.clear()
    file_metadata.clear()
    
    logger.info(f"Cleared {records_count} records and {files_count} file metadata entries")
    
    return {
        "message": f"Successfully cleared {records_count} records and {files_count} files",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/files")
async def get_files_metadata():
    """Get metadata for all processed files"""
    return {
        "files": file_metadata,
        "total": len(file_metadata),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/insights")
async def get_health_insights():
    """Get AI-powered health insights and recommendations"""
    if not health_records:
        return {
            "message": "No health data available for insights",
            "insights": [],
            "recommendations": []
        }
    
    # Analyze health records for insights
    insights = []
    recommendations = []
    
    # Group by parameter type
    parameter_groups = {}
    for record in health_records:
        param_name = record.name
        if param_name not in parameter_groups:
            parameter_groups[param_name] = []
        parameter_groups[param_name].append(record)
    
    # Generate insights for each parameter
    for param_name, records in parameter_groups.items():
        latest_record = max(records, key=lambda x: x.created_at)
        
        # Count abnormal values
        abnormal_count = sum(1 for r in records if r.status != "Normal")
        total_count = len(records)
        
        insight = {
            "parameter": param_name,
            "latest_value": latest_record.value,
            "latest_status": latest_record.status,
            "severity": latest_record.severity,
            "ai_insight": latest_record.ai_insight,
            "trend": "stable",  # Could be enhanced with trend analysis
            "abnormal_percentage": round((abnormal_count / total_count) * 100, 1),
            "total_tests": total_count
        }
        insights.append(insight)
        
        # Generate recommendations
        if latest_record.status != "Normal":
            recommendations.append({
                "parameter": param_name,
                "priority": "high" if latest_record.severity in ["Severe", "Moderate"] else "medium",
                "recommendation": _generate_recommendation(param_name, latest_record.status, latest_record.severity),
                "follow_up_needed": latest_record.severity in ["Severe", "Moderate"]
            })
    
    # Overall health summary
    total_parameters = len(parameter_groups)
    abnormal_parameters = sum(1 for records in parameter_groups.values() 
                            if max(records, key=lambda x: x.created_at).status != "Normal")
    
    health_score = max(0, 100 - (abnormal_parameters / total_parameters * 100)) if total_parameters > 0 else 0
    
    return {
        "health_summary": {
            "total_parameters": total_parameters,
            "abnormal_parameters": abnormal_parameters,
            "health_score": round(health_score, 1),
            "overall_status": "Good" if health_score >= 80 else "Needs Attention" if health_score >= 60 else "Poor"
        },
        "insights": insights,
        "recommendations": recommendations,
        "timestamp": datetime.now().isoformat()
    }

def _generate_recommendation(parameter: str, status: str, severity: str) -> str:
    """Generate specific recommendations based on parameter and status"""
    param_lower = parameter.lower()
    
    recommendations = {
        "hemoglobin": {
            "high": "Consider hydration status and underlying blood disorders. Consult hematologist if persistent.",
            "low": "Increase iron-rich foods, consider iron supplements, and investigate for bleeding sources."
        },
        "glucose": {
            "high": "Monitor blood sugar regularly, consider dietary modifications, and consult endocrinologist.",
            "low": "Carry glucose tablets, eat regular meals, and monitor for hypoglycemic episodes."
        },
        "cholesterol": {
            "high": "Adopt heart-healthy diet, increase physical activity, and consider statin therapy.",
            "low": "Generally good, but ensure adequate nutrition and monitor for underlying conditions."
        },
        "blood pressure": {
            "high": "Reduce sodium intake, exercise regularly, manage stress, and consider antihypertensive medication.",
            "low": "Stay hydrated, avoid sudden position changes, and monitor for symptoms."
        },
        "creatinine": {
            "high": "Monitor kidney function, stay hydrated, and consult nephrologist for further evaluation.",
            "low": "Usually not concerning, but ensure adequate protein intake."
        },
        "white blood cells": {
            "high": "Investigate for infections or inflammatory conditions. Consider complete blood count with differential.",
            "low": "Monitor for infections, consider immune system evaluation, and avoid sick contacts."
        },
        "platelets": {
            "high": "Monitor for clotting disorders and consider hematology consultation.",
            "low": "Avoid activities with bleeding risk, monitor for easy bruising, and consult hematologist."
        }
    }
    
    # Find specific recommendation
    for param, rec_dict in recommendations.items():
        if param in param_lower:
            status_key = "high" if status in ["High", "Above Normal"] else "low"
            if status_key in rec_dict:
                return rec_dict[status_key]
    
    # Generic recommendations
    if status in ["High", "Above Normal"]:
        return "Parameter is elevated. Consider lifestyle modifications and follow up with healthcare provider."
    elif status in ["Low", "Below Normal"]:
        return "Parameter is below normal. Monitor symptoms and consult healthcare provider if concerned."
    
    return "Abnormal result detected. Recommend follow-up with healthcare provider for proper evaluation."

@app.get("/stats")
async def get_statistics():
    """Get comprehensive statistics about the processed data"""
    if not health_records:
        return {
            "message": "No data available",
            "total_records": 0,
            "total_files": 0
        }
    
    # Calculate statistics
    total_records = len(health_records)
    total_files = len(file_metadata)
    
    # Group by status
    status_counts = {}
    severity_counts = {}
    for record in health_records:
        status = record.status
        severity = record.severity
        status_counts[status] = status_counts.get(status, 0) + 1
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    # Group by test type
    test_counts = {}
    for record in health_records:
        test_name = record.name
        test_counts[test_name] = test_counts.get(test_name, 0) + 1
    
    # Recent records (last 10)
    recent_records = sorted(health_records, key=lambda x: x.created_at, reverse=True)[:10]
    
    # Calculate health metrics
    abnormal_count = sum(1 for r in health_records if r.status != "Normal")
    normal_percentage = ((total_records - abnormal_count) / total_records * 100) if total_records > 0 else 0
    
    return {
        "overview": {
            "total_records": total_records,
            "total_files": total_files,
            "normal_percentage": round(normal_percentage, 1),
            "abnormal_count": abnormal_count
        },
        "distributions": {
            "status_distribution": status_counts,
            "severity_distribution": severity_counts,
            "test_distribution": dict(sorted(test_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        },
        "recent_records": [record.to_dict() for record in recent_records],
        "timestamp": datetime.now().isoformat()
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "An unexpected error occurred",
            "status_code": 500,
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Health Report Extractor API server...")
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower()
    )

