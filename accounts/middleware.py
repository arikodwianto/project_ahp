from django.shortcuts import redirect
from django.conf import settings

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Daftar URL yang boleh diakses tanpa login
        allowed_paths = [settings.LOGIN_URL, settings.LOGOUT_REDIRECT_URL, '/static/']

        # Cegah redirect loop: biarkan pengguna mengakses halaman login/logout
        if not request.user.is_authenticated and not any(request.path.startswith(path) for path in allowed_paths):
            return redirect(settings.LOGIN_URL)

        return self.get_response(request)
