from rest_framework.throttling import UserRateThrottle, SimpleRateThrottle
from oauth2_provider.models import AccessToken
import logging

from django_prometheus.models import ExportModelOperationsMixin
from prometheus_client import Counter
from .models import OAuth2AppRateLimit

allowed_requests = Counter(
    'allowed_requests', 'Number of allowed API requests', ['cliente'])
blocked_requests = Counter(
    'blocked_requests', 'Number of blocked API requests', ['cliente'])


class CustomUserRateThrottle(UserRateThrottle):
    def wait(self):
        return super().wait()

    def allow_request(self, request, view):
        is_allowed = super().allow_request(request, view)
        if not is_allowed:
            wait_time = self.wait()
            if wait_time:
                request.META['X-RateLimit-Retry-After'] = str(wait_time)

        return is_allowed


class CustomRateThrottle(SimpleRateThrottle):
    scope = 'oauth2_app'

    def get_cache_key(self, request, view):
        # Si el usuario está autenticado, usar su ID
        if request.user and request.user.is_authenticated:
            return f"throttle_{self.scope}_{request.user.id}"

        # Registrar consumo de aplicaciones

        # Si el usuario no está autenticado, usar la IP
        ip = self.get_ident(request)
        return f"throttle_{self.scope}_{ip}"

    def wait(self):
        return super().wait()

    def allow_request(self, request, view):
        is_allowed = super().allow_request(request, view)

        if self.history and self.num_requests:
            print("HISTORY: ", self.history)
            print("REQUESTS: ", self.num_requests)
            remaining_request = self.num_requests - len(self.history)
            print("REMAINING:", remaining_request)
            request.throttle_remaining = remaining_request
            print("REQUEST REMAINING:", request.throttle_remaining)

            request.throttle_limit = self.num_requests
            print("REQUEST LIMIT:", request.throttle_limit)

        return is_allowed


class OAuth2AppThrottle(SimpleRateThrottle):
    scope = 'oauth2_app'

    def get_rate_custom(self, client_id):
        client_id = getattr(self, 'client_id', None)
        print("CLIENTE ID > ", client_id)
        if not client_id:
            print("RETORNANDO")
            return '10/m'

        try:
            rate_limit = OAuth2AppRateLimit.objects.filter(
                client_id=client_id).first()
            print("RATE LIMIT : ", rate_limit)
            return str(rate_limit)
        except:
            OAuth2AppRateLimit.DoesNotExist
            return '12/h'

    def get_cache_key(self, request, view):
        # Utilizar el ID de la aplicación OAuth2 para generar la clave de caché
        self.client_id = request.headers.get('cliente')

        # print("Headers completos:", request.headers)
        print(f"CLIENT ID 1 : {self.client_id}")
        if not self.client_id:
            return None
        return f"throttle_{self.scope}_{self.client_id}"

    def allow_request(self, request, view):
        # Asegurarte de que self.key esté inicializada
        self.key = self.get_cache_key(request, view)

        print("Llamando a get rate")
        self.rate = self.get_rate_custom(self.client_id)

        # Inicializar el historial solo si self.key es válido
        self.history = self.cache.get(self.key, []) if self.key else []

        self.num_requests, self.duration = self.parse_rate(self.rate)

        # Llama al método base para determinar si la solicitud está permitida
        is_allowed = super().allow_request(request, view)

        # Configurar los encabezados personalizados para límites de solicitud
        if self.history and self.num_requests:
            remaining_request = self.num_requests - len(self.history)
            request.throttle_remaining = remaining_request
            request.throttle_limit = self.num_requests

        # Monitoreo con Prometheus
        if self.client_id:
            if is_allowed:
                allowed_requests.labels(cliente=self.client_id).inc()
            else:
                blocked_requests.labels(cliente=self.client_id).inc()

        return is_allowed
