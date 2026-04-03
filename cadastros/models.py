from datetime import date, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction


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

    class Produto(models.TextChoices):
        NAO_APLICAVEL = "nao_aplicavel", "Não se aplica"
        CESTA_BASICA = "cesta_basica", "Cesta básica"
        FEIJAO = "feijao", "Feijão"
        ARROZ = "arroz", "Arroz"
        OLEO = "oleo", "Óleo"
        BRINQUEDOS = "brinquedos", "Brinquedos"
        FRALDAS = "fraldas", "Fraldas"
        LEITE = "leite", "Leite"
        ROUPAS = "roupas", "Roupas"
        HIGIENE = "higiene", "Itens de higiene"
        MATERIAL_ESCOLAR = "material_escolar", "Material escolar"
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
    produto = models.CharField(
        max_length=30,
        choices=Produto.choices,
        default=Produto.NAO_APLICAVEL,
    )
    descricao = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantidade = models.PositiveIntegerField(default=1)
    unidade = models.CharField(max_length=30, blank=True, default="")
    data_doacao = models.DateField(default=date.today)
    data_validade = models.DateField(null=True, blank=True)
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

    @classmethod
    def produtos_pereciveis(cls):
        return {
            cls.Produto.CESTA_BASICA,
            cls.Produto.FEIJAO,
            cls.Produto.ARROZ,
            cls.Produto.OLEO,
            cls.Produto.LEITE,
        }

    @classmethod
    def is_produto_perecivel(cls, produto):
        return produto in cls.produtos_pereciveis()


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
    produto = models.CharField(
        max_length=30,
        choices=Doacao.Produto.choices,
        default=Doacao.Produto.NAO_APLICAVEL,
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


class EstoqueItem(models.Model):
    produto = models.CharField(
        max_length=30,
        choices=Doacao.Produto.choices,
        unique=True,
    )
    quantidade = models.PositiveIntegerField(default=0)
    unidade = models.CharField(max_length=30, blank=True, default="un")
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["produto"]

    def __str__(self):
        return f"{self.get_produto_display()} ({self.quantidade} {self.unidade})"

    @classmethod
    def produtos_controlados(cls):
        return [
            (codigo, nome)
            for codigo, nome in Doacao.Produto.choices
            if codigo != Doacao.Produto.NAO_APLICAVEL
        ]

    @classmethod
    def registrar_entrada(cls, produto, quantidade, unidade="un", data_validade=None, doacao=None):
        if not produto or produto == Doacao.Produto.NAO_APLICAVEL:
            return None
        if quantidade <= 0:
            return None
        if Doacao.is_produto_perecivel(produto) and not data_validade:
            nome_produto = dict(Doacao.Produto.choices).get(produto, produto)
            raise ValidationError(f"Informe a data de validade para o produto perecível {nome_produto}.")
        if not Doacao.is_produto_perecivel(produto):
            data_validade = None

        with transaction.atomic():
            item, _ = cls.objects.select_for_update().get_or_create(
                produto=produto,
                defaults={"unidade": unidade or "un", "quantidade": 0},
            )
            if unidade and item.unidade and item.unidade != unidade and item.quantidade > 0:
                nome_produto = dict(Doacao.Produto.choices).get(produto, produto)
                raise ValidationError(
                    f"O produto {nome_produto} já está controlado em {item.unidade}. "
                    f"Use a mesma unidade no lançamento."
                )

            item.quantidade += quantidade
            if unidade and not item.unidade:
                item.unidade = unidade
            item.save(update_fields=["quantidade", "unidade", "atualizado_em"])

            if Doacao.is_produto_perecivel(produto):
                lote, _ = EstoqueLote.objects.select_for_update().get_or_create(
                    produto=produto,
                    unidade=item.unidade or unidade or "un",
                    data_validade=data_validade,
                    defaults={"quantidade": 0, "doacao": doacao},
                )
                lote.quantidade += quantidade
                if doacao and not lote.doacao:
                    lote.doacao = doacao
                lote.save(update_fields=["quantidade", "doacao", "atualizado_em"])
            return item

    @classmethod
    def registrar_saida(cls, produto, quantidade, unidade="un", permitir_vencido=False):
        if not produto or produto == Doacao.Produto.NAO_APLICAVEL:
            return None
        if quantidade <= 0:
            return None

        with transaction.atomic():
            item, _ = cls.objects.select_for_update().get_or_create(
                produto=produto,
                defaults={"unidade": unidade or "un", "quantidade": 0},
            )
            if unidade and item.unidade and item.unidade != unidade:
                nome_produto = dict(Doacao.Produto.choices).get(produto, produto)
                raise ValidationError(
                    f"O produto {nome_produto} está controlado em {item.unidade}. "
                    f"Use a mesma unidade no repasse."
                )

            if item.quantidade < quantidade:
                nome_produto = dict(Doacao.Produto.choices).get(produto, produto)
                raise ValidationError(
                    f"Estoque insuficiente para {nome_produto}. Disponível: {item.quantidade}."
                )

            if Doacao.is_produto_perecivel(produto):
                if not permitir_vencido and EstoqueLote.existe_vencido(produto):
                    raise ValidationError("Você está doando produto vencido.")

                restante = quantidade
                lotes = (
                    EstoqueLote.objects.select_for_update()
                    .filter(produto=produto, quantidade__gt=0)
                    .order_by("data_validade", "id")
                )
                for lote in lotes:
                    if restante <= 0:
                        break
                    consumo = min(restante, lote.quantidade)
                    lote.quantidade -= consumo
                    lote.save(update_fields=["quantidade", "atualizado_em"])
                    restante -= consumo

                if restante > 0:
                    nome_produto = dict(Doacao.Produto.choices).get(produto, produto)
                    raise ValidationError(
                        f"Estoque insuficiente para {nome_produto}. Disponível: {item.quantidade}."
                    )

            item.quantidade -= quantidade
            if unidade and not item.unidade:
                item.unidade = unidade
            item.save(update_fields=["quantidade", "unidade", "atualizado_em"])
            return item


class EstoqueLote(models.Model):
    produto = models.CharField(max_length=30, choices=Doacao.Produto.choices)
    quantidade = models.PositiveIntegerField(default=0)
    unidade = models.CharField(max_length=30, blank=True, default="un")
    data_validade = models.DateField()
    doacao = models.ForeignKey(
        Doacao,
        on_delete=models.SET_NULL,
        related_name="lotes_estoque",
        null=True,
        blank=True,
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["data_validade", "produto", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["produto", "unidade", "data_validade"],
                name="unique_lote_estoque_produto_unidade_validade",
            )
        ]

    def __str__(self):
        return f"{self.get_produto_display()} - {self.quantidade} {self.unidade} (val. {self.data_validade:%d/%m/%Y})"

    @property
    def descricao_alerta(self):
        if self.doacao and self.doacao.descricao:
            return self.doacao.descricao
        return self.get_produto_display()

    @property
    def dias_para_vencer(self):
        return (self.data_validade - date.today()).days

    @classmethod
    def lotes_ativos(cls):
        return cls.objects.filter(quantidade__gt=0)

    @classmethod
    def existe_vencido(cls, produto, referencia=None):
        referencia = referencia or date.today()
        return cls.lotes_ativos().filter(produto=produto, data_validade__lt=referencia).exists()

    @classmethod
    def alertas(cls, referencia=None, janela_dias=30):
        referencia = referencia or date.today()
        limite = referencia + timedelta(days=janela_dias)
        base = cls.lotes_ativos().filter(produto__in=Doacao.produtos_pereciveis()).select_related("doacao")
        proximos = list(
            base.filter(data_validade__gte=referencia, data_validade__lte=limite).order_by(
                "data_validade",
                "produto",
                "id",
            )
        )
        vencidos = list(base.filter(data_validade__lt=referencia).order_by("data_validade", "produto", "id"))
        return {"proximos": proximos, "vencidos": vencidos, "referencia": referencia}


class AuditoriaEstoqueValidade(models.Model):
    class Evento(models.TextChoices):
        BLOQUEIO_DOACAO_VENCIDO = "bloqueio_doacao_vencido", "Bloqueio de doação vencida"
        REAUTENTICACAO_FALHA = "reauth_falha", "Reautenticação falhou"
        REAUTENTICACAO_SUCESSO = "reauth_sucesso", "Reautenticação com sucesso"
        REPASSE_VENCIDO_CONFIRMADO = "repasse_vencido_confirmado", "Repasse vencido confirmado"
        ALERTA_EMAIL_ENVIADO = "alerta_email_enviado", "Alerta de validade por e-mail enviado"
        ALERTA_EMAIL_ERRO = "alerta_email_erro", "Erro ao enviar alerta de validade por e-mail"

    evento = models.CharField(max_length=40, choices=Evento.choices)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="auditorias_validade",
        null=True,
        blank=True,
    )
    produto = models.CharField(max_length=30, choices=Doacao.Produto.choices, blank=True, default="")
    data_validade = models.DateField(null=True, blank=True)
    mensagem = models.CharField(max_length=255)
    detalhes = models.JSONField(blank=True, default=dict)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em", "-id"]

    def __str__(self):
        return f"[{self.get_evento_display()}] {self.mensagem}"

    @classmethod
    def registrar(
        cls,
        *,
        evento,
        mensagem,
        usuario=None,
        produto="",
        data_validade=None,
        detalhes=None,
    ):
        return cls.objects.create(
            evento=evento,
            usuario=usuario,
            produto=produto,
            data_validade=data_validade,
            mensagem=mensagem,
            detalhes=detalhes or {},
        )
