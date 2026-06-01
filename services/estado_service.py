class EstadoService:
    """Serialização e restauração do estado local da aplicação."""

    @staticmethod
    def gerar_estado_para_salvar(state):
        return {
            "linhas_bloqueadas": sorted(int(item) for item in state.linhas_bloqueadas),
            "codigos_itens_bloqueados": sorted(str(item) for item in state.codigos_itens_bloqueados),
            "pedidos_bloqueados": sorted(str(item) for item in state.pedidos_bloqueados),
            "observacoes_bloqueadas": sorted(str(item) for item in state.observacoes_bloqueadas),
            "clientes_bloqueados": sorted(str(item) for item in state.clientes_bloqueados),
            "pedidos_prog2": [str(item) for item in state.pedidos_prog2],
            "pedidos_faturados": sorted(str(item) for item in state.pedidos_faturados),
            "datas_faturamento_pedido": {str(k): str(v) for k, v in state.datas_faturamento_pedido.items()},
            "pendencias_prog2": {str(int(k)): str(v) for k, v in state.pendencias_prog2.items()},
            "motivos_linha": {str(k): v for k, v in state.motivos_linha.items()},
            "motivos_item": dict(state.motivos_item),
            "motivos_pedido": dict(state.motivos_pedido),
            "motivos_observacao": dict(state.motivos_observacao),
            "motivos_cliente": dict(state.motivos_cliente),
        }

    @staticmethod
    def restaurar_estado_salvo(state, config, observacoes_internas):
        if not state.tem_dados():
            return observacoes_internas

        estado = config.get("estado", {})
        df = state.df_original

        ids_existentes = set(int(valor) for valor in df["ID Linha"].unique())
        pedidos_existentes = set(str(valor) for valor in df["Pedido Texto"].unique())
        itens_existentes = set(str(valor) for valor in df["Item Texto"].unique())

        state.linhas_bloqueadas = {
            int(item)
            for item in estado.get("linhas_bloqueadas", [])
            if str(item).isdigit() and int(item) in ids_existentes
        }

        state.codigos_itens_bloqueados = {
            str(item)
            for item in estado.get("codigos_itens_bloqueados", [])
            if str(item) in itens_existentes
        }

        state.pedidos_bloqueados = {
            str(item)
            for item in estado.get("pedidos_bloqueados", [])
            if str(item) in pedidos_existentes
        }

        state.observacoes_bloqueadas = {
            str(item)
            for item in estado.get("observacoes_bloqueadas", [])
        }

        state.clientes_bloqueados = {
            str(item)
            for item in estado.get("clientes_bloqueados", [])
        }

        state.pedidos_faturados = {
            str(item)
            for item in estado.get("pedidos_faturados", [])
        }

        state.datas_faturamento_pedido = {
            str(k): str(v)
            for k, v in estado.get("datas_faturamento_pedido", {}).items()
        }

        state.pedidos_prog2 = [
            str(item)
            for item in estado.get("pedidos_prog2", [])
            if str(item) in pedidos_existentes
            and str(item) not in state.pedidos_faturados
        ]

        state.pendencias_prog2 = {
            int(k): str(v)
            for k, v in estado.get("pendencias_prog2", {}).items()
            if str(k).isdigit() and int(k) in ids_existentes
        }

        state.motivos_linha = {
            int(k): v
            for k, v in estado.get("motivos_linha", {}).items()
            if str(k).isdigit() and int(k) in ids_existentes
        }

        state.motivos_item = dict(estado.get("motivos_item", {}))
        state.motivos_pedido = dict(estado.get("motivos_pedido", {}))
        state.motivos_observacao = dict(estado.get("motivos_observacao", {}))
        state.motivos_cliente = dict(estado.get("motivos_cliente", {}))

        observacoes_filtradas = {
            str(pedido): texto
            for pedido, texto in observacoes_internas.items()
            if str(pedido) in pedidos_existentes
        }

        state.marcar_estado_alterado()
        return observacoes_filtradas
