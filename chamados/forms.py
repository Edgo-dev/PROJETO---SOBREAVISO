"""Forms do app chamados."""

from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Ativo, Chamado, Fornecedor, Obra, StatusChamado


class LoginForm(forms.Form):
    first_name = forms.CharField(
        max_length=150,
        label="Nome",
        widget=forms.TextInput(
            attrs={
                "class": "auth-input",
                "autocomplete": "given-name",
                "autofocus": True,
                "placeholder": "Seu nome",
            }
        ),
    )
    last_name = forms.CharField(
        max_length=150,
        label="Sobrenome",
        widget=forms.TextInput(
            attrs={
                "class": "auth-input",
                "autocomplete": "family-name",
                "placeholder": "Seu sobrenome",
            }
        ),
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(
            attrs={
                "class": "auth-input",
                "autocomplete": "current-password",
                "placeholder": "Sua senha",
            }
        ),
    )


class RegisterForm(forms.Form):
    first_name = forms.CharField(
        max_length=150,
        label="Nome",
        widget=forms.TextInput(
            attrs={
                "class": "auth-input",
                "autocomplete": "given-name",
                "autofocus": True,
                "placeholder": "Seu nome",
            }
        ),
    )
    last_name = forms.CharField(
        max_length=150,
        label="Sobrenome",
        widget=forms.TextInput(
            attrs={
                "class": "auth-input",
                "autocomplete": "family-name",
                "placeholder": "Seu sobrenome",
            }
        ),
    )
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(
            attrs={
                "class": "auth-input",
                "autocomplete": "email",
                "placeholder": "voce@exemplo.com",
            }
        ),
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(
            attrs={
                "class": "auth-input",
                "autocomplete": "new-password",
                "placeholder": "Crie uma senha forte",
            }
        ),
        help_text="Mínimo 8 caracteres, evite senhas óbvias.",
    )
    password_confirmation = forms.CharField(
        label="Confirmar senha",
        widget=forms.PasswordInput(
            attrs={
                "class": "auth-input",
                "autocomplete": "new-password",
                "placeholder": "Repita a senha",
            }
        ),
    )

    def clean_first_name(self):
        return self.cleaned_data["first_name"].strip()

    def clean_last_name(self):
        return self.cleaned_data["last_name"].strip()

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        UserModel = get_user_model()
        if UserModel.objects.filter(email__iexact=email).exists():
            raise ValidationError("Já existe uma conta cadastrada com este e-mail.")
        return email

    def clean(self):
        cleaned = super().clean()
        first = cleaned.get("first_name", "")
        last = cleaned.get("last_name", "")
        pwd = cleaned.get("password")
        pwd2 = cleaned.get("password_confirmation")

        if pwd and pwd2 and pwd != pwd2:
            self.add_error("password_confirmation", "As senhas não conferem.")

        if first and last:
            UserModel = get_user_model()
            if UserModel.objects.filter(
                first_name__iexact=first,
                last_name__iexact=last,
                is_active=True,
            ).exists():
                raise ValidationError(
                    "Já existe um usuário ativo com este nome e sobrenome. "
                    "Use um segundo nome para diferenciar (ex.: 'João Carlos') "
                    "ou peça suporte ao administrador."
                )

        if pwd:
            try:
                password_validation.validate_password(pwd)
            except ValidationError as exc:
                self.add_error("password", exc)

        return cleaned


DENOMINACAO_OPCOES = [
    "Arrombamento de portas / vitrines (Por assalto / furto)",
    "Dificuldades de abrir e/ou fechar portas de enrolar",
    "Estilhaçamento de porta / vitrines de vidro",
    "Infiltrações diversas",
    "Fachada com revestimento em geral descolando",
    "Forros cedendo",
    "Queda de árvores",
    "Sinistros em ativos (colisão de veículos / incêndio etc.)",
    "Serviços de serralheria para reparo em portas de portões",
    "Notificações de órgãos públicos em geral",
    "Curto-circuito",
    "Desarme de disjuntores",
    "Falta de energia",
    "Reparo em motores de portas automáticas",
    "Vazamentos em geral",
    "Abastecimento de óleo diesel (emergencial)",
    "Desentupimento de tubulações / prumadas",
    "Manutenção em cavaletes",
    "Vazamento em tubulações / prumadas",
    "Reposição de água",
    "Controle remoto não funciona",
    "Desentupir dreno",
    "Reparo em compressores",
    "Ar-condicionado – defeito",
    "Falta de água",
    "Outros serviços de limpeza",
]


class AtivoForm(forms.ModelForm):
    class Meta:
        model = Ativo
        fields = [
            "ativo_prisma",
            "nome_site",
            "endereco",
            "cidade",
            "uf",
            "regional",
            "tipo_imovel",
            "lider_coordenacao",
            "tipo_site_sla",
            "ativo",
        ]
        widgets = {
            "ativo_prisma": forms.TextInput(attrs={"class": "form-control"}),
            "nome_site": forms.TextInput(attrs={"class": "form-control"}),
            "endereco": forms.TextInput(attrs={"class": "form-control"}),
            "cidade": forms.TextInput(attrs={"class": "form-control"}),
            "uf": forms.TextInput(attrs={"class": "form-control", "maxlength": "2"}),
            "regional": forms.TextInput(attrs={"class": "form-control"}),
            "tipo_imovel": forms.TextInput(attrs={"class": "form-control"}),
            "lider_coordenacao": forms.TextInput(attrs={"class": "form-control"}),
            "tipo_site_sla": forms.TextInput(attrs={"class": "form-control"}),
            "ativo": forms.CheckboxInput(attrs={"class": "form-check"}),
        }

    def clean_ativo_prisma(self):
        valor = self.cleaned_data.get("ativo_prisma", "")
        return valor.strip()

    def clean_cidade(self):
        valor = self.cleaned_data.get("cidade", "")
        return valor.strip()

    def clean_regional(self):
        valor = self.cleaned_data.get("regional", "")
        return valor.strip()

    def clean_uf(self):
        valor = self.cleaned_data.get("uf", "")
        return valor.strip().upper()


class AtivosImportForm(forms.Form):
    arquivo = forms.FileField(
        label="Arquivo .xlsx",
        required=True,
        widget=forms.FileInput(
            attrs={"class": "form-control", "accept": ".xlsx"}
        ),
    )

    def clean_arquivo(self):
        arquivo = self.cleaned_data["arquivo"]
        if not arquivo.name.lower().endswith(".xlsx"):
            raise forms.ValidationError(
                "Envie uma planilha Excel válida no formato .xlsx."
            )
        if arquivo.size == 0:
            raise forms.ValidationError("O arquivo enviado está vazio.")
        return arquivo


class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = ["nome", "telefone", "email", "empresa", "estados_atendidos", "ativo"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "telefone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "empresa": forms.TextInput(attrs={"class": "form-control"}),
            "estados_atendidos": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "SP, RJ, MG",
                }
            ),
            "ativo": forms.CheckboxInput(attrs={"class": "form-check"}),
        }

    def clean_nome(self):
        return self.cleaned_data.get("nome", "").strip()

    def clean_telefone(self):
        return self.cleaned_data.get("telefone", "").strip()

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        return email.lower()

    def clean_empresa(self):
        return self.cleaned_data.get("empresa", "").strip()

    def clean_estados_atendidos(self):
        valor = self.cleaned_data.get("estados_atendidos", "")
        ufs = [parte.strip().upper() for parte in valor.split(",") if parte.strip()]
        return ", ".join(ufs)


class FornecedoresImportForm(forms.Form):
    arquivo = forms.FileField(
        label="Arquivo .xlsx",
        required=True,
        widget=forms.FileInput(
            attrs={"class": "form-control", "accept": ".xlsx"}
        ),
    )

    def clean_arquivo(self):
        arquivo = self.cleaned_data["arquivo"]
        if not arquivo.name.lower().endswith(".xlsx"):
            raise forms.ValidationError(
                "Envie uma planilha Excel válida no formato .xlsx."
            )
        if arquivo.size == 0:
            raise forms.ValidationError("O arquivo enviado está vazio.")
        return arquivo


class ChamadoForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = [
            "ativo",
            "fornecedor",
            "numero_os",
            "data_abertura",
            "solicitante",
            "contato_solicitante",
            "dados_portaria_retirada_chave",
            "denominacao",
            "acao_tomada",
            "command_center",
            "detalhamento_situacao",
            "status",
        ]
        widgets = {
            "numero_os": forms.TextInput(attrs={"class": "form-control"}),
            "data_abertura": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "solicitante": forms.TextInput(attrs={"class": "form-control"}),
            "contato_solicitante": forms.TextInput(attrs={"class": "form-control"}),
            "dados_portaria_retirada_chave": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
            "denominacao": forms.Select(attrs={"class": "form-control"}),
            "acao_tomada": forms.TextInput(attrs={"class": "form-control"}),
            "command_center": forms.TextInput(attrs={"class": "form-control"}),
            "detalhamento_situacao": forms.Textarea(
                attrs={"class": "form-control", "rows": 8}
            ),
            "status": forms.Select(attrs={"class": "form-control"}),
            "ativo": forms.Select(attrs={"class": "form-control"}),
            "fornecedor": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ativo"].queryset = Ativo.objects.filter(ativo=True)
        self.fields["fornecedor"].queryset = Fornecedor.objects.filter(ativo=True)
        self.fields["fornecedor"].required = False
        self.fields["fornecedor"].empty_label = "---"
        self.fields["status"].choices = StatusChamado.choices
        self.fields["status"].required = False
        # Denominacao: ChoiceField com lista predefinida; aceita o valor
        # existente no banco (caso seja diferente das opcoes) para nao quebrar
        # edicoes de chamados antigos.
        denominacao_choices = [("", "---")] + [(o, o) for o in DENOMINACAO_OPCOES]
        valor_atual = (self.initial.get("denominacao") or "").strip()
        if valor_atual and valor_atual not in DENOMINACAO_OPCOES:
            denominacao_choices.append((valor_atual, valor_atual))
        self.fields["denominacao"] = forms.ChoiceField(
            choices=denominacao_choices,
            required=False,
            label=self.fields["denominacao"].label,
            widget=forms.Select(attrs={"class": "form-control"}),
        )
        if not self.is_bound and not self.initial.get("status"):
            self.initial["status"] = StatusChamado.ABERTO
        if not self.is_bound and not self.initial.get("data_abertura"):
            # Chamado emergencial e sempre aberto "agora" (data/hora atual local).
            self.initial["data_abertura"] = timezone.localtime()
        self.fields["data_abertura"].input_formats = [
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
        ]

    def clean_numero_os(self):
        return self.cleaned_data.get("numero_os", "").strip()

    def clean_status(self):
        valor = self.cleaned_data.get("status") or StatusChamado.ABERTO
        valores_validos = {v for v, _ in StatusChamado.choices}
        if valor not in valores_validos:
            raise forms.ValidationError("Status invalido.")
        return valor


class ObraForm(forms.ModelForm):
    class Meta:
        model = Obra
        fields = [
            "ativo",
            "descricao",
            "data_inicio",
            "data_fim_planejada",
            "data_fim_real",
            "responsavel",
            "observacoes",
            "ativa",
        ]
        widgets = {
            "ativo": forms.Select(attrs={"class": "form-control"}),
            "descricao": forms.Textarea(
                attrs={"class": "form-control", "rows": 3,
                       "placeholder": "Ex.: Reforma do telhado e impermeabilização"}
            ),
            "data_inicio": forms.DateInput(
                attrs={"class": "form-control", "type": "date"},
                format="%Y-%m-%d",
            ),
            "data_fim_planejada": forms.DateInput(
                attrs={"class": "form-control", "type": "date"},
                format="%Y-%m-%d",
            ),
            "data_fim_real": forms.DateInput(
                attrs={"class": "form-control", "type": "date"},
                format="%Y-%m-%d",
            ),
            "responsavel": forms.TextInput(
                attrs={"class": "form-control",
                       "placeholder": "Empresa ou supervisor responsável"}
            ),
            "observacoes": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
            "ativa": forms.CheckboxInput(attrs={"class": "form-check"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ativo"].queryset = Ativo.objects.filter(ativo=True)
        self.fields["data_fim_real"].required = False
        self.fields["responsavel"].required = False
        self.fields["observacoes"].required = False
        for nome in ("data_inicio", "data_fim_planejada", "data_fim_real"):
            self.fields[nome].input_formats = ["%Y-%m-%d", "%d/%m/%Y"]

        dark = (
            "background:rgba(255,255,255,.05);"
            "border:1px solid rgba(255,255,255,.08);"
            "color:#e5e7eb;"
            "border-radius:6px;"
            "padding:7px 10px;"
            "width:100%;"
        )
        for nome in (
            "ativo",
            "descricao",
            "data_inicio",
            "data_fim_planejada",
            "data_fim_real",
            "responsavel",
            "observacoes",
        ):
            self.fields[nome].widget.attrs["style"] = dark

    def clean_descricao(self):
        return self.cleaned_data.get("descricao", "").strip()

    def clean_responsavel(self):
        return self.cleaned_data.get("responsavel", "").strip()

    def clean(self):
        cleaned = super().clean()
        inicio = cleaned.get("data_inicio")
        fim = cleaned.get("data_fim_planejada")
        fim_real = cleaned.get("data_fim_real")
        if inicio and fim and fim < inicio:
            raise forms.ValidationError(
                "A data fim planejada não pode ser anterior à data de início."
            )
        if fim_real and inicio and fim_real < inicio:
            raise forms.ValidationError(
                "A data fim real não pode ser anterior à data de início."
            )
        return cleaned


class ObrasImportForm(forms.Form):
    arquivo = forms.FileField(
        label="Arquivo .xlsx",
        required=True,
        widget=forms.FileInput(
            attrs={"class": "form-control", "accept": ".xlsx"}
        ),
    )

    def clean_arquivo(self):
        arquivo = self.cleaned_data["arquivo"]
        if not arquivo.name.lower().endswith(".xlsx"):
            raise forms.ValidationError(
                "Envie uma planilha Excel válida no formato .xlsx."
            )
        if arquivo.size == 0:
            raise forms.ValidationError("O arquivo enviado está vazio.")
        return arquivo


class RegistrarReportForm(forms.Form):
    STATUS_OPERACIONAIS = [
        (StatusChamado.ABERTO, StatusChamado.ABERTO.label),
        (StatusChamado.PENDENTE, StatusChamado.PENDENTE.label),
        (StatusChamado.CONCLUIDO, StatusChamado.CONCLUIDO.label),
        (StatusChamado.CANCELADO, StatusChamado.CANCELADO.label),
        (StatusChamado.NAO_EMERGENCIAL, StatusChamado.NAO_EMERGENCIAL.label),
    ]

    texto_atualizacao = forms.CharField(
        label="Atualização",
        required=True,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 6}),
    )
    status_resultante = forms.ChoiceField(
        label="Status resultante",
        choices=[("", "---")] + STATUS_OPERACIONAIS,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
