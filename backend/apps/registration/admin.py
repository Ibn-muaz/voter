"""
Admin interface for the voter registration system.
"""

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Q
from .models import VoterRegistration, RegistrationStep, TemporaryVoterCard


@admin.register(VoterRegistration)
class VoterRegistrationAdmin(ModelAdmin):
    """
    Admin interface for voter registrations.
    """

    # List display
    list_display = [
        'vin', 'full_name', 'date_of_birth', 'status', 'ai_verification_score',
        'created_at', 'flagged_for_review', 'action_buttons'
    ]

    list_filter = [
        'status', 'gender', 'state_of_origin',
        'flagged_for_review', 'created_at', 'approved_at'
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
        ('Status & Tracking', {
            'fields': (
                'status', 'created_at',
                'approved_at', 'registration_officer'
            )
        }),
    )

    readonly_fields = [
        'vin', 'ai_verification_score', 'age_verification_passed',
        'document_verification_passed', 'biometric_verification_passed',
        'anomaly_detection_passed', 'created_at', 'approved_at'
    ]

    # Actions
    actions = [
        'approve_registrations', 'reject_registrations',
        'mark_as_suspected', 'clear_suspicion', 'export_selected'
    ]

    def full_name(self, obj):
        """Display full name."""
        return f"{obj.first_name} {obj.surname}"
    full_name.short_description = 'Full Name'

    def action_buttons(self, obj):
        """Display action buttons."""
        actions = []

        if obj.status == 'pending_review':
            actions.append(
                f'<a href="{reverse("admin:registration_voterregistration_change", args=[obj.pk])}?action=approve" '
                'class="button">Approve</a>'
            )
            actions.append(
                f'<a href="{reverse("admin:registration_voterregistration_change", args=[obj.pk])}?action=reject" '
                'class="button">Reject</a>'
            )

        if obj.temporary_voter_card:
            actions.append(
                f'<a href="{reverse("registration:download_tvc", args=[obj.pk])}" '
                'class="button" target="_blank">Download TVC</a>'
            )

        return format_html(' '.join(actions)) if actions else '-'
    action_buttons.short_description = 'Actions'

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'state_of_origin', 'lga_of_origin'
        )

    def approve_registrations(self, request, queryset):
        """Approve selected registrations."""
        updated = 0
        for registration in queryset.filter(status__in=['pending_review', 'draft']):
            if not registration.vin:
                from .views import generate_vin, generate_temporary_voter_card
                registration.vin = generate_vin(registration)
                generate_temporary_voter_card(registration)

            registration.status = 'approved'
            registration.completed_at = timezone.now()
            registration.save()
            updated += 1

        self.message_user(
            request,
            f'Successfully approved {updated} registration(s).'
        )
    approve_registrations.short_description = 'Approve selected registrations'

    def reject_registrations(self, request, queryset):
        """Reject selected registrations."""
        updated = queryset.filter(
            status__in=['pending_review', 'draft', 'approved']
        ).update(status='rejected', completed_at=timezone.now())

        self.message_user(
            request,
            f'Successfully rejected {updated} registration(s).'
        )
    reject_registrations.short_description = 'Reject selected registrations'

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
            'State', 'LGA', 'Status', 'AI Score', 'Created At'
        ])

        for reg in queryset:
            writer.writerow([
                reg.vin, reg.first_name, reg.surname, reg.date_of_birth,
                reg.phone_number, reg.state_of_origin,
                reg.lga_of_origin,
                reg.status, reg.ai_verification_score, reg.created_at
            ])

        return response
    export_selected.short_description = 'Export selected to CSV'


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
        suspected = VoterRegistration.objects.filter(is_underage_suspected=True).count()

        return {
            'total': total,
            'approved': approved,
            'rejected': rejected,
            'suspected': suspected,
            'approval_rate': (approved / total * 100) if total > 0 else 0,
        }


# Create the custom admin site
registration_admin = RegistrationAdminSite(name='registration_admin')

# Register models with the custom admin site
registration_admin.register(VoterRegistration, VoterRegistrationAdmin)
registration_admin.register(RegistrationStep, RegistrationStepAdmin)
registration_admin.register(TemporaryVoterCard, TemporaryVoterCardAdmin)