from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Document(models.Model):
    """
    Model for uploaded documents during registration.
    """

    DOCUMENT_TYPES = [
        ('birth_certificate', 'Birth Certificate'),
        ('national_id', 'National ID (NIMC)'),
        ('passport', 'International Passport'),
        ('drivers_license', "Driver's License"),
        ('baptismal_certificate', 'Baptismal Certificate'),
    ]

    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
    ]

    registration = models.ForeignKey(
        'registration.VoterRegistration',
        on_delete=models.CASCADE,
        related_name='documents'
    )

    document_type = models.CharField(
        max_length=30,
        choices=DOCUMENT_TYPES
    )

    file = models.FileField(
        upload_to='documents/%Y/%m/%d/',
        help_text="Uploaded document file"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='uploaded'
    )

    ocr_text = models.TextField(
        blank=True,
        help_text="Extracted text from OCR processing"
    )

    extracted_data = models.JSONField(
        default=dict,
        help_text="Structured data extracted from document"
    )

    confidence_score = models.FloatField(
        default=0.0,
        help_text="OCR confidence score (0-1)"
    )

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents'
    )

    uploaded_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['registration', 'document_type']),
            models.Index(fields=['status', 'uploaded_at']),
        ]

    def __str__(self):
        return f"{self.document_type} for {self.registration.get_full_name()}"

    @property
    def file_size_mb(self):
        """Return file size in MB."""
        try:
            return self.file.size / (1024 * 1024)
        except:
            return 0.0


class DocumentVerification(models.Model):
    """
    Model for document verification results.
    """

    document = models.OneToOneField(
        Document,
        on_delete=models.CASCADE,
        related_name='verification'
    )

    is_authentic = models.BooleanField(
        default=False,
        help_text="Whether document appears authentic"
    )

    authenticity_score = models.FloatField(
        default=0.0,
        help_text="Authenticity confidence score (0-1)"
    )

    verification_details = models.JSONField(
        default=dict,
        help_text="Detailed verification results"
    )

    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='document_verifications'
    )

    verified_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Document Verification"
        verbose_name_plural = "Document Verifications"
        ordering = ['-verified_at']

    def __str__(self):
        return f"Verification for {self.document}"