import pandas as pd


class CarteiraCacheService:
    """Cache de DataFrames derivados do estado atual da carteira.

    O cache usa a versão do AppState para evitar recalcular bloqueios a cada refresh
    e também para se invalidar automaticamente quando o estado mudar.
    """

    def __init__(self, state):
        self.state = state
        self._cache = {}
        self._versao_estado = None

    def invalidar(self):
        self._cache.clear()
        self._versao_estado = getattr(self.state, "versao_estado", None)

    def _garantir_cache_atual(self):
        versao_atual = getattr(self.state, "versao_estado", None)

        if versao_atual != self._versao_estado:
            self._cache.clear()
            self._versao_estado = versao_atual

    def obter_df_aberto(self):
        if not self.state.tem_dados():
            return pd.DataFrame()

        self._garantir_cache_atual()

        if "df_aberto" not in self._cache:
            df = self.state.df_aberto().copy()
            pedidos_faturados = set(str(pedido) for pedido in self.state.pedidos_faturados)

            if pedidos_faturados and not df.empty:
                coluna_pedido = "Pedido Texto" if "Pedido Texto" in df.columns else "Pedido"
                df = df[~df[coluna_pedido].astype(str).isin(pedidos_faturados)].copy()

            self._cache["df_aberto"] = df

        return self._cache["df_aberto"]

    def obter_df_com_bloqueios(self):
        if not self.state.tem_dados():
            return pd.DataFrame()

        self._garantir_cache_atual()

        if "df_com_bloqueios" not in self._cache:
            self._cache["df_com_bloqueios"] = self.state.df_com_bloqueios(self.obter_df_aberto())

        return self._cache["df_com_bloqueios"]
