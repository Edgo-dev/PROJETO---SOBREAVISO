"""Middleware do app chamados."""

import logging as _logging
from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse

_logger = _logging.getLogger(__name__)


class LoginRequiredMiddleware:
    """Exige autenticacao para qualquer rota fora dos prefixos isentos.

    Mantemos /admin/ isento para que o login proprio do Django Admin continue
    funcionando (util para superusers e gestao de usuarios).
    """

    EXEMPT_PREFIXES = (
        "/login/",
        "/logout/",
        "/cadastro/",
        "/recuperar-senha/",
        "/admin/",
        "/static/",
        "/media/",
        "/favicon.ico",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info or "/"
        if request.user.is_authenticated or any(
            path.startswith(prefix) for prefix in self.EXEMPT_PREFIXES
        ):
            return self.get_response(request)

        try:
            login_url = reverse(settings.LOGIN_URL)
        except Exception as exc:
            _logger.debug(
                "LoginRequiredMiddleware: erro ao resolver URL %s — %s",
                request.path,
                exc,
            )
            login_url = settings.LOGIN_URL
        query = urlencode({"next": request.get_full_path()})
        return HttpResponseRedirect(f"{login_url}?{query}")
