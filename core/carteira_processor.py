import csv
from datetime import datetime

import pandas as pd

from core.formatters import converter_numero_br


COLUNAS_ORIGINAIS = {
    "pedido": "Pedido - Pedido (Número)",
    "codigo_cliente": "Pedido - Cliente (Código)",
    "cliente": "Cliente - Razão social (Cliente)",
    "data_emissao": "Pedido - Data de emissão",
    "data_base_faturamento": "Pedido - Data base de faturamento",
    "data_entrega": "Pedido - Data de entrega",
    "data_previsao_faturamento": "Pedido - Data de previsão de faturamento",
    "item": "Item",
    "descricao_item": "Item - Descrição (Item)",
    "qtde_solicitada": "Qtde. solicitada",
    "qtde_faturada": "Qtde. faturada",
    "valor_unitario": "Valor unitário",
    "valor_total": "Valor total",
    "grupo_faturamento": "Grupo de faturamento - Descrição (Grupo Faturamento)",
    "observacao": "Pedido - Observação 01",
}


def detectar_encoding(caminho_arquivo):
    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin1"]

    for encoding in encodings:
        try:
            with open(caminho_arquivo, "r", encoding=encoding) as arquivo:
                arquivo.read(5000)
            return encoding
        except UnicodeDecodeError:
            continue

    return "latin1"


def detectar_separador(caminho_arquivo, encoding):
    with open(caminho_arquivo, "r", encoding=encoding, errors="replace") as arquivo:
        amostra = arquivo.read(5000)

    try:
        dialecto = csv.Sniffer().sniff(amostra)
        return dialecto.delimiter
    except Exception:
        if "\t" in amostra:
            return "\t"
        if ";" in amostra:
            return ";"
        if "," in amostra:
            return ","

    return ";"


def carregar_carteira(caminho_arquivo):
    encoding = detectar_encoding(caminho_arquivo)
    separador = detectar_separador(caminho_arquivo, encoding)

    df = pd.read_csv(
        caminho_arquivo,
        sep=separador,
        encoding=encoding,
        dtype=str,
        engine="python"
    )

    df.columns = df.columns.str.strip()

    colunas_necessarias = list(COLUNAS_ORIGINAIS.values())
    colunas_faltando = [coluna for coluna in colunas_necessarias if coluna not in df.columns]

    if colunas_faltando:
        raise ValueError(
            "O arquivo importado não tem todas as colunas necessárias.\n\n"
            "Colunas faltando:\n"
            + "\n".join(colunas_faltando)
        )

    df = df[colunas_necessarias].copy()

    df.rename(
        columns={
            COLUNAS_ORIGINAIS["pedido"]: "Pedido",
            COLUNAS_ORIGINAIS["codigo_cliente"]: "Código Cliente",
            COLUNAS_ORIGINAIS["cliente"]: "Cliente",
            COLUNAS_ORIGINAIS["data_emissao"]: "Data Emissão",
            COLUNAS_ORIGINAIS["data_base_faturamento"]: "Data Base Faturamento",
            COLUNAS_ORIGINAIS["data_entrega"]: "Data Entrega",
            COLUNAS_ORIGINAIS["data_previsao_faturamento"]: "Previsão Faturamento",
            COLUNAS_ORIGINAIS["item"]: "Item",
            COLUNAS_ORIGINAIS["descricao_item"]: "Descrição Item",
            COLUNAS_ORIGINAIS["qtde_solicitada"]: "Qtde Solicitada",
            COLUNAS_ORIGINAIS["qtde_faturada"]: "Qtde Faturada",
            COLUNAS_ORIGINAIS["valor_unitario"]: "Valor Unitário",
            COLUNAS_ORIGINAIS["valor_total"]: "Valor Total",
            COLUNAS_ORIGINAIS["grupo_faturamento"]: "Grupo Faturamento",
            COLUNAS_ORIGINAIS["observacao"]: "Observação",
        },
        inplace=True
    )

    df.insert(0, "ID Linha", range(1, len(df) + 1))

    df["Qtde Solicitada"] = converter_numero_br(df["Qtde Solicitada"])
    df["Qtde Faturada"] = converter_numero_br(df["Qtde Faturada"])
    df["Valor Unitário"] = converter_numero_br(df["Valor Unitário"])
    df["Valor Total"] = converter_numero_br(df["Valor Total"])

    df["Saldo a Faturar"] = df["Qtde Solicitada"] - df["Qtde Faturada"]
    df["Valor em Carteira"] = df["Saldo a Faturar"] * df["Valor Unitário"]

    df["% Faturado"] = df.apply(
        lambda linha: (linha["Qtde Faturada"] / linha["Qtde Solicitada"] * 100)
        if linha["Qtde Solicitada"] > 0 else 0,
        axis=1
    )

    df["Status"] = df.apply(definir_status, axis=1)

    df["Previsão Faturamento Data"] = pd.to_datetime(
        df["Previsão Faturamento"],
        format="%d/%m/%Y",
        errors="coerce"
    )

    hoje = pd.Timestamp(datetime.today().date())

    df["Situação Prazo"] = df.apply(
        lambda linha: "Vencido"
        if pd.notna(linha["Previsão Faturamento Data"])
        and linha["Previsão Faturamento Data"] < hoje
        and linha["Saldo a Faturar"] > 0
        else "No prazo",
        axis=1
    )

    df.drop(columns=["Previsão Faturamento Data"], inplace=True)

    return df


def definir_status(linha):
    qtde_solicitada = linha["Qtde Solicitada"]
    qtde_faturada = linha["Qtde Faturada"]
    saldo = linha["Saldo a Faturar"]

    if saldo <= 0:
        return "Faturado"

    if qtde_faturada > 0 and qtde_faturada < qtde_solicitada:
        return "Parcial"

    return "Aberto"


def gerar_resumo(df):
    return {
        "Total de Linhas": len(df),
        "Pedidos Únicos": df["Pedido"].nunique(),
        "Clientes Únicos": df["Cliente"].nunique(),
        "Itens Únicos": df["Item"].nunique(),
        "Qtde Solicitada": df["Qtde Solicitada"].sum(),
        "Qtde Faturada": df["Qtde Faturada"].sum(),
        "Saldo a Faturar": df["Saldo a Faturar"].sum(),
        "Valor Total": df["Valor Total"].sum(),
        "Valor em Carteira": df["Valor em Carteira"].sum(),
        "Itens Vencidos": len(df[df["Situação Prazo"] == "Vencido"]),
    }


def consolidar_por_item(df):
    resultado = df.groupby(
        ["Item", "Descrição Item"],
        as_index=False
    ).agg({
        "Pedido": "nunique",
        "Cliente": "nunique",
        "Qtde Solicitada": "sum",
        "Qtde Faturada": "sum",
        "Saldo a Faturar": "sum",
        "Valor Total": "sum",
        "Valor em Carteira": "sum",
    })

    resultado.rename(
        columns={
            "Pedido": "Qtd. Pedidos",
            "Cliente": "Qtd. Clientes",
        },
        inplace=True
    )

    resultado.sort_values("Valor em Carteira", ascending=False, inplace=True)

    return resultado


def consolidar_por_pedido(df):
    resultado = df.groupby(
        ["Pedido", "Cliente", "Grupo Faturamento", "Previsão Faturamento"],
        as_index=False
    ).agg({
        "Item": "nunique",
        "Qtde Solicitada": "sum",
        "Qtde Faturada": "sum",
        "Saldo a Faturar": "sum",
        "Valor Total": "sum",
        "Valor em Carteira": "sum",
    })

    resultado.rename(
        columns={
            "Item": "Qtd. Itens",
        },
        inplace=True
    )

    resultado.sort_values("Valor em Carteira", ascending=False, inplace=True)

    return resultado


def consolidar_por_cliente(df):
    resultado = df.groupby(
        ["Código Cliente", "Cliente"],
        as_index=False
    ).agg({
        "Pedido": "nunique",
        "Item": "nunique",
        "Qtde Solicitada": "sum",
        "Qtde Faturada": "sum",
        "Saldo a Faturar": "sum",
        "Valor Total": "sum",
        "Valor em Carteira": "sum",
    })

    resultado.rename(
        columns={
            "Pedido": "Qtd. Pedidos",
            "Item": "Qtd. Itens",
        },
        inplace=True
    )

    resultado.sort_values("Valor em Carteira", ascending=False, inplace=True)

    return resultado


def consolidar_por_grupo(df):
    resultado = df.groupby(
        ["Grupo Faturamento"],
        as_index=False
    ).agg({
        "Pedido": "nunique",
        "Cliente": "nunique",
        "Item": "nunique",
        "Qtde Solicitada": "sum",
        "Qtde Faturada": "sum",
        "Saldo a Faturar": "sum",
        "Valor Total": "sum",
        "Valor em Carteira": "sum",
    })

    resultado.rename(
        columns={
            "Pedido": "Qtd. Pedidos",
            "Cliente": "Qtd. Clientes",
            "Item": "Qtd. Itens",
        },
        inplace=True
    )

    resultado.sort_values("Valor em Carteira", ascending=False, inplace=True)

    return resultado


def consolidar_por_previsao(df):
    resultado = df.groupby(
        ["Previsão Faturamento"],
        as_index=False
    ).agg({
        "Pedido": "nunique",
        "Cliente": "nunique",
        "Item": "nunique",
        "Qtde Solicitada": "sum",
        "Qtde Faturada": "sum",
        "Saldo a Faturar": "sum",
        "Valor Total": "sum",
        "Valor em Carteira": "sum",
    })

    resultado.rename(
        columns={
            "Pedido": "Qtd. Pedidos",
            "Cliente": "Qtd. Clientes",
            "Item": "Qtd. Itens",
        },
        inplace=True
    )

    return resultado


def obter_consolidacao(df, tipo):
    if tipo == "Carteira Detalhada":
        return df.copy()

    if tipo == "Por Item":
        return consolidar_por_item(df)

    if tipo == "Por Pedido":
        return consolidar_por_pedido(df)

    if tipo == "Por Cliente":
        return consolidar_por_cliente(df)

    if tipo == "Por Grupo de Faturamento":
        return consolidar_por_grupo(df)

    if tipo == "Por Previsão de Faturamento":
        return consolidar_por_previsao(df)

    return df.copy()
