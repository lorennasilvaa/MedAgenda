import logging
from pathlib import Path
from django.utils import timezone

# configura o logger padrão do django
logger = logging.getLogger('clinica_auditoria')


class AuditoriaService:
    _caminho_padrao: str = "logs.log"

    def __init__(self, caminho_log: str | Path | None = None):
        self.caminho_log = Path(caminho_log) if caminho_log else Path(self._caminho_padrao)

    @classmethod
    def _resolver_caminho(cls, instancia=None) -> Path:
        if instancia is not None and getattr(instancia, "caminho_log", None):
            return Path(instancia.caminho_log)
        return Path(cls._caminho_padrao)

    # registra um evento de log no sistema com timestamp e usuario responsavel
    @classmethod
    def registrar_log(cls, evento: str, usuario=None, caminho_log: str | Path | None = None) -> None:
        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        username = usuario.username if usuario else "anônimo"
        cargo = getattr(usuario, "cargo", "SEM_CARGO") if usuario else "N/A"

        mensagem_log = f"[{timestamp}] [AUDITORIA] Usuário: {username} ({cargo}) - Evento: {evento}"

        # grava no log oficial do django - console ou arquivo
        logger.info(mensagem_log)

        destino = Path(caminho_log) if caminho_log else Path(cls._caminho_padrao)

        # salva em um arquivo dedicado
        try:
            destino.parent.mkdir(parents=True, exist_ok=True)
            with destino.open("a", encoding="utf-8") as arquivo:
                arquivo.write(mensagem_log + "\n")
        except Exception as e:
            logger.error(f"erro ao salvar arquivo de log: {e}")
            