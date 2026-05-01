from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import base64
import json
from .models import BiometricData
from .utils import BiometricProcessor

biometric_processor = BiometricProcessor()

@csrf_exempt
@require_POST
def capture_biometric(request):
    """
    Capture and process biometric data
    """
    try:
        data = json.loads(request.body)
        biometric_type = data.get('type', 'face')  # face, fingerprint, iris
        image_data = data.get('image_data')  # base64 encoded image
        registration_id = data.get('registration_id')

        if not registration_id or not image_data:
            return JsonResponse({'error': 'Registration ID and image data required'}, status=400)

        # Decode base64 image
        try:
            image_bytes = base64.b64decode(image_data.split(',')[1])  # Remove data:image/jpeg;base64,
        except:
            return JsonResponse({'error': 'Invalid image data'}, status=400)

        # Process biometric data
        processing_result = biometric_processor.process_biometric(
            image_bytes, biometric_type
        )

        # Save biometric data
        biometric = BiometricData.objects.create(
            registration_id=registration_id,
            biometric_type=biometric_type,
            template_data=processing_result.get('template'),
            quality_score=processing_result.get('quality_score', 0),
            capture_metadata=processing_result.get('metadata', {})
        )

        return JsonResponse({
            'biometric_id': biometric.id,
            'quality_score': biometric.quality_score,
            'processing_status': 'success'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def verify_biometric(request, biometric_id):
    """
    Verify biometric data quality and authenticity
    """
    try:
        biometric = get_object_or_404(BiometricData, id=biometric_id)

        # In a real implementation, this would perform advanced verification
        # For now, return mock results
        verification_result = {
            'is_valid': biometric.quality_score > 0.7,
            'quality_score': biometric.quality_score,
            'checks_passed': ['quality_check', 'liveness_check', 'spoof_detection']
        }

        biometric.verification_status = 'verified' if verification_result['is_valid'] else 'rejected'
        biometric.save()

        return JsonResponse(verification_result)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_POST
def match_biometric(request):
    """
    Match biometric data against database
    """
    try:
        data = json.loads(request.body)
        biometric_id = data.get('biometric_id')
        match_threshold = data.get('threshold', 0.8)

        if not biometric_id:
            return JsonResponse({'error': 'Biometric ID required'}, status=400)

        biometric = get_object_or_404(BiometricData, id=biometric_id)

        # In a real implementation, this would search the biometric database
        # For now, return mock match result
        match_result = {
            'is_match': False,  # No duplicates found
            'match_score': 0.0,
            'matched_records': [],
            'search_status': 'completed'
        }

        return JsonResponse(match_result)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)