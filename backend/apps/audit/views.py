from django.shortcuts import render
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import AuditLog, SystemEvent, DataAccessLog
import json

def audit_logs(request):
    """
    View audit logs with filtering and pagination
    """
    try:
        # Get query parameters
        page = request.GET.get('page', 1)
        per_page = request.GET.get('per_page', 50)
        action_type = request.GET.get('action_type')
        user_id = request.GET.get('user_id')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')

        # Build query
        queryset = AuditLog.objects.all().order_by('-timestamp')

        if action_type:
            queryset = queryset.filter(action_type=action_type)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)

        # Paginate
        paginator = Paginator(queryset, per_page)
        logs_page = paginator.page(page)

        # Serialize logs
        logs_data = [{
            'id': log.id,
            'timestamp': log.timestamp.isoformat(),
            'user_id': log.user_id,
            'action_type': log.action_type,
            'resource_type': log.resource_type,
            'resource_id': log.resource_id,
            'details': log.details,
            'ip_address': log.ip_address,
            'user_agent': log.user_agent
        } for log in logs_page]

        return JsonResponse({
            'logs': logs_data,
            'pagination': {
                'page': logs_page.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': logs_page.has_next(),
                'has_previous': logs_page.has_previous()
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def system_events(request):
    """
    View system events
    """
    try:
        page = request.GET.get('page', 1)
        per_page = request.GET.get('per_page', 50)
        event_type = request.GET.get('event_type')

        queryset = SystemEvent.objects.all().order_by('-timestamp')

        if event_type:
            queryset = queryset.filter(event_type=event_type)

        paginator = Paginator(queryset, per_page)
        events_page = paginator.page(page)

        events_data = [{
            'id': event.id,
            'timestamp': event.timestamp.isoformat(),
            'event_type': event.event_type,
            'severity': event.severity,
            'message': event.message,
            'details': event.details,
            'source': event.source
        } for event in events_page]

        return JsonResponse({
            'events': events_data,
            'pagination': {
                'page': events_page.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def data_access_logs(request):
    """
    View data access logs
    """
    try:
        page = request.GET.get('page', 1)
        per_page = request.GET.get('per_page', 50)

        queryset = DataAccessLog.objects.all().order_by('-timestamp')

        paginator = Paginator(queryset, per_page)
        logs_page = paginator.page(page)

        logs_data = [{
            'id': log.id,
            'timestamp': log.timestamp.isoformat(),
            'user_id': log.user_id,
            'data_type': log.data_type,
            'data_id': log.data_id,
            'access_type': log.access_type,
            'purpose': log.purpose,
            'ip_address': log.ip_address
        } for log in logs_page]

        return JsonResponse({
            'logs': logs_data,
            'pagination': {
                'page': logs_page.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def audit_report(request):
    """
    Generate audit report
    """
    try:
        # Get date range
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')

        # Generate summary statistics
        total_logs = AuditLog.objects.count()
        total_events = SystemEvent.objects.count()
        total_access = DataAccessLog.objects.count()

        if date_from and date_to:
            date_logs = AuditLog.objects.filter(timestamp__range=[date_from, date_to]).count()
            date_events = SystemEvent.objects.filter(timestamp__range=[date_from, date_to]).count()
            date_access = DataAccessLog.objects.filter(timestamp__range=[date_from, date_to]).count()
        else:
            date_logs = total_logs
            date_events = total_events
            date_access = total_access

        return JsonResponse({
            'summary': {
                'total_audit_logs': total_logs,
                'total_system_events': total_events,
                'total_data_access': total_access,
                'period_logs': date_logs,
                'period_events': date_events,
                'period_access': date_access
            },
            'date_range': {
                'from': date_from,
                'to': date_to
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)