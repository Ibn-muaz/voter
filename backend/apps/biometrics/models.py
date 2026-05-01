from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class BiometricData(models.Model):
    """
    Model for biometric data captured during registration.
    """

    BIOMETRIC_TYPES = [
        ('photo', 'Passport Photo'),
        ('fingerprint_left_thumb', 'Left Thumb Fingerprint'),
        ('fingerprint_right_thumb', 'Right Thumb Fingerprint'),
        ('fingerprint_left_index', 'Left Index Fingerprint'),
        ('fingerprint_right_index', 'Right Index Fingerprint'),
    ]

    registration = models.ForeignKey(
        'registration.VoterRegistration',
        on_delete=models.CASCADE,
        related_name='biometric_data'
    )

    biometric_type = models.CharField(
        max_length=30,
        choices=BIOMETRIC_TYPES
    )

    image_file = models.ImageField(
        upload_to='biometrics/%Y/%m/%d/',
        help_text="Biometric image file"
    )

    quality_score = models.FloatField(
        default=0.0,
        help_text="Image quality score (0-1)"
    )

    features_extracted = models.BooleanField(
        default=False,
        help_text="Whether biometric features were successfully extracted"
    )

    feature_data = models.JSONField(
        default=dict,
        help_text="Extracted biometric features"
    )

    captured_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='captured_biometrics'
    )

    captured_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Biometric Data"
        verbose_name_plural = "Biometric Data"
        ordering = ['-captured_at']
        indexes = [
            models.Index(fields=['registration', 'biometric_type']),
            models.Index(fields=['quality_score']),
        ]
        unique_together = ['registration', 'biometric_type']

    def __str__(self):
        return f"{self.biometric_type} for {self.registration.get_full_name()}"


class BiometricVerification(models.Model):
    """
    Model for biometric verification results.
    """

    VERIFICATION_TYPES = [
        ('photo_face_match', 'Photo-Face Match'),
        ('fingerprint_match', 'Fingerprint Match'),
        ('photo_fingerprint_consistency', 'Photo-Fingerprint Consistency'),
    ]

    registration = models.ForeignKey(
        'registration.VoterRegistration',
        on_delete=models.CASCADE,
        related_name='biometric_verifications'
    )

    verification_type = models.CharField(
        max_length=30,
        choices=VERIFICATION_TYPES
    )

    is_verified = models.BooleanField(
        default=False,
        help_text="Whether verification passed"
    )

    confidence_score = models.FloatField(
        default=0.0,
        help_text="Verification confidence score (0-1)"
    )

    verification_details = models.JSONField(
        default=dict,
        help_text="Detailed verification results"
    )

    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='biometric_verifications'
    )

    verified_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Biometric Verification"
        verbose_name_plural = "Biometric Verifications"
        ordering = ['-verified_at']
        indexes = [
            models.Index(fields=['registration', 'verification_type']),
            models.Index(fields=['is_verified', 'confidence_score']),
        ]

    def __str__(self):
        return f"{self.verification_type} for {self.registration}"


class BiometricTemplate(models.Model):
    """
    Model for storing biometric templates for matching.
    """

    biometric_data = models.OneToOneField(
        BiometricData,
        on_delete=models.CASCADE,
        related_name='template'
    )

    template_data = models.BinaryField(
        help_text="Serialized biometric template"
    )

    template_type = models.CharField(
        max_length=50,
        help_text="Type of template (e.g., fingerprint minutiae, face embedding)"
    )

    algorithm_version = models.CharField(
        max_length=20,
        default='1.0',
        help_text="Algorithm version used to generate template"
    )

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Biometric Template"
        verbose_name_plural = "Biometric Templates"
        indexes = [
            models.Index(fields=['template_type', 'algorithm_version']),
        ]

    def __str__(self):
        return f"Template for {self.biometric_data}"