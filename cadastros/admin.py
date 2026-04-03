from django.contrib import admin

from .models import AuditoriaEstoqueValidade, Doacao, Doador, EstoqueItem, EstoqueLote, Familia, Filho, Repasse


class FilhoInline(admin.TabularInline):
    model = Filho
    extra = 0


@admin.register(Familia)
class FamiliaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "lider_familia", "contato", "cidade_estado_nasc_lider", "data_visita")
    list_filter = ("estado_civil", "tem_filhos", "data_visita")
    search_fields = ("codigo", "lider_familia", "cpf_lider", "contato")
    inlines = [FilhoInline]


@admin.register(Doador)
class DoadorAdmin(admin.ModelAdmin):
    list_display = ("nome", "documento", "email", "telefone", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "documento", "email")


@admin.register(Doacao)
class DoacaoAdmin(admin.ModelAdmin):
    list_display = ("id", "categoria", "produto", "descricao", "valor", "data_doacao", "data_validade")
    list_filter = ("categoria", "produto", "data_doacao", "data_validade")
    search_fields = ("descricao",)
    autocomplete_fields = ("registrada_por",)


@admin.register(Repasse)
class RepasseAdmin(admin.ModelAdmin):
    list_display = ("id", "familia", "categoria", "produto", "status", "valor_estimado", "data_repasse")
    list_filter = ("status", "categoria", "produto", "data_repasse")
    search_fields = ("familia__lider_familia", "descricao")
    autocomplete_fields = ("familia", "doacao", "responsavel")


@admin.register(EstoqueItem)
class EstoqueItemAdmin(admin.ModelAdmin):
    list_display = ("produto", "quantidade", "unidade", "atualizado_em")
    list_filter = ("produto",)
    search_fields = ("produto",)


@admin.register(EstoqueLote)
class EstoqueLoteAdmin(admin.ModelAdmin):
    list_display = ("produto", "quantidade", "unidade", "data_validade", "atualizado_em")
    list_filter = ("produto", "data_validade")
    search_fields = ("produto", "doacao__descricao")


@admin.register(AuditoriaEstoqueValidade)
class AuditoriaEstoqueValidadeAdmin(admin.ModelAdmin):
    list_display = ("evento", "produto", "data_validade", "usuario", "criado_em")
    list_filter = ("evento", "produto", "data_validade", "criado_em")
    search_fields = ("mensagem", "usuario__username")
