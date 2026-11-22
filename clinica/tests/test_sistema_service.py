from pathlib import Path
import tempfile
from django.test import TestCase
from ..models import (
    UsuarioClinica,
    Recepcionista,
    Medico,
    AdministradorTI,
)
from ..services.services import AuditoriaService
from ..services.sistemaServices import SistemaService


class SistemaServiceTestCase(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = Path(self.temp_dir.name) / "test_auditoria.log"

        # Garante que o AuditoriaService escreva no arquivo temporário deste teste
        self.auditoria = AuditoriaService()
        self.auditoria.caminho_log = str(self.log_path)

        self.sistema_service = SistemaService(
            auditoria_service=self.auditoria,
            caminho_log=str(self.log_path),
        )

        self.recepcionista = Recepcionista.objects.create_user(
            username="ana_rec",
            password="password123",
            nome="Ana Recepção",
            cpf="111.111.111-11",
            cargo=UsuarioClinica.TipoCargo.RECEPCIONISTA,
        )
        self.medico = Medico.objects.create_user(
            username="dr_house",
            password="password123",
            nome="Dr. House",
            cpf="222.222.222-22",
            cargo=UsuarioClinica.TipoCargo.MEDICO,
            crm="12345-SP",
        )
        self.admin_ti = AdministradorTI.objects.create_user(
            username="joao_ti",
            password="password123",
            nome="João TI",
            cpf="333.333.333-33",
            cargo=UsuarioClinica.TipoCargo.TI,
        )
        self.alvo = UsuarioClinica.objects.create_user(
            username="usuario_alvo",
            password="password123",
            nome="Usuário Alvo",
            cpf="444.444.444-44",
            cargo=UsuarioClinica.TipoCargo.RECEPCIONISTA,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def _conteudo_log(self) -> str:
        if not self.log_path.exists():
            return ""
        return self.log_path.read_text(encoding="utf-8")

    def test_bloqueio_rbac_recepcionista_e_medico_registra_log(self):
        for ator in (self.recepcionista, self.medico):
            with self.assertRaises(PermissionError):
                self.sistema_service.alterar_cargo_usuario(
                    ator=ator,
                    alvo=self.alvo,
                    novo_cargo=UsuarioClinica.TipoCargo.TI,
                )

            with self.assertRaises(PermissionError):
                self.sistema_service.alterar_status_usuario(
                    ator=ator,
                    alvo=self.alvo,
                    ativo=False,
                )

            with self.assertRaises(PermissionError):
                self.sistema_service.ler_logs_auditoria(ator=ator)

        log_texto = self._conteudo_log()
        self.assertIn("ACESSO NEGADO", log_texto)
        self.assertIn("ana_rec", log_texto)
        self.assertIn("dr_house", log_texto)

    def test_alterar_cargo_para_medico_exige_crm(self):
        with self.assertRaises(ValueError):
            self.sistema_service.alterar_cargo_usuario(
                ator=self.admin_ti,
                alvo=self.alvo,
                novo_cargo=UsuarioClinica.TipoCargo.MEDICO,
            )

        atualizado = self.sistema_service.alterar_cargo_usuario(
            ator=self.admin_ti,
            alvo=self.alvo,
            novo_cargo=UsuarioClinica.TipoCargo.MEDICO,
            crm="99999-RN",
        )
        atualizado.refresh_from_db()

        self.assertEqual(atualizado.cargo, UsuarioClinica.TipoCargo.MEDICO)
        self.assertEqual(atualizado.crm, "99999-RN")
        self.assertIn("joao_ti", self._conteudo_log())

    def test_alterar_status_usuario_e_impede_auto_desativacao(self):
        with self.assertRaises(ValueError):
            self.sistema_service.alterar_status_usuario(
                ator=self.admin_ti,
                alvo=self.admin_ti,
                ativo=False,
            )

        desativado = self.sistema_service.alterar_status_usuario(
            ator=self.admin_ti,
            alvo=self.alvo,
            ativo=False,
        )
        desativado.refresh_from_db()
        self.assertFalse(desativado.is_active)

        reativado = self.sistema_service.alterar_status_usuario(
            ator=self.admin_ti,
            alvo=self.alvo,
            ativo=True,
        )
        reativado.refresh_from_db()
        self.assertTrue(reativado.is_active)

    def test_ler_logs_auditoria_retorna_linhas_e_audita_leitura(self):
        self.sistema_service.alterar_status_usuario(
            ator=self.admin_ti,
            alvo=self.alvo,
            ativo=False,
        )

        linhas = self.sistema_service.ler_logs_auditoria(ator=self.admin_ti, limite=10)

        self.assertGreaterEqual(len(linhas), 1)
        self.assertTrue(any("DESATIVADA" in linha for linha in linhas))
        self.assertIn("Consultou os últimos", self._conteudo_log())