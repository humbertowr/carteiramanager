from datetime import date, timedelta

import pandas as pd


class SimulacaoFaturamentoService:
    """Gera uma simulação de faturamento por dia sem alterar o estado do app."""

    def calcular(
        self,
        state,
        data_inicio,
        data_fim,
        meta_diaria,
        somente_dias_uteis=True,
        tolerancia_percentual=10.0,
        priorizar_data_entrega=True,
        valor_minimo_pedido=1000.0,
    ):
        if not state.tem_dados():
            raise ValueError("Importe a carteira antes de gerar a simulação.")

        if data_fim < data_inicio:
            raise ValueError("A data final não pode ser menor que a data inicial.")

        if meta_diaria <= 0:
            raise ValueError("Informe uma meta diária maior que zero.")

        tolerancia_percentual = self._normalizar_tolerancia(tolerancia_percentual)
        valor_minimo_pedido = self._normalizar_valor_minimo_pedido(valor_minimo_pedido)
        dias = self._gerar_dias(data_inicio, data_fim, somente_dias_uteis)
        if not dias:
            raise ValueError("O período selecionado não possui dias úteis.")

        candidatos = self._preparar_candidatos(state)
        candidatos_filtrados = [
            item for item in candidatos
            if float(item.get("valor_liberado", 0) or 0) >= valor_minimo_pedido
        ]
        candidatos_ignorados_minimo = [
            item for item in candidatos
            if float(item.get("valor_liberado", 0) or 0) < valor_minimo_pedido
        ]
        restantes = list(candidatos_filtrados)
        dias_resultado = []
        pedidos_usados = set()

        for dia in dias:
            selecionados, restantes = self._selecionar_pedidos(
                restantes,
                meta_diaria,
                tolerancia_percentual=tolerancia_percentual,
                priorizar_data_entrega=priorizar_data_entrega,
            )
            total_dia = sum(item["valor_liberado"] for item in selecionados)
            diferenca = total_dia - meta_diaria

            for item in selecionados:
                pedidos_usados.add(item["pedido"])

            dias_resultado.append({
                "data": dia,
                "meta": meta_diaria,
                "valor_estimado": total_dia,
                "diferenca": diferenca,
                "pedidos": selecionados,
                "qtd_pedidos": len(selecionados),
                "status": self._classificar_dia(total_dia, meta_diaria, tolerancia_percentual),
                "limite_minimo": self._limite_minimo(meta_diaria, tolerancia_percentual),
                "limite_maximo": self._limite_maximo(meta_diaria, tolerancia_percentual),
            })

        total_estimado = sum(dia["valor_estimado"] for dia in dias_resultado)
        meta_total = meta_diaria * len(dias_resultado)

        return {
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "somente_dias_uteis": somente_dias_uteis,
            "meta_diaria": meta_diaria,
            "tolerancia_percentual": tolerancia_percentual,
            "priorizar_data_entrega": bool(priorizar_data_entrega),
            "valor_minimo_pedido": valor_minimo_pedido,
            "pedidos_ignorados_valor_minimo": candidatos_ignorados_minimo,
            "qtd_pedidos_ignorados_valor_minimo": len(candidatos_ignorados_minimo),
            "valor_ignorado_valor_minimo": sum(item["valor_liberado"] for item in candidatos_ignorados_minimo),
            "meta_total": meta_total,
            "valor_estimado_total": total_estimado,
            "diferenca_total": total_estimado - meta_total,
            "qtd_dias": len(dias_resultado),
            "qtd_pedidos": len(pedidos_usados),
            "dias": dias_resultado,
            "pedidos_restantes": restantes,
            "pedidos_excluidos_simulacao": [],
            "valor_restante": sum(item["valor_liberado"] for item in restantes),
        }

    def recalcular_dia(self, resultado, indice_dia):
        if not resultado or "dias" not in resultado:
            raise ValueError("Gere uma simulação antes de recalcular o dia.")

        if indice_dia < 0 or indice_dia >= len(resultado["dias"]):
            raise ValueError("Dia inválido para recalcular.")

        dia = resultado["dias"][indice_dia]
        excluidos = set(str(p) for p in resultado.get("pedidos_excluidos_simulacao", []))
        tolerancia = self._normalizar_tolerancia(resultado.get("tolerancia_percentual", 10.0))
        priorizar = bool(resultado.get("priorizar_data_entrega", True))

        pool = []
        for pedido in dia.get("pedidos", []):
            if str(pedido.get("pedido", "")) not in excluidos:
                pool.append(pedido)

        for pedido in resultado.get("pedidos_restantes", []):
            if str(pedido.get("pedido", "")) not in excluidos:
                pool.append(pedido)

        selecionados, restantes = self._selecionar_pedidos(
            pool,
            dia.get("meta", resultado.get("meta_diaria", 0)),
            tolerancia_percentual=tolerancia,
            priorizar_data_entrega=priorizar,
        )

        dia["pedidos"] = selecionados
        resultado["pedidos_restantes"] = restantes
        self._atualizar_dia(dia, tolerancia)
        self._atualizar_totais_resultado(resultado)
        return resultado

    def remover_pedido_da_simulacao(self, resultado, indice_dia, pedido_numero):
        if not resultado or "dias" not in resultado:
            raise ValueError("Gere uma simulação antes de remover pedidos.")

        if indice_dia < 0 or indice_dia >= len(resultado["dias"]):
            raise ValueError("Dia inválido para remover pedido.")

        pedido_numero = str(pedido_numero).strip()
        if not pedido_numero:
            raise ValueError("Pedido inválido.")

        dia = resultado["dias"][indice_dia]
        pedidos_atuais = dia.get("pedidos", [])
        novos_pedidos = [p for p in pedidos_atuais if str(p.get("pedido", "")) != pedido_numero]

        if len(novos_pedidos) == len(pedidos_atuais):
            raise ValueError("Pedido não encontrado neste dia.")

        dia["pedidos"] = novos_pedidos
        excluidos = set(str(p) for p in resultado.get("pedidos_excluidos_simulacao", []))
        excluidos.add(pedido_numero)
        resultado["pedidos_excluidos_simulacao"] = sorted(excluidos)

        resultado["pedidos_restantes"] = [
            p for p in resultado.get("pedidos_restantes", []) if str(p.get("pedido", "")) != pedido_numero
        ]

        tolerancia = self._normalizar_tolerancia(resultado.get("tolerancia_percentual", 10.0))
        self._atualizar_dia(dia, tolerancia)
        self._atualizar_totais_resultado(resultado)
        return resultado

    def _atualizar_dia(self, dia, tolerancia_percentual):
        pedidos = dia.get("pedidos", [])
        meta = float(dia.get("meta", 0) or 0)
        valor = sum(float(p.get("valor_liberado", 0) or 0) for p in pedidos)
        dia["valor_estimado"] = valor
        dia["diferenca"] = valor - meta
        dia["qtd_pedidos"] = len(pedidos)
        dia["status"] = self._classificar_dia(valor, meta, tolerancia_percentual)
        dia["limite_minimo"] = self._limite_minimo(meta, tolerancia_percentual)
        dia["limite_maximo"] = self._limite_maximo(meta, tolerancia_percentual)

    def _atualizar_totais_resultado(self, resultado):
        dias = resultado.get("dias", [])
        total_estimado = sum(float(dia.get("valor_estimado", 0) or 0) for dia in dias)
        meta_total = sum(float(dia.get("meta", 0) or 0) for dia in dias)
        pedidos_usados = set()
        for dia in dias:
            for pedido in dia.get("pedidos", []):
                pedidos_usados.add(str(pedido.get("pedido", "")))

        resultado["meta_total"] = meta_total
        resultado["valor_estimado_total"] = total_estimado
        resultado["diferenca_total"] = total_estimado - meta_total
        resultado["qtd_dias"] = len(dias)
        resultado["qtd_pedidos"] = len([p for p in pedidos_usados if p])
        resultado["valor_restante"] = sum(float(p.get("valor_liberado", 0) or 0) for p in resultado.get("pedidos_restantes", []))

    def _gerar_dias(self, data_inicio, data_fim, somente_dias_uteis):
        dias = []
        atual = data_inicio

        while atual <= data_fim:
            if not somente_dias_uteis or atual.weekday() < 5:
                dias.append(atual)
            atual += timedelta(days=1)

        return dias

    def _preparar_candidatos(self, state):
        df = state.df_com_bloqueios(state.df_aberto())
        if df.empty:
            return []

        df = df.copy()

        pedidos_faturados = set(str(pedido) for pedido in getattr(state, "pedidos_faturados", set()))
        if pedidos_faturados:
            df = df[~df["Pedido Texto"].astype(str).isin(pedidos_faturados)].copy()

        pendencias = set()
        for id_linha in getattr(state, "pendencias_prog2", {}).keys():
            try:
                pendencias.add(int(id_linha))
            except (TypeError, ValueError):
                continue

        if pendencias and "ID Linha" in df.columns:
            df["_Pendente Prog2"] = df["ID Linha"].astype(int).isin(pendencias)
        else:
            df["_Pendente Prog2"] = False

        df["_Valor Elegivel"] = df["_Valor Liberado"].where(~df["_Pendente Prog2"], 0)
        df["_Item Elegivel"] = (df["_Valor Elegivel"] > 0) & (~df["_Bloqueado"])

        registros = []

        for pedido, grupo in df.groupby("Pedido Texto", sort=False):
            grupo_elegivel = grupo[grupo["_Item Elegivel"]].copy()
            valor_liberado = float(grupo_elegivel["_Valor Elegivel"].sum()) if not grupo_elegivel.empty else 0.0

            if valor_liberado <= 0:
                continue

            valor_total = float(grupo["Valor em Carteira"].sum())
            valor_bloqueado = float(max(valor_total - valor_liberado, 0))
            qtde_total = float(grupo_elegivel["Saldo a Faturar"].sum()) if "Saldo a Faturar" in grupo_elegivel else 0.0

            data_entrega = self._menor_data(grupo.get("Data Entrega"))
            cliente = str(grupo["Cliente"].iloc[0]) if "Cliente" in grupo.columns else ""
            cliente_abrev = str(grupo["Cliente Abrev"].iloc[0]) if "Cliente Abrev" in grupo.columns else cliente

            itens = self._preparar_itens_pedido(grupo_elegivel)

            registros.append({
                "pedido": str(pedido),
                "cliente": cliente_abrev,
                "cliente_original": cliente,
                "data_entrega": data_entrega,
                "valor_total": valor_total,
                "valor_liberado": valor_liberado,
                "valor_bloqueado": valor_bloqueado,
                "qtd_itens": int(len(grupo_elegivel)),
                "qtd_itens_ignorados": int(len(grupo) - len(grupo_elegivel)),
                "quantidade": qtde_total,
                "status": "Parcial" if valor_bloqueado > 0 else "Total",
                "itens": itens,
            })

        registros.sort(
            key=lambda item: (
                item["data_entrega"] or date.max,
                -item["valor_liberado"],
                item["pedido"],
            )
        )

        return registros

    def _preparar_itens_pedido(self, grupo_elegivel):
        itens = []

        if grupo_elegivel is None or grupo_elegivel.empty:
            return itens

        for _, linha in grupo_elegivel.iterrows():
            valor = self._valor_float(linha.get("_Valor Elegivel", linha.get("Valor em Carteira", 0)))
            quantidade = self._valor_float(linha.get("Saldo a Faturar", 0))
            data_entrega = self._data_linha(linha.get("Data Entrega"))

            itens.append({
                "id_linha": self._valor_int(linha.get("ID Linha")),
                "item": self._texto(linha.get("Item")),
                "descricao": self._texto(linha.get("Descrição Item")),
                "quantidade": quantidade,
                "valor": valor,
                "data_entrega": data_entrega,
                "grupo": self._texto(linha.get("Grupo de faturamento Descrição", linha.get("Grupo Faturamento", ""))),
                "observacao": self._primeiro_texto(linha, ["Observação", "Observação 01", "OBS"]),
            })

        itens.sort(key=lambda item: (item["data_entrega"] or date.max, item["item"], item["descricao"]))
        return itens

    def _texto(self, valor):
        if valor is None or pd.isna(valor):
            return ""
        return str(valor).strip()

    def _primeiro_texto(self, linha, colunas):
        for coluna in colunas:
            if coluna in linha.index:
                texto = self._texto(linha.get(coluna))
                if texto:
                    return texto
        return ""

    def _valor_float(self, valor):
        try:
            if valor is None or pd.isna(valor):
                return 0.0
            return float(valor)
        except (TypeError, ValueError):
            return 0.0

    def _valor_int(self, valor):
        try:
            if valor is None or pd.isna(valor):
                return None
            return int(valor)
        except (TypeError, ValueError):
            return None

    def _data_linha(self, valor):
        if valor is None or pd.isna(valor):
            return None

        data = pd.to_datetime(valor, errors="coerce", dayfirst=True)
        if pd.isna(data):
            return None

        return data.date()

    def _menor_data(self, serie):
        if serie is None:
            return None

        datas = pd.to_datetime(serie, errors="coerce", dayfirst=True)
        datas = datas.dropna()

        if datas.empty:
            return None

        return datas.min().date()

    def _selecionar_pedidos(
        self,
        candidatos,
        meta_diaria,
        tolerancia_percentual=10.0,
        priorizar_data_entrega=True,
    ):
        restantes = list(candidatos)
        selecionados = []
        total = 0.0
        tolerancia_percentual = self._normalizar_tolerancia(tolerancia_percentual)
        limite_minimo = self._limite_minimo(meta_diaria, tolerancia_percentual)
        limite_maximo = self._limite_maximo(meta_diaria, tolerancia_percentual)

        while restantes:
            if total >= limite_minimo and total <= limite_maximo:
                break

            melhor_indice = None
            melhor_chave = None

            for indice, candidato in enumerate(restantes):
                valor = float(candidato.get("valor_liberado", 0) or 0)
                novo_total = total + valor
                entrega = candidato.get("data_entrega") or date.max
                pedido = str(candidato.get("pedido", ""))

                if priorizar_data_entrega:
                    chave = self._chave_prioridade_entrega(
                        entrega,
                        novo_total,
                        meta_diaria,
                        limite_minimo,
                        limite_maximo,
                        valor,
                        pedido,
                    )
                else:
                    chave = self._chave_prioridade_meta(
                        entrega,
                        novo_total,
                        meta_diaria,
                        limite_minimo,
                        limite_maximo,
                        valor,
                        pedido,
                    )

                if melhor_chave is None or chave < melhor_chave:
                    melhor_chave = chave
                    melhor_indice = indice

            if melhor_indice is None:
                break

            candidato = restantes[melhor_indice]
            novo_total = total + float(candidato.get("valor_liberado", 0) or 0)

            # Se já existe seleção e a melhor opção só piora muito acima da tolerância, para.
            if selecionados and novo_total > limite_maximo:
                diferenca_atual = abs(meta_diaria - total)
                nova_diferenca = abs(meta_diaria - novo_total)
                if nova_diferenca >= diferenca_atual:
                    break

            selecionados.append(restantes.pop(melhor_indice))
            total = novo_total

        return selecionados, restantes

    def _chave_prioridade_meta(self, entrega, novo_total, meta, minimo, maximo, valor, pedido):
        if minimo <= novo_total <= maximo:
            faixa = 0
            ajuste = abs(meta - novo_total)
        elif novo_total < minimo:
            faixa = 1
            ajuste = minimo - novo_total
        else:
            faixa = 2
            ajuste = novo_total - maximo

        return (
            faixa,
            ajuste,
            abs(meta - novo_total),
            entrega,
            -valor,
            pedido,
        )

    def _chave_prioridade_entrega(self, entrega, novo_total, meta, minimo, maximo, valor, pedido):
        if novo_total <= maximo:
            estoura_tolerancia = 0
        else:
            estoura_tolerancia = 1

        if minimo <= novo_total <= maximo:
            faixa = 0
        elif novo_total < minimo:
            faixa = 1
        else:
            faixa = 2

        return (
            estoura_tolerancia,
            entrega,
            faixa,
            abs(meta - novo_total),
            -valor,
            pedido,
        )

    def _normalizar_tolerancia(self, tolerancia_percentual):
        try:
            valor = float(tolerancia_percentual)
        except (TypeError, ValueError):
            valor = 10.0
        return max(0.0, min(valor, 100.0))

    def _normalizar_valor_minimo_pedido(self, valor_minimo_pedido):
        try:
            valor = float(valor_minimo_pedido)
        except (TypeError, ValueError):
            valor = 1000.0
        return max(0.0, valor)

    def _limite_minimo(self, meta, tolerancia_percentual):
        return float(meta or 0) * (1 - (float(tolerancia_percentual or 0) / 100))

    def _limite_maximo(self, meta, tolerancia_percentual):
        return float(meta or 0) * (1 + (float(tolerancia_percentual or 0) / 100))

    def _classificar_dia(self, valor, meta, tolerancia_percentual=10.0):
        if meta <= 0:
            return "Sem meta"

        minimo = self._limite_minimo(meta, tolerancia_percentual)
        maximo = self._limite_maximo(meta, tolerancia_percentual)

        if minimo <= valor <= maximo:
            return "Dentro da tolerância"
        if valor < minimo:
            return "Abaixo da meta"
        return "Acima da tolerância"
