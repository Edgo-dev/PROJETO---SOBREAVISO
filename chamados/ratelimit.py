"""Rate limiting leve por IP para telas sensíveis (cadastro, reset de senha).

Baseado no cache do Django. É best-effort: com o cache local (LocMemCache)
padrão, a contagem é por processo — suficiente para conter abuso automatizado
neste sistema interno. Em produção multi-processo, configure um cache
compartilhado (Redis/Memcached) para a contagem valer entre os workers.

O django-axes já protege o login (força bruta de senha). Este módulo cobre o
que o axes não cobre: spam de auto-cadastro e de e-mails de recuperação.
"""

from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render


def _client_ip(request) -> str:
    encaminhado = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if encaminhado:
        return encaminhado.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "") or "desconhecido"


def throttle_post(scope: str, limite_padrao: int, janela_padrao: int):
    """Limita requisições POST por IP dentro de um scope.

    Só conta POST (a ação cara/abusável); GET passa livre. Os limites podem ser
    sobrescritos por settings ``THROTTLE_<SCOPE>_LIMIT`` e
    ``THROTTLE_<SCOPE>_WINDOW`` (em segundos). Limite <= 0 desabilita o scope.
    """

    def decorator(view):
        @wraps(view)
        def _wrapped(request, *args, **kwargs):
            if request.method == "POST":
                limite = getattr(
                    settings, f"THROTTLE_{scope.upper()}_LIMIT", limite_padrao
                )
                janela = getattr(
                    settings, f"THROTTLE_{scope.upper()}_WINDOW", janela_padrao
                )
                if limite > 0:
                    chave = f"throttle:{scope}:{_client_ip(request)}"
                    contagem = cache.get(chave, 0)
                    if contagem >= limite:
                        return render(
                            request,
                            "chamados/muitas_requisicoes.html",
                            status=429,
                        )
                    if contagem:
                        try:
                            cache.incr(chave)
                        except ValueError:
                            # A chave expirou entre o get e o incr: reinicia.
                            cache.set(chave, 1, janela)
                    else:
                        cache.set(chave, 1, janela)
            return view(request, *args, **kwargs)

        return _wrapped

    return decorator
