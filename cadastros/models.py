from datetime import date

from django.conf import settings
from django.db import models


class Doador(models.Model):
    nome = models.CharField(max_length=120)
    documento = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Doacao(models.Model):
    class Categoria(models.TextChoices):
        FINANCEIRA = "financeira", "Financeira"
        ALIMENTOS = "alimentos", "Alimentos"
        VESTUARIO = "vestuario", "Vestuário"
        HIGIENE = "higiene", "Higiene"
        MATERIAL_ESCOLAR = "material_escolar", "Material Escolar"
        OUTROS = "outros", "Outros"

    doador = models.ForeignKey(
        Doador,
        on_delete=models.SET_NULL,
        related_name="doacoes",
        null=True,
        blank=True,
    )
    categoria = models.CharField(
        max_length=30,
        choices=Categoria.choices,
        default=Categoria.FINANCEIRA,
    )
    descricao = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantidade = models.PositiveIntegerField(default=1)
    unidade = models.CharField(max_length=30, blank=True, default="")
    data_doacao = models.DateField(default=date.today)
    observacoes = models.TextField(blank=True, default="")
    registrada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="doacoes_registradas",
        null=True,
        blank=True,
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data_doacao", "-id"]

    def __str__(self):
        return f"{self.get_categoria_display()} - {self.descricao}"


class Familia(models.Model):
    codigo = models.AutoField(primary_key=True)
    lider_familia = models.CharField(max_length=100, null=False, blank=False)
    dt_nasc_lider = models.DateField(null=False, blank=False)
    cidade_estado_nasc_lider = models.CharField(max_length=100, null=True, blank=True)
    profissao_lider = models.CharField(max_length=100, null=True, blank=True)
    escolaridade_lider = models.CharField(max_length=100, null=True, blank=True)
    cpf_lider = models.CharField(max_length=14, null=True, blank=True)
    rg_lider = models.CharField(max_length=20, null=True, blank=True)
    conjuge = models.CharField(max_length=100, blank=True, null=True)
    dt_nasc_conjuge = models.DateField(blank=True, null=True)
    cidade_estado_nasc_conjuge = models.CharField(max_length=100, blank=True, null=True)
    profissao_conjuge = models.CharField(max_length=100, blank=True, null=True)
    escolaridade_conjuge = models.CharField(max_length=100, blank=True, null=True)
    cpf_conjuge = models.CharField(max_length=14, blank=True, null=True)
    rg_conjuge = models.CharField(max_length=20, blank=True, null=True)
    estado_civil_choices = [
        ("solteiro", "Solteiro"),
        ("casado", "Casado"),
        ("religioso", "Religioso"),
        ("viuvo", "Viúvo"),
        ("uniaoEstavel", "União Estável"),
    ]

    estado_civil = models.CharField(
        max_length=15,
        choices=estado_civil_choices,
        default="solteiro",
        null=True,
        blank=True,
    )

    religiao = models.CharField(max_length=100, null=True, blank=True)
    bolsa_familia = models.BooleanField(default=False)
    outro_beneficio = models.BooleanField(default=False)
    renda_familiar = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0, blank=True, null=True
    )
    tempo_bairro = models.CharField(max_length=100, null=True, blank=True)
    tempo_cidade = models.CharField(max_length=100, null=True, blank=True)
    residencia = models.CharField(max_length=20, null=True, blank=True)
    qt_dependentes = models.IntegerField(blank=True, null=True, default=0)
    tem_filhos = models.BooleanField(default=False)
    qt_filhos = models.IntegerField(blank=True, null=True, default=0)
    carteira_vacinacao = models.BooleanField(default=True)
    doenca_cronica = models.CharField(max_length=100, blank=True, null=True)
    qt_outros_moradores = models.IntegerField(blank=True, null=True, default=0)
    contato = models.CharField(max_length=100, null=True, blank=True)
    endereco = models.CharField(max_length=200, null=True, blank=True)
    tel_fixo = models.CharField(max_length=15, blank=True, null=True)
    celular = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    observacoes = models.CharField(max_length=1000, default="", null=True, blank=True)
    data_visita = models.DateField(default=date.today, blank=True, null=True)
    responsavel_visita = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.lider_familia


class Filho(models.Model):
    familia = models.ForeignKey(
        Familia, related_name="filhos", on_delete=models.CASCADE
    )
    nome = models.CharField(max_length=100, null=True, blank=True)
    dt_nasc_filho = models.DateField(null=True, blank=True)
    escola = models.CharField(max_length=100, blank=True, null=True)
    serie = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.nome} ({self.familia.lider_familia})"


class Repasse(models.Model):
    class Status(models.TextChoices):
        PLANEJADO = "planejado", "Planejado"
        ENTREGUE = "entregue", "Entregue"
        CANCELADO = "cancelado", "Cancelado"

    familia = models.ForeignKey(
        Familia,
        on_delete=models.PROTECT,
        related_name="repasses",
    )
    doacao = models.ForeignKey(
        Doacao,
        on_delete=models.SET_NULL,
        related_name="repasses",
        null=True,
        blank=True,
    )
    categoria = models.CharField(
        max_length=30,
        choices=Doacao.Categoria.choices,
        default=Doacao.Categoria.FINANCEIRA,
    )
    descricao = models.CharField(max_length=255)
    valor_estimado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    quantidade = models.PositiveIntegerField(default=1)
    unidade = models.CharField(max_length=30, blank=True, default="")
    data_repasse = models.DateField(default=date.today)
    observacoes = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ENTREGUE,
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="repasses_registrados",
        null=True,
        blank=True,
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data_repasse", "-id"]

    def __str__(self):
        return f"Repasse #{self.id} - {self.familia.lider_familia}"
