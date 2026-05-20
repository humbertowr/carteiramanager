import re
import unicodedata

import pandas as pd

from core.formatters import formatar_numero, normalizar_texto


CLIENTES_BLOQUEADOS_1 = {
    "WEG CESTARI REDUTORES E MOTORREDUTORES S A": "WEG",
    "IND DE IMPL AGRICOLAS VENCE TUDO IMP E EXPORTACAO LTDA": "VENCE TUDO",
    "EIXO SUL DISTRIBUIDORA DE PECAS LTDA ME": "EIXO SUL",
    "SCHEER CHURRASQUEIRAS E ACESSORIOS LTDA": "SHER",
    "ZURLO IMPLEMENTOS RODOVIARIOS LTDA": "ZURLO",
    "RODOTECNICA INDUSTRIA DE IMPLEMENTOS RODOVIARIOS EIRELI": "RODOTECNICA",
    "NIJU INDUSTRIA E COMERCIO DE IMPLEMENTOS RODOVIARIOS LTDA": "NIJU",
    "MIGRA EQUIPAMENTOS PARA MOVIMENTACAO LTDA": "MIGRA",
}

CLIENTES_BLOQUEIO_PADRAO = CLIENTES_BLOQUEADOS_1


PALAVRAS_REMOVER_ABREVIACAO = {
    "LTDA",
    "ME",
    "EIRELI",
    "S",
    "A",
    "SA",
    "S A",
    "DE",
    "DA",
    "DO",
    "DAS",
    "DOS",
    "E",
    "IND",
    "INDUSTRIA",
    "COMERCIO",
    "COMERCIAL",
    "IMPORTACAO",
    "EXPORTACAO",
    "IMP",
    "EXP",
}


