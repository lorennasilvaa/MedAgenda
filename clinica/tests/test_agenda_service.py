from django.test import TestCase
from django.utils import timezone
from ..models import (
    Medico, Recepcionista, Paciente, Prontuario, Consulta, StatusConsulta, 
    UsuarioClinica
)
from ..services.agendaServices import AgendaService

class AgendaServiceTestCase(TestCase):
  def setUp(self):
    self.medico = Medico.objects.create_user(
        username="drhouse",
        password="password123",
        nome="Dr. House",
        cpf="111.111.111-11",
        crm="12345-SP"
    )

    self.recepcionista = Recepcionista.objects.create_user(
        username="carmem",
        password="password123",
        nome="Carmem Recepção",
        cpf="222.222.222-22"
    )

    self.usuario_base = UsuarioClinica.objects.create_user(
        username="base_user",
        password="123",
        nome="Usuário Base",
        cpf="444.444.444-44",
    )

    self.prontuario = Prontuario.objects.create()
    self.paciente = Paciente.objects.create(
        nome="Carlos Silva",
        cpf="333.333.333-33",
        telefone="(11) 98888-7777",
        prontuario=self.prontuario
    )

    self.agenda_service = AgendaService()

  def test_agendar_consulta_com_sucesso(self):
    data_hora = timezone.now() + timezone.timedelta(days=1)

    consulta = self.agenda_service.agendar_consulta(
        usuario=self.recepcionista,
        paciente=self.paciente,
        medico=self.medico,
        data_hora=data_hora,
        observacoes_recepcao="Paciente com diabetes."
    )

    self.assertEqual(consulta.status, StatusConsulta.AGENDADA)
    self.assertEqual(consulta.paciente, self.paciente)
    self.assertEqual(consulta.medico, self.medico)
    self.assertEqual(consulta.data_hora, data_hora)
    self.assertEqual(consulta.observacoes_recepcao, "Paciente com diabetes.")

  def test_agendar_consulta_sem_permissao(self):
    data_hora = timezone.now() + timezone.timedelta(days=1)

    with self.assertRaises(PermissionError):
        self.agenda_service.agendar_consulta(
            usuario=self.usuario_base,
            paciente=self.paciente,
            medico=self.medico,
            data_hora=data_hora,
            observacoes_recepcao="Paciente com diabetes."
        )

  def test_agendar_consulta_em_horario_passado(self):
    data_hora = timezone.now() - timezone.timedelta(days=1)

    with self.assertRaises(ValueError):
        self.agenda_service.agendar_consulta(
            usuario=self.recepcionista,
            paciente=self.paciente,
            medico=self.medico,
            data_hora=data_hora,
            observacoes_recepcao="Tentativa de agendamento em horário passado."
        )

  def test_cancelar_consulta_com_sucesso(self):
    data_hora = timezone.now() + timezone.timedelta(days=1)

    consulta = self.agenda_service.agendar_consulta(
        usuario=self.recepcionista,
        paciente=self.paciente,
        medico=self.medico,
        data_hora=data_hora,
        observacoes_recepcao="Paciente com diabetes."
    )

    consulta_cancelada = self.agenda_service.cancelar_consulta(
        usuario=self.recepcionista,
        consulta=consulta,
        motivo="Paciente não poderá comparecer."
    )

    self.assertEqual(consulta_cancelada.status, StatusConsulta.CANCELADA)

  def test_cancelar_consulta_sem_permissao(self):
    data_hora = timezone.now() + timezone.timedelta(days=1)

    consulta = self.agenda_service.agendar_consulta(
        usuario=self.recepcionista,
        paciente=self.paciente,
        medico=self.medico,
        data_hora=data_hora,
        observacoes_recepcao="Paciente com diabetes."
    )

    with self.assertRaises(PermissionError):
        self.agenda_service.cancelar_consulta(
            usuario=self.usuario_base,
            consulta=consulta,
            motivo="Paciente não poderá comparecer."
        )

  def test_cancelar_consulta_realizada(self):
    data_hora = timezone.now() + timezone.timedelta(days=1)

    consulta = self.agenda_service.agendar_consulta(
        usuario=self.recepcionista,
        paciente=self.paciente,
        medico=self.medico,
        data_hora=data_hora,
        observacoes_recepcao="Paciente com diabetes."
    )

    # Simula a realização da consulta
    consulta.status = StatusConsulta.REALIZADA
    consulta.save()

    with self.assertRaises(ValueError):
        self.agenda_service.cancelar_consulta(
            usuario=self.recepcionista,
            consulta=consulta,
            motivo="Tentativa de cancelamento após realização."
        )

  def test_listar_agenda_medico_com_sucesso(self):
    data_hora1 = timezone.now() + timezone.timedelta(days=1)
    data_hora2 = timezone.now() + timezone.timedelta(days=2)

    consulta1 = self.agenda_service.agendar_consulta(
        usuario=self.recepcionista,
        paciente=self.paciente,
        medico=self.medico,
        data_hora=data_hora1,
        observacoes_recepcao="Consulta 1"
    )

    consulta2 = self.agenda_service.agendar_consulta(
        usuario=self.recepcionista,
        paciente=self.paciente,
        medico=self.medico,
        data_hora=data_hora2,
        observacoes_recepcao="Consulta 2"
    )

    agenda = self.agenda_service.listar_agenda_medico(
        usuario=self.recepcionista,
        medico=self.medico
    )

    self.assertIn(consulta1, agenda)
    self.assertIn(consulta2, agenda)

  def test_listar_agenda_medico_sem_permissao(self):
    data_hora = timezone.now() + timezone.timedelta(days=1)

    self.agenda_service.agendar_consulta(
        usuario=self.recepcionista,
        paciente=self.paciente,
        medico=self.medico,
        data_hora=data_hora,
        observacoes_recepcao="Consulta 1"
    )

    with self.assertRaises(PermissionError):
        self.agenda_service.listar_agenda_medico(
            usuario=self.usuario_base,
            medico=self.medico
        )

  def test_concluir_atendimento_consulta(self):
    data_hora = timezone.now() + timezone.timedelta(days=1)

    consulta = self.agenda_service.agendar_consulta(
        usuario=self.recepcionista,
        paciente=self.paciente,
        medico=self.medico,
        data_hora=data_hora,
        observacoes_recepcao="Paciente com sintomas de gripe."
    )

    diagnostico_teste = "Gripe comum"
    prescricao_teste = "Paracetamol 500mg de 8 em 8 horas"

    consulta.finalizar_atendimento(
        medico=self.medico,
        diagnostico=diagnostico_teste,
        prescricao=prescricao_teste
    )

    self.assertEqual(consulta.status, StatusConsulta.REALIZADA)
    self.assertIn(diagnostico_teste, self.prontuario.historico_diagnosticos)
    self.assertIn(prescricao_teste, self.prontuario.prescricoes)

  def test_concluir_atendimento_sem_permissao(self):
    data_hora = timezone.now() + timezone.timedelta(days=1)

    consulta = self.agenda_service.agendar_consulta(
        usuario=self.recepcionista,
        paciente=self.paciente,
        medico=self.medico,
        data_hora=data_hora,
        observacoes_recepcao="Paciente com sintomas de gripe."
    )

    diagnostico_teste = "Gripe comum"
    prescricao_teste = "Paracetamol 500mg de 8 em 8 horas"

    with self.assertRaises(PermissionError):
        consulta.finalizar_atendimento(
            medico=self.usuario_base,  # Usuário sem permissão
            diagnostico=diagnostico_teste,
            prescricao=prescricao_teste
        )

    