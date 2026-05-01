from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class AuditLog(models.Model):
    """
    Comprehensive audit log for all system activities.
    """

    ACTION_TYPES = [
        ('registration_created', 'Registration Created'),
        ('registration_updated', 'Registration Updated'),
        ('registration_approved', 'Registration Approved'),
        ('registration_rejected', 'Registration Rejected'),
        ('document_uploaded', 'Document Uploaded'),
        ('document_processed', 'Document Processed'),
        ('biometric_captured', 'Biometric Captured'),
        ('biometric_verified', 'Biometric Verified'),
        ('ai_verification_run', 'AI Verification Run'),
        ('manual_review', 'Manual Review Performed'),
        ('user_login', 'User Login'),
        ('user_logout', 'User Logout'),
        ('admin_action', 'Administrative Action'),
        ('registration_started', 'Registration Started'),
        ('registration_completed', 'Registration Completed'),
        ('tvc_generation_failed', 'TVC Generation Failed'),
        ('system_error', 'System Error'),
    ]

    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    # Core audit fields
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='low')

    # User information
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    user_role = models.CharField(max_length=20, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Object information
    object_type = models.CharField(max_length=50, blank=True)  # e.g., 'VoterRegistration'
    object_id = models.PositiveIntegerField(null=True, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)  # String representation

    # Action details
    description = models.TextField(blank=True)
    old_values = models.JSONField(default=dict, blank=True)  # For update actions
    new_values = models.JSONField(default=dict, blank=True)  # For update actions
    metadata = models.JSONField(default=dict, blank=True)    # Additional context

    # System information
    session_id = models.CharField(max_length=40, blank=True)
    request_id = models.CharField(max_length=36, blank=True)  # UUID for request tracing

    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['action_type', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['object_type', 'object_id']),
            models.Index(fields=['severity', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.action_type} by {self.user} at {self.timestamp}"


class AuditLogArchive(models.Model):
    """
    Archived audit logs for long-term storage.
    """

    original_id = models.PositiveIntegerField(unique=True)
    archived_data = models.JSONField()
    archived_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Audit Log Archive"
        verbose_name_plural = "Audit Log Archives"
        ordering = ['-archived_at']


class SystemEvent(models.Model):
    """
    System-wide events and alerts.
    """

    EVENT_TYPES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('security', 'Security Alert'),
        ('performance', 'Performance Issue'),
    ]

    timestamp = models.DateTimeField(default=timezone.now)
    event_type = models.CharField(max_length=15, choices=EVENT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    source = models.CharField(max_length=100, blank=True)  # Module/component that generated the event

    # Context
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    metadata = models.JSONField(default=dict)

    # Resolution
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_events'
    )
    resolution_notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "System Event"
        verbose_name_plural = "System Events"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['resolved', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.event_type}: {self.title}"


class DataAccessLog(models.Model):
    """
    Log of data access for compliance and security.
    """

    ACCESS_TYPES = [
        ('read', 'Read'),
        ('write', 'Write'),
        ('delete', 'Delete'),
        ('export', 'Export'),
    ]

    timestamp = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    access_type = models.CharField(max_length=10, choices=ACCESS_TYPES)

    # Data accessed
    data_type = models.CharField(max_length=50)  # e.g., 'VoterRegistration'
    data_id = models.PositiveIntegerField()
    data_description = models.CharField(max_length=200, blank=True)

    # Access context
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    purpose = models.CharField(max_length=100, blank=True)  # e.g., 'manual_review', 'report_generation'

    # Compliance
    gdpr_consent = models.BooleanField(default=True)
    retention_period_days = models.PositiveIntegerField(default=2555)  # 7 years

    class Meta:
        verbose_name = "Data Access Log"
        verbose_name_plural = "Data Access Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['data_type', 'data_id']),
            models.Index(fields=['access_type', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.access_type} access by {self.user} to {self.data_type}:{self.data_id}"