from datetime import datetime
from django.utils import timezone
from ..models import (
    UsuarioClinica,
    Medico,
    Paciente,
    Consulta,
    StatusConsulta,
)


class AgendaService:
    """
    Camada de serviço responsável pelas regras operacionais de agendamento,
    cancelamento e consulta da agenda médica com controle RBAC.
    """

    @staticmethod
    def _resolver_medico(usuario: UsuarioClinica) -> Medico:
        if isinstance(usuario, Medico):
            return usuario
        if usuario.cargo == UsuarioClinica.TipoCargo.MEDICO:
            return Medico.objects.get(pk=usuario.pk)
        raise ValueError("O usuário informado não possui perfil de médico.")

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def concluir_atendimento(
        self,
        usuario: UsuarioClinica,
        consulta: Consulta,
        diagnostico: str,
        prescricao: str,
    ) -> Consulta:
        medico_obj = self._resolver_medico(usuario)

        if consulta.medico_id != medico_obj.pk:
            raise PermissionError("Apenas o médico responsável pela consulta pode finalizá-la.")

        consulta.finalizar_atendimento(
            medico=medico_obj,
            diagnostico=diagnostico,
            prescricao=prescricao,
        )
        return consulta