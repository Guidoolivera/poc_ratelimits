from rest_framework.throttling import UserRateThrottle, SimpleRateThrottle


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
    scope = 'custom'

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
