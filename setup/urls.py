from django.contrib import admin
from django.urls import path
from cadastros import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("login/", views.login, name="login"),
    path("perfil/", views.perfil, name="perfil"),
    path(
        "cadastro_funcionario/", views.cadastro_funcionario, name="cadastro_funcionario"
    ),
    path("cadastrar_familia/", views.cadastrar_familia, name="cadastrar_familia"),
    path("alterar_cadastro/", views.alterar_cadastro, name="alterar_cadastro"),
    path("buscar_cadastro/", views.buscar_cadastro, name="buscar_cadastro"),
    path("buscar_cadastro_ajax/", views.buscar_cadastro_ajax, name="buscar_cadastro_ajax"),
    path("doacoes/", views.doacoes, name="doacoes"),
    path("repasses/", views.repasses, name="repasses"),
    path("nossa_historia/", views.nossa_historia, name="nossa_historia"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
]