def normalizar_chave_cliente(valor):
    texto = normalizar_texto(valor)

    if not texto:
        return ""

    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(char for char in texto if not unicodedata.combining(char))
    texto = texto.upper()
    texto = re.sub(r"[^A-Z0-9]+", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


def gerar_abreviacao_generica_cliente(cliente):
    chave = normalizar_chave_cliente(cliente)

    if not chave:
        return ""

    palavras = [
        palavra
        for palavra in chave.split()
        if palavra not in PALAVRAS_REMOVER_ABREVIACAO
    ]

    if not palavras:
        return normalizar_texto(cliente)

    if len(palavras) == 1:
        return palavras[0]

    return " ".join(palavras[:2])


def abreviar_grupo_faturamento(valor):
    texto = normalizar_chave_cliente(valor)

    if texto == "IMEDIATO":
        return "I"

    if texto == "PROGRAMADO":
        return "P"

    return normalizar_texto(valor)


class AppState:
    def __init__(self):
        self.df_original = None

        self.linhas_bloqueadas = set()
        self.codigos_itens_bloqueados = set()
        self.pedidos_bloqueados = set()
        self.observacoes_bloqueadas = set()
        self.clientes_bloqueados = set()

        self.pedidos_prog2 = []

        self.motivos_linha = {}
        self.motivos_item = {}
        self.motivos_pedido = {}
        self.motivos_observacao = {}
        self.motivos_cliente = {}

    def carregar_dataframe(self, df):
        df = df.copy()

        df["Pedido Texto"] = df["Pedido"].astype(str)
        df["Item Texto"] = df["Item"].astype(str)
        df["Cliente Chave"] = df["Cliente"].apply(normalizar_chave_cliente)
        df["Cliente Abrev"] = df["Cliente"].apply(self.abreviar_cliente)
        df["Observação Normalizada"] = df["Observação"].apply(normalizar_texto)
        df["Grupo Faturamento Abrev"] = df["Grupo Faturamento"].apply(abreviar_grupo_faturamento)

        self.df_original = df

        self.linhas_bloqueadas.clear()
        self.codigos_itens_bloqueados.clear()
        self.pedidos_bloqueados.clear()
        self.observacoes_bloqueadas.clear()
        self.clientes_bloqueados.clear()
        self.pedidos_prog2.clear()

        self.motivos_linha.clear()
        self.motivos_item.clear()
        self.motivos_pedido.clear()
        self.motivos_observacao.clear()
        self.motivos_cliente.clear()

    def tem_dados(self):
        return self.df_original is not None

    def df_aberto(self):
        if self.df_original is None:
            return pd.DataFrame()

        return self.df_original[self.df_original["Saldo a Faturar"] > 0].copy()

    def pegar_linha_por_id(self, id_linha):
        if self.df_original is None:
            return None

        resultado = self.df_original[self.df_original["ID Linha"] == int(id_linha)]

        if resultado.empty:
            return None

        return resultado.iloc[0]

    def abreviar_cliente(self, cliente):
        chave = normalizar_chave_cliente(cliente)

        if chave in CLIENTES_BLOQUEADOS_1:
            return CLIENTES_BLOQUEADOS_1[chave]

        return gerar_abreviacao_generica_cliente(cliente)

    def clientes_preset_bloqueados_1(self):
        return set(CLIENTES_BLOQUEADOS_1.keys())

    def pedidos_bloqueados_por_observacao_set(self):
        if self.df_original is None or not self.observacoes_bloqueadas:
            return set()

        df = self.df_aberto()

        if df.empty:
            return set()

        df_obs = df[df["Observação Normalizada"].isin(self.observacoes_bloqueadas)]

        return set(df_obs["Pedido Texto"].unique())

    def pedidos_bloqueados_por_cliente_set(self):
        if self.df_original is None or not self.clientes_bloqueados:
            return set()

        df = self.df_aberto()

        if df.empty:
            return set()

        df_clientes = df[df["Cliente Chave"].isin(self.clientes_bloqueados)]

        return set(df_clientes["Pedido Texto"].unique())

    def df_com_bloqueios(self, df):
        if df is None or df.empty:
            return pd.DataFrame() if df is None else df.copy()

        resultado = df.copy()

        mask_linha = resultado["ID Linha"].astype(int).isin(self.linhas_bloqueadas)
        mask_item = resultado["Item Texto"].isin(self.codigos_itens_bloqueados)
        mask_pedido = resultado["Pedido Texto"].isin(self.pedidos_bloqueados)

        if self.observacoes_bloqueadas:
            pedidos_obs = self.pedidos_bloqueados_por_observacao_set()
            mask_observacao = resultado["Pedido Texto"].isin(pedidos_obs)
        else:
            mask_observacao = pd.Series(False, index=resultado.index)

        if self.clientes_bloqueados:
            mask_cliente = resultado["Cliente Chave"].isin(self.clientes_bloqueados)
        else:
            mask_cliente = pd.Series(False, index=resultado.index)

        mask_bloqueado = (
            mask_linha
            | mask_item
            | mask_pedido
            | mask_observacao
            | mask_cliente
        )

        resultado["_Bloqueado"] = mask_bloqueado
        resultado["_Tipo Bloqueio"] = ""

        resultado.loc[mask_linha, "_Tipo Bloqueio"] = "Item bloqueado"
        resultado.loc[mask_item, "_Tipo Bloqueio"] = "Item bloqueado global"
        resultado.loc[mask_observacao, "_Tipo Bloqueio"] = "Observação bloqueada"
        resultado.loc[mask_cliente, "_Tipo Bloqueio"] = resultado.loc[mask_cliente, "Cliente Chave"].apply(
            lambda chave: f"Cliente bloqueado: {CLIENTES_BLOQUEADOS_1.get(chave, gerar_abreviacao_generica_cliente(chave))}"
        )
        resultado.loc[mask_pedido, "_Tipo Bloqueio"] = "Pedido bloqueado"

        resultado["_Valor Bloqueado"] = resultado["Valor em Carteira"].where(resultado["_Bloqueado"], 0)
        resultado["_Valor Liberado"] = resultado["Valor em Carteira"] - resultado["_Valor Bloqueado"]

        return resultado

    def cliente_bloqueado_da_linha(self, linha):
        chave_cliente = linha.get("Cliente Chave", normalizar_chave_cliente(linha["Cliente"]))

        if chave_cliente in self.clientes_bloqueados:
            return chave_cliente

        return None

    def cliente_bloqueado_do_pedido(self, pedido):
        if self.df_original is None or not self.clientes_bloqueados:
            return None

        pedido_str = str(pedido)

        grupo = self.df_original[self.df_original["Pedido Texto"] == pedido_str]

        if grupo.empty:
            return None

        clientes = grupo["Cliente Chave"].unique()

        for cliente in clientes:
            if cliente in self.clientes_bloqueados:
                return cliente

        return None

    def pedido_bloqueado_por_cliente(self, pedido):
        return self.cliente_bloqueado_do_pedido(pedido) is not None

    def observacao_bloqueada_do_pedido(self, pedido):
        if self.df_original is None or not self.observacoes_bloqueadas:
            return None

        pedido_str = str(pedido)

        grupo = self.df_original[self.df_original["Pedido Texto"] == pedido_str]

        if grupo.empty:
            return None

        observacoes = grupo["Observação Normalizada"].unique()

        for observacao in observacoes:
            if observacao in self.observacoes_bloqueadas:
                return observacao

        return None

    def pedido_bloqueado_por_observacao(self, pedido):
        return self.observacao_bloqueada_do_pedido(pedido) is not None

    def linha_bloqueada(self, linha):
        id_linha = int(linha["ID Linha"])
        pedido = str(linha["Pedido"])
        item = str(linha["Item"])
        cliente_chave = linha.get("Cliente Chave", normalizar_chave_cliente(linha["Cliente"]))

        return (
            id_linha in self.linhas_bloqueadas
            or item in self.codigos_itens_bloqueados
            or pedido in self.pedidos_bloqueados
            or self.pedido_bloqueado_por_observacao(pedido)
            or cliente_chave in self.clientes_bloqueados
        )

    def tipo_bloqueio_linha(self, linha):
        if "_Tipo Bloqueio" in linha and linha["_Tipo Bloqueio"]:
            return linha["_Tipo Bloqueio"]

        id_linha = int(linha["ID Linha"])
        pedido = str(linha["Pedido"])
        item = str(linha["Item"])
        cliente_chave = linha.get("Cliente Chave", normalizar_chave_cliente(linha["Cliente"]))

        if pedido in self.pedidos_bloqueados:
            return "Pedido bloqueado"

        if cliente_chave in self.clientes_bloqueados:
            nome_curto = CLIENTES_BLOQUEADOS_1.get(
                cliente_chave,
                gerar_abreviacao_generica_cliente(cliente_chave)
            )
            return f"Cliente bloqueado: {nome_curto}"

        if self.pedido_bloqueado_por_observacao(pedido):
            return "Observação bloqueada"

        if item in self.codigos_itens_bloqueados:
            return "Item bloqueado global"

        if id_linha in self.linhas_bloqueadas:
            return "Item bloqueado"

        return ""

    def motivo_bloqueio_linha(self, linha):
        id_linha = int(linha["ID Linha"])
        pedido = str(linha["Pedido"])
        item = str(linha["Item"])
        cliente_chave = linha.get("Cliente Chave", normalizar_chave_cliente(linha["Cliente"]))

        if pedido in self.pedidos_bloqueados:
            return self.motivos_pedido.get(pedido, "")

        if cliente_chave in self.clientes_bloqueados:
            nome_curto = CLIENTES_BLOQUEADOS_1.get(
                cliente_chave,
                gerar_abreviacao_generica_cliente(cliente_chave)
            )
            return self.motivos_cliente.get(
                cliente_chave,
                f"Bloqueado por cliente: {nome_curto}"
            )

        observacao_bloqueada = self.observacao_bloqueada_do_pedido(pedido)
        if observacao_bloqueada:
            return self.motivos_observacao.get(
                observacao_bloqueada,
                f"Bloqueado por observação: {observacao_bloqueada}"
            )

        if item in self.codigos_itens_bloqueados:
            return self.motivos_item.get(item, "")

        if id_linha in self.linhas_bloqueadas:
            return self.motivos_linha.get(id_linha, "")

        return ""

    def calcular_valores_pedido(self, grupo):
        if grupo.empty:
            return 0, 0, 0

        grupo_bloqueios = self.df_com_bloqueios(grupo)

        valor_original = grupo_bloqueios["Valor em Carteira"].sum()
        valor_bloqueado = grupo_bloqueios["_Valor Bloqueado"].sum()
        valor_liberado = grupo_bloqueios["_Valor Liberado"].sum()

        return valor_original, valor_bloqueado, valor_liberado

    def calcular_valor_bloqueado_total(self):
        if self.df_original is None:
            return 0

        df = self.df_com_bloqueios(self.df_aberto())

        if df.empty:
            return 0

        return df["_Valor Bloqueado"].sum()

    def calcular_totais_prog2(self):
        if self.df_original is None:
            return {
                "pedidos": 0,
                "itens": 0,
                "valor_total": 0,
                "valor_bloqueado": 0,
                "valor_liberado": 0,
            }

        df = self.df_com_bloqueios(self.df_aberto())

        total_pedidos = 0
        total_itens = 0
        valor_total = 0
        valor_bloqueado = 0
        valor_liberado = 0

        pedidos_prog2 = set(str(pedido) for pedido in self.pedidos_prog2)

        if not pedidos_prog2:
            return {
                "pedidos": 0,
                "itens": 0,
                "valor_total": 0,
                "valor_bloqueado": 0,
                "valor_liberado": 0,
            }

        df = df[df["Pedido Texto"].isin(pedidos_prog2)]

        for pedido, grupo in df.groupby("Pedido Texto", sort=False):
            total_pedidos += 1
            total_itens += len(grupo)
            valor_total += grupo["Valor em Carteira"].sum()
            valor_bloqueado += grupo["_Valor Bloqueado"].sum()
            valor_liberado += grupo["_Valor Liberado"].sum()

        return {
            "pedidos": total_pedidos,
            "itens": total_itens,
            "valor_total": valor_total,
            "valor_bloqueado": valor_bloqueado,
            "valor_liberado": valor_liberado,
        }

    def obter_observacoes_disponiveis(self):
        if self.df_original is None:
            return []

        df = self.df_aberto().copy()

        if df.empty:
            return []

        df = df[df["Observação Normalizada"] != ""]

        if df.empty:
            return []

        registros = []

        for observacao, grupo in df.groupby("Observação Normalizada", sort=True):
            registros.append({
                "observacao": observacao,
                "pedidos": grupo["Pedido"].nunique(),
                "itens": len(grupo),
                "valor": grupo["Valor em Carteira"].sum(),
            })

        registros.sort(key=lambda item: item["observacao"].lower())

        return registros

    def obter_clientes_bloqueio_disponiveis(self):
        if self.df_original is None:
            return []

        df = self.df_aberto().copy()

        if df.empty:
            return []

        df = df[df["Cliente Chave"] != ""]

        registros = []

        for cliente_chave, grupo in df.groupby("Cliente Chave", sort=True):
            nome_original = normalizar_texto(grupo["Cliente"].iloc[0])
            nome_curto = self.abreviar_cliente(nome_original)

            registros.append({
                "cliente_chave": cliente_chave,
                "cliente_curto": nome_curto,
                "cliente_original": nome_original,
                "pedidos": grupo["Pedido"].nunique(),
                "itens": len(grupo),
                "valor": grupo["Valor em Carteira"].sum(),
                "preset_1": cliente_chave in CLIENTES_BLOQUEADOS_1,
            })

        registros.sort(key=lambda item: item["cliente_curto"].lower())

        return registros

    def obter_itens_bloqueio_disponiveis(self):
        if self.df_original is None:
            return []

        df = self.df_aberto().copy()

        if df.empty:
            return []

        registros = []

        for item, grupo in df.groupby("Item Texto", sort=True):
            descricoes = [
                normalizar_texto(valor)
                for valor in grupo["Descrição Item"].dropna().unique()
                if normalizar_texto(valor)
            ]

            descricao = descricoes[0] if descricoes else ""

            registros.append({
                "item": str(item),
                "descricao": descricao,
                "pedidos": grupo["Pedido"].nunique(),
                "clientes": grupo["Cliente"].nunique(),
                "linhas": len(group := grupo),
                "valor": group["Valor em Carteira"].sum(),
            })

        registros.sort(key=lambda item: item["item"])

        return registros

    def bloquear_linha(self, id_linha, motivo=""):
        id_linha = int(id_linha)
        self.linhas_bloqueadas.add(id_linha)

        if motivo:
            self.motivos_linha[id_linha] = motivo

    def bloquear_pedido(self, pedido, motivo=""):
        pedido = str(pedido)
        self.pedidos_bloqueados.add(pedido)

        if motivo:
            self.motivos_pedido[pedido] = motivo

    def bloquear_item_global(self, codigo_item, motivo=""):
        codigo_item = str(codigo_item)
        self.codigos_itens_bloqueados.add(codigo_item)

        if motivo:
            self.motivos_item[codigo_item] = motivo

    def bloquear_itens_globais(self, codigos_itens, motivo=""):
        for codigo_item in codigos_itens:
            self.bloquear_item_global(codigo_item, motivo)

    def bloquear_observacoes(self, observacoes, motivo=""):
        for observacao in observacoes:
            observacao = str(observacao)
            self.observacoes_bloqueadas.add(observacao)

            if motivo:
                self.motivos_observacao[observacao] = motivo
            else:
                self.motivos_observacao[observacao] = f"Bloqueado por observação: {observacao}"

    def bloquear_clientes(self, clientes_chave, motivo=""):
        for cliente_chave in clientes_chave:
            cliente_chave = str(cliente_chave)
            self.clientes_bloqueados.add(cliente_chave)

            nome_curto = CLIENTES_BLOQUEADOS_1.get(
                cliente_chave,
                gerar_abreviacao_generica_cliente(cliente_chave)
            )

            if motivo:
                self.motivos_cliente[cliente_chave] = motivo
            else:
                self.motivos_cliente[cliente_chave] = f"Bloqueado por cliente: {nome_curto}"

    def liberar_linha(self, id_linha):
        id_linha = int(id_linha)
        self.linhas_bloqueadas.discard(id_linha)
        self.motivos_linha.pop(id_linha, None)

    def liberar_pedido(self, pedido):
        pedido = str(pedido)
        self.pedidos_bloqueados.discard(pedido)
        self.motivos_pedido.pop(pedido, None)

    def liberar_item_global(self, codigo_item):
        codigo_item = str(codigo_item)
        self.codigos_itens_bloqueados.discard(codigo_item)
        self.motivos_item.pop(codigo_item, None)

    def liberar_itens_globais(self, codigos_itens):
        for codigo_item in codigos_itens:
            self.liberar_item_global(codigo_item)

    def liberar_observacao(self, observacao):
        observacao = str(observacao)
        self.observacoes_bloqueadas.discard(observacao)
        self.motivos_observacao.pop(observacao, None)

    def liberar_cliente(self, cliente_chave):
        cliente_chave = str(cliente_chave)
        self.clientes_bloqueados.discard(cliente_chave)
        self.motivos_cliente.pop(cliente_chave, None)

    def limpar_bloqueios(self):
        self.linhas_bloqueadas.clear()
        self.codigos_itens_bloqueados.clear()
        self.pedidos_bloqueados.clear()
        self.observacoes_bloqueadas.clear()
        self.clientes_bloqueados.clear()

        self.motivos_linha.clear()
        self.motivos_item.clear()
        self.motivos_pedido.clear()
        self.motivos_observacao.clear()
        self.motivos_cliente.clear()

    def adicionar_pedido_prog2(self, pedido):
        pedido = str(pedido)

        if pedido not in self.pedidos_prog2:
            self.pedidos_prog2.append(pedido)

    def remover_pedido_prog2(self, pedido):
        pedido = str(pedido)

        self.pedidos_prog2 = [
            p for p in self.pedidos_prog2
            if str(p) != pedido
        ]

    def limpar_prog2(self):
        self.pedidos_prog2.clear()

    def gerar_df_pedidos_ajustados(self):
        if self.df_original is None:
            return pd.DataFrame()

        df = self.df_com_bloqueios(self.df_aberto())
        registros = []

        for pedido, grupo in df.groupby("Pedido", sort=False):
            cliente_original = str(grupo["Cliente"].iloc[0])
            cliente_abrev = self.abreviar_cliente(cliente_original)
            valor_original = grupo["Valor em Carteira"].sum()
            valor_bloqueado = grupo["_Valor Bloqueado"].sum()
            valor_liberado = group_liberado = grupo["_Valor Liberado"].sum()
            pedido_str = str(pedido)

            if pedido_str in self.pedidos_bloqueados:
                status = "Pedido bloqueado"
            elif self.pedido_bloqueado_por_cliente(pedido_str):
                status = "Bloqueado por cliente"
            elif self.pedido_bloqueado_por_observacao(pedido_str):
                status = "Bloqueado por observação"
            elif valor_original > 0 and valor_bloqueado >= valor_original:
                status = "Totalmente bloqueado"
            elif valor_bloqueado > 0:
                status = "Parcialmente bloqueado"
            else:
                status = "Liberado"

            registros.append({
                "Pedido": pedido,
                "Cliente": cliente_abrev,
                "Cliente Original": cliente_original,
                "Qtd. Itens": len(grupo),
                "Qtde Saldo": grupo["Saldo a Faturar"].sum(),
                "Valor Original Pedido": valor_original,
                "Valor Bloqueado": valor_bloqueado,
                "Valor Liberado Pedido": group_liberado,
                "Status Bloqueio": status,
            })

        return pd.DataFrame(registros)

    def gerar_df_prog2(self):
        if self.df_original is None:
            return pd.DataFrame()

        df = self.df_com_bloqueios(self.df_aberto())
        registros = []

        for pedido in self.pedidos_prog2:
            grupo = df[df["Pedido Texto"] == str(pedido)]

            if grupo.empty:
                continue

            cliente_original = str(grupo["Cliente"].iloc[0])
            cliente_abrev = self.abreviar_cliente(cliente_original)

            valor_original = grupo["Valor em Carteira"].sum()
            valor_bloqueado = grupo["_Valor Bloqueado"].sum()
            valor_liberado = grupo["_Valor Liberado"].sum()

            itens_texto = []

            for _, linha in grupo.iterrows():
                itens_texto.append(
                    f'{linha["Item"]} - {linha["Descrição Item"]} | Qtd: {formatar_numero(linha["Saldo a Faturar"])}'
                )

            registros.append({
                "Pedido": pedido,
                "Cliente": cliente_abrev,
                "Cliente Original": cliente_original,
                "Valor Total Pedido": valor_original,
                "Valor Bloqueado": valor_bloqueado,
                "Valor Liberado": valor_liberado,
                "Qtd. Itens": len(grupo),
                "Itens": " ; ".join(itens_texto),
            })

        return pd.DataFrame(registros)

    def gerar_df_pedidos_liberados(self):
        if self.df_original is None:
            return pd.DataFrame()

        df = self.df_com_bloqueios(self.df_aberto())
        df = df[~df["_Bloqueado"]].copy()

        registros = []

        for pedido, grupo in df.groupby("Pedido", sort=False):
            cliente_original = str(grupo["Cliente"].iloc[0])
            cliente_abrev = self.abreviar_cliente(cliente_original)

            registros.append({
                "Pedido": pedido,
                "Cliente": cliente_abrev,
                "Cliente Original": cliente_original,
                "Qtd. Itens Liberados": len(grupo),
                "Qtde Saldo Liberada": grupo["Saldo a Faturar"].sum(),
                "Valor Liberado": grupo["Valor em Carteira"].sum(),
                "Status": "Liberado para faturar",
            })

        return pd.DataFrame(registros)

    def gerar_df_bloqueios(self):
        if self.df_original is None:
            return pd.DataFrame()

        df = self.df_com_bloqueios(self.df_aberto())
        df_bloqueados = df[df["_Bloqueado"]].copy()

        if df_bloqueados.empty:
            return pd.DataFrame(
                columns=[
                    "Tipo Bloqueio",
                    "ID Linha",
                    "Pedido",
                    "Cliente",
                    "Cliente Original",
                    "Item",
                    "Descrição Item",
                    "Observação",
                    "Qtde Saldo",
                    "Valor Bloqueado",
                    "Motivo",
                ]
            )

        df_bloqueados["Motivo"] = df_bloqueados.apply(
            lambda linha: self.motivo_bloqueio_linha(linha),
            axis=1
        )

        df_saida = df_bloqueados[[
            "_Tipo Bloqueio",
            "ID Linha",
            "Pedido",
            "Cliente Abrev",
            "Cliente",
            "Item",
            "Descrição Item",
            "Observação Normalizada",
            "Saldo a Faturar",
            "Valor em Carteira",
            "Motivo",
        ]].copy()

        df_saida.rename(
            columns={
                "_Tipo Bloqueio": "Tipo Bloqueio",
                "Cliente Abrev": "Cliente",
                "Cliente": "Cliente Original",
                "Observação Normalizada": "Observação",
                "Saldo a Faturar": "Qtde Saldo",
                "Valor em Carteira": "Valor Bloqueado",
            },
            inplace=True
        )

        df_saida.sort_values(["Pedido", "Item"], inplace=True)

        return df_saida

    def gerar_df_carteira_com_bloqueios(self):
        if self.df_original is None:
            return pd.DataFrame()

        df = self.df_com_bloqueios(self.df_original)

        df["Cliente Original"] = df["Cliente"]
        df["Bloqueado para Faturar"] = df["_Bloqueado"].apply(lambda valor: "Sim" if valor else "Não")
        df["Tipo Bloqueio"] = df["_Tipo Bloqueio"]
        df["Motivo Bloqueio"] = df.apply(
            lambda linha: self.motivo_bloqueio_linha(linha),
            axis=1
        )
        df["Valor Bloqueado"] = df["_Valor Bloqueado"]
        df["Valor Liberado"] = df["_Valor Liberado"]

        return df