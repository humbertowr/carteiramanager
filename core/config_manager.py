import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path


class ConfigManager:
    """Gerencia configuração local ou compartilhada do Carteira Manager.

    Quando existir um arquivo ``config_local.json`` ao lado do executável/app.py com
    ``modo_compartilhado=true``, o estado principal passa a ser salvo na pasta de
    rede definida em ``pasta_dados``. O arquivo local continua servindo apenas para
    apontar usuário e pastas do servidor.
    """

    def __init__(self):
        self.app_dir = self._descobrir_app_dir()
        self.local_config_path = self.app_dir / "config_local.json"
        self.local_config = self._carregar_config_local()

        self.modo_compartilhado = bool(self.local_config.get("modo_compartilhado", False))
        self.usuario = str(self.local_config.get("usuario", "Usuário") or "Usuário").strip()

        if self.modo_compartilhado and self.local_config.get("pasta_dados"):
            self.base_dir = Path(self.local_config["pasta_dados"])
            self.base_dir.mkdir(parents=True, exist_ok=True)

            pasta_backups = self.local_config.get("pasta_backups") or str(self.base_dir / "backups")
            pasta_logs = self.local_config.get("pasta_logs") or str(self.base_dir / "logs")
            pasta_exports = self.local_config.get("pasta_exports") or str(self.base_dir / "exports")

            self.backup_dir = Path(pasta_backups)
            self.log_dir = Path(pasta_logs)
            self.export_dir = Path(pasta_exports)

            self.config_path = self.base_dir / "estado_compartilhado.json"
            self.backup_path = self.backup_dir / "estado_compartilhado.backup.json"
            self.lock_path = self.base_dir / "estado_compartilhado.lock"
        else:
            self.modo_compartilhado = False
            self.base_dir = Path.home() / ".carteira_ops"
            self.backup_dir = self.base_dir / "backups"
            self.log_dir = self.base_dir / "logs"
            self.export_dir = self.base_dir / "exports"

            self.config_path = self.base_dir / "config.json"
            self.backup_path = self.base_dir / "config.backup.json"
            self.lock_path = self.base_dir / "config.lock"

        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def _descobrir_app_dir(self):
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parents[1]

    def _carregar_config_local(self):
        caminhos = [self.local_config_path]

        # Quando executado por atalho, garante tentativa também no diretório atual.
        cwd_config = Path.cwd() / "config_local.json"
        if cwd_config not in caminhos:
            caminhos.append(cwd_config)

        for caminho in caminhos:
            if not caminho.exists():
                continue

            try:
                with open(caminho, "r", encoding="utf-8") as arquivo:
                    dados = json.load(arquivo)
                if isinstance(dados, dict):
                    self.local_config_path = caminho
                    return dados
            except Exception:
                continue

        return {}

    def config_padrao(self):
        pasta_exportacao = str(self.export_dir) if getattr(self, "modo_compartilhado", False) else ""
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
                "registros_faturamento": [],
                "pendencias_prog2": {},
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
            "historico": [],
            "settings": {
                "valor_minimo_padrao": "1000",
                "abrir_pdf_automaticamente": True,
                "salvar_estado_automaticamente": True,
                "restaurar_ultimo_csv_ao_abrir": bool(getattr(self, "modo_compartilhado", False)),
                "pasta_exportacao": pasta_exportacao,
                "meta_faturamento_dia": "",
                "meta_faturamento_mes": "",
            },
            "_sistema": {
                "modo_compartilhado": bool(getattr(self, "modo_compartilhado", False)),
                "criado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "atualizado_em": "",
                "atualizado_por": "",
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

        if "historico" not in config or not isinstance(config["historico"], list):
            config["historico"] = []

        if "settings" not in config or not isinstance(config["settings"], dict):
            config["settings"] = padrao["settings"]

        if "_sistema" not in config or not isinstance(config["_sistema"], dict):
            config["_sistema"] = padrao["_sistema"]

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

        config["_sistema"]["modo_compartilhado"] = bool(self.modo_compartilhado)

        return config

    def descricao_modo(self):
        if self.modo_compartilhado:
            return f"Compartilhado: {self.config_path}"
        return f"Local: {self.config_path}"

    def registrar_historico(self, config, acao, detalhe="", pedido="", item=""):
        historico = config.setdefault("historico", [])
        historico.append({
            "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "usuario": self.usuario,
            "acao": str(acao),
            "detalhe": str(detalhe or ""),
            "pedido": str(pedido or ""),
            "item": str(item or ""),
        })

        # Limita crescimento do JSON em pasta de rede.
        if len(historico) > 1000:
            del historico[:-1000]

    def _adquirir_lock(self, timeout=12):
        inicio = time.time()

        while True:
            try:
                fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                with os.fdopen(fd, "w", encoding="utf-8") as arquivo:
                    arquivo.write(f"usuario={self.usuario}\n")
                    arquivo.write(f"pid={os.getpid()}\n")
                    arquivo.write(f"criado_em={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                return True
            except FileExistsError:
                # Remove trava antiga deixada por app fechado incorretamente.
                try:
                    idade = time.time() - self.lock_path.stat().st_mtime
                    if idade > 120:
                        self.lock_path.unlink()
                        continue
                except Exception:
                    pass

                if time.time() - inicio >= timeout:
                    raise RuntimeError(
                        "O estado compartilhado está em uso por outro usuário. "
                        "Tente salvar novamente em alguns segundos."
                    )

                time.sleep(0.25)

    def _liberar_lock(self):
        try:
            if self.lock_path.exists():
                self.lock_path.unlink()
        except Exception:
            pass

    def criar_backup_config_atual(self):
        if not self.config_path.exists():
            return

        try:
            shutil.copy2(self.config_path, self.backup_path)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome = "estado_compartilhado" if self.modo_compartilhado else "config"
            backup_historico = self.backup_dir / f"{nome}_{timestamp}.json"
            shutil.copy2(self.config_path, backup_historico)
            self.remover_backups_antigos(limite=30 if self.modo_compartilhado else 20)
        except Exception:
            pass

    def criar_backup_corrompido(self):
        if not self.config_path.exists():
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome = "estado_compartilhado" if self.modo_compartilhado else "config"
            destino = self.backup_dir / f"{nome}_corrompido_{timestamp}.json"
            shutil.copy2(self.config_path, destino)
        except Exception:
            pass

    def remover_backups_antigos(self, limite=20):
        padrao = "estado_compartilhado_*.json" if self.modo_compartilhado else "config_*.json"
        backups = sorted(
            self.backup_dir.glob(padrao),
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
        config.setdefault("_sistema", {})["atualizado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        config.setdefault("_sistema", {})["atualizado_por"] = self.usuario

        self._adquirir_lock()
        try:
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
        finally:
            self._liberar_lock()
