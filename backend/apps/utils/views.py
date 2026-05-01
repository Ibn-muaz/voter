from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import NigerianState, LocalGovernmentArea
from .security import SecurityUtils

security_utils = SecurityUtils()

@require_GET
def generate_captcha(request):
    """
    Generate a CAPTCHA challenge
    """
    try:
        captcha_data = security_utils.generate_captcha()

        return JsonResponse({
            'captcha_id': captcha_data['captcha_id'],
            'image_data': captcha_data['image_data'],
            'audio_data': captcha_data.get('audio_data')
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def get_states(request):
    """
    Get list of Nigerian states
    """
    try:
        states = NigerianState.objects.all().values('code', 'name')

        return JsonResponse({
            'states': list(states)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def get_lgas(request, state_code):
    """
    Get LGAs for a specific state
    """
    try:
        state = NigerianState.objects.get(code=state_code)
        lgas = LocalGovernmentArea.objects.filter(state=state).values('code', 'name')

        return JsonResponse({
            'state': state_code,
            'lgas': list(lgas)
        })

    except NigerianState.DoesNotExist:
        return JsonResponse({'error': 'State not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)