from pathlib import Path
from ..models import UsuarioClinica
from .services import AuditoriaService


class SistemaService:
    """
    Camada de serviço voltada à administração técnica do sistema,
    controlada pelas permissões 'sistema:gerenciar' e 'auditoria:ler'.
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

    
    def alterar_cargo_usuario(
        self,
        ator: UsuarioClinica,
        alvo: UsuarioClinica,
        novo_cargo: str,
        crm: str | None = None,
    ) -> UsuarioClinica:
        self._exigir_permissao(ator, "sistema:gerenciar", "alterar cargo de usuário")

        cargos_validos = {escolha[0] for escolha in UsuarioClinica.TipoCargo.choices}
        if novo_cargo not in cargos_validos:
            raise ValueError(f"Cargo inválido: {novo_cargo}")

        cargo_anterior = alvo.cargo
        alvo.cargo = novo_cargo

        if novo_cargo == UsuarioClinica.TipoCargo.MEDICO:
            if crm:
                alvo.crm = crm
            elif not alvo.crm:
                raise ValueError("Médicos exigem um CRM informado.")

        alvo.save()

        self.auditoria.registrar_log(
            evento=(
                f"Cargo do usuário '{alvo.username}' alterado de {cargo_anterior} "
                f"para {novo_cargo}"
            ),
            usuario=ator,
        )
        return alvo

    
    def alterar_status_usuario(
        self,
        ator: UsuarioClinica,
        alvo: UsuarioClinica,
        ativo: bool,
    ) -> UsuarioClinica:
        self._exigir_permissao(ator, "sistema:gerenciar", "alterar status de conta")

        if ator.pk == alvo.pk and not ativo:
            raise ValueError("Não é permitido desativar a própria conta de administrador.")

        alvo.is_active = ativo
        alvo.save()

        estado = "ATIVADA" if ativo else "DESATIVADA"
        self.auditoria.registrar_log(
            evento=f"Conta do usuário '{alvo.username}' {estado}",
            usuario=ator,
        )
        return alvo

    
    def ler_logs_auditoria(self, ator: UsuarioClinica, limite: int = 100) -> list[str]:
        self._exigir_permissao(ator, "auditoria:ler", "ler logs de auditoria")

        if limite <= 0:
            raise ValueError("O limite de linhas deve ser maior que zero.")

        if not self.caminho_log.exists():
            return []

        with self.caminho_log.open("r", encoding="utf-8") as arquivo:
            linhas = [linha.rstrip("\n") for linha in arquivo if linha.strip()]

        self.auditoria.registrar_log(
            evento=f"Consultou os últimos {min(limite, len(linhas))} registros de auditoria",
            usuario=ator,
        )
        return linhas[-limite:]