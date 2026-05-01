from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Report(models.Model):
    """
    Generated reports for INEC compliance and analytics.
    """

    REPORT_TYPES = [
        ('daily_registration', 'Daily Registration Report'),
        ('weekly_registration', 'Weekly Registration Report'),
        ('monthly_registration', 'Monthly Registration Report'),
        ('rejection_analysis', 'Rejection Analysis Report'),
        ('ai_performance', 'AI Performance Report'),
        ('officer_performance', 'Officer Performance Report'),
        ('state_lga_summary', 'State/LGA Summary Report'),
        ('anomaly_report', 'Anomaly Detection Report'),
        ('custom', 'Custom Report'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')

    # Date range
    start_date = models.DateField()
    end_date = models.DateField()

    # Generation details
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_reports'
    )
    generated_at = models.DateTimeField(null=True, blank=True)

    # Report data
    parameters = models.JSONField(
        default=dict,
        help_text="Report generation parameters"
    )
    data = models.JSONField(
        default=dict,
        help_text="Generated report data"
    )

    # Files
    pdf_file = models.FileField(
        upload_to='reports/pdf/%Y/%m/%d/',
        null=True,
        blank=True
    )
    csv_file = models.FileField(
        upload_to='reports/csv/%Y/%m/%d/',
        null=True,
        blank=True
    )
    excel_file = models.FileField(
        upload_to='reports/excel/%Y/%m/%d/',
        null=True,
        blank=True
    )

    # Metadata
    record_count = models.PositiveIntegerField(default=0)
    file_size_bytes = models.PositiveIntegerField(default=0)
    generation_time_seconds = models.FloatField(default=0.0)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Report"
        verbose_name_plural = "Reports"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['report_type', 'status']),
            models.Index(fields=['generated_by', 'created_at']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_report_type_display()})"


class ReportTemplate(models.Model):
    """
    Templates for recurring reports.
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=30, choices=Report.REPORT_TYPES)

    # Default parameters
    default_parameters = models.JSONField(default=dict)

    # Schedule
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
        ],
        blank=True
    )
    schedule_time = models.TimeField(null=True, blank=True)

    # Recipients
    email_recipients = models.JSONField(
        default=list,
        help_text="List of email addresses to receive the report"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Report Template"
        verbose_name_plural = "Report Templates"
        ordering = ['name']

    def __str__(self):
        return self.name


class DashboardMetric(models.Model):
    """
    Real-time dashboard metrics.
    """

    METRIC_TYPES = [
        ('total_registrations', 'Total Registrations'),
        ('approved_registrations', 'Approved Registrations'),
        ('rejected_registrations', 'Rejected Registrations'),
        ('pending_reviews', 'Pending Manual Reviews'),
        ('ai_accuracy', 'AI Verification Accuracy'),
        ('average_processing_time', 'Average Processing Time'),
        ('state_distribution', 'State-wise Distribution'),
        ('rejection_reasons', 'Rejection Reasons Breakdown'),
    ]

    name = models.CharField(max_length=50, unique=True)
    metric_type = models.CharField(max_length=30, choices=METRIC_TYPES)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Current value
    value = models.FloatField(default=0.0)
    value_text = models.CharField(max_length=100, blank=True)

    # Metadata
    unit = models.CharField(max_length=20, blank=True)  # e.g., 'count', 'percentage', 'seconds'
    last_updated = models.DateTimeField(default=timezone.now)

    # Update frequency
    update_frequency_minutes = models.PositiveIntegerField(default=5)

    class Meta:
        verbose_name = "Dashboard Metric"
        verbose_name_plural = "Dashboard Metrics"
        ordering = ['name']

    def __str__(self):
        return f"{self.display_name}: {self.value_text or self.value}"


class ReportSchedule(models.Model):
    """
    Scheduled report generation.
    """

    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE)
    next_run = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    # Last execution
    last_run = models.DateTimeField(null=True, blank=True)
    last_status = models.CharField(
        max_length=15,
        choices=Report.STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Report Schedule"
        verbose_name_plural = "Report Schedules"
        ordering = ['next_run']

    def __str__(self):
        return f"Schedule for {self.template.name}"