import re
import unicodedata
from pathlib import Path

import pandas as pd

from core.formatters import normalizar_texto


COLUNAS_OBRIGATORIAS = [
    "Pedido",
    "Cliente",
    "Item",
    "Descrição Item",
    "Saldo a Faturar",
    "Valor em Carteira",
    "Data Entrega",
    "Grupo Faturamento",
]


COLUNAS_OPCIONAIS_PADRAO = {
    "Observação": "",
}


MAPEAMENTO_COLUNAS = {
    # Pedido
    "PEDIDO": "Pedido",
    "N PEDIDO": "Pedido",
    "NUMERO PEDIDO": "Pedido",
    "NUMERO DO PEDIDO": "Pedido",
    "ORDEM": "Pedido",
    "PEDIDO PEDIDO NUMERO": "Pedido",
    "PEDIDO NUMERO": "Pedido",

    # Cliente
    "CLIENTE": "Cliente",
    "NOME CLIENTE": "Cliente",
    "NOME DO CLIENTE": "Cliente",
    "RAZAO SOCIAL": "Cliente",
    "DESCRICAO CLIENTE": "Cliente",
    "CLIENTE RAZAO SOCIAL CLIENTE": "Cliente",

    # Item
    "ITEM": "Item",
    "COD ITEM": "Item",
    "CODIGO ITEM": "Item",
    "CODIGO DO ITEM": "Item",
    "PRODUTO": "Item",

    # Descrição do item
    "DESCRICAO ITEM": "Descrição Item",
    "DESCRIÇÃO ITEM": "Descrição Item",
    "DESCRICAO DO ITEM": "Descrição Item",
    "DESCRIÇÃO DO ITEM": "Descrição Item",
    "DESC ITEM": "Descrição Item",
    "ITEM DESCRICAO ITEM": "Descrição Item",

    # Quantidade / saldo
    "SALDO A FATURAR": "Saldo a Faturar",
    "QTDE A FATURAR": "Saldo a Faturar",
    "QTD A FATURAR": "Saldo a Faturar",
    "QUANTIDADE A FATURAR": "Saldo a Faturar",
    "SALDO": "Saldo a Faturar",

    # Quantidade solicitada/faturada do ERP
    "QTDE SOLICITADA": "Qtde Solicitada",
    "QTD SOLICITADA": "Qtde Solicitada",
    "QUANTIDADE SOLICITADA": "Qtde Solicitada",
    "QTDE FATURADA": "Qtde Faturada",
    "QTD FATURADA": "Qtde Faturada",
    "QUANTIDADE FATURADA": "Qtde Faturada",

    # Valores
    "VALOR EM CARTEIRA": "Valor em Carteira",
    "VALOR CARTEIRA": "Valor em Carteira",
    "VALOR": "Valor em Carteira",
    "VALOR TOTAL": "Valor em Carteira",
    "VLR CARTEIRA": "Valor em Carteira",

    "VALOR UNITARIO": "Valor Unitário",
    "VLR UNITARIO": "Valor Unitário",

    # Datas
    "DATA ENTREGA": "Data Entrega",
    "DATA DE ENTREGA": "Data Entrega",
    "ENTREGA": "Data Entrega",
    "PREVISAO ENTREGA": "Data Entrega",
    "PREVISÃO ENTREGA": "Data Entrega",
    "PREVISAO DE FATURAMENTO": "Data Entrega",
    "PREVISÃO DE FATURAMENTO": "Data Entrega",
    "PEDIDO DATA DE ENTREGA": "Data Entrega",
    "PEDIDO DATA DE PREVISAO DE FATURAMENTO": "Data Entrega",

    # Grupo de faturamento
    "GRUPO FATURAMENTO": "Grupo Faturamento",
    "GRUPO DE FATURAMENTO": "Grupo Faturamento",
    "GR FATURAMENTO": "Grupo Faturamento",
    "GF": "Grupo Faturamento",
    "GRUPO DE FATURAMENTO DESCRICAO GRUPO FATURAMENTO": "Grupo Faturamento",

    # Observação
    "OBSERVACAO": "Observação",
    "OBSERVAÇÃO": "Observação",
    "OBS": "Observação",
    "OBSERVACOES": "Observação",
    "OBSERVAÇÕES": "Observação",
    "PEDIDO OBSERVACAO 01": "Observação",
}


def normalizar_nome_coluna(nome):
    texto = str(nome).strip()

    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(char for char in texto if not unicodedata.combining(char))

    texto = texto.upper()
    texto = re.sub(r"[^A-Z0-9]+", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


def identificar_coluna_padrao(nome_coluna):
    chave = normalizar_nome_coluna(nome_coluna)

    if chave in MAPEAMENTO_COLUNAS:
        return MAPEAMENTO_COLUNAS[chave]

    if chave.startswith("PEDIDO PEDIDO") and "NUMERO" in chave:
        return "Pedido"

    if chave.startswith("CLIENTE RAZAO SOCIAL"):
        return "Cliente"

    if chave.startswith("ITEM DESCRICAO"):
        return "Descrição Item"

    if chave.startswith("PEDIDO DATA DE ENTREGA"):
        return "Data Entrega"

    if "DATA" in chave and "PREVISAO" in chave and "FATURAMENTO" in chave:
        return "Data Entrega"

    if chave.startswith("GRUPO DE FATURAMENTO") and "DESCRICAO" in chave:
        return "Grupo Faturamento"

    if chave.startswith("PEDIDO OBSERVACAO"):
        return "Observação"

    if "QTDE" in chave and "SOLICITADA" in chave:
        return "Qtde Solicitada"

    if "QTD" in chave and "SOLICITADA" in chave:
        return "Qtde Solicitada"

    if "QUANTIDADE" in chave and "SOLICITADA" in chave:
        return "Qtde Solicitada"

    if "QTDE" in chave and "FATURADA" in chave:
        return "Qtde Faturada"

    if "QTD" in chave and "FATURADA" in chave:
        return "Qtde Faturada"

    if "QUANTIDADE" in chave and "FATURADA" in chave:
        return "Qtde Faturada"

    if "VALOR" in chave and "TOTAL" in chave:
        return "Valor em Carteira"

    if "VALOR" in chave and "CARTEIRA" in chave:
        return "Valor em Carteira"

    if "VALOR" in chave and "UNITARIO" in chave:
        return "Valor Unitário"

    return str(nome_coluna).strip()


def converter_numero(valor):
    if pd.isna(valor):
        return 0.0

    if isinstance(valor, (int, float)):
        return float(valor)

    texto = str(valor).strip()

    if not texto:
        return 0.0

    texto = texto.replace("R$", "").replace(" ", "")

    if "," in texto and "." in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")

    texto = re.sub(r"[^0-9.\-]", "", texto)

    if not texto or texto in {"-", ".", "-."}:
        return 0.0

    try:
        return float(texto)
    except ValueError:
        return 0.0


def formatar_data(valor):
    if pd.isna(valor):
        return ""

    texto = str(valor).strip()

    if not texto:
        return ""

    data = pd.to_datetime(texto, errors="coerce", dayfirst=True)

    if pd.isna(data):
        return texto

    return data.strftime("%d/%m/%Y")


def ler_csv_com_fallback(caminho):
    caminho = Path(caminho)

    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    tentativas = [
        {"encoding": "utf-8-sig", "sep": None},
        {"encoding": "cp1252", "sep": None},
        {"encoding": "latin1", "sep": None},
        {"encoding": "utf-8-sig", "sep": "\t"},
        {"encoding": "cp1252", "sep": "\t"},
        {"encoding": "latin1", "sep": "\t"},
        {"encoding": "utf-8-sig", "sep": ";"},
        {"encoding": "cp1252", "sep": ";"},
        {"encoding": "latin1", "sep": ";"},
        {"encoding": "utf-8-sig", "sep": ","},
        {"encoding": "cp1252", "sep": ","},
        {"encoding": "latin1", "sep": ","},
    ]

    ultimo_erro = None

    for tentativa in tentativas:
        try:
            df = pd.read_csv(
                caminho,
                sep=tentativa["sep"],
                encoding=tentativa["encoding"],
                engine="python",
                dtype=str,
            )

            if len(df.columns) > 1:
                return df

        except Exception as erro:
            ultimo_erro = erro

    raise ValueError(
        "Não foi possível ler o arquivo CSV. "
        "Verifique se ele está separado por tabulação, ponto e vírgula ou vírgula, "
        "e se não está aberto/bloqueado em outro programa."
    ) from ultimo_erro


def consolidar_colunas_duplicadas(df):
    resultado = pd.DataFrame(index=df.index)

    for nome_coluna in dict.fromkeys(df.columns):
        colunas = df.loc[:, df.columns == nome_coluna]

        if colunas.shape[1] == 1:
            resultado[nome_coluna] = colunas.iloc[:, 0]
            continue

        serie = colunas.iloc[:, 0].astype(str)

        for indice in range(1, colunas.shape[1]):
            candidata = colunas.iloc[:, indice].astype(str)

            mascara_vazia = serie.str.strip().isin(["", "nan", "None", "NaN"])
            serie = serie.where(~mascara_vazia, candidata)

        resultado[nome_coluna] = serie

    return resultado


def padronizar_colunas(df):
    renomear = {}

    for coluna in df.columns:
        renomear[coluna] = identificar_coluna_padrao(coluna)

    df = df.rename(columns=renomear)
    df = consolidar_colunas_duplicadas(df)

    return df


def garantir_colunas_calculadas(df):
    df = df.copy()

    if "Saldo a Faturar" not in df.columns:
        if "Qtde Solicitada" in df.columns and "Qtde Faturada" in df.columns:
            df["Saldo a Faturar"] = (
                df["Qtde Solicitada"].apply(converter_numero)
                - df["Qtde Faturada"].apply(converter_numero)
            )
        elif "Qtde Solicitada" in df.columns:
            df["Saldo a Faturar"] = df["Qtde Solicitada"].apply(converter_numero)

    if "Valor em Carteira" not in df.columns:
        if "Valor Unitário" in df.columns and "Saldo a Faturar" in df.columns:
            df["Valor em Carteira"] = (
                df["Valor Unitário"].apply(converter_numero)
                * df["Saldo a Faturar"].apply(converter_numero)
            )

    return df


def validar_colunas_obrigatorias(df):
    faltantes = [
        coluna for coluna in COLUNAS_OBRIGATORIAS
        if coluna not in df.columns
    ]

    if not faltantes:
        return

    colunas_encontradas = "\n".join(f"- {coluna}" for coluna in df.columns)
    colunas_faltantes = "\n".join(f"- {coluna}" for coluna in faltantes)

    raise ValueError(
        "O arquivo importado não possui todas as colunas obrigatórias.\n\n"
        "Colunas faltantes:\n"
        f"{colunas_faltantes}\n\n"
        "Colunas encontradas no arquivo:\n"
        f"{colunas_encontradas}\n\n"
        "O CSV pode estar correto, mas o programa ainda não reconheceu algum nome de coluna do ERP."
    )


def preparar_dataframe(df):
    df = df.copy()

    for coluna, valor_padrao in COLUNAS_OPCIONAIS_PADRAO.items():
        if coluna not in df.columns:
            df[coluna] = valor_padrao

    df = garantir_colunas_calculadas(df)

    validar_colunas_obrigatorias(df)

    df = df.fillna("")

    df["Pedido"] = df["Pedido"].astype(str).str.strip()
    df["Cliente"] = df["Cliente"].astype(str).str.strip()
    df["Item"] = df["Item"].astype(str).str.strip()
    df["Descrição Item"] = df["Descrição Item"].astype(str).str.strip()
    df["Observação"] = df["Observação"].astype(str).str.strip()
    df["Grupo Faturamento"] = df["Grupo Faturamento"].astype(str).str.strip()
    df["Data Entrega"] = df["Data Entrega"].apply(formatar_data)

    df["Saldo a Faturar"] = df["Saldo a Faturar"].apply(converter_numero)
    df["Valor em Carteira"] = df["Valor em Carteira"].apply(converter_numero)

    df = df[df["Pedido"] != ""].copy()
    df = df[df["Item"] != ""].copy()

    if df.empty:
        raise ValueError(
            "O arquivo foi lido, mas não restaram linhas válidas. "
            "Verifique se há pedidos, itens e saldo a faturar no CSV."
        )

    df.reset_index(drop=True, inplace=True)
    df["ID Linha"] = df.index + 1

    return df


def carregar_carteira(caminho):
    df = ler_csv_com_fallback(caminho)
    df = padronizar_colunas(df)
    df = preparar_dataframe(df)

    return df


def obter_consolidacao(df, tipo):
    if df is None or df.empty:
        return pd.DataFrame()

    tipo_normalizado = normalizar_nome_coluna(tipo)

    if tipo_normalizado == "POR ITEM":
        return (
            df.groupby(["Item", "Descrição Item"], as_index=False)
            .agg({
                "Pedido": "nunique",
                "Cliente": "nunique",
                "Saldo a Faturar": "sum",
                "Valor em Carteira": "sum",
            })
            .rename(columns={
                "Pedido": "Qtd. Pedidos",
                "Cliente": "Qtd. Clientes",
                "Saldo a Faturar": "Qtde",
                "Valor em Carteira": "Valor",
            })
            .sort_values("Valor", ascending=False)
        )

    if tipo_normalizado == "POR PEDIDO":
        return (
            df.groupby(["Pedido", "Cliente"], as_index=False)
            .agg({
                "Item": "nunique",
                "Saldo a Faturar": "sum",
                "Valor em Carteira": "sum",
            })
            .rename(columns={
                "Item": "Qtd. Itens",
                "Saldo a Faturar": "Qtde",
                "Valor em Carteira": "Valor",
            })
            .sort_values("Valor", ascending=False)
        )

    if tipo_normalizado == "POR CLIENTE":
        return (
            df.groupby("Cliente", as_index=False)
            .agg({
                "Pedido": "nunique",
                "Item": "nunique",
                "Saldo a Faturar": "sum",
                "Valor em Carteira": "sum",
            })
            .rename(columns={
                "Pedido": "Qtd. Pedidos",
                "Item": "Qtd. Itens",
                "Saldo a Faturar": "Qtde",
                "Valor em Carteira": "Valor",
            })
            .sort_values("Valor", ascending=False)
        )

    if tipo_normalizado == "POR GRUPO DE FATURAMENTO":
        return (
            df.groupby("Grupo Faturamento", as_index=False)
            .agg({
                "Pedido": "nunique",
                "Item": "nunique",
                "Saldo a Faturar": "sum",
                "Valor em Carteira": "sum",
            })
            .rename(columns={
                "Pedido": "Qtd. Pedidos",
                "Item": "Qtd. Itens",
                "Saldo a Faturar": "Qtde",
                "Valor em Carteira": "Valor",
            })
            .sort_values("Valor", ascending=False)
        )

    if tipo_normalizado == "POR PREVISAO DE FATURAMENTO":
        return (
            df.groupby("Data Entrega", as_index=False)
            .agg({
                "Pedido": "nunique",
                "Item": "nunique",
                "Saldo a Faturar": "sum",
                "Valor em Carteira": "sum",
            })
            .rename(columns={
                "Pedido": "Qtd. Pedidos",
                "Item": "Qtd. Itens",
                "Saldo a Faturar": "Qtde",
                "Valor em Carteira": "Valor",
            })
            .sort_values("Data Entrega", ascending=True)
        )

    return pd.DataFrame()