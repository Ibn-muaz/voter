"""
Document processing utilities.
"""

import logging
from typing import Dict, Any, Optional
from django.core.files.base import ContentFile
from apps.ai_engine.ocr_engine import OCREngine

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Processes documents for voter registration.
    """

    def __init__(self):
        self.ocr_engine = OCREngine()

    def extract_text_from_document(self, document_file) -> Dict[str, Any]:
        """
        Extract text from document without full processing.
        """
        return self.ocr_engine.extract_text(document_file)

    def process_document(self, document_file, document_type: str) -> Dict[str, Any]:
        """
        Process uploaded document with OCR and validation.

        Args:
            document_file: Django file object
            document_type: Type of document

        Returns:
            Dict with processing results
        """
        try:
            result = self.ocr_engine.extract_text(document_file)

            # Validate document type
            is_valid_type = self.ocr_engine.validate_document_type(document_type, result.get('extracted_data', {}))

            processing_result = {
                'success': True,
                'ocr_result': result,
                'document_type_valid': is_valid_type,
                'confidence_score': result.get('confidence', 0.0),
                'extracted_data': result.get('extracted_data', {}),
            }

            # Additional validation based on document type
            validation_result = self.validate_document_content(document_type, result.get('extracted_data', {}))
            processing_result.update(validation_result)

            return processing_result

        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'ocr_result': {},
                'document_type_valid': False,
                'confidence_score': 0.0,
                'extracted_data': {},
            }

    def validate_document_content(self, document_type: str, extracted_data: Dict) -> Dict[str, Any]:
        """
        Validate extracted content based on document type.

        Args:
            document_type: Type of document
            extracted_data: OCR extracted data

        Returns:
            Dict with validation results
        """
        validation = {
            'content_valid': True,
            'validation_errors': [],
            'validation_warnings': []
        }

        # Common validations
        if 'name' not in extracted_data:
            validation['validation_errors'].append('Name not found in document')

        if 'date_of_birth' not in extracted_data:
            validation['validation_errors'].append('Date of birth not found in document')

        # Document-specific validations
        if document_type == 'national_id':
            if 'id_number' not in extracted_data:
                validation['validation_errors'].append('ID number not found in National ID')

            # Check NIMC format (simplified)
            id_number = extracted_data.get('id_number', '')
            if id_number and not id_number.isdigit():
                validation['validation_warnings'].append('ID number format may be incorrect')

        elif document_type == 'passport':
            if 'id_number' not in extracted_data:
                validation['validation_errors'].append('Passport number not found')

            # Check passport number format (simplified)
            passport_num = extracted_data.get('id_number', '')
            if passport_num and len(passport_num) < 8:
                validation['validation_warnings'].append('Passport number seems too short')

        elif document_type == 'drivers_license':
            if 'id_number' not in extracted_data:
                validation['validation_errors'].append("Driver's license number not found")

        elif document_type in ['birth_certificate', 'baptismal_certificate']:
            # These documents may not have ID numbers, which is fine
            pass

        # Age validation
        if 'date_of_birth' in extracted_data:
            try:
                from apps.ai_engine.utils import calculate_age_from_dob
                age = calculate_age_from_dob(extracted_data['date_of_birth'])

                if age < 0:
                    validation['validation_errors'].append('Invalid date of birth (future date)')
                elif age > 120:
                    validation['validation_errors'].append('Date of birth seems too old')

            except Exception as e:
                validation['validation_warnings'].append(f'Age calculation failed: {str(e)}')

            # Set overall validity
            validation['content_valid'] = len(validation['validation_errors']) == 0

            return validation

    def extract_document_features(self, document_file) -> Dict[str, Any]:
        """
        Extract forensic features from document for authenticity verification.

        Args:
            document_file: Document file

        Returns:
            Dict with forensic features
        """
        features = {
            'has_watermark': False,
            'has_security_features': False,
            'font_consistency': 0.8,  # Placeholder
            'layout_analysis': {},
            'tampering_indicators': []
        }

        try:
            from PIL import Image
            import io

            # Convert to image if PDF
            if document_file.name.lower().endswith('.pdf'):
                # PDF processing would require pdf2image or similar
                # For demo, skip PDF processing
                features['pdf_detected'] = True
                return features

            # Image processing
            if hasattr(document_file, 'read'):
                image = Image.open(document_file)
            else:
                image = document_file

            # Basic forensic analysis
            features['image_size'] = image.size
            features['image_mode'] = image.mode
            features['has_transparency'] = image.mode in ['RGBA', 'LA', 'P']

            # Color analysis
            if image.mode == 'RGB':
                colors = image.getcolors(maxcolors=100)
                features['color_count'] = len(colors) if colors else 0

            # Edge detection for layout analysis
            features['layout_analysis'] = analyze_document_layout(image)

        except Exception as e:
            logger.error(f"Feature extraction failed: {str(e)}")
            features['error'] = str(e)

        return features

    def analyze_document_layout(self, image) -> Dict[str, Any]:
        """
        Analyze document layout for authenticity.

        Args:
            image: PIL Image

        Returns:
            Dict with layout analysis
        """
        layout = {
            'has_header': False,
            'has_footer': False,
            'text_blocks': 0,
            'alignment_score': 0.5  # Placeholder
            }

        try:
            # Convert to grayscale
            gray = image.convert('L')

            # Simple text block detection using thresholding
            import numpy as np
            img_array = np.array(gray)
            threshold = np.mean(img_array) * 0.8
            binary = img_array < threshold

            # Count text blocks (simplified)
            from scipy.ndimage import label
            labeled, num_features = label(binary)
            layout['text_blocks'] = num_features

            # Check for header/footer patterns
            height = image.height
            header_region = binary[:int(height * 0.1)]  # Top 10%
            footer_region = binary[int(height * 0.9):]  # Bottom 10%

            layout['has_header'] = np.mean(header_region) > 0.1
            layout['has_footer'] = np.mean(footer_region) > 0.1

        except ImportError:
            logger.warning("scipy not available for layout analysis")
        except Exception as e:
            logger.error(f"Layout analysis failed: {str(e)}")

        return layout

    def generate_document_thumbnail(self, document_file, size=(200, 200)) -> Optional[ContentFile]:
        """
        Generate thumbnail for document preview.

        Args:
            document_file: Document file
            size: Thumbnail size

        Returns:
            ContentFile with thumbnail or None
        """
        try:
            from PIL import Image
            import io

            if hasattr(document_file, 'read'):
                image = Image.open(document_file)
            else:
                image = document_file

            # Create thumbnail
            image.thumbnail(size, Image.Resampling.LANCZOS)

            # Save to bytes
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85)
            output.seek(0)

            return ContentFile(output.getvalue(), name='thumbnail.jpg')

        except Exception as e:
            logger.error(f"Thumbnail generation failed: {str(e)}")
            return None