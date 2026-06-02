from datetime import datetime


class FaturamentoService:
    """Regras de faturamento ligadas aos pedidos do PROG2."""

    def __init__(self, state):
        self.state = state

    def listar_pedidos_prog2(self):
        return [str(pedido) for pedido in self.state.pedidos_prog2]

    def _data_referencia(self, data_faturamento):
        texto = str(data_faturamento or "").strip()
        if texto:
            return texto.split()[0]
        return datetime.now().strftime("%d/%m/%Y")

    def _valor_float(self, valor):
        try:
            if valor is None:
                return 0.0
            return float(valor)
        except (TypeError, ValueError):
            return 0.0

    def _texto(self, valor):
        if valor is None:
            return ""
        return str(valor)

    def _calcular_saldo_por_pedido(self, df_pedidos, df_faturado, coluna_pedido):
        if df_pedidos is None or getattr(df_pedidos, "empty", True):
            return {}

        if "Valor em Carteira" not in df_pedidos.columns:
            return {}

        totais_pedido = (
            df_pedidos
            .assign(_pedido=df_pedidos[coluna_pedido].astype(str))
            .groupby("_pedido", sort=False)["Valor em Carteira"]
            .sum()
            .to_dict()
        )

        if df_faturado is None or getattr(df_faturado, "empty", True) or "Valor em Carteira" not in df_faturado.columns:
            faturado_pedido = {}
        else:
            faturado_pedido = (
                df_faturado
                .assign(_pedido=df_faturado[coluna_pedido].astype(str))
                .groupby("_pedido", sort=False)["Valor em Carteira"]
                .sum()
                .to_dict()
            )

        saldos = {}
        for pedido, total in totais_pedido.items():
            valor_total = self._valor_float(total)
            valor_faturado = self._valor_float(faturado_pedido.get(pedido, 0))
            saldos[str(pedido)] = max(valor_total - valor_faturado, 0)

        return saldos

    def _gerar_registros_faturamento(self, pedidos, data_faturamento, df_fechamento=None):
        data_ref = self._data_referencia(data_faturamento)
        registros = []

        if df_fechamento is None or getattr(df_fechamento, "empty", True):
            return [
                {
                    "Data Referência": data_ref,
                    "Data Faturamento": data_faturamento,
                    "Pedido": pedido,
                    "Cliente": "",
                    "Item": "",
                    "Descrição Item": "",
                    "Qtde": 0.0,
                    "Valor Total Faturamento": 0.0,
                    "Valor Saldo Pedido": 0.0,
                    "Data Entrega": "",
                    "Grupo": "",
                    "OBS": "",
                    "ID Linha": "",
                }
                for pedido in pedidos
            ]

        df = df_fechamento.copy()
        coluna_pedido = "Pedido Texto" if "Pedido Texto" in df.columns else "Pedido"
        df_pedidos = df[df[coluna_pedido].astype(str).isin(set(pedidos))].copy()
        df = df_pedidos.copy()

        if "_Bloqueado" in df.columns:
            df = df[~df["_Bloqueado"]].copy()

        saldo_por_pedido = self._calcular_saldo_por_pedido(df_pedidos, df, coluna_pedido)

        if df.empty:
            return [
                {
                    "Data Referência": data_ref,
                    "Data Faturamento": data_faturamento,
                    "Pedido": pedido,
                    "Cliente": "",
                    "Item": "",
                    "Descrição Item": "",
                    "Qtde": 0.0,
                    "Valor Total Faturamento": 0.0,
                    "Valor Saldo Pedido": 0.0,
                    "Data Entrega": "",
                    "Grupo": "",
                    "OBS": "",
                    "ID Linha": "",
                }
                for pedido in pedidos
            ]

        for _, linha in df.iterrows():
            id_linha = linha.get("ID Linha", "")
            try:
                id_pendencia = int(id_linha)
            except (TypeError, ValueError):
                id_pendencia = None

            pendencia = ""
            if id_pendencia is not None:
                pendencia = str(getattr(self.state, "pendencias_prog2", {}).get(id_pendencia, "") or "").strip()

            pedido = self._texto(linha.get(coluna_pedido, linha.get("Pedido", "")))
            grupo = self._texto(linha.get("Grupo Faturamento Abrev", linha.get("Grupo Faturamento", "")))

            registros.append({
                "Data Referência": data_ref,
                "Data Faturamento": data_faturamento,
                "Pedido": pedido,
                "Cliente": self._texto(linha.get("Cliente", "")),
                "Item": self._texto(linha.get("Item", "")),
                "Descrição Item": self._texto(linha.get("Descrição Item", "")),
                "Qtde": self._valor_float(linha.get("Saldo a Faturar", 0)),
                "Valor Total Faturamento": self._valor_float(linha.get("Valor em Carteira", 0)),
                "Valor Saldo Pedido": self._valor_float(saldo_por_pedido.get(pedido, 0)),
                "Data Entrega": self._texto(linha.get("Data Entrega", "")),
                "Grupo": grupo,
                "OBS": pendencia,
                "ID Linha": self._texto(id_linha),
            })

        return registros

    def fechar_prog2(self, data_faturamento=None, df_fechamento=None):
        pedidos = self.listar_pedidos_prog2()

        if not pedidos:
            return []

        if data_faturamento is None:
            data_faturamento = datetime.now().strftime("%d/%m/%Y %H:%M")

        data_ref = self._data_referencia(data_faturamento)
        novos_registros = self._gerar_registros_faturamento(pedidos, data_faturamento, df_fechamento)

        for pedido in pedidos:
            self.state.pedidos_faturados.add(str(pedido))
            self.state.datas_faturamento_pedido[str(pedido)] = data_faturamento

        registros_atuais = getattr(self.state, "registros_faturamento", [])
        self.state.registros_faturamento = [
            registro
            for registro in registros_atuais
            if not (
                str(registro.get("Pedido", "")) in set(pedidos)
                and str(registro.get("Data Referência", registro.get("Data Faturamento", ""))).split()[0] == data_ref
            )
        ]
        self.state.registros_faturamento.extend(novos_registros)

        self.state.limpar_prog2()
        self.state.marcar_estado_alterado()

        return pedidos

    def remover_pedido_faturado(self, pedido):
        pedido = str(pedido)

        if pedido not in self.state.pedidos_faturados:
            return False

        self.state.pedidos_faturados.discard(pedido)
        self.state.datas_faturamento_pedido.pop(pedido, None)
        self.state.registros_faturamento = [
            registro
            for registro in getattr(self.state, "registros_faturamento", [])
            if str(registro.get("Pedido", "")) != pedido
        ]
        self.state.marcar_estado_alterado()

        return True
