import json
from pathlib import Path


class ConfigManager:
    def __init__(self):
        self.base_dir = Path.home() / ".carteira_ops"
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.config_path = self.base_dir / "config.json"

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

        for chave, valor in padrao["estado"].items():
            if chave not in config["estado"]:
                config["estado"][chave] = valor

        if "itens" not in config["presets"] or not isinstance(config["presets"]["itens"], dict):
            config["presets"]["itens"] = {}

        if "clientes" not in config["presets"] or not isinstance(config["presets"]["clientes"], dict):
            config["presets"]["clientes"] = {}

        return config

    def salvar(self, config):
        config = self.normalizar_config(config)

        with open(self.config_path, "w", encoding="utf-8") as arquivo:
            json.dump(
                config,
                arquivo,
                ensure_ascii=False,
                indent=4
            )