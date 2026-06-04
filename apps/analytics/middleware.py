class PageViewMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Skip admin, static, media
        path = request.path
        if not any(path.startswith(p) for p in ['/aura-admin/', '/static/', '/media/', '/__debug__/']):
            try:
                from .models import PageView
                PageView.objects.create(
                    path=path,
                    user=request.user if request.user.is_authenticated else None,
                    session_key=request.session.session_key or '',
                    ip_address=self._get_ip(request),
                    referrer=request.META.get('HTTP_REFERER', '')[:500],
                )
            except Exception:
                pass
        return response

    def _get_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
