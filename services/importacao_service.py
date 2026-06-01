from core.carteira_processor import carregar_carteira


class ImportacaoService:
    """Responsável por carregar o CSV e alimentar o estado da aplicação."""

    def __init__(self, state):
        self.state = state

    def carregar_csv(self, caminho):
        df = carregar_carteira(caminho)
        self.state.carregar_dataframe(df)
        return df
