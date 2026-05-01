from django.db import models
from django.utils import timezone


class SystemSetting(models.Model):
    """
    Dynamic system settings.
    """

    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    value_type = models.CharField(
        max_length=20,
        choices=[
            ('string', 'String'),
            ('integer', 'Integer'),
            ('float', 'Float'),
            ('boolean', 'Boolean'),
            ('json', 'JSON'),
        ],
        default='string'
    )
    description = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"
        ordering = ['key']

    def __str__(self):
        return f"{self.key}: {self.value}"

    @property
    def typed_value(self):
        """Return the value in its proper type."""
        if self.value_type == 'integer':
            return int(self.value)
        elif self.value_type == 'float':
            return float(self.value)
        elif self.value_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.value_type == 'json':
            import json
            return json.loads(self.value)
        else:
            return self.value


class NigerianState(models.Model):
    """
    Nigerian states and their LGAs.
    """

    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=5, unique=True)  # e.g., 'LA' for Lagos
    capital = models.CharField(max_length=50)
    population = models.PositiveIntegerField(null=True, blank=True)

    # Geographic data
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = "Nigerian State"
        verbose_name_plural = "Nigerian States"
        ordering = ['name']

    def __str__(self):
        return self.name


class LocalGovernmentArea(models.Model):
    """
    Local Government Areas within states.
    """

    name = models.CharField(max_length=100)
    state = models.ForeignKey(NigerianState, on_delete=models.CASCADE, related_name='lgas')
    code = models.CharField(max_length=10, unique=True)  # e.g., 'LA001'

    # Geographic data
    headquarters = models.CharField(max_length=50, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = "Local Government Area"
        verbose_name_plural = "Local Government Areas"
        ordering = ['state__name', 'name']
        unique_together = ['name', 'state']

    def __str__(self):
        return f"{self.name}, {self.state.name}"


class Occupation(models.Model):
    """
    Common occupations in Nigeria.
    """

    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(
        max_length=30,
        choices=[
            ('professional', 'Professional'),
            ('business', 'Business/Trade'),
            ('skilled', 'Skilled Labor'),
            ('unskilled', 'Unskilled Labor'),
            ('student', 'Student'),
            ('unemployed', 'Unemployed'),
            ('retired', 'Retired'),
            ('other', 'Other'),
        ]
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Occupation"
        verbose_name_plural = "Occupations"
        ordering = ['name']

    def __str__(self):
        return self.name


class SystemHealth(models.Model):
    """
    System health monitoring.
    """

    COMPONENT_TYPES = [
        ('database', 'Database'),
        ('ai_engine', 'AI Engine'),
        ('file_storage', 'File Storage'),
        ('email', 'Email Service'),
        ('cache', 'Cache'),
        ('ocr', 'OCR Service'),
        ('biometric', 'Biometric Service'),
    ]

    STATUS_TYPES = [
        ('healthy', 'Healthy'),
        ('degraded', 'Degraded'),
        ('unhealthy', 'Unhealthy'),
        ('offline', 'Offline'),
    ]

    component = models.CharField(max_length=20, choices=COMPONENT_TYPES)
    status = models.CharField(max_length=15, choices=STATUS_TYPES, default='healthy')

    # Metrics
    response_time_ms = models.FloatField(null=True, blank=True)
    uptime_percentage = models.FloatField(null=True, blank=True)
    error_count = models.PositiveIntegerField(default=0)

    # Details
    message = models.TextField(blank=True)
    last_check = models.DateTimeField(default=timezone.now)
    next_check = models.DateTimeField()

    class Meta:
        verbose_name = "System Health"
        verbose_name_plural = "System Health"
        unique_together = ['component']
        ordering = ['component']

    def __str__(self):
        return f"{self.component}: {self.status}"