"""
Admin interface for the voter registration system.
Enhanced with robust admin approval workflow.
"""

from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Q
from django.utils import timezone
from .models import VoterRegistration, RegistrationStep, TemporaryVoterCard, ApprovalAuditLog


class ApprovalAuditLogInline(admin.TabularInline):
    """
    Inline admin for approval audit logs.
    """
    model = ApprovalAuditLog
    readonly_fields = ['admin_user', 'action', 'reason', 'timestamp', 'ai_score_at_approval']
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(VoterRegistration)
class VoterRegistrationAdmin(ModelAdmin):
    """
    Admin interface for voter registrations.
    Enhanced with admin approval workflow.
    """

    # List display
    list_display = [
        'vin', 'full_name', 'date_of_birth', 'status', 'risk_level_badge',
        'ai_verification_score', 'approved_by_name', 'created_at', 'approval_actions'
    ]

    list_filter = [
        'status', 'gender', 'state_of_origin', 'risk_level',
        'flagged_for_review', 'created_at', 'approved_at', 'approval_timestamp'
    ]

    search_fields = [
        'vin', 'first_name', 'surname', 'phone_number'
    ]

    # Detail view
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'vin', 'first_name', 'surname', 'middle_name',
                'date_of_birth', 'gender'
            )
        }),
        ('Contact & Occupation', {
            'fields': ('phone_number', 'occupation')
        }),
        ('Location', {
            'fields': (
                'state_of_origin', 'lga_of_origin',
                'residence_address', 'ward', 'polling_unit'
            )
        }),
        ('AI Verification', {
            'fields': (
                'ai_verification_score', 'age_verification_passed',
                'document_verification_passed', 'biometric_verification_passed',
                'anomaly_detection_passed', 'flagged_for_review',
                'rejection_reason', 'rejection_details'
            )
        }),
        ('Risk Assessment', {
            'fields': (
                'risk_level', 'risk_assessment_notes', 'is_underage_suspected'
            ),
            'description': 'Automated risk assessment based on AI verification'
        }),
        ('Admin Approval', {
            'fields': (
                'status', 'approved_by', 'approval_notes',
                'approval_timestamp'
            ),
            'classes': ('collapse',),
            'description': 'Admin approval workflow and decision tracking'
        }),
        ('Status & Tracking', {
            'fields': (
                'created_at', 'updated_at', 'completed_at', 'registration_officer'
            )
        }),
    )

    readonly_fields = [
        'vin', 'ai_verification_score', 'age_verification_passed',
        'document_verification_passed', 'biometric_verification_passed',
        'anomaly_detection_passed', 'created_at', 'updated_at',
        'approval_timestamp'
    ]

    # Actions
    actions = [
        'approve_registrations', 'reject_registrations',
        'flag_for_review', 'clear_flag',
        'mark_as_suspected', 'clear_suspicion',
        'export_selected', 'export_pending_approvals'
    ]

    inlines = [ApprovalAuditLogInline]

    def full_name(self, obj):
        """Display full name."""
        return f"{obj.first_name} {obj.surname}"
    full_name.short_description = 'Full Name'

    def risk_level_badge(self, obj):
        """Display risk level with color coding."""
        colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#dc3545',
        }
        color = colors.get(obj.risk_level, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_risk_level_display()
        )
    risk_level_badge.short_description = 'Risk Level'

    def approved_by_name(self, obj):
        """Display admin who approved."""
        return obj.approved_by.username if obj.approved_by else '—'
    approved_by_name.short_description = 'Approved By'

    def approval_actions(self, obj):
        """Display approval action buttons."""
        if obj.status == 'pending_admin_approval':
            approve_url = reverse('admin:registration_voterregistration_change', args=[obj.pk])
            return format_html(
                '<a class="button" href="{}">Review & Approve</a>',
                approve_url
            )
        return '—'
    approval_actions.short_description = 'Actions'

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'state_of_origin', 'lga_of_origin', 'approved_by'
        )

    def get_readonly_fields(self, request, obj=None):
        """Make approval fields read-only for non-superusers."""
        readonly = list(self.readonly_fields)
        if obj and obj.status == 'approved':
            # Lock down approved registrations
            readonly.extend(['status', 'approved_by', 'approval_notes', 'vin'])
        return readonly

    def approve_registrations(self, request, queryset):
        """
        Approve selected registrations with validation.
        """
        if not request.user.is_superuser:
            self.message_user(
                request,
                'Only superusers can approve registrations.',
                messages.ERROR
            )
            return

        updated = 0
        errors = 0
        
        for registration in queryset.filter(status__in=['pending_admin_approval', 'pending_verification']):
            try:
                # Validate registration is ready
                if not registration.is_ready_for_approval():
                    errors += 1
                    continue

                # Generate VIN if needed
                if not registration.vin:
                    from .views import generate_vin, generate_temporary_voter_card
                    registration.vin = generate_vin(registration)
                    generate_temporary_voter_card(registration)

                # Update registration
                registration.status = 'approved'
                registration.approved_by = request.user
                registration.approval_timestamp = timezone.now()
                registration.approved_at = timezone.now()
                registration.save()

                # Create audit log
                ApprovalAuditLog.objects.create(
                    registration=registration,
                    admin_user=request.user,
                    action='approve',
                    reason='Approved via admin panel',
                    risk_assessment=registration.risk_level,
                    ai_score_at_approval=registration.ai_verification_score,
                    documents_verified=registration.document_verification_passed,
                    biometrics_verified=registration.biometric_verification_passed,
                    age_verified=registration.age_verification_passed,
                    ip_address=self._get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )

                updated += 1
            except Exception as e:
                errors += 1
                self.message_user(
                    request,
                    f'Error approving registration {registration.id}: {str(e)}',
                    messages.ERROR
                )

        msg = f'Successfully approved {updated} registration(s).'
        if errors:
            msg += f' {errors} error(s) occurred.'
        self.message_user(request, msg)
    approve_registrations.short_description = '✓ Approve selected registrations'

    def reject_registrations(self, request, queryset):
        """
        Reject selected registrations with reason tracking.
        """
        if not request.user.is_superuser:
            self.message_user(
                request,
                'Only superusers can reject registrations.',
                messages.ERROR
            )
            return

        # Filter to only approvable/pending registrations
        updated = queryset.filter(
            status__in=['pending_admin_approval', 'pending_verification', 'draft']
        ).update(
            status='rejected',
            completed_at=timezone.now(),
            rejection_reason='admin_rejection',
            approved_by=request.user,
            approval_timestamp=timezone.now()
        )

        # Create audit logs for rejected registrations
        for registration in queryset.filter(status='rejected'):
            ApprovalAuditLog.objects.create(
                registration=registration,
                admin_user=request.user,
                action='reject',
                reason='Rejected via admin panel',
                risk_assessment=registration.risk_level,
                ai_score_at_approval=registration.ai_verification_score,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

        self.message_user(request, f'Successfully rejected {updated} registration(s).')
    reject_registrations.short_description = '✗ Reject selected registrations'

    def flag_for_review(self, request, queryset):
        """Flag registrations for manual review."""
        updated = queryset.update(
            flagged_for_review=True,
            status='flagged'
        )
        self.message_user(
            request,
            f'Flagged {updated} registration(s) for review.'
        )
    flag_for_review.short_description = '🚩 Flag for review'

    def clear_flag(self, request, queryset):
        """Clear manual review flag."""
        updated = queryset.update(flagged_for_review=False)
        self.message_user(
            request,
            f'Cleared flag for {updated} registration(s).'
        )
    clear_flag.short_description = '🗑️ Clear review flag'

    def mark_as_suspected(self, request, queryset):
        """Mark registrations as suspected underage."""
        updated = queryset.update(is_underage_suspected=True)
        self.message_user(
            request,
            f'Marked {updated} registration(s) as suspected underage.'
        )
    mark_as_suspected.short_description = 'Mark as suspected underage'

    def clear_suspicion(self, request, queryset):
        """Clear underage suspicion."""
        updated = queryset.update(is_underage_suspected=False)
        self.message_user(
            request,
            f'Cleared suspicion for {updated} registration(s).'
        )
    clear_suspicion.short_description = 'Clear underage suspicion'

    def export_selected(self, request, queryset):
        """Export selected registrations to CSV."""
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="registrations.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'VIN', 'First Name', 'Last Name', 'Date of Birth', 'Phone',
            'State', 'LGA', 'Status', 'Risk Level', 'AI Score', 'Approved By', 'Created At'
        ])

        for reg in queryset:
            writer.writerow([
                reg.vin, reg.first_name, reg.surname, reg.date_of_birth,
                reg.phone_number, reg.state_of_origin,
                reg.lga_of_origin, reg.status, reg.risk_level,
                reg.ai_verification_score,
                reg.approved_by.username if reg.approved_by else 'N/A',
                reg.created_at
            ])

        return response
    export_selected.short_description = '📥 Export selected to CSV'

    def export_pending_approvals(self, request, queryset):
        """Export pending approvals report."""
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="pending_approvals.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'VIN', 'Full Name', 'Age', 'Risk Level', 'AI Score',
            'Documents Verified', 'Biometrics Score', 'Days Pending', 'Created At'
        ])

        pending = queryset.filter(status='pending_admin_approval')
        for reg in pending:
            days_pending = (timezone.now() - reg.created_at).days
            writer.writerow([
                reg.vin or 'PENDING',
                reg.get_full_name(),
                reg.age if reg.date_of_birth else 'N/A',
                reg.get_risk_level_display(),
                f"{reg.ai_verification_score:.2f}",
                '✓' if reg.document_verification_passed else '✗',
                f"{reg.facial_quality_score:.2f}",
                days_pending,
                reg.created_at
            ])

        return response
    export_pending_approvals.short_description = '📊 Export pending approvals'

    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@admin.register(RegistrationStep)
