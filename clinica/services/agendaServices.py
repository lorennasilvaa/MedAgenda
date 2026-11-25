from pathlib import Path
from datetime import datetime
from django.utils import timezone
from ..models import (
    UsuarioClinica,
    Medico,
    Paciente,
    Consulta,
    StatusConsulta,
)
from .services import AuditoriaService


class AgendaService:
    """
    Camada de serviço responsável pelas regras operacionais de agendamento,
    cancelamento e consulta da agenda médica com controle RBAC.
    """
    
    def __init__(self, auditoria_service=None, caminho_log: str = "logs.log"):
        self.auditoria = auditoria_service or AuditoriaService()
        self.caminho_log = Path(caminho_log)

    def _exigir_permissao(self, ator: UsuarioClinica, permissao: str, acao_descrita: str) -> None:
        if not ator or not ator.validar_acesso(permissao):
            self.auditoria.registrar_log(
                evento=f"ACESSO NEGADO ({permissao}) ao tentar: {acao_descrita}",
                usuario=ator,
            )
            raise PermissionError(
                f"O usuário não possui a permissão '{permissao}' para {acao_descrita}."
            )
        
    def _resolver_medico(self, usuario: UsuarioClinica | Medico) -> Medico:
        if isinstance(usuario, Medico):
            return usuario
        if usuario.cargo == UsuarioClinica.TipoCargo.MEDICO:
            return Medico.objects.get(pk=usuario.pk)
        raise ValueError("O usuário informado não possui perfil de médico.")

    def cadastrar_paciente(
        self,
        usuario: UsuarioClinica,
        nomePaciente: str,
        cpf: str,
        telefone: str
    ) -> Paciente:
        if not usuario.validar_acesso("paciente:cadastrar"):
            raise PermissionError("O usuário não possui permissão para cadastrar pacientes.")

        conflito = Paciente.objects.filter(
                nome=nomePaciente,
                cpf=cpf,
                telefone=telefone
            ).exists()
        if conflito:
            raise ValueError("O paciente já está cadastrado.")

        paciente = Paciente.cadastrar_paciente(nome=nomePaciente, cpf=cpf, telefone=telefone)

        return paciente

    def agendar_consulta(
        self,
        usuario: UsuarioClinica,
        paciente: Paciente,
        medico: UsuarioClinica | Medico,
        data_hora: datetime,
        observacoes_recepcao: str | None = None,
    ) -> Consulta:
        if not usuario.validar_acesso("consulta:agendar"):
            raise PermissionError("O usuário não possui permissão para agendar consultas.")

        if data_hora <= timezone.now():
            raise ValueError("Não é possível agendar consultas em datas ou horários passados.")

        medico_obj = self._resolver_medico(medico)

        conflito = Consulta.objects.filter(
            medico=medico_obj,
            data_hora=data_hora,
            status=StatusConsulta.AGENDADA,
        ).exists()
        if conflito:
            raise ValueError("O médico já possui uma consulta agendada neste horário.")

        consulta = Consulta(
            paciente=paciente,
            medico=medico_obj,
            data_hora=data_hora,
            observacoes_recepcao=observacoes_recepcao,
            status=StatusConsulta.AGENDADA,
        )
        consulta.save()
        return consulta

    def cancelar_consulta(
        self,
        usuario: UsuarioClinica,
        consulta: Consulta,
        motivo: str = "",
    ) -> Consulta:
        if not usuario.validar_acesso("consulta:agendar"):
            raise PermissionError("O usuário não possui permissão para cancelar consultas.")

        if consulta.status == StatusConsulta.REALIZADA:
            raise ValueError("Não é possível cancelar uma consulta já realizada.")

        consulta.cancelar(usuario=usuario, motivo=motivo)
        return consulta

    def listar_agenda_medico(
        self,
        usuario: UsuarioClinica,
        medico: UsuarioClinica | Medico,
    ):
        if not (
            usuario.validar_acesso("consulta:visualizar")
            or usuario.validar_acesso("consulta:agendar")
        ):
            raise PermissionError("O usuário não possui permissão para visualizar a agenda.")

        medico_obj = self._resolver_medico(medico)
        return Consulta.objects.filter(medico=medico_obj).order_by("data_hora")

    def concluir_atendimento(
        self,
        usuario: UsuarioClinica,
        consulta: Consulta,
        diagnostico: str,
        prescricao: str,
    ) -> Consulta:
        if not usuario.validar_acesso("prontuario:escrever"):
            raise PermissionError("O usuário não possui permissão para escrever no prontuário.")
        
        medico_obj = self._resolver_medico(usuario)

        if consulta.medico_id != medico_obj.pk:
            raise PermissionError("Apenas o médico responsável pela consulta pode finalizá-la.")

        consulta.finalizar_atendimento(
            medico=medico_obj,
            diagnostico=diagnostico,
            prescricao=prescricao,
        )
        return consulta