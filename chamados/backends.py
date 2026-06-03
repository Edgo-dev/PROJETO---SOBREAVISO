"""Backend de autenticacao por nome + sobrenome + senha."""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


def axes_username(request, credentials=None):
    """Identidade usada pelo django-axes para contabilizar tentativas.

    O login deste sistema e por (first_name, last_name), nao por 'username',
    entao compomos a chave a partir desses campos. Procura primeiro nas
    credentials passadas ao authenticate() e cai para o POST quando ausentes.
    """
    fontes = []
    if credentials:
        fontes.append(credentials)
    if request is not None and getattr(request, "POST", None):
        fontes.append(request.POST)
    for fonte in fontes:
        nome = (fonte.get("first_name") or "").strip()
        sobrenome = (fonte.get("last_name") or "").strip()
        composto = f"{nome} {sobrenome}".strip()
        if composto:
            return composto.lower()
    return None


class NomeSobrenomeBackend(ModelBackend):
    """Autentica por (first_name, last_name, password).

    Como o User do Django nao garante unicidade em first/last name nativamente,
    se mais de um usuario ativo coincidir a autenticacao e rejeitada por
    ambiguidade. O cadastro deve assegurar combinacoes unicas.
    """

    def authenticate(  # type: ignore[override]
        self,
        request,
        first_name=None,
        last_name=None,
        password=None,
        **kwargs,
    ):
        if not first_name or not last_name or not password:
            return None

        UserModel = get_user_model()
        qs = UserModel.objects.filter(
            first_name__iexact=first_name.strip(),
            last_name__iexact=last_name.strip(),
            is_active=True,
        )
        if qs.count() != 1:
            return None

        user = qs.first()
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
