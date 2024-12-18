from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django_ratelimit.decorators import ratelimit
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from rest_framework.throttling import UserRateThrottle
from .customs import CustomUserRateThrottle, OAuth2AppThrottle, CustomRateThrottle
from django.core.cache import cache


# Create your views here.


def ratelimit_with_headers(key=None, rate=None, method=None):
    def decorator(view_func):
        @ratelimit(key=key, rate=rate, method=method)
        def wrapped_view(request, *args, **kwargs):
            # Verificar si se aplicó el límite
            was_limited = getattr(request, 'limited', False)
            response = view_func(request, *args, **kwargs)

            # Agregar encabezados
            if isinstance(response, Response):
                response['X-RateLimit-Limit'] = rate
                response['X-RateLimit-Remaining'] = (
                    int(request.ratelimit_remaining) if hasattr(
                        request, 'ratelimit_remaining') else 0
                )
                response['X-RateLimit-Reset'] = getattr(
                    request, 'ratelimit_reset_time', 'N/A')
                if was_limited:
                    response.status_code = 429  # Too Many Requests
            return response
        return wrapped_view
    return decorator


@ratelimit(key='ip', rate='5/h')
@api_view(['GET'])
def saludar(request):
    return Response({'mensaje': 'HOLA!'})


class SaludarView(APIView):
    @method_decorator(ratelimit(key='ip', rate='5/h', method='GET'))
    def get(self, request):
        return Response({
            'message': 'BIENVENIDO!'
        })


@method_decorator(ratelimit_with_headers(key='ip', rate='5/h', method='GET'), name='dispatch')
class SaludarView2(APIView):
    def get(self, request):
        return Response({
            'message': 'CHAU!'
        })


class SaludarViewThrottle(APIView):
    throttle_classes = [CustomRateThrottle]

    def get(self, request):
        return Response({
            'status': 'Permitido',
            'message': 'Hola!'
        })


class CheckThrottleData(APIView):
    throttle_classes = [CustomRateThrottle]  # Usando tu throttle personalizado

    def get(self, request):
        # Crear la instancia de CustomRateThrottle
        throttle = CustomRateThrottle()

        cache_key = throttle.get_cache_key(request, self)

        cache_data = cache.get(cache_key)
        remaining_requests = get_remaining_requests(request, self)

        return Response({
            "cache_key": cache_key,
            "cache_data": cache_data,
            "remaining_requests": remaining_requests,
            "limit": request.throttle_limit
        })
    
class ProtectedViewForOauthApps(APIView):
    throttle_classes = [OAuth2AppThrottle]

    def get(self, request):
        # Crear la instancia de CustomRateThrottle
        throttle = OAuth2AppThrottle()

        cache_key = throttle.get_cache_key(request, self)

        cache_data = cache.get(cache_key)
        remaining_requests = getattr(request, 'throttle_remaining', None)
        limit = getattr(request, 'throttle_limit', None)

        return Response({
            "message": "Permitido.",
            "cache_key": cache_key,
            "cache_data": cache_data,
            "remaining_requests": remaining_requests,
            "limit": limit
        })

def get_remaining_requests(request, view):
    throttle = CustomRateThrottle()
    cache_key = throttle.get_cache_key(request, view)
    cache_data = cache.get(cache_key)

    if not cache_data:
        # Si no hay datos en el cache, todas las solicitudes están disponibles
        return throttle.num_requests

    remaining_requests = throttle.num_requests - len(cache_data)
    return max(0, remaining_requests)
