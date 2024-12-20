from django.utils.deprecation import MiddlewareMixin
from api_tests.customs import CustomUserRateThrottle


class ThrottleAssignmentMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Obtenemos el throttle y lo asignamos al request
        throttle = CustomUserRateThrottle()
        # Aquí `None` es el view (no necesario en este contexto)
        if throttle.allow_request(request, None):
            request.throttle = throttle
        print('Throttle asignado:', request.throttle)


class RateLimitHeadersMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        print('PROCCESSING')

        if hasattr(request, 'throttle') and request.throttle:
            print('Middleware: throttle detected')
            throttle = request.throttle
            response['X-RateLimit-Limit'] = throttle.num_requests

            # Si history es una lista o un deque, usar len() en lugar de count()
            response['X-RateLimit-Remaining'] = max(
                0, throttle.num_requests -
                len(throttle.history)  # Aquí usamos len()
            )

            # Asegurarnos de que wait() retorne un valor adecuado
            response['X-RateLimit-Reset'] = throttle.wait() if throttle.wait() else 'N/A'
        else:
            print('Middleware: No throttle detected')

        return response


class ThrottleHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        print("calling")
        print(request)
        if hasattr(request, 'throttle_remaining') and hasattr(request, 'throttle_limit'):
            print("HAS ATTR")
            response['X-RateLimit-Limit'] = request.throttle_limit
            response['X-RateLimit-Remaining'] = max(0,
                                                    request.throttle_remaining)

        return response
