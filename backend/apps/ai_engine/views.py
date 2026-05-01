from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from .underage_eradicator import UnderageEradicator
from apps.registration.models import VoterRegistration

# Initialize the AI engine
ai_engine = UnderageEradicator()

@csrf_exempt
@require_POST
def verify_registration(request):
    """
    API endpoint to verify a registration using AI
    """
    try:
        data = json.loads(request.body)
        registration_id = data.get('registration_id')

        if not registration_id:
            return JsonResponse({'error': 'Registration ID required'}, status=400)

        # Get the registration
        registration = get_object_or_404(VoterRegistration, id=registration_id)

        # Run AI verification
        result = ai_engine.verify_registration(registration)

        return JsonResponse({
            'verification_id': result['verification_id'],
            'overall_result': result['overall_result'],
            'confidence_score': result['confidence_score'],
            'layer_results': result['layer_results'],
            'processing_time': result['processing_time']
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def verification_status(request, verification_id):
    """
    Get the status of a verification process
    """
    try:
        # In a real implementation, this would check a database/cache
        # For now, return a mock status
        return JsonResponse({
            'verification_id': str(verification_id),
            'status': 'completed',
            'progress': 100
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def verification_results(request, verification_id):
    """
    Get detailed results of a verification
    """
    try:
        # In a real implementation, this would fetch from database
        # For now, return mock results
        return JsonResponse({
            'verification_id': str(verification_id),
            'results': {
                'layer_1': {'result': 'PASS', 'confidence': 0.95},
                'layer_2': {'result': 'PASS', 'confidence': 0.92},
                'layer_3': {'result': 'PASS', 'confidence': 0.88},
                'layer_4': {'result': 'PASS', 'confidence': 0.91},
                'layer_5': {'result': 'PASS', 'confidence': 0.94}
            },
            'overall_result': 'APPROVED',
            'confidence_score': 0.92
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)