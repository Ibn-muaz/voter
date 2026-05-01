from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User


class VoterRegistration(models.Model):
    """
    Main model for voter registration records.
    Follows INEC Form EC1A structure.
    """

    # Registration Status
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_verification', 'Pending Verification'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged for Review'),
    ]

    REJECTION_REASONS = [
        ('underage', 'Underage (below 18 years)'),
        ('document_mismatch', 'Document information mismatch'),
        ('biometric_failure', 'Biometric verification failed'),
        ('duplicate', 'Duplicate registration detected'),
        ('anomaly_detected', 'Anomaly detected in registration'),
        ('manual_review', 'Requires manual review'),
    ]

    # Personal Information (Step 1)
    vin = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text="Voter Identification Number (assigned after approval)"
    )

    surname = models.CharField(max_length=100, null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    middle_name = models.CharField(max_length=100, blank=True, null=True)

    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[('male', 'Male'), ('female', 'Female')],
        null=True, blank=True
    )

    occupation = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    # Residence Information (Step 2)
    state_of_origin = models.ForeignKey(
        'utils.NigerianState',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='voters_origin'
    )
    lga_of_origin = models.ForeignKey(
        'utils.LocalGovernmentArea',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='voters_origin'
    )
    ward = models.CharField(max_length=100, null=True, blank=True)
    polling_unit = models.CharField(max_length=100, null=True, blank=True)

    # Current Residence
    residence_state = models.ForeignKey(
        'utils.NigerianState',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='voters_residence'
    )
    residence_lga = models.ForeignKey(
        'utils.LocalGovernmentArea',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='voters_residence'
    )
    residence_address = models.TextField(null=True, blank=True)

    # Document Uploads (Step 2)
    proof_of_age_document = models.FileField(upload_to='documents/age/', null=True, blank=True)
    proof_of_age_ocr_text = models.TextField(blank=True, null=True)
    proof_of_age_confidence = models.FloatField(default=0.0)

    proof_of_identity_document = models.FileField(upload_to='documents/identity/', null=True, blank=True)
    proof_of_identity_ocr_text = models.TextField(blank=True, null=True)
    proof_of_identity_confidence = models.FloatField(default=0.0)

    proof_of_address_document = models.FileField(upload_to='documents/address/', null=True, blank=True)
    proof_of_address_ocr_text = models.TextField(blank=True, null=True)
    proof_of_address_confidence = models.FloatField(default=0.0)

    # Biometric Capture (Step 3)
    fingerprint_image = models.ImageField(upload_to='biometrics/fingerprints/', null=True, blank=True)
    fingerprint_template = models.TextField(blank=True, null=True)
    fingerprint_quality_score = models.FloatField(default=0.0)

    facial_image = models.ImageField(upload_to='biometrics/faces/', null=True, blank=True)
    facial_template = models.TextField(blank=True, null=True)
    facial_quality_score = models.FloatField(default=0.0)

    # Progress Tracking
    step_1_completed = models.BooleanField(default=False)
    step_2_completed = models.BooleanField(default=False)
    step_3_completed = models.BooleanField(default=False)
    step_4_completed = models.BooleanField(default=False)

    # Registration Details
    registration_date = models.DateTimeField(default=timezone.now)
    registration_officer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='registrations_processed'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    rejection_reason = models.CharField(
        max_length=50,
        choices=REJECTION_REASONS,
        blank=True
    )

    rejection_details = models.TextField(blank=True)

    # AI Verification Results
    ai_verification_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Overall AI verification confidence score (0-1)"
    )

    age_verification_passed = models.BooleanField(default=False)
    document_verification_passed = models.BooleanField(default=False)
    biometric_verification_passed = models.BooleanField(default=False)
    anomaly_detection_passed = models.BooleanField(default=False)

    # Flags for manual review
    flagged_for_review = models.BooleanField(default=False)
    review_notes = models.TextField(blank=True)

    # Session Tracking
    session_id = models.CharField(max_length=100, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)

    # AI Verification Details
    ai_verification_result = models.JSONField(null=True, blank=True)
    ai_verification_layers = models.JSONField(null=True, blank=True)
    is_underage_suspected = models.BooleanField(default=False)
    verification_completed_at = models.DateTimeField(null=True, blank=True)

    # Completion Info
    completed_at = models.DateTimeField(null=True, blank=True)
    temporary_voter_card = models.FileField(upload_to='tvc/', null=True, blank=True)

    # Timestamps

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Voter Registration"
        verbose_name_plural = "Voter Registrations"
        ordering = ['-registration_date']
        indexes = [
            models.Index(fields=['vin']),
            models.Index(fields=['status', 'registration_date']),
            models.Index(fields=['state_of_origin', 'lga_of_origin']),
            models.Index(fields=['ai_verification_score']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} - {self.vin or 'No VIN'}"

    def get_full_name(self):
        """Return the full name of the voter."""
        names = [self.surname, self.first_name]
        if self.middle_name:
            names.append(self.middle_name)
        return ' '.join(names)

    def calculate_age(self):
        """Calculate age based on date of birth."""
        today = timezone.now().date()
        age = today.year - self.date_of_birth.year
        if today.month < self.date_of_birth.month or \
           (today.month == self.date_of_birth.month and today.day < self.date_of_birth.day):
            age -= 1
        return age

    def is_eligible_age(self):
        """Check if voter is 18 or older."""
        return self.calculate_age() >= 18

    @property
    def age(self):
        return self.calculate_age()

    def step_completed(self, step_number):
        """Check if a specific step has been completed."""
        if step_number == 1:
            return self.step_1_completed
        elif step_number == 2:
            return self.step_2_completed
        elif step_number == 3:
            return self.step_3_completed
        elif step_number == 4:
            return self.step_4_completed
        return False

    def get_next_required_step(self):
        """Get the number of the first incomplete step."""
        if not self.step_1_completed:
            return 1
        if not self.step_2_completed:
            return 2
        if not self.step_3_completed:
            return 3
        if not self.step_4_completed:
            return 4
        return 5


class RegistrationStep(models.Model):
    """
    Track progress through the multi-step registration process.
    """
    STEP_CHOICES = [
        ('personal_info', 'Personal Information'),
        ('residence', 'Residence & LGA Selection'),
        ('documents', 'Document Upload & OCR'),
        ('biometrics', 'Biometric Capture'),
        ('verification', 'AI Verification & Review'),
        ('complete', 'Registration Complete'),
    ]

    registration = models.ForeignKey(
        VoterRegistration,
        on_delete=models.CASCADE,
        related_name='steps'
    )

    step_number = models.PositiveSmallIntegerField(default=1)
    step_name = models.CharField(max_length=100, blank=True)
    
    completed_at = models.DateTimeField(null=True, blank=True)

    step_data = models.JSONField(
        default=dict,
        help_text="JSON data for the current step"
    )

    completed_steps = models.JSONField(
        default=list,
        help_text="List of completed step identifiers"
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Registration Step"
        verbose_name_plural = "Registration Steps"

    def __str__(self):
        return f"{self.registration} - {self.get_current_step_display()}"


class TemporaryVoterCard(models.Model):
    """
    Model for temporary voter card generation.
    """
    registration = models.OneToOneField(
        VoterRegistration,
        on_delete=models.CASCADE,
        related_name='temp_card'
    )

    card_number = models.CharField(max_length=20, unique=True)
    issued_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateField()

    # Card details
    card_data = models.JSONField(
        default=dict,
        help_text="JSON data for card generation"
    )

    pdf_file = models.FileField(
        upload_to='temp_cards/',
        blank=True,
        null=True
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Temporary Voter Card"
        verbose_name_plural = "Temporary Voter Cards"
        ordering = ['-issued_date']

    def __str__(self):
        return f"TVC-{self.card_number} for {self.registration}"