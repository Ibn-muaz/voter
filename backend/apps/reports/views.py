from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from .models import Report
from .utils import ReportGenerator
import json

report_generator = ReportGenerator()

@require_POST
def generate_report(request):
    """
    Generate a report
    """
    try:
        data = json.loads(request.body)
        report_type = data.get('report_type', 'registration_summary')
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        filters = data.get('filters', {})

        # Generate the report
        report_data = report_generator.generate_report(
            report_type=report_type,
            date_from=date_from,
            date_to=date_to,
            filters=filters
        )

        # Save report record
        report = Report.objects.create(
            report_type=report_type,
            parameters={
                'date_from': date_from,
                'date_to': date_to,
                'filters': filters
            },
            generated_by=request.user if request.user.is_authenticated else None,
            file_path=report_data.get('file_path'),
            file_size=report_data.get('file_size', 0)
        )

        return JsonResponse({
            'report_id': report.id,
            'report_type': report.report_type,
            'generated_at': report.generated_at.isoformat(),
            'file_path': report.file_path,
            'status': 'generated'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def download_report(request, report_id):
    """
    Download a generated report
    """
    try:
        report = get_object_or_404(Report, id=report_id)

        if not report.file_path or not default_storage.exists(report.file_path):
            return JsonResponse({'error': 'Report file not found'}, status=404)

        file_content = default_storage.open(report.file_path).read()
        response = HttpResponse(file_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="inec_report_{report.id}.pdf"'

        return response

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def dashboard(request):
    """
    Dashboard with key metrics and charts
    """
    try:
        # Get dashboard data
        dashboard_data = report_generator.get_dashboard_data()

        return JsonResponse({
            'metrics': dashboard_data.get('metrics', {}),
            'charts': dashboard_data.get('charts', {}),
            'alerts': dashboard_data.get('alerts', []),
            'last_updated': dashboard_data.get('last_updated')
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)