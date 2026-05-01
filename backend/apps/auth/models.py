from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class INECUser(AbstractUser):
    """
    Custom user model for INEC officials and administrators.
    """
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('officer', 'Registration Officer'),
        ('supervisor', 'Supervisory Officer'),
        ('auditor', 'Audit Officer'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='officer',
        help_text="User's role in the INEC system"
    )

    state = models.CharField(
        max_length=50,
        blank=True,
        help_text="State of operation for the officer"
    )

    lga = models.CharField(
        max_length=100,
        blank=True,
        help_text="Local Government Area of operation"
    )

    employee_id = models.CharField(
        max_length=20,
        unique=True,
        help_text="INEC employee identification number"
    )

    is_active_officer = models.BooleanField(
        default=True,
        help_text="Whether the officer is currently active"
    )

    last_login_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of last login"
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "INEC User"
        verbose_name_plural = "INEC Users"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name()} ({self.employee_id}) - {self.get_role_display()}"


class UserSession(models.Model):
    """
    Model to track user sessions for security auditing.
    """
    user = models.ForeignKey(INECUser, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    login_time = models.DateTimeField(default=timezone.now)
    logout_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "User Session"
        verbose_name_plural = "User Sessions"
        ordering = ['-login_time']

    def __str__(self):
        return f"{self.user.username} - {self.login_time}"