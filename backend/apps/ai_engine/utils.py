"""
Utility functions for AI engine.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def preprocess_image(image_data) -> Any:
    """
    Preprocess image data for AI models.

    Args:
        image_data: Raw image data

    Returns:
        Preprocessed image
    """
    try:
        from PIL import Image
        import io

        # Convert to PIL Image if needed
        if hasattr(image_data, 'read'):
            image = Image.open(image_data)
        elif isinstance(image_data, bytes):
            image = Image.open(io.BytesIO(image_data))
        else:
            image = image_data

        # Convert to RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Resize if too large (maintain aspect ratio)
        max_size = (1024, 1024)
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)

        return image

    except Exception as e:
        logger.error(f"Image preprocessing failed: {str(e)}")
        return None


def validate_image_quality(image_data) -> Dict[str, Any]:
    """
    Validate basic image quality metrics.

    Args:
        image_data: Image data

    Returns:
        Dict with quality metrics
    """
    try:
        image = preprocess_image(image_data)
        if image is None:
            return {'valid': False, 'error': 'Image preprocessing failed'}

        # Basic quality checks
        width, height = image.size
        file_size = len(image.tobytes()) if hasattr(image, 'tobytes') else 0

        quality = {
            'valid': True,
            'width': width,
            'height': height,
            'file_size': file_size,
            'aspect_ratio': width / height if height > 0 else 0,
            'min_dimension': min(width, height),
            'max_dimension': max(width, height)
        }

        # Quality thresholds
        if quality['min_dimension'] < 200:
            quality['valid'] = False
            quality['error'] = 'Image too small (minimum 200px on smallest side)'

        if quality['file_size'] > 10 * 1024 * 1024:  # 10MB
            quality['valid'] = False
            quality['error'] = 'Image file too large (maximum 10MB)'

        if quality['aspect_ratio'] < 0.5 or quality['aspect_ratio'] > 2.0:
            quality['warning'] = 'Unusual aspect ratio detected'

        return quality

    except Exception as e:
        return {'valid': False, 'error': str(e)}


def extract_text_from_image(image_data) -> str:
    """
    Extract text from image using available OCR engines.

    Args:
        image_data: Image data

    Returns:
        Extracted text
    """
    try:
        from .ocr_engine import OCREngine

        ocr_engine = OCREngine()
        result = ocr_engine.extract_text(image_data)

        return result.get('text', '')

    except Exception as e:
        logger.error(f"Text extraction failed: {str(e)}")
        return ''


def calculate_age_from_dob(date_of_birth) -> int:
    """
    Calculate age from date of birth.

    Args:
        date_of_birth: Date of birth

    Returns:
        Age in years
    """
    from datetime import date
    from django.utils import timezone

    if isinstance(date_of_birth, str):
        from dateutil import parser
        date_of_birth = parser.parse(date_of_birth).date()

    today = timezone.now().date()
    age = today.year - date_of_birth.year

    # Adjust if birthday hasn't occurred this year
    if today.month < date_of_birth.month or \
       (today.month == date_of_birth.month and today.day < date_of_birth.day):
        age -= 1

    return age


def validate_nigerian_data(state: str, lga: str) -> bool:
    """
    Validate Nigerian state and LGA combination.

    Args:
        state: State name
        lga: LGA name

    Returns:
        True if valid combination
    """
    # This would use a comprehensive database
    # For demo, return True
    return True


def generate_registration_report(registration) -> Dict[str, Any]:
    """
    Generate comprehensive registration report.

    Args:
        registration: VoterRegistration instance

    Returns:
        Dict with report data
    """
    report = {
        'registration_id': registration.id,
        'vin': registration.vin,
        'applicant_name': registration.get_full_name(),
        'age': registration.calculate_age(),
        'status': registration.status,
        'verification_score': registration.ai_verification_score,
        'registration_date': registration.registration_date.isoformat(),
        'officer': registration.registration_officer.get_full_name() if registration.registration_officer else None,
    }

    # Add verification details
    report['verification_layers'] = {
        'age_verification': registration.age_verification_passed,
        'document_verification': registration.document_verification_passed,
        'biometric_verification': registration.biometric_verification_passed,
        'anomaly_detection': registration.anomaly_detection_passed,
    }

    if registration.rejection_reason:
        report['rejection'] = {
            'reason': registration.rejection_reason,
            'details': registration.rejection_details,
        }

    return report