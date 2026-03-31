from django.db import models
from datetime import date


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
