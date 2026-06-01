from datetime import datetime


class FaturamentoService:
    """Regras de faturamento ligadas aos pedidos do PROG2."""

    def __init__(self, state):
        self.state = state

    def listar_pedidos_prog2(self):
        return [str(pedido) for pedido in self.state.pedidos_prog2]

    def fechar_prog2(self, data_faturamento=None):
        pedidos = self.listar_pedidos_prog2()

        if not pedidos:
            return []

        if data_faturamento is None:
            data_faturamento = datetime.now().strftime("%d/%m/%Y %H:%M")

        for pedido in pedidos:
            self.state.pedidos_faturados.add(str(pedido))
            self.state.datas_faturamento_pedido[str(pedido)] = data_faturamento

        self.state.limpar_prog2()
        self.state.marcar_estado_alterado()

        return pedidos

    def remover_pedido_faturado(self, pedido):
        pedido = str(pedido)

        if pedido not in self.state.pedidos_faturados:
            return False

        self.state.pedidos_faturados.discard(pedido)
        self.state.datas_faturamento_pedido.pop(pedido, None)
        self.state.marcar_estado_alterado()

        return True
