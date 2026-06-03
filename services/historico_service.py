from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Dict, Any

import pandas as pd


class HistoricoService:
    """Normaliza e prepara o histórico de alterações para tela/exportação."""

    COLUNAS = ["Data/Hora", "Usuário", "Ação", "Pedido", "Item", "Detalhe"]

    @staticmethod
    def normalizar(historico: Iterable[Dict[str, Any]] | None) -> List[Dict[str, str]]:
        registros = []
        for registro in historico or []:
            if not isinstance(registro, dict):
                continue
            registros.append({
                "Data/Hora": str(registro.get("data_hora", "") or ""),
                "Usuário": str(registro.get("usuario", "") or ""),
                "Ação": str(registro.get("acao", "") or ""),
                "Pedido": str(registro.get("pedido", "") or ""),
                "Item": str(registro.get("item", "") or ""),
                "Detalhe": str(registro.get("detalhe", "") or ""),
            })
        registros.sort(key=lambda item: item.get("Data/Hora", ""), reverse=True)
        return registros

    @classmethod
    def filtrar(cls, historico, termo="", acao="Todos"):
        termo = str(termo or "").strip().lower()
        acao = str(acao or "Todos").strip()
        registros = cls.normalizar(historico)

        if acao and acao != "Todos":
            registros = [registro for registro in registros if registro.get("Ação") == acao]

        if termo:
            filtrados = []
            for registro in registros:
                texto = " ".join(str(valor) for valor in registro.values()).lower()
                if termo in texto:
                    filtrados.append(registro)
            registros = filtrados

        return registros

    @classmethod
    def acoes_disponiveis(cls, historico):
        acoes = sorted({registro.get("Ação", "") for registro in cls.normalizar(historico) if registro.get("Ação")})
        return ["Todos", *acoes]

    @classmethod
    def para_dataframe(cls, historico, termo="", acao="Todos"):
        registros = cls.filtrar(historico, termo=termo, acao=acao)
        if not registros:
            return pd.DataFrame(columns=cls.COLUNAS)
        return pd.DataFrame(registros, columns=cls.COLUNAS)

    @staticmethod
    def resumo(registros):
        registros = list(registros or [])
        if not registros:
            return {
                "total": 0,
                "ultimo_evento": "-",
                "usuarios": 0,
                "acao_mais_recente": "-",
            }

        usuarios = {registro.get("Usuário", "") for registro in registros if registro.get("Usuário")}
        mais_recente = registros[0]
        return {
            "total": len(registros),
            "ultimo_evento": mais_recente.get("Data/Hora", "-"),
            "usuarios": len(usuarios),
            "acao_mais_recente": mais_recente.get("Ação", "-"),
        }
