from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from .models import AdministradorTI, Medico, Recepcionista, UsuarioClinica


class ClinicaLoginView(LoginView):
    template_name = "base/login.html"
    redirect_authenticated_user = True


def resolver_perfil_usuario(user: UsuarioClinica) -> UsuarioClinica:
    if user.cargo == UsuarioClinica.TipoCargo.RECEPCIONISTA:
        return Recepcionista.objects.get(pk=user.pk)
    if user.cargo == UsuarioClinica.TipoCargo.MEDICO:
        return Medico.objects.get(pk=user.pk)
    if user.cargo == UsuarioClinica.TipoCargo.TI:
        return AdministradorTI.objects.get(pk=user.pk)
    return user


@login_required
def dashboard_view(request):
    ator = resolver_perfil_usuario(request.user)
    if ator.cargo == UsuarioClinica.TipoCargo.RECEPCIONISTA:
        return redirect("painel_recepcionista")
    if ator.cargo == UsuarioClinica.TipoCargo.MEDICO:
        return redirect("painel_medico")
    if ator.cargo == UsuarioClinica.TipoCargo.TI:
        return redirect("painel_admin_ti")
    messages.error(request, "Perfil sem painel configurado.")
    return redirect("login")


@login_required
def painel_recepcionista_view(request):
    ator = resolver_perfil_usuario(request.user)
    if not ator.validar_acesso("consulta:agendar"):
        return render(request, "error/403.html", status=403)
    return render(request, "usuarios/recepcionista.html", {"ator": ator})


@login_required
def painel_medico_view(request):
    ator = resolver_perfil_usuario(request.user)
    if not ator.validar_acesso("consulta:visualizar"):
        return render(request, "error/403.html", status=403)
    return render(request, "usuarios/medico.html", {"ator": ator})


@login_required
def painel_admin_ti_view(request):
    ator = resolver_perfil_usuario(request.user)
    if not (ator.validar_acesso("sistema:gerenciar") or ator.validar_acesso("auditoria:ler")):
        return render(request, "error/403.html", status=403)
    return render(request, "usuarios/admin_ti.html", {"ator": ator})
