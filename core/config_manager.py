import json
import shutil
from datetime import datetime
from pathlib import Path


class ConfigManager:
    def __init__(self):
        self.base_dir = Path.home() / ".carteira_ops"
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.config_path = self.base_dir / "config.json"
        self.backup_path = self.base_dir / "config.backup.json"
        self.backup_dir = self.base_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def config_padrao(self):
        return {
            "ultimo_csv": "",
            "estado": {
                "linhas_bloqueadas": [],
                "codigos_itens_bloqueados": [],
                "pedidos_bloqueados": [],
                "observacoes_bloqueadas": [],
                "clientes_bloqueados": [],
                "pedidos_prog2": [],
                "pedidos_faturados": [],
                "datas_faturamento_pedido": {},
                "motivos_linha": {},
                "motivos_item": {},
                "motivos_pedido": {},
                "motivos_observacao": {},
                "motivos_cliente": {},
            },
            "presets": {
                "itens": {},
                "clientes": {},
            },
            "observacoes_internas": {},
            "settings": {
                "valor_minimo_padrao": "1000",
                "abrir_pdf_automaticamente": True,
                "salvar_estado_automaticamente": True,
                "restaurar_ultimo_csv_ao_abrir": False,
                "pasta_exportacao": "",
            },
        }

    def carregar(self):
        if not self.config_path.exists():
            config = self.config_padrao()
            self.salvar(config)
            return config

        try:
            with open(self.config_path, "r", encoding="utf-8") as arquivo:
                config = json.load(arquivo)

            return self.normalizar_config(config)

        except Exception:
            self.criar_backup_corrompido()
            config = self.config_padrao()
            self.salvar(config)
            return config

    def normalizar_config(self, config):
        padrao = self.config_padrao()

        if not isinstance(config, dict):
            return padrao

        if "ultimo_csv" not in config:
            config["ultimo_csv"] = padrao["ultimo_csv"]

        if "estado" not in config or not isinstance(config["estado"], dict):
            config["estado"] = padrao["estado"]

        if "presets" not in config or not isinstance(config["presets"], dict):
            config["presets"] = padrao["presets"]

        if "observacoes_internas" not in config or not isinstance(config["observacoes_internas"], dict):
            config["observacoes_internas"] = {}

        if "settings" not in config or not isinstance(config["settings"], dict):
            config["settings"] = padrao["settings"]

        for chave, valor in padrao["estado"].items():
            if chave not in config["estado"]:
                config["estado"][chave] = valor

        if "itens" not in config["presets"] or not isinstance(config["presets"]["itens"], dict):
            config["presets"]["itens"] = {}

        if "clientes" not in config["presets"] or not isinstance(config["presets"]["clientes"], dict):
            config["presets"]["clientes"] = {}

        for chave, valor in padrao["settings"].items():
            if chave not in config["settings"]:
                config["settings"][chave] = valor

        return config

    def criar_backup_config_atual(self):
        if not self.config_path.exists():
            return

        try:
            shutil.copy2(self.config_path, self.backup_path)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_historico = self.backup_dir / f"config_{timestamp}.json"
            shutil.copy2(self.config_path, backup_historico)
            self.remover_backups_antigos(limite=20)
        except Exception:
            pass

    def criar_backup_corrompido(self):
        if not self.config_path.exists():
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            destino = self.backup_dir / f"config_corrompido_{timestamp}.json"
            shutil.copy2(self.config_path, destino)
        except Exception:
            pass

    def remover_backups_antigos(self, limite=20):
        backups = sorted(
            self.backup_dir.glob("config_*.json"),
            key=lambda caminho: caminho.stat().st_mtime,
            reverse=True,
        )

        for caminho in backups[limite:]:
            try:
                caminho.unlink()
            except Exception:
                pass

    def salvar(self, config):
        config = self.normalizar_config(config)
        self.criar_backup_config_atual()

        arquivo_temporario = self.config_path.with_suffix(".tmp")

        with open(arquivo_temporario, "w", encoding="utf-8") as arquivo:
            json.dump(
                config,
                arquivo,
                ensure_ascii=False,
                indent=4,
            )

        arquivo_temporario.replace(self.config_path)
