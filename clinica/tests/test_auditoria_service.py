from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone

from ..models import Medico, Paciente, Prontuario, Consulta, StatusConsulta
from clinica.services.services import AuditoriaService

class AuditoriaWorkflowTestCase(TestCase):
    
    def setUp(self):
        # configura dados básicos para os testes
        self.medico = Medico.objects.create_user(
            username="drhouse",
            password="password123",
            nome="Dr. House",
            cpf="111.111.111-11",
            crm="12345-SP"
        )
        self.prontuario = Prontuario.objects.create()
        self.paciente = Paciente.objects.create(
            nome="Carlos Silva",
            cpf="333.333.333-33",
            prontuario=self.prontuario
        )
        self.consulta = Consulta.objects.create(
            paciente=self.paciente,
            medico=self.medico,
            data_hora=timezone.now(),
            status=StatusConsulta.AGENDADA
        )

    # testa se a classe Consulta dispara o log de auditoria ao finalizar o atendimento
    @patch('clinica.services.services.AuditoriaService.registrar_log')
    def test_geracao_log_ao_finalizar_consulta(self, mock_registrar_log):

        # executa a ação que deve gerar log
        self.consulta.finalizar_atendimento(
            medico=self.medico,
            diagnostico="Enxaqueca",
            prescricao="Anador 500mg"
        )
        
        # verifica se o método de auditoria foi chamado pelo menos uma vez
        self.assertTrue(mock_registrar_log.called)
        
        # verifica se foi passado o usuário correto no log
        args, kwargs = mock_registrar_log.call_args
        self.assertEqual(kwargs.get('usuario'), self.medico)

    # testa se a classe Prontuario dispara o log de auditoria ao registrar uma alergia
    @patch('clinica.services.services.AuditoriaService.registrar_log')
    def test_geracao_log_ao_adicionar_alergia(self, mock_registrar_log):
        
        # executa a ação no prontuário
        self.prontuario.adicionar_alergia(
            usuario=self.medico,
            alergia="Dipirona"
        )
        
        # verifica se o serviço de auditoria foi acionado
        self.assertTrue(mock_registrar_log.called)
        
        # garante que a alergia foi salva na lista do prontuário
        self.assertIn("Dipirona", self.prontuario.alergias)