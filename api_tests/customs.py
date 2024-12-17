from rest_framework.throttling import UserRateThrottle


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