class RegistrationStepAdmin(ModelAdmin):
    """
    Admin interface for registration steps.
    """

    list_display = ['registration', 'step_number', 'step_name', 'completed_at']
    list_filter = ['step_number', 'completed_at']
    search_fields = ['registration__vin', 'registration__first_name', 'registration__surname']

    readonly_fields = ['registration', 'step_number', 'step_name', 'completed_at', 'step_data']

    def has_add_permission(self, request):
        """Disable adding steps manually."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disable deleting steps."""
        return False


@admin.register(TemporaryVoterCard)
class TemporaryVoterCardAdmin(ModelAdmin):
    """
    Admin interface for temporary voter cards.
    """

    list_display = ['registration', 'card_number', 'issued_date', 'is_active']
    list_filter = ['issued_date', 'is_active']
    search_fields = ['registration__vin', 'registration__first_name', 'registration__surname', 'card_number']

    readonly_fields = ['registration', 'card_number', 'card_data', 'issued_date', 'expiry_date', 'pdf_file']

    def has_add_permission(self, request):
        """Disable adding TVCs manually."""
        return False


@admin.register(ApprovalAuditLog)
class ApprovalAuditLogAdmin(ModelAdmin):
    """
    Admin interface for approval audit logs.
    """

    list_display = [
        'registration_id', 'action_badge', 'admin_user', 'risk_assessment',
        'ai_score_at_approval', 'timestamp'
    ]

    list_filter = [
        'action', 'risk_assessment', 'timestamp',
        'documents_verified', 'biometrics_verified', 'age_verified'
    ]

    search_fields = [
        'registration__vin', 'admin_user__username',
        'registration__first_name', 'registration__surname'
    ]

    readonly_fields = [
        'registration', 'admin_user', 'action', 'reason',
        'risk_assessment', 'ai_score_at_approval', 'timestamp',
        'documents_verified', 'biometrics_verified', 'age_verified',
        'ip_address', 'user_agent'
    ]

    fieldsets = (
        ('Approval Details', {
            'fields': (
                'registration', 'admin_user', 'action', 'reason'
            )
        }),
        ('Risk Assessment', {
            'fields': (
                'risk_assessment', 'ai_score_at_approval'
            )
        }),
        ('Verification Checklist', {
            'fields': (
                'documents_verified', 'biometrics_verified', 'age_verified'
            )
        }),
        ('Audit Trail', {
            'fields': (
                'timestamp', 'ip_address', 'user_agent'
            ),
            'classes': ('collapse',)
        }),
    )

    def action_badge(self, obj):
        """Display action with color coding."""
        colors = {
            'approve': '#28a745',
            'reject': '#dc3545',
            'flag': '#ffc107',
            'override': '#17a2b8',
        }
        color = colors.get(obj.action, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_action_display()
        )
    action_badge.short_description = 'Action'

    def registration_id(self, obj):
        """Display registration VIN as link."""
        url = reverse('admin:registration_voterregistration_change', args=[obj.registration.pk])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.registration.vin or obj.registration.id
        )
    registration_id.short_description = 'Registration'

    def has_add_permission(self, request):
        """Disable manual audit log creation."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of audit logs."""
        return False


# Custom admin site configuration
class RegistrationAdminSite(admin.AdminSite):
    """
    Custom admin site for registration management.
    """

    site_header = 'INEC Underage Eradicator - Registration Admin'
    site_title = 'INEC Registration Admin'
    index_title = 'Registration Management'

    def get_app_list(self, request):
        """
        Customize the app list to show relevant stats.
        """
        app_list = super().get_app_list(request)

        # Add custom stats for registration app
        for app in app_list:
            if app['app_label'] == 'registration':
                # Add model counts
                for model in app['models']:
                    if model['object_name'] == 'VoterRegistration':
                        model['stats'] = self._get_registration_stats()

        return app_list

    def _get_registration_stats(self):
        """Get registration statistics."""
        total = VoterRegistration.objects.count()
        approved = VoterRegistration.objects.filter(status='approved').count()
        rejected = VoterRegistration.objects.filter(status='rejected').count()
        pending_approval = VoterRegistration.objects.filter(status='pending_admin_approval').count()
        suspected = VoterRegistration.objects.filter(is_underage_suspected=True).count()
        high_risk = VoterRegistration.objects.filter(risk_level='high').count()

        return {
            'total': total,
            'approved': approved,
            'rejected': rejected,
            'pending_approval': pending_approval,
            'suspected': suspected,
            'high_risk': high_risk,
            'approval_rate': (approved / total * 100) if total > 0 else 0,
        }


# Create the custom admin site
registration_admin = RegistrationAdminSite(name='registration_admin')

# Register models with the custom admin site
registration_admin.register(VoterRegistration, VoterRegistrationAdmin)
registration_admin.register(RegistrationStep, RegistrationStepAdmin)
registration_admin.register(TemporaryVoterCard, TemporaryVoterCardAdmin)
registration_admin.register(ApprovalAuditLog, ApprovalAuditLogAdmin)
