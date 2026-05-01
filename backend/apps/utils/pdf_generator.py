"""
PDF Generation Module for INEC Underage Eradicator

This module generates Temporary Voter Cards (TVCs) and other PDF documents
for the voter registration system.
"""

# Mock PDF generation - in production, install reportlab
import os
import uuid
from datetime import datetime
from io import BytesIO
import json

class TVCGenerator:
    """
    Generates Temporary Voter Cards (TVCs) for approved registrations.
    Mock implementation for development.
    """

    def __init__(self):
        pass  # No setup needed for mock implementation

    def generate_tvc(self, registration):
        """
        Generate a Temporary Voter Card PDF for a registration.
        Mock implementation that returns JSON data instead of PDF.

        Args:
            registration: VoterRegistration instance

        Returns:
            dict: Contains mock PDF data and metadata
        """
        # Generate mock PDF content as JSON
        tvc_content = {
            "title": "INDEPENDENT NATIONAL ELECTORAL COMMISSION",
            "subtitle": "TEMPORARY VOTER CARD",
            "voter_id": registration.vin or "Pending Assignment",
            "full_name": f"{registration.surname} {registration.first_name} {registration.middle_name or ''}".strip(),
            "date_of_birth": registration.date_of_birth.strftime('%d/%m/%Y') if registration.date_of_birth else "N/A",
            "state_of_origin": registration.state_of_origin or "N/A",
            "lga_of_origin": registration.lga_of_origin or "N/A",
            "residence_address": registration.residence_address or "N/A",
            "phone_number": registration.phone_number or "N/A",
            "registration_date": registration.created_at.strftime('%d/%m/%Y %H:%M') if registration.created_at else "N/A",
            "notice": "This Temporary Voter Card is issued pending final verification and approval.",
            "verification_code": f"INEC-TVC-{registration.id}-{uuid.uuid4().hex[:8]}",
            "footer": "Independent National Electoral Commission (INEC)"
        }

        # Convert to JSON bytes (mock PDF)
        pdf_data = json.dumps(tvc_content, indent=2).encode('utf-8')

        return {
            'pdf_data': pdf_data,
            'file_name': f"TVC_{registration.id}.pdf",
            'content_type': 'application/pdf',  # Still claim it's PDF for compatibility
            'verification_code': tvc_content['verification_code'],
            'generated_at': datetime.now()
        }

    def generate_bulk_tvcs(self, registrations):
        """
        Generate TVCs for multiple registrations.

        Args:
            registrations: List of VoterRegistration instances

        Returns:
            dict: Contains PDF data for all TVCs
        """
        results = []
        for registration in registrations:
            try:
                tvc_data = self.generate_tvc(registration)
                results.append({
                    'registration_id': registration.id,
                    'tvc_data': tvc_data,
                    'status': 'success'
                })
            except Exception as e:
                results.append({
                    'registration_id': registration.id,
                    'error': str(e),
                    'status': 'failed'
                })

        return {
            'total_processed': len(registrations),
            'successful': len([r for r in results if r['status'] == 'success']),
            'failed': len([r for r in results if r['status'] == 'failed']),
            'results': results
        }

class ReportGenerator:
    """
    Generates various reports for the INEC system.
    """

    def __init__(self):
        self.tvc_generator = TVCGenerator()

    def generate_registration_report(self, registrations, date_from=None, date_to=None):
        """
        Generate a registration summary report.
        Mock implementation that returns JSON data.

        Args:
            registrations: Queryset of VoterRegistration instances
            date_from: Start date filter
            date_to: End date filter

        Returns:
            dict: Report data
        """
        # Calculate statistics
        total_registrations = len(registrations)
        approved_count = len([r for r in registrations if getattr(r, 'status', None) == 'approved'])
        pending_count = len([r for r in registrations if getattr(r, 'status', None) == 'pending'])
        rejected_count = len([r for r in registrations if getattr(r, 'status', None) == 'rejected'])

        report_content = {
            "title": "INEC Voter Registration Report",
            "generated_on": datetime.now().strftime('%d/%m/%Y %H:%M'),
            "date_range": {
                "from": date_from.strftime('%d/%m/%Y') if date_from else None,
                "to": date_to.strftime('%d/%m/%Y') if date_to else None
            },
            "summary_statistics": {
                "total_registrations": total_registrations,
                "approved": approved_count,
                "pending_review": pending_count,
                "rejected": rejected_count,
                "approval_rate": ".1f" if total_registrations > 0 else "0%"
            },
            "registrations": [
                {
                    "id": getattr(r, 'id', None),
                    "name": f"{getattr(r, 'surname', '')} {getattr(r, 'first_name', '')}".strip(),
                    "status": getattr(r, 'status', 'unknown'),
                    "registration_date": getattr(r, 'created_at', None).strftime('%d/%m/%Y') if getattr(r, 'created_at', None) else None
                } for r in registrations[:10]  # Limit to first 10 for mock
            ]
        }

        # Convert to JSON bytes (mock PDF)
        pdf_data = json.dumps(report_content, indent=2).encode('utf-8')

        return {
            'pdf_data': pdf_data,
            'file_name': f"registration_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            'content_type': 'application/pdf',
            'summary': {
                'total': total_registrations,
                'approved': approved_count,
                'pending': pending_count,
                'rejected': rejected_count
            }
        }

    def generate_report(self, report_type, **kwargs):
        """
        Generic report generation method.

        Args:
            report_type: Type of report to generate
            **kwargs: Additional parameters

        Returns:
            dict: Report data
        """
        if report_type == 'registration_summary':
            registrations = kwargs.get('registrations', [])
            return self.generate_registration_report(
                registrations,
                kwargs.get('date_from'),
                kwargs.get('date_to')
            )
        else:
            raise ValueError(f"Unknown report type: {report_type}")

    def get_dashboard_data(self):
        """
        Get data for dashboard display.

        Returns:
            dict: Dashboard metrics and charts data
        """
        # Mock dashboard data - in a real implementation, this would query the database
        return {
            'metrics': {
                'total_registrations': 1250,
                'approved_today': 45,
                'pending_review': 23,
                'rejected_today': 3,
                'underage_detected': 156
            },
            'charts': {
                'registrations_by_state': {
                    'labels': ['Lagos', 'Kano', 'Rivers', 'Oyo', 'Kaduna'],
                    'data': [250, 180, 150, 120, 100]
                },
                'verification_status': {
                    'labels': ['Approved', 'Pending', 'Rejected'],
                    'data': [850, 150, 250]
                }
            },
            'alerts': [
                {'type': 'warning', 'message': 'High rejection rate in Lagos State'},
                {'type': 'info', 'message': 'System performance optimal'}
            ],
            'last_updated': datetime.now().isoformat()
        }