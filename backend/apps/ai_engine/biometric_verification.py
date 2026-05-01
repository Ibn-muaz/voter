"""
Biometric Verification Module

Handles fingerprint and facial recognition verification.
"""

import logging
from typing import Dict, Any, Optional
from PIL import Image
import io
import numpy as np

logger = logging.getLogger(__name__)


class BiometricVerifier:
    """
    Biometric verification system for voter registration.
    """

    def __init__(self):
        self.face_recognition_model = None
        self.fingerprint_model = None
        self._load_models()

    def _load_models(self):
        """Load biometric verification models."""
        try:
            # Try to load face recognition model
            import deepface
            from deepface import DeepFace
            self.face_recognition_model = DeepFace
            logger.info("DeepFace loaded for biometric verification")
        except ImportError:
            logger.warning("DeepFace not available for face verification")

        # Fingerprint verification would require specialized libraries
        # For demo purposes, we'll use placeholder logic
        logger.info("Fingerprint verification using placeholder logic")

    def verify_fingerprint(self, fingerprint_data, finger_type: str) -> Dict[str, Any]:
        """
        Verify fingerprint quality and extract features.

        Args:
            fingerprint_data: Fingerprint image data
            finger_type: Type of finger (left_thumb, right_thumb, etc.)

        Returns:
            Dict with verification results
        """
        try:
            # Convert to PIL Image
            if hasattr(fingerprint_data, 'read'):
                image = Image.open(fingerprint_data)
            elif isinstance(fingerprint_data, bytes):
                image = Image.open(io.BytesIO(fingerprint_data))
            else:
                image = fingerprint_data

            # Convert to grayscale for fingerprint analysis
            if image.mode != 'L':
                image = image.convert('L')

            # Analyze fingerprint quality
            quality_score = self._analyze_fingerprint_quality(image)

            # Extract features (placeholder)
            features = self._extract_fingerprint_features(image)

            result = {
                'finger_type': finger_type,
                'quality_score': quality_score,
                'features_extracted': features is not None,
                'features': features,
                'verified': quality_score > 0.6  # Minimum quality threshold
            }

            return result

        except Exception as e:
            logger.error(f"Fingerprint verification failed: {str(e)}")
            return {
                'finger_type': finger_type,
                'quality_score': 0.0,
                'features_extracted': False,
                'verified': False,
                'error': str(e)
            }

    def verify_face(self, face_data) -> Dict[str, Any]:
        """
        Verify face image quality and extract features.

        Args:
            face_data: Face image data

        Returns:
            Dict with verification results
        """
        try:
            # Convert to PIL Image
            if hasattr(face_data, 'read'):
                image = Image.open(face_data)
            elif isinstance(face_data, bytes):
                image = Image.open(io.BytesIO(face_data))
            else:
                image = face_data

            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Analyze face quality
            quality_score = self._analyze_face_quality(image)

            # Extract facial features
            features = self._extract_facial_features(image)

            result = {
                'quality_score': quality_score,
                'features_extracted': features is not None,
                'features': features,
                'verified': quality_score > 0.7  # Minimum quality threshold
            }

            return result

        except Exception as e:
            logger.error(f"Face verification failed: {str(e)}")
            return {
                'quality_score': 0.0,
                'features_extracted': False,
                'verified': False,
                'error': str(e)
            }

    def check_photo_consistency(self, photo_data: Dict, fingerprint_data: Dict) -> float:
        """
        Check consistency between photo and fingerprint data.

        Returns:
            Consistency score (0-1)
        """
        try:
            # This is a simplified consistency check
            # In a real system, this would compare biometric templates

            photo_quality = photo_data.get('quality_score', 0)
            fingerprint_quality = fingerprint_data.get('quality_score', 0) if fingerprint_data else 0

            # Simple consistency metric
            consistency_score = min(photo_quality, fingerprint_quality)

            # Additional checks could include:
            # - Age consistency between photo and fingerprints
            # - Gender consistency
            # - Template matching scores

            return consistency_score

        except Exception as e:
            logger.error(f"Consistency check failed: {str(e)}")
            return 0.5

    def _analyze_fingerprint_quality(self, image: Image.Image) -> float:
        """Analyze fingerprint image quality."""
        try:
            # Convert to numpy array
            img_array = np.array(image)

            # Basic quality metrics
            # 1. Contrast
            contrast = np.std(img_array)

            # 2. Sharpness (using Laplacian variance)
            laplacian_var = self._calculate_laplacian_variance(img_array)

            # 3. Ridge clarity (simplified)
            ridge_score = self._analyze_ridge_patterns(img_array)

            # Combine metrics
            quality_score = (
                min(1.0, contrast / 50.0) * 0.4 +
                min(1.0, laplacian_var / 500.0) * 0.4 +
                ridge_score * 0.2
            )

            return min(1.0, max(0.0, quality_score))

        except Exception:
            return 0.3  # Default low quality

    def _analyze_face_quality(self, image: Image.Image) -> float:
        """Analyze face image quality."""
        try:
            img_array = np.array(image)

            # Basic quality metrics
            # 1. Brightness
            brightness = np.mean(img_array)

            # 2. Contrast
            contrast = np.std(img_array)

            # 3. Sharpness
            laplacian_var = self._calculate_laplacian_variance(img_array)

            # 4. Face detection (simplified)
            face_score = self._detect_face_presence(img_array)

            # Combine metrics
            quality_score = (
                min(1.0, brightness / 128.0) * 0.2 +
                min(1.0, contrast / 50.0) * 0.3 +
                min(1.0, laplacian_var / 500.0) * 0.3 +
                face_score * 0.2
            )

            return min(1.0, max(0.0, quality_score))

        except Exception:
            return 0.3

    def _calculate_laplacian_variance(self, img_array: np.ndarray) -> float:
        """Calculate Laplacian variance for sharpness measurement."""
        try:
            # Apply Laplacian filter
            laplacian = np.array([
                [0, 1, 0],
                [1, -4, 1],
                [0, 1, 0]
            ], dtype=np.float32)

            if len(img_array.shape) == 3:
                # For RGB images, convert to grayscale first
                gray = np.dot(img_array[...,:3], [0.2989, 0.5870, 0.1140])
            else:
                gray = img_array

            # Apply filter
            filtered = np.abs(np.convolve(gray.flatten(), laplacian.flatten(), mode='valid'))
            return np.var(filtered)
        except Exception:
            return 0.0

    def _analyze_ridge_patterns(self, img_array: np.ndarray) -> float:
        """Analyze fingerprint ridge patterns (simplified)."""
        try:
            # This is a very simplified ridge analysis
            # In a real system, this would use proper fingerprint processing

            # Calculate local variance (ridge/valley detection)
            from scipy.ndimage import generic_filter
            def variance_filter(window):
                return np.var(window)

            local_var = generic_filter(img_array.astype(float), variance_filter, size=5)

            # High variance areas indicate ridges/valleys
            ridge_score = np.mean(local_var > np.percentile(local_var, 70))

            return min(1.0, ridge_score * 2.0)
        except Exception:
            return 0.5

    def _detect_face_presence(self, img_array: np.ndarray) -> float:
        """Detect face presence in image (simplified)."""
        try:
            if self.face_recognition_model:
                # Use DeepFace for face detection
                from deepface import DeepFace
                # This would require actual face detection
                # For demo, return a placeholder score
                return 0.8
            else:
                # Simple heuristic: look for skin-tone colors
                # This is very basic and not accurate
                hsv = self._rgb_to_hsv(img_array)
                skin_mask = (
                    (hsv[..., 0] >= 0) & (hsv[..., 0] <= 50) &  # Hue range for skin
                    (hsv[..., 1] >= 0.1) & (hsv[..., 1] <= 0.8) &  # Saturation
                    (hsv[..., 2] >= 0.2) & (hsv[..., 2] <= 0.95)   # Value
                )
                skin_ratio = np.mean(skin_mask)
                return min(1.0, skin_ratio * 3.0)  # Scale up the ratio
        except Exception:
            return 0.5

    def _rgb_to_hsv(self, rgb: np.ndarray) -> np.ndarray:
        """Convert RGB to HSV color space."""
        rgb = rgb.astype(float) / 255.0
        hsv = np.zeros_like(rgb)

        max_rgb = np.max(rgb, axis=2)
        min_rgb = np.min(rgb, axis=2)
        diff = max_rgb - min_rgb

        # Hue
        hsv[..., 0] = np.where(diff == 0, 0,
            np.where(max_rgb == rgb[..., 0],
                60 * ((rgb[..., 1] - rgb[..., 2]) / diff) % 360,
                np.where(max_rgb == rgb[..., 1],
                    60 * ((rgb[..., 2] - rgb[..., 0]) / diff + 2),
                    60 * ((rgb[..., 0] - rgb[..., 1]) / diff + 4)
                )
            )
        )

        # Saturation
        hsv[..., 1] = np.where(max_rgb == 0, 0, diff / max_rgb)

        # Value
        hsv[..., 2] = max_rgb

        return hsv

    def _extract_fingerprint_features(self, image: Image.Image) -> Optional[Dict]:
        """Extract fingerprint features (placeholder)."""
        # In a real system, this would extract minutiae points
        # For demo, return placeholder features
        return {
            'minutiae_count': 50,  # Placeholder
            'ridge_count': 100,    # Placeholder
            'pattern_type': 'whorl'  # Placeholder
        }

    def _extract_facial_features(self, image: Image.Image) -> Optional[Dict]:
        """Extract facial features."""
        try:
            if self.face_recognition_model:
                # Use DeepFace for feature extraction
                embedding = self.face_recognition_model.represent(image, enforce_detection=True)
                return {
                    'embedding': embedding.tolist() if hasattr(embedding, 'tolist') else embedding,
                    'embedding_model': 'deepface'
                }
            else:
                # Placeholder
                return {
                    'embedding': [0.1] * 128,  # Fake 128-dim embedding
                    'embedding_model': 'placeholder'
                }
        except Exception:
            return None