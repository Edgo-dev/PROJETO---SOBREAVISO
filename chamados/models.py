"""Models do app chamados.

Modelagem minima de dominio: Fornecedor, Ativo, Chamado, AtualizacaoChamado.
Status e historico de Report sao representados por TextChoices e por
AtualizacaoChamado, respectivamente, sem tabelas auxiliares.
"""

from django.conf import settings
from django.db import models


class StatusChamado(models.TextChoices):
    ABERTO = "aberto", "Aberto"
    PENDENTE = "pendente", "Pendente"
    CONCLUIDO = "concluido", "Concluído"
    CANCELADO = "cancelado", "Cancelado"
    NAO_EMERGENCIAL = "nao_emergencial", "Não emergencial"


class TipoEventoAtualizacao(models.TextChoices):
    ABERTURA_EMERGENCIAL = "abertura_emergencial", "Abertura emergencial"
    ATUALIZACAO_STATUS = "atualizacao_status", "Atualização de status"
    COMENTARIO = "comentario", "Comentário"


class Fornecedor(models.Model):
    nome = models.CharField(max_length=150, unique=True)
    contato = models.CharField(max_length=120, blank=True)
    telefone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    empresa = models.CharField(max_length=150, blank=True)
    estados_atendidos = models.CharField(
        max_length=255,
        blank=True,
        help_text="UFs separadas por vírgula, ex.: SP, RJ, MG",
    )
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"

    def __str__(self):
        return self.nome

    @property
    def estados_atendidos_list(self):
        if not self.estados_atendidos:
            return []
        return [uf.strip().upper() for uf in self.estados_atendidos.split(",") if uf.strip()]

    @property
    def inicial(self):
        return (self.nome[:1] or "?").upper()


class Ativo(models.Model):
    ativo_prisma = models.CharField(max_length=80, unique=True)
    nome_site = models.CharField(max_length=200)
    endereco = models.CharField(max_length=255)
    cidade = models.CharField(max_length=120)
    uf = models.CharField(max_length=2)
    regional = models.CharField(max_length=120)
    tipo_imovel = models.CharField(max_length=80, blank=True)
    lider_coordenacao = models.CharField(max_length=120, blank=True)
    tipo_site_sla = models.CharField(max_length=80, blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["regional", "cidade", "nome_site"]
        verbose_name = "Ativo"
        verbose_name_plural = "Ativos"
        indexes = [
            models.Index(fields=["ativo_prisma"]),
            models.Index(fields=["cidade"]),
            models.Index(fields=["regional"]),
            models.Index(fields=["nome_site"]),
        ]

    def __str__(self):
        return f"{self.ativo_prisma} - {self.nome_site}"


class Chamado(models.Model):
    Status = StatusChamado

    ativo = models.ForeignKey(
        Ativo,
        on_delete=models.PROTECT,
        related_name="chamados",
    )
    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chamados",
    )
    numero_os = models.CharField(max_length=80, unique=True)
    data_abertura = models.DateTimeField()
    solicitante = models.CharField(max_length=120, blank=True)
    contato_solicitante = models.CharField(max_length=80, blank=True)
    dados_portaria_retirada_chave = models.TextField(blank=True)
    denominacao = models.CharField(max_length=120, blank=True)
    acao_tomada = models.CharField(max_length=160, blank=True)
    command_center = models.CharField(max_length=120, blank=True)
    detalhamento_situacao = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=StatusChamado.choices,
        default=StatusChamado.ABERTO,
    )
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chamados_criados",
    )
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chamados_atualizados",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-data_abertura", "-criado_em"]
        verbose_name = "Chamado"
        verbose_name_plural = "Chamados"
        indexes = [
            models.Index(fields=["numero_os"]),
            models.Index(fields=["data_abertura"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"OS {self.numero_os} - {self.ativo.nome_site}"


class AtualizacaoChamado(models.Model):
    TipoEvento = TipoEventoAtualizacao
    StatusResultante = StatusChamado

    chamado = models.ForeignKey(
        Chamado,
        on_delete=models.CASCADE,
        related_name="atualizacoes",
    )
    tipo_evento = models.CharField(
        max_length=30,
        choices=TipoEventoAtualizacao.choices,
        default=TipoEventoAtualizacao.COMENTARIO,
    )
    texto_atualizacao = models.TextField()
    status_resultante = models.CharField(
        max_length=20,
        choices=StatusChamado.choices,
        default=StatusChamado.PENDENTE,
    )
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="atualizacoes_chamados",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["criado_em"]
        verbose_name = "Atualização de chamado"
        verbose_name_plural = "Atualizações de chamados"
        indexes = [
            models.Index(fields=["chamado"]),
            models.Index(fields=["tipo_evento"]),
            models.Index(fields=["status_resultante"]),
            models.Index(fields=["criado_em"]),
        ]

    def __str__(self):
        return f"{self.chamado.numero_os} - {self.get_tipo_evento_display()}"


class Obra(models.Model):
    """Obra/reforma em andamento em um Ativo do parque imobiliário.

    Permite que ao abrir um chamado emergencial o sistema avise quando o
    endereço já está sendo tratado por uma obra em curso, evitando
    duplicação de esforços.
    """

    ativo = models.ForeignKey(
        Ativo,
        on_delete=models.PROTECT,
        related_name="obras",
    )
    descricao = models.TextField(help_text="O que está sendo feito na obra.")
    data_inicio = models.DateField()
    data_fim_planejada = models.DateField()
    data_fim_real = models.DateField(null=True, blank=True)
    responsavel = models.CharField(max_length=150, blank=True)
    observacoes = models.TextField(blank=True)
    ativa = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-data_inicio", "ativo__nome_site"]
        verbose_name = "Obra"
        verbose_name_plural = "Obras"
        indexes = [
            models.Index(fields=["ativo"]),
            models.Index(fields=["data_inicio"]),
            models.Index(fields=["data_fim_planejada"]),
            models.Index(fields=["ativa"]),
        ]

    def __str__(self):
        return f"Obra em {self.ativo.nome_site} ({self.data_inicio:%d/%m/%Y})"

    @property
    def esta_em_andamento(self) -> bool:
        from datetime import date
        hoje = date.today()
        if not self.ativa or self.data_fim_real is not None:
            return False
        return self.data_inicio <= hoje <= self.data_fim_planejada

    @property
    def esta_atrasada(self) -> bool:
        from datetime import date
        if not self.ativa or self.data_fim_real is not None:
            return False
        return date.today() > self.data_fim_planejada

    @property
    def situacao(self) -> str:
        from datetime import date
        if self.data_fim_real is not None:
            return "concluida"
        if not self.ativa:
            return "inativa"
        hoje = date.today()
        if hoje < self.data_inicio:
            return "planejada"
        if hoje > self.data_fim_planejada:
            return "atrasada"
        return "em_andamento"

    @property
    def situacao_label(self) -> str:
        labels = {
            "concluida": "Concluída",
            "inativa": "Inativa",
            "planejada": "Planejada",
            "atrasada": "Atrasada",
            "em_andamento": "Em andamento",
        }
        return labels.get(self.situacao, self.situacao)
