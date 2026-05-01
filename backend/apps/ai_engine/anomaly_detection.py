"""
Anomaly Detection Module for INEC Underage Eradicator

This module implements rule-based anomaly detection to identify
suspicious registration patterns that may indicate fraudulent activity.
"""

import numpy as np
from datetime import datetime, timedelta
import logging
import statistics

logger = logging.getLogger(__name__)

class AnomalyDetector:
    """
    Rule-based anomaly detection for voter registration patterns.
    """

    def __init__(self):
        self.anomaly_rules = self._define_anomaly_rules()
        self.baseline_stats = {}

    def _define_anomaly_rules(self):
        """
        Define rules for detecting anomalous registrations.
        """
        return {
            'unusual_registration_time': {
                'check': lambda reg: self._check_registration_time(reg),
                'weight': 0.3,
                'description': 'Registration at unusual hours'
            },
            'suspicious_age': {
                'check': lambda reg: self._check_age_anomaly(reg),
                'weight': 0.4,
                'description': 'Age outside normal distribution'
            },
            'rapid_registrations': {
                'check': lambda reg: self._check_rapid_registrations(reg),
                'weight': 0.2,
                'description': 'Multiple registrations in short time'
            },
            'inconsistent_data': {
                'check': lambda reg: self._check_data_consistency(reg),
                'weight': 0.3,
                'description': 'Inconsistent or suspicious data patterns'
            }
        }

    def _check_registration_time(self, registration):
        """Check if registration time is unusual."""
        if not registration.created_at:
            return False

        hour = registration.created_at.hour
        # Flag registrations outside normal business hours (6 AM - 10 PM)
        return hour < 6 or hour > 22

    def _check_age_anomaly(self, registration):
        """Check if age is anomalous."""
        if not registration.date_of_birth:
            return True  # Missing DOB is suspicious

        today = datetime.now().date()
        age = today.year - registration.date_of_birth.year

        # Flag ages that are too young, too old, or exactly 18 (suspiciously precise)
        if age < 18 or age > 100:
            return True

        # Flag registrations claiming exactly 18 years old (potential manipulation)
        if age == 18:
            months_diff = (today.month - registration.date_of_birth.month) + \
                         (today.day - registration.date_of_birth.day) / 30
            if abs(months_diff) < 1:  # Within 1 month of 18th birthday
                return True

        return False

    def _check_rapid_registrations(self, registration):
        """Check for rapid successive registrations from same source."""
        # This would require database queries in a real implementation
        # For now, return False (no rapid registrations detected)
        return False

    def _check_data_consistency(self, registration):
        """Check for inconsistent or suspicious data patterns."""
        issues = []

        # Check name lengths (too short or too long)
        if len(registration.surname or '') < 2 or len(registration.surname or '') > 50:
            issues.append('suspicious_name_length')

        # Check phone number format
        phone = registration.phone_number or ''
        if not phone.startswith('0') or len(phone) != 11:
            issues.append('invalid_phone_format')

        # Check address completeness
        address = registration.residence_address or ''
        if len(address) < 10:
            issues.append('incomplete_address')

        return len(issues) > 0

    def detect_anomalies(self, registration):
        """
        Detect anomalies in a registration using rule-based checks.

        Args:
            registration: VoterRegistration instance

        Returns:
            dict: Anomaly detection results
        """
        anomalies = []
        total_weight = 0
        triggered_weight = 0

        for rule_name, rule_config in self.anomaly_rules.items():
            if rule_config['check'](registration):
                anomalies.append({
                    'rule': rule_name,
                    'description': rule_config['description'],
                    'weight': rule_config['weight']
                })
                triggered_weight += rule_config['weight']
            total_weight += rule_config['weight']

        # Calculate anomaly score and confidence
        anomaly_score = triggered_weight / total_weight if total_weight > 0 else 0
        confidence = min(anomaly_score * 100, 100)

        # Determine risk level
        if anomaly_score > 0.7:
            risk_level = 'high'
        elif anomaly_score > 0.3:
            risk_level = 'medium'
        else:
            risk_level = 'low'

        result = {
            'is_anomaly': anomaly_score > 0.5,  # Threshold for anomaly detection
            'anomaly_score': anomaly_score,
            'confidence': confidence,
            'risk_level': risk_level,
            'triggered_rules': anomalies,
            'total_rules': len(self.anomaly_rules)
        }

        return result

    def batch_detect_anomalies(self, registrations):
        """
        Detect anomalies in a batch of registrations.

        Args:
            registrations: List of VoterRegistration instances

        Returns:
            list: List of anomaly detection results
        """
        results = []
        for registration in registrations:
            result = self.detect_anomalies(registration)
            results.append(result)

        return results

    def get_anomaly_statistics(self, registrations):
        """
        Calculate anomaly statistics for a set of registrations.

        Args:
            registrations: List of VoterRegistration instances

        Returns:
            dict: Statistics about anomalies
        """
        if not registrations:
            return {'total_registrations': 0, 'anomalies_detected': 0, 'anomaly_rate': 0}

        results = self.batch_detect_anomalies(registrations)
        anomalies = [r for r in results if r['is_anomaly']]

        if results:
            avg_score = statistics.mean([r['anomaly_score'] for r in results])
        else:
            avg_score = 0

        stats = {
            'total_registrations': len(registrations),
            'anomalies_detected': len(anomalies),
            'anomaly_rate': len(anomalies) / len(registrations) * 100,
            'average_anomaly_score': avg_score,
            'high_risk_count': len([r for r in anomalies if r['risk_level'] == 'high'])
        }

        return stats