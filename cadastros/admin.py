from django.contrib import admin

from .models import Doacao, Doador, Familia, Filho, Repasse


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
    list_display = ("id", "categoria", "descricao", "doador", "valor", "data_doacao")
    list_filter = ("categoria", "data_doacao")
    search_fields = ("descricao", "doador__nome")
    autocomplete_fields = ("doador", "registrada_por")


@admin.register(Repasse)
class RepasseAdmin(admin.ModelAdmin):
    list_display = ("id", "familia", "categoria", "status", "valor_estimado", "data_repasse")
    list_filter = ("status", "categoria", "data_repasse")
    search_fields = ("familia__lider_familia", "descricao")
    autocomplete_fields = ("familia", "doacao", "responsavel")
