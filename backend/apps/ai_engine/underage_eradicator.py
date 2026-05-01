"""
INEC Underage Eradicator - Core AI Engine

This module implements the 5-layer AI-powered verification system to prevent
underage voter registration in Nigeria.
"""

import logging
from typing import Dict, Any, Tuple
from datetime import datetime, date
from django.utils import timezone

from .age_estimation import AgeEstimator
from .ocr_engine import OCREngine
from .biometric_verification import BiometricVerifier
from .anomaly_detection import AnomalyDetector

logger = logging.getLogger(__name__)


class UnderageEradicator:
    """
    Main AI engine for underage voter registration prevention.

    Implements 5 independent verification layers:
    1. Hard Rule Check
    2. Document OCR + Cross-Verification
    3. AI Face Age Estimation
    4. Biometric Consistency
    5. Anomaly Detection
    """

    def __init__(self):
        self.age_estimator = AgeEstimator()
        self.ocr_engine = OCREngine()
        self.biometric_verifier = BiometricVerifier()
        self.anomaly_detector = AnomalyDetector()

        # Layer weights for final score calculation
        self.layer_weights = {
            'hard_rule': 0.2,
            'document_verification': 0.25,
            'age_estimation': 0.25,
            'biometric_consistency': 0.15,
            'anomaly_detection': 0.15
        }

    def verify_registration(self, registration) -> Dict[str, Any]:
        """
        Run complete 5-layer verification on a registration.

        Args:
            registration: VoterRegistration instance

        Returns:
            Dict with verification results
        """
        results = {
            'approved': False,
            'score': 0.0,
            'reason': '',
            'details': '',
            'layer_results': {}
        }

        try:
            # Layer 1: Hard Rule Check
            hard_rule_result = self._check_hard_rules(registration)
            results['layer_results']['hard_rule'] = hard_rule_result

            # If hard rule fails, reject immediately
            if not hard_rule_result['passed']:
                results.update({
                    'reason': 'hard_rule',
                    'details': hard_rule_result['details'],
                    'score': 0.0
                })
                return results

            # Layer 2: Document OCR + Cross-Verification
            document_result = self._verify_documents(registration)
            results['layer_results']['document_verification'] = document_result

            # Layer 3: AI Face Age Estimation
            age_estimation_result = self._estimate_age(registration)
            results['layer_results']['age_estimation'] = age_estimation_result

            # Layer 4: Biometric Consistency
            biometric_result = self._verify_biometrics(registration)
            results['layer_results']['biometric_consistency'] = biometric_result

            # Layer 5: Anomaly Detection
            anomaly_result = self._detect_anomalies(registration)
            results['layer_results']['anomaly_detection'] = anomaly_result

            # Calculate final score
            final_score = self._calculate_final_score(results['layer_results'])

            # Decision logic
            if final_score >= 0.8:  # 80% confidence threshold
                results['approved'] = True
                results['score'] = final_score
            else:
                results['approved'] = False
                results['score'] = final_score
                results['reason'] = self._determine_rejection_reason(results['layer_results'])
                results['details'] = self._generate_rejection_details(results['layer_results'])

            # Update registration with layer results
            self._update_registration_flags(registration, results['layer_results'])

        except Exception as e:
            logger.error(f"Verification failed for registration {registration.id}: {str(e)}")
            results['approved'] = False
            results['reason'] = 'system_error'
            results['details'] = f'Verification system error: {str(e)}'

        return results

    def preview_verification(self, registration) -> Dict[str, Any]:
        """
        Preview verification results without saving.
        Used in step 5 for user review.
        """
        # Run lightweight checks for preview
        preview_results = {
            'age_check': self._preview_age_check(registration),
            'document_check': self._preview_document_check(registration),
            'estimated_risk': 'low'  # Default
        }

        # Estimate risk level
        if registration.calculate_age() < 20:
            preview_results['estimated_risk'] = 'high'
        elif registration.calculate_age() < 25:
            preview_results['estimated_risk'] = 'medium'

        return preview_results

    def _check_hard_rules(self, registration) -> Dict[str, Any]:
        """Layer 1: Hard Rule Check"""
        result = {'passed': True, 'details': '', 'score': 1.0}

        age = registration.calculate_age()

        if age < 18:
            result['passed'] = False
            result['details'] = f'Applicant is {age} years old. Must be 18 or older.'
            result['score'] = 0.0
        elif age < 16:
            # Extremely young - flag for investigation
            result['passed'] = False
            result['details'] = f'Applicant is {age} years old. Registration not allowed.'
            result['score'] = 0.0

        return result

    def _verify_documents(self, registration) -> Dict[str, Any]:
        """Layer 2: Document OCR + Cross-Verification"""
        result = {'passed': True, 'details': '', 'score': 0.8}

        try:
            # Get OCR data from registration step
            step = registration.current_step
            ocr_data = step.step_data.get('documents', {}).get('ocr_result', {})

            if not ocr_data:
                result['passed'] = False
                result['details'] = 'No document data available for verification.'
                result['score'] = 0.0
                return result

            # Extract DOB from OCR
            ocr_dob = ocr_data.get('date_of_birth')
            if ocr_dob:
                # Compare with provided DOB
                if isinstance(ocr_dob, str):
                    try:
                        ocr_dob_date = datetime.strptime(ocr_dob, '%Y-%m-%d').date()
                    except ValueError:
                        result['passed'] = False
                        result['details'] = 'Invalid date format in document.'
                        result['score'] = 0.3
                        return result
                else:
                    ocr_dob_date = ocr_dob

                # Check if DOBs match
                if ocr_dob_date != registration.date_of_birth:
                    result['passed'] = False
                    result['details'] = 'Date of birth on document does not match provided information.'
                    result['score'] = 0.2
                    return result

                # Check if age from document is valid
                today = timezone.now().date()
                document_age = today.year - ocr_dob_date.year
                if today.month < ocr_dob_date.month or \
                   (today.month == ocr_dob_date.month and today.day < ocr_dob_date.day):
                    document_age -= 1

                if document_age < 18:
                    result['passed'] = False
                    result['details'] = f'Document indicates age of {document_age} years. Must be 18 or older.'
                    result['score'] = 0.0
                    return result

            # Additional document validation
            document_type = step.step_data.get('documents', {}).get('document_type')
            if document_type and not self._validate_document_type(registration, document_type, ocr_data):
                result['passed'] = False
                result['details'] = 'Document validation failed.'
                result['score'] = 0.4

        except Exception as e:
            logger.error(f"Document verification failed: {str(e)}")
            result['passed'] = False
            result['details'] = 'Document verification system error.'
            result['score'] = 0.5

        return result

    def _estimate_age(self, registration) -> Dict[str, Any]:
        """Layer 3: AI Face Age Estimation"""
        result = {'passed': True, 'details': '', 'score': 0.7}

        try:
            # Get photo from biometric data
            step = registration.current_step
            photo_data = step.step_data.get('biometric_photo')

            if not photo_data:
                result['passed'] = False
                result['details'] = 'No photo available for age estimation.'
                result['score'] = 0.0
                return result

            # Run age estimation
            estimated_age = self.age_estimator.estimate_age(photo_data)

            if estimated_age is None:
                result['passed'] = False
                result['details'] = 'Age estimation failed.'
                result['score'] = 0.3
                return result

            declared_age = registration.calculate_age()

            # Check for significant discrepancy
            age_difference = abs(estimated_age - declared_age)

            if estimated_age < 20 and declared_age >= 18:
                # High risk case
                result['passed'] = False
                result['details'] = f'Estimated age ({estimated_age}) suggests underage. Declared age: {declared_age}.'
                result['score'] = 0.1
            elif age_difference > 10:
                # Large discrepancy
                result['passed'] = False
                result['details'] = f'Large age discrepancy. Estimated: {estimated_age}, Declared: {declared_age}.'
                result['score'] = 0.4
            elif age_difference > 5:
                # Moderate discrepancy - flag for review
                result['passed'] = True
                result['details'] = f'Moderate age discrepancy detected. Estimated: {estimated_age}, Declared: {declared_age}.'
                result['score'] = 0.6
            else:
                result['score'] = 0.9
                result['details'] = f'Age estimation successful. Estimated: {estimated_age}, Declared: {declared_age}.'

        except Exception as e:
            logger.error(f"Age estimation failed: {str(e)}")
            result['passed'] = False
            result['details'] = 'Age estimation system error.'
            result['score'] = 0.4

        return result

    def _verify_biometrics(self, registration) -> Dict[str, Any]:
        """Layer 4: Biometric Consistency"""
        result = {'passed': True, 'details': '', 'score': 0.8}

        try:
            step = registration.current_step
            biometric_data = step.step_data.get('biometric_fingerprints', {})

            if not biometric_data:
                result['passed'] = False
                result['details'] = 'No biometric data available.'
                result['score'] = 0.0
                return result

            # Check for required fingerprints (left and right thumb as per INEC)
            required_fingers = ['left_thumb', 'right_thumb']
            captured_fingers = list(biometric_data.keys())

            missing_fingers = [f for f in required_fingers if f not in captured_fingers]
            if missing_fingers:
                result['passed'] = False
                result['details'] = f'Missing required fingerprints: {", ".join(missing_fingers)}'
                result['score'] = 0.3
                return result

            # Verify fingerprint quality
            for finger, data in biometric_data.items():
                quality_score = data.get('quality_score', 0)
                if quality_score < 0.6:  # Minimum quality threshold
                    result['passed'] = False
                    result['details'] = f'Poor quality {finger.replace("_", " ")} fingerprint.'
                    result['score'] = 0.5
                    return result

            # Check for photo-biometric consistency
            photo_data = step.step_data.get('biometric_photo')
            if photo_data:
                consistency_score = self.biometric_verifier.check_photo_consistency(photo_data, biometric_data)
                if consistency_score < 0.7:
                    result['passed'] = False
                    result['details'] = 'Biometric data inconsistency detected.'
                    result['score'] = 0.4

        except Exception as e:
            logger.error(f"Biometric verification failed: {str(e)}")
            result['passed'] = False
            result['details'] = 'Biometric verification system error.'
            result['score'] = 0.5

        return result

    def _detect_anomalies(self, registration) -> Dict[str, Any]:
        """Layer 5: Anomaly Detection"""
        result = {'passed': True, 'details': '', 'score': 0.9}

        try:
            anomalies = self.anomaly_detector.detect_anomalies(registration)

            if anomalies:
                # Check severity of anomalies
                high_severity = [a for a in anomalies if a.get('severity') == 'high']
                medium_severity = [a for a in anomalies if a.get('severity') == 'medium']

                if high_severity:
                    result['passed'] = False
                    result['details'] = f'High-risk anomalies detected: {", ".join([a["description"] for a in high_severity])}'
                    result['score'] = 0.2
                elif medium_severity:
                    result['passed'] = True
                    result['details'] = f'Medium-risk anomalies detected: {", ".join([a["description"] for a in medium_severity])}'
                    result['score'] = 0.6
                else:
                    result['score'] = 0.8
                    result['details'] = 'Minor anomalies detected but not blocking.'
            else:
                result['score'] = 1.0
                result['details'] = 'No anomalies detected.'

        except Exception as e:
            logger.error(f"Anomaly detection failed: {str(e)}")
            result['passed'] = False
            result['details'] = 'Anomaly detection system error.'
            result['score'] = 0.7

        return result

    def _calculate_final_score(self, layer_results: Dict) -> float:
        """Calculate weighted final verification score."""
        total_score = 0.0
        total_weight = 0.0

        for layer_name, result in layer_results.items():
            weight = self.layer_weights.get(layer_name, 0.2)
            score = result.get('score', 0.0)
            total_score += score * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    def _determine_rejection_reason(self, layer_results: Dict) -> str:
        """Determine the primary reason for rejection."""
        failed_layers = [
            layer for layer, result in layer_results.items()
            if not result.get('passed', True)
        ]

        if 'hard_rule' in failed_layers:
            return 'underage'
        elif 'age_estimation' in failed_layers:
            return 'age_verification_failed'
        elif 'document_verification' in failed_layers:
            return 'document_mismatch'
        elif 'biometric_consistency' in failed_layers:
            return 'biometric_failure'
        elif 'anomaly_detection' in failed_layers:
            return 'anomaly_detected'
        else:
            return 'multiple_failures'

    def _generate_rejection_details(self, layer_results: Dict) -> str:
        """Generate detailed rejection explanation."""
        failed_details = [
            result.get('details', f'{layer} failed')
            for layer, result in layer_results.items()
            if not result.get('passed', True)
        ]

        return ' '.join(failed_details) if failed_details else 'Multiple verification failures.'

    def _update_registration_flags(self, registration, layer_results: Dict):
        """Update registration model with verification results."""
        registration.age_verification_passed = layer_results.get('hard_rule', {}).get('passed', False)
        registration.document_verification_passed = layer_results.get('document_verification', {}).get('passed', False)
        registration.biometric_verification_passed = layer_results.get('biometric_consistency', {}).get('passed', False)
        registration.anomaly_detection_passed = layer_results.get('anomaly_detection', {}).get('passed', False)

        # Flag for manual review if needed
        high_risk_indicators = [
            not layer_results.get('age_estimation', {}).get('passed', True),
            layer_results.get('anomaly_detection', {}).get('score', 1.0) < 0.7
        ]

        if any(high_risk_indicators):
            registration.flagged_for_review = True

    def _preview_age_check(self, registration) -> Dict[str, Any]:
        """Quick age check for preview."""
        age = registration.calculate_age()
        return {
            'age': age,
            'eligible': age >= 18,
            'message': f'You will be {age} years old on registration day.'
        }

    def _preview_document_check(self, registration) -> Dict[str, Any]:
        """Quick document check for preview."""
        step = getattr(registration, 'current_step', None)
        if step and 'documents' in step.step_data:
            return {'status': 'processed', 'message': 'Document uploaded and processed.'}
        else:
            return {'status': 'pending', 'message': 'Document upload required.'}

    def _validate_document_type(self, registration, document_type: str, ocr_data: Dict) -> bool:
        """Validate document type specific requirements."""
        # Basic validation - can be extended for specific document types
        required_fields = ['name', 'date_of_birth']

        for field in required_fields:
            if field not in ocr_data:
                return False

        # Check name consistency
        ocr_name = ocr_data.get('name', '').upper()
        reg_name = f"{registration.surname} {registration.first_name}".upper()

        # Simple name matching (can be improved with fuzzy matching)
        if ocr_name and reg_name not in ocr_name and ocr_name not in reg_name:
            return False

        return True