import json
from datetime import datetime
from pathlib import Path

from core.app_info import APP_VERSION, VERSION_FILE_NAME


def parse_version(version):
    """Converte versões simples, como 1.2.3, para tupla comparável."""
    if version is None:
        return (0, 0, 0)

    texto = str(version).strip().lower().lstrip("v")
    partes = []

    for parte in texto.replace("-", ".").split("."):
        numero = ""
        for caractere in parte:
            if caractere.isdigit():
                numero += caractere
            else:
                break
        partes.append(int(numero or 0))

    while len(partes) < 3:
        partes.append(0)

    return tuple(partes[:4])


def comparar_versoes(versao_atual, versao_referencia):
    atual = parse_version(versao_atual)
    referencia = parse_version(versao_referencia)

    tamanho = max(len(atual), len(referencia))
    atual = atual + (0,) * (tamanho - len(atual))
    referencia = referencia + (0,) * (tamanho - len(referencia))

    if atual < referencia:
        return -1
    if atual > referencia:
        return 1
    return 0


class VersionService:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.version_file_path = self._descobrir_arquivo_versao()

    def _descobrir_arquivo_versao(self):
        local_config = getattr(self.config_manager, "local_config", {}) or {}
        caminho_configurado = (
            local_config.get("arquivo_versao")
            or local_config.get("version_file")
            or local_config.get("caminho_versao")
        )

        if caminho_configurado:
            return Path(caminho_configurado)

        if getattr(self.config_manager, "modo_compartilhado", False):
            base_dir = Path(getattr(self.config_manager, "base_dir", ""))
            if base_dir.name.lower() == "data":
                return base_dir.parent / VERSION_FILE_NAME
            return base_dir / VERSION_FILE_NAME

        return Path(getattr(self.config_manager, "app_dir", Path.cwd())) / VERSION_FILE_NAME

    def carregar_arquivo_versao(self):
        if not self.version_file_path.exists():
            return None

        with open(self.version_file_path, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        if not isinstance(dados, dict):
            return None

        return dados

    def verificar(self, versao_atual=APP_VERSION):
        resultado = {
            "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_version": versao_atual,
            "latest_version": versao_atual,
            "min_version": "",
            "update_available": False,
            "blocked": False,
            "message": "",
            "download_path": "",
            "version_file": str(self.version_file_path),
            "available": False,
            "error": "",
        }

        try:
            dados = self.carregar_arquivo_versao()
        except Exception as erro:
            resultado["error"] = str(erro)
            return resultado

        if not dados:
            resultado["message"] = "Arquivo de versão não encontrado."
            return resultado

        latest = (
            dados.get("latest_version")
            or dados.get("versao_atual")
            or dados.get("versao_disponivel")
            or dados.get("version")
            or versao_atual
        )
        minimum = (
            dados.get("min_version")
            or dados.get("minimum_version")
            or dados.get("versao_minima")
            or ""
        )

        resultado.update({
            "latest_version": str(latest),
            "min_version": str(minimum or ""),
            "message": str(dados.get("message") or dados.get("mensagem") or ""),
            "download_path": str(dados.get("download_path") or dados.get("caminho_download") or ""),
            "available": True,
        })

        resultado["update_available"] = comparar_versoes(versao_atual, latest) < 0
        resultado["blocked"] = bool(minimum) and comparar_versoes(versao_atual, minimum) < 0

        return resultado
