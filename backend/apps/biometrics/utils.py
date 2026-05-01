"""
Biometric processing utilities.
"""

import logging
from typing import Dict, Any, Optional
from django.core.files.base import ContentFile
from apps.ai_engine.biometric_verification import BiometricVerifier

logger = logging.getLogger(__name__)


class BiometricProcessor:
    """
    Processes biometric data for voter registration.
    """

    def __init__(self):
        self.verifier = BiometricVerifier()

    def process_biometric_data(self, biometric_file, biometric_type: str, finger_type: str = None) -> Dict[str, Any]:
        """
        Process biometric data (photo or fingerprint).

        Args:
            biometric_file: Biometric image file
            biometric_type: Type of biometric ('photo' or 'fingerprint')
            finger_type: Specific finger type for fingerprints

        Returns:
            Dict with processing results
        """
        try:
            if biometric_type == 'photo':
                result = self.verifier.verify_face(biometric_file)
                result['biometric_type'] = 'photo'

            elif biometric_type == 'fingerprint':
                result = self.verifier.verify_fingerprint(biometric_file, finger_type or 'unknown')
                result['biometric_type'] = 'fingerprint'
                result['finger_type'] = finger_type

            else:
                return {
                    'success': False,
                    'error': f'Unsupported biometric type: {biometric_type}'
                }

            # Add processing metadata
            result['processed_at'] = 'now'  # Would be actual timestamp
            result['processing_version'] = '1.0'

            return result

        except Exception as e:
            logger.error(f"Biometric processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def process_fingerprint(self, fingerprint_file, finger_type: str = 'right_index') -> Dict[str, Any]:
        """
        Process fingerprint image.

        Args:
            fingerprint_file: Fingerprint image file
            finger_type: Type of finger

        Returns:
            Dict with fingerprint processing results
        """
        return self.process_biometric_data(fingerprint_file, 'fingerprint', finger_type)

    def process_facial_image(self, facial_file) -> Dict[str, Any]:
        """
        Process facial image.

        Args:
            facial_file: Facial image file

        Returns:
            Dict with facial processing results
        """
        return self.process_biometric_data(facial_file, 'photo')


def process_biometric_data(biometric_file, biometric_type: str, finger_type: str = None) -> Dict[str, Any]:
    """
    Process biometric data (photo or fingerprint).

    Args:
        biometric_file: Biometric image file
        biometric_type: Type of biometric ('photo' or 'fingerprint')
        finger_type: Specific finger type for fingerprints

    Returns:
        Dict with processing results
    """
    try:
        verifier = BiometricVerifier()

        if biometric_type == 'photo':
            result = verifier.verify_face(biometric_file)
            result['biometric_type'] = 'photo'

        elif biometric_type == 'fingerprint':
            result = verifier.verify_fingerprint(biometric_file, finger_type or 'unknown')
            result['biometric_type'] = 'fingerprint'
            result['finger_type'] = finger_type

        else:
            return {
                'success': False,
                'error': f'Unsupported biometric type: {biometric_type}'
            }

        # Add processing metadata
        result['processed_at'] = 'now'  # Would be actual timestamp
        result['processing_version'] = '1.0'

        return result

    except Exception as e:
        logger.error(f"Biometric processing failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'biometric_type': biometric_type,
            'verified': False,
            'quality_score': 0.0
        }


def generate_biometric_template(biometric_data: Dict, template_type: str) -> Optional[bytes]:
    """
    Generate biometric template for storage and matching.

    Args:
        biometric_data: Processed biometric data
        template_type: Type of template to generate

    Returns:
        Serialized template bytes or None
    """
    try:
        import pickle
        import json

        if template_type == 'face_embedding':
            embedding = biometric_data.get('features', {}).get('embedding')
            if embedding:
                return pickle.dumps(embedding)

        elif template_type == 'fingerprint_minutiae':
            minutiae = biometric_data.get('features', {}).get('minutiae')
            if minutiae:
                return json.dumps(minutiae).encode('utf-8')

        return None

    except Exception as e:
        logger.error(f"Template generation failed: {str(e)}")
        return None


def compare_biometric_templates(template1: bytes, template2: bytes, template_type: str) -> float:
    """
    Compare two biometric templates.

    Args:
        template1: First template
        template2: Second template
        template_type: Type of templates

    Returns:
        Similarity score (0-1)
    """
    try:
        import pickle
        import json
        import numpy as np

        if template_type == 'face_embedding':
            embedding1 = pickle.loads(template1)
            embedding2 = pickle.loads(template2)

            # Cosine similarity
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)

            similarity = dot_product / (norm1 * norm2)
            return max(0.0, min(1.0, similarity))

        elif template_type == 'fingerprint_minutiae':
            minutiae1 = json.loads(template1.decode('utf-8'))
            minutiae2 = json.loads(template2.decode('utf-8'))

            # Simple minutiae matching (placeholder)
            # In real implementation, use proper fingerprint matching algorithm
            matches = 0
            total = max(len(minutiae1), len(minutiae2))

            if total > 0:
                matches = min(len(minutiae1), len(minutiae2))  # Placeholder
                return matches / total

        return 0.0

    except Exception as e:
        logger.error(f"Template comparison failed: {str(e)}")
        return 0.0


def validate_biometric_capture(capture_data: Dict) -> Dict[str, Any]:
    """
    Validate biometric capture data.

    Args:
        capture_data: Capture data from frontend

    Returns:
        Dict with validation results
    """
    validation = {
        'valid': True,
        'errors': [],
        'warnings': []
    }

    # Check required fields
    required_fields = ['biometric_type', 'image_data']
    for field in required_fields:
        if field not in capture_data:
            validation['errors'].append(f'Missing required field: {field}')
            validation['valid'] = False

    if not validation['valid']:
        return validation

    # Validate biometric type
    valid_types = ['photo', 'fingerprint']
    if capture_data['biometric_type'] not in valid_types:
        validation['errors'].append(f'Invalid biometric type: {capture_data["biometric_type"]}')
        validation['valid'] = False
        return validation

    # Validate image data
    image_data = capture_data.get('image_data', '')
    if not image_data:
        validation['errors'].append('No image data provided')
        validation['valid'] = False
        return validation

    # Check image size (base64 encoded)
    # Rough estimate: base64 is ~33% larger than binary
    estimated_size = len(image_data) * 0.75
    if estimated_size > 5 * 1024 * 1024:  # 5MB
        validation['warnings'].append('Image data seems large, may affect processing')

    # Validate fingerprint specific requirements
    if capture_data['biometric_type'] == 'fingerprint':
        finger_type = capture_data.get('finger_type')
        if not finger_type:
            validation['errors'].append('Finger type required for fingerprint capture')
            validation['valid'] = False

        valid_fingers = [
            'left_thumb', 'right_thumb', 'left_index', 'right_index',
            'left_middle', 'right_middle', 'left_ring', 'right_ring',
            'left_pinky', 'right_pinky'
        ]

        if finger_type and finger_type not in valid_fingers:
            validation['errors'].append(f'Invalid finger type: {finger_type}')
            validation['valid'] = False

    return validation


def preprocess_biometric_image(image_data, biometric_type: str) -> Optional[Any]:
    """
    Preprocess biometric image for better quality.

    Args:
        image_data: Raw image data
        biometric_type: Type of biometric

    Returns:
        Preprocessed image or None
    """
    try:
        from PIL import Image, ImageFilter, ImageEnhance
        import io

        # Decode base64 if needed
        if isinstance(image_data, str) and image_data.startswith('data:image'):
            # Extract base64 data
            header, base64_data = image_data.split(',', 1)
            import base64
            image_bytes = base64.b64decode(base64_data)
            image = Image.open(io.BytesIO(image_bytes))
        elif hasattr(image_data, 'read'):
            image = Image.open(image_data)
        else:
            image = image_data

        # Convert to RGB if needed
        if image.mode not in ['RGB', 'L']:
            image = image.convert('RGB')

        # Apply preprocessing based on biometric type
        if biometric_type == 'photo':
            # Face image preprocessing
            image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)

        elif biometric_type == 'fingerprint':
            # Fingerprint preprocessing
            if image.mode != 'L':
                image = image.convert('L')

            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)

            # Apply slight sharpening
            image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=100, threshold=5))

        return image

    except Exception as e:
        logger.error(f"Image preprocessing failed: {str(e)}")
        return None


def estimate_capture_quality(image) -> float:
    """
    Estimate the quality of a biometric capture.

    Args:
        image: PIL Image

    Returns:
        Quality score (0-1)
    """
    try:
        import numpy as np

        # Convert to grayscale
        if image.mode != 'L':
            gray = image.convert('L')
        else:
            gray = image

        img_array = np.array(gray, dtype=np.float32)

        # Basic quality metrics
        # 1. Focus/blur detection using Laplacian variance
        laplacian_var = np.var(np.abs(np.gradient(img_array)))

        # 2. Contrast
        contrast = np.std(img_array)

        # 3. Brightness uniformity
        brightness_std = np.std(img_array)

        # Combine metrics
        quality_score = (
            min(1.0, laplacian_var / 500.0) * 0.4 +
            min(1.0, contrast / 50.0) * 0.4 +
            max(0.0, 1.0 - brightness_std / 50.0) * 0.2
        )

        return min(1.0, max(0.0, quality_score))

    except Exception as e:
        logger.error(f"Quality estimation failed: {str(e)}")
        return 0.5