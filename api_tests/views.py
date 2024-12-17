from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django_ratelimit.decorators import ratelimit
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from rest_framework.throttling import UserRateThrottle
from .customs import CustomUserRateThrottle


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
    throttle_classes = [CustomUserRateThrottle]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        # Asignamos el throttle al request aquí para que esté disponible para el middleware
        # Aquí obtenemos el throttle, asumiendo que hay uno
        throttle = self.get_throttles()[0]
        request.throttle = throttle
        print('THR - -', request.throttle)

    def get(self, request):
        return Response({
            'status': 'Permitido',
            'message': 'Hola!'
        })