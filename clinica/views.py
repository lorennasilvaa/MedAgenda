from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from .models import AdministradorTI, Medico, Recepcionista, UsuarioClinica, Paciente, Consulta, Prontuario


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

    if request.method == 'POST':
        acao = request.POST.get('acao')
        
        try:
            if acao == 'cadastrar_paciente':
                nome = request.POST.get('nome')
                cpf = request.POST.get('cpf')
                telefone = request.POST.get('telefone')
                
                # utiliza o método estático do model Paciente
                Paciente.cadastrar_paciente(nome=nome, cpf=cpf, telefone=telefone)
                messages.success(request, "Paciente cadastrado com sucesso!")

            elif acao == 'agendar_consulta':
                paciente_id = request.POST.get('paciente_id')
                medico_id = request.POST.get('medico_id')
                data_hora = request.POST.get('data_hora')
                observacoes = request.POST.get('observacoes_recepcao')
                
                paciente = Paciente.objects.get(pk=paciente_id)
                medico = Medico.objects.get(pk=medico_id)
                
                nova_consulta = Consulta(
                    paciente=paciente,
                    medico=medico,
                    data_hora=data_hora,
                    observacoes_recepcao=observacoes
                )
                # utiliza o método do model Consulta passando o ator logado
                nova_consulta.agendar(usuario=ator)
                messages.success(request, "Consulta agendada com sucesso!")

            elif acao == 'cancelar_consulta':
                consulta_id = request.POST.get('consulta_id')
                motivo = request.POST.get('motivo')
                
                consulta = Consulta.objects.get(pk=consulta_id)

                consulta.cancelar(usuario=ator, motivo=motivo)
                messages.success(request, "Consulta cancelada com sucesso!")

        except Exception as e:
            messages.error(request, f"Erro ao realizar a operação: {e}")
            
        return redirect('painel_recepcionista')

    # carregando dados para exibir no template
    consultas = Consulta.objects.select_related("paciente", "medico").order_by("-data_hora")
    pacientes = Paciente.objects.all().order_by("nome")
    medicos = Medico.objects.filter(cargo=UsuarioClinica.TipoCargo.MEDICO).order_by("nome")

    context = {
        "ator": ator,
        "consultas": consultas,
        "pacientes": pacientes,
        "medicos": medicos,
    }
    return render(request, "usuarios/recepcionista.html", context)


@login_required
def painel_medico_view(request):
    ator = resolver_perfil_usuario(request.user)
    if not ator.validar_acesso("consulta:visualizar"):
        return render(request, "error/403.html", status=403)

    if request.method == 'POST':
        acao = request.POST.get('acao')
        
        try:
            if acao == 'finalizar_atendimento':
                consulta_id = request.POST.get('consulta_id')
                diagnostico = request.POST.get('diagnostico')
                prescricao = request.POST.get('prescricao')
                
                # garante que a consulta pertence ao médico logado
                consulta = Consulta.objects.get(pk=consulta_id, medico=ator)
                
                # chama o método do model Consulta que atualiza o status e o prontuário
                consulta.finalizar_atendimento(
                    medico=ator,
                    diagnostico=diagnostico,
                    prescricao=prescricao
                )
                messages.success(request, "Atendimento finalizado e prontuário atualizado com sucesso!")

            elif acao == 'adicionar_alergia':
                prontuario_id = request.POST.get('prontuario_id')
                alergia = request.POST.get('alergia')
                
                prontuario = Prontuario.objects.get(pk=prontuario_id)
                # chama o método do model Prontuario validando permissão
                prontuario.adicionar_alergia(usuario=ator, alergia=alergia)
                messages.success(request, f"Alergia '{alergia}' adicionada com sucesso.")

        except Exception as e:
            messages.error(request, f"Erro ao processar a solicitação: {e}")
            
        return redirect('painel_medico')

    # filtra apenas as consultas destinadas ao médico atual
    consultas = Consulta.objects.filter(medico=ator).select_related("paciente", "paciente__prontuario").order_by("-data_hora")

    context = {
        "ator": ator,
        "consultas": consultas,
    }
    return render(request, "usuarios/medico.html", context)


@login_required
def painel_admin_ti_view(request):
    ator = resolver_perfil_usuario(request.user)
    if not (ator.validar_acesso("sistema:gerenciar") or ator.validar_acesso("auditoria:ler")):
        return render(request, "error/403.html", status=403)
    return render(request, "usuarios/admin_ti.html", {"ator": ator})
