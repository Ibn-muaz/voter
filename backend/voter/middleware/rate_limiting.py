import time
from django.core.cache import cache
from django.http import HttpResponse
from django.conf import settings


class RateLimitingMiddleware:
    """
    Middleware to implement rate limiting for API endpoints.
    Uses Django's cache framework to track requests per IP address.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip rate limiting for admin and static files
        if request.path.startswith('/admin/') or request.path.startswith('/static/'):
            return self.get_response(request)

        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        # Create cache key
        cache_key = f"rate_limit_{ip}"
        current_time = int(time.time())

        # Get current request count and window start
        cache_data = cache.get(cache_key, {'count': 0, 'window_start': current_time})

        # Reset counter if window has expired
        if current_time - cache_data['window_start'] >= settings.RATE_LIMIT_WINDOW:
            cache_data = {'count': 0, 'window_start': current_time}

        # Increment counter
        cache_data['count'] += 1

        # Check if limit exceeded
        if cache_data['count'] > settings.RATE_LIMIT_REQUESTS:
            return HttpResponse(
                '{"error": "Rate limit exceeded. Please try again later."}',
                content_type='application/json',
                status=429
            )

        # Store updated data
        cache.set(cache_key, cache_data, settings.RATE_LIMIT_WINDOW)

        response = self.get_response(request)
        return response