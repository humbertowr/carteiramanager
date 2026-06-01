import pandas as pd


class ExportacaoService:
    """Geração de DataFrames de exportação sem dependência de interface gráfica."""

    @staticmethod
    def _pendencia_item(state, id_linha):
        try:
            return str(state.pendencias_prog2.get(int(id_linha), "") or "").strip()
        except (TypeError, ValueError):
            return ""

    @staticmethod
    def _juntar_observacoes_pendencia(valores):
        observacoes = []
        for valor in valores:
            valor = str(valor or "").strip()
            if valor and valor not in observacoes:
                observacoes.append(valor)
        return " ; ".join(observacoes)

    @staticmethod
    def gerar_df_prog2_itens_liberados(state, df_bloqueios):
        if not state.tem_dados() or not state.pedidos_prog2:
            return pd.DataFrame()

        df = df_bloqueios.copy()
        pedidos_prog2 = set(str(pedido) for pedido in state.pedidos_prog2)
        df = df[df["Pedido Texto"].isin(pedidos_prog2)]

        if df.empty:
            return pd.DataFrame()

        df = df[~df["_Bloqueado"]].copy()

        if df.empty:
            return pd.DataFrame()

        df["OBS"] = df["ID Linha"].apply(lambda id_linha: ExportacaoService._pendencia_item(state, id_linha))

        resultado = df.groupby(
            ["Item", "Descrição Item"],
            as_index=False,
        ).agg({
            "Pedido": "nunique",
            "Cliente": "nunique",
            "Saldo a Faturar": "sum",
            "Valor em Carteira": "sum",
            "OBS": ExportacaoService._juntar_observacoes_pendencia,
        })

        resultado.rename(
            columns={
                "Pedido": "Qtd. Pedidos",
                "Cliente": "Qtd. Clientes",
                "Saldo a Faturar": "Qtde Liberada",
                "Valor em Carteira": "Valor Liberado",
            },
            inplace=True,
        )

        resultado.sort_values("Qtde Liberada", ascending=False, inplace=True)

        return resultado

    @staticmethod
    def gerar_df_prog2_pedidos_liberados(state, df_bloqueios):
        if not state.tem_dados() or not state.pedidos_prog2:
            return pd.DataFrame()

        df = df_bloqueios.copy()
        pedidos_prog2 = set(str(pedido) for pedido in state.pedidos_prog2)
        df = df[df["Pedido Texto"].isin(pedidos_prog2)]

        if df.empty:
            return pd.DataFrame()

        df = df[~df["_Bloqueado"]].copy()

        if df.empty:
            return pd.DataFrame()

        registros = []

        for pedido, grupo in df.groupby("Pedido", sort=False):
            cliente_original = str(grupo["Cliente"].iloc[0])
            cliente_abrev = state.abreviar_cliente(cliente_original)
            observacoes = []

            for _, linha in grupo.iterrows():
                pendencia = ExportacaoService._pendencia_item(state, linha.get("ID Linha"))
                if pendencia:
                    item_obs = f'{linha.get("Item", "")} - {pendencia}'
                    if item_obs not in observacoes:
                        observacoes.append(item_obs)

            registros.append({
                "Pedido": pedido,
                "Cliente": cliente_abrev,
                "Cliente Original": cliente_original,
                "Data Entrega": str(grupo["Data Entrega"].iloc[0]),
                "Grupo": str(grupo["Grupo Faturamento Abrev"].iloc[0]),
                "Qtd. Itens Liberados": grupo["Item"].nunique(),
                "Qtde Liberada": grupo["Saldo a Faturar"].sum(),
                "Valor Total Liberado": grupo["Valor em Carteira"].sum(),
                "OBS": " ; ".join(observacoes),
            })

        resultado = pd.DataFrame(registros)

        if not resultado.empty:
            resultado.sort_values("Qtde Liberada", ascending=False, inplace=True)

        return resultado
