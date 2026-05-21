import pandas as pd


MAPEAMENTO_COLUNAS = {
    "Pedido - Pedido (Número)": "Pedido",
    "Pedido": "Pedido",

    "Cliente - Razão social (Cliente)": "Cliente",
    "Cliente": "Cliente",

    "Pedido - Cliente (Código)": "Código Cliente",
    "Código Cliente": "Código Cliente",

    "Pedido - Data de entrega": "Data Entrega",
    "Data Entrega": "Data Entrega",

    "Pedido - Data de previsão de faturamento": "Data Previsão Faturamento",
    "Data Previsão Faturamento": "Data Previsão Faturamento",

    "Item": "Item",

    "Item - Descrição (Item)": "Descrição Item",
    "Descrição Item": "Descrição Item",

    "Qtde. solicitada": "Qtde Solicitada",
    "Qtde Solicitada": "Qtde Solicitada",

    "Qtde. faturada": "Qtde Faturada",
    "Qtde Faturada": "Qtde Faturada",

    "Valor unitário": "Valor Unitário",
    "Valor Unitário": "Valor Unitário",

    "Valor em Carteira": "Valor em Carteira",

    "Grupo de faturamento - Descrição (Grupo Faturamento)": "Grupo Faturamento",
    "Grupo Faturamento": "Grupo Faturamento",

    "Pedido - Observação 01": "Observação",
    "Observação": "Observação",
}


COLUNAS_OBRIGATORIAS = [
    "Pedido",
    "Cliente",
    "Item",
    "Descrição Item",
    "Qtde Solicitada",
    "Qtde Faturada",
    "Valor Unitário",
    "Data Entrega",
    "Grupo Faturamento",
]


def limpar_nome_coluna(coluna):
    return str(coluna).strip()


def normalizar_colunas(df):
    df = df.copy()
    df.columns = [limpar_nome_coluna(coluna) for coluna in df.columns]

    renomear = {}

    for coluna in df.columns:
        if coluna in MAPEAMENTO_COLUNAS:
            renomear[coluna] = MAPEAMENTO_COLUNAS[coluna]

    df.rename(columns=renomear, inplace=True)

    return df


def converter_numero(valor):
    if pd.isna(valor):
        return 0.0

    texto = str(valor).strip()

    if texto == "":
        return 0.0

    texto = texto.replace("R$", "")
    texto = texto.replace(" ", "")

    if "," in texto and "." in texto:
        texto = texto.replace(".", "")
        texto = texto.replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")

    try:
        return float(texto)
    except ValueError:
        return 0.0


def converter_data(valor):
    if pd.isna(valor):
        return ""

    texto = str(valor).strip()

    if texto == "":
        return ""

    data = pd.to_datetime(texto, errors="coerce", dayfirst=True)

    if pd.isna(data):
        return texto

    return data.strftime("%d/%m/%Y")


def validar_colunas_obrigatorias(df):
    faltantes = [
        coluna for coluna in COLUNAS_OBRIGATORIAS
        if coluna not in df.columns
    ]

    if not faltantes:
        return

    colunas_encontradas = "\n".join(
        f"- {coluna}"
        for coluna in df.columns
    )

    colunas_faltantes = "\n".join(
        f"- {coluna}"
        for coluna in faltantes
    )

    raise ValueError(
        "O arquivo importado não possui todas as colunas obrigatórias.\n\n"
        "Colunas faltantes:\n"
        f"{colunas_faltantes}\n\n"
        "Colunas encontradas no arquivo:\n"
        f"{colunas_encontradas}\n\n"
        "Corrija o CSV exportado do ERP ou ajuste os nomes das colunas."
    )


def abreviar_grupo_faturamento(valor):
    texto = str(valor).strip().upper()

    if texto == "IMEDIATO":
        return "I"

    if texto == "PROGRAMADO":
        return "P"

    if texto.startswith("IMEDIATO"):
        return "I"

    if texto.startswith("PROGRAMADO"):
        return "P"

    if texto in {"I", "P"}:
        return texto

    return texto


def calcular_saldo_e_valor(df):
    df = df.copy()

    df["Qtde Solicitada"] = df["Qtde Solicitada"].apply(converter_numero)
    df["Qtde Faturada"] = df["Qtde Faturada"].apply(converter_numero)
    df["Valor Unitário"] = df["Valor Unitário"].apply(converter_numero)

    df["Saldo a Faturar"] = df["Qtde Solicitada"] - df["Qtde Faturada"]

    df.loc[df["Saldo a Faturar"] < 0, "Saldo a Faturar"] = 0

    df["Valor em Carteira"] = df["Saldo a Faturar"] * df["Valor Unitário"]

    return df


def preparar_dataframe(df):
    df = normalizar_colunas(df)

    validar_colunas_obrigatorias(df)

    df = df.copy()

    df["Pedido"] = df["Pedido"].astype(str).str.strip()
    df["Pedido Texto"] = df["Pedido"].astype(str).str.strip()

    df["Cliente"] = df["Cliente"].astype(str).str.strip()

    if "Código Cliente" not in df.columns:
        df["Código Cliente"] = ""

    df["Código Cliente"] = df["Código Cliente"].astype(str).str.strip()

    df["Item"] = df["Item"].astype(str).str.strip()
    df["Item Texto"] = df["Item"].astype(str).str.strip()

    df["Descrição Item"] = df["Descrição Item"].astype(str).str.strip()

    df["Data Entrega"] = df["Data Entrega"].apply(converter_data)

    if "Data Previsão Faturamento" not in df.columns:
        df["Data Previsão Faturamento"] = ""

    df["Data Previsão Faturamento"] = df["Data Previsão Faturamento"].apply(converter_data)

    df["Grupo Faturamento"] = df["Grupo Faturamento"].astype(str).str.strip()
    df["Grupo Faturamento Abrev"] = df["Grupo Faturamento"].apply(abreviar_grupo_faturamento)

    if "Observação" not in df.columns:
        df["Observação"] = ""

    df["Observação"] = df["Observação"].fillna("").astype(str).str.strip()

    df = calcular_saldo_e_valor(df)

    df["ID Linha"] = range(1, len(df) + 1)

    colunas_principais = [
        "ID Linha",
        "Pedido",
        "Pedido Texto",
        "Código Cliente",
        "Cliente",
        "Data Entrega",
        "Data Previsão Faturamento",
        "Item",
        "Item Texto",
        "Descrição Item",
        "Qtde Solicitada",
        "Qtde Faturada",
        "Valor Unitário",
        "Saldo a Faturar",
        "Valor em Carteira",
        "Grupo Faturamento",
        "Grupo Faturamento Abrev",
        "Observação",
    ]

    colunas_existentes = [
        coluna for coluna in colunas_principais
        if coluna in df.columns
    ]

    outras_colunas = [
        coluna for coluna in df.columns
        if coluna not in colunas_existentes
    ]

    df = df[colunas_existentes + outras_colunas]

    return df


def carregar_carteira(caminho):
    tentativas = [
        {"sep": ";", "encoding": "utf-8-sig"},
        {"sep": ";", "encoding": "latin1"},
        {"sep": ",", "encoding": "utf-8-sig"},
        {"sep": ",", "encoding": "latin1"},
        {"sep": "\t", "encoding": "utf-8-sig"},
        {"sep": "\t", "encoding": "latin1"},
    ]

    ultimo_erro = None

    for tentativa in tentativas:
        try:
            df = pd.read_csv(
                caminho,
                sep=tentativa["sep"],
                encoding=tentativa["encoding"],
                dtype=str
            )

            if len(df.columns) <= 1:
                continue

            return preparar_dataframe(df)

        except Exception as erro:
            ultimo_erro = erro

    raise ValueError(
        f"Não foi possível importar o arquivo CSV.\n\nErro:\n{ultimo_erro}"
    )


def obter_consolidacao(df, tipo):
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    if tipo == "Por Item":
        resultado = df.groupby(
            ["Item", "Descrição Item"],
            as_index=False
        ).agg({
            "Pedido": "nunique",
            "Cliente": "nunique",
            "Saldo a Faturar": "sum",
            "Valor em Carteira": "sum",
        })

        resultado.rename(
            columns={
                "Pedido": "Qtd. Pedidos",
                "Cliente": "Qtd. Clientes",
                "Saldo a Faturar": "Qtde",
                "Valor em Carteira": "Valor",
            },
            inplace=True
        )

        resultado.sort_values("Valor", ascending=False, inplace=True)

        return resultado

    if tipo == "Por Pedido":
        resultado = df.groupby(
            ["Pedido", "Cliente"],
            as_index=False
        ).agg({
            "Item": "nunique",
            "Saldo a Faturar": "sum",
            "Valor em Carteira": "sum",
        })

        resultado.rename(
            columns={
                "Item": "Qtd. Itens",
                "Saldo a Faturar": "Qtde",
                "Valor em Carteira": "Valor",
            },
            inplace=True
        )

        resultado.sort_values("Valor", ascending=False, inplace=True)

        return resultado

    if tipo == "Por Cliente":
        resultado = df.groupby(
            ["Cliente"],
            as_index=False
        ).agg({
            "Pedido": "nunique",
            "Item": "nunique",
            "Saldo a Faturar": "sum",
            "Valor em Carteira": "sum",
        })

        resultado.rename(
            columns={
                "Pedido": "Qtd. Pedidos",
                "Item": "Qtd. Itens",
                "Saldo a Faturar": "Qtde",
                "Valor em Carteira": "Valor",
            },
            inplace=True
        )

        resultado.sort_values("Valor", ascending=False, inplace=True)

        return resultado

    if tipo == "Por Grupo de Faturamento":
        resultado = df.groupby(
            ["Grupo Faturamento Abrev", "Grupo Faturamento"],
            as_index=False
        ).agg({
            "Pedido": "nunique",
            "Item": "nunique",
            "Saldo a Faturar": "sum",
            "Valor em Carteira": "sum",
        })

        resultado.rename(
            columns={
                "Grupo Faturamento Abrev": "Grupo",
                "Pedido": "Qtd. Pedidos",
                "Item": "Qtd. Itens",
                "Saldo a Faturar": "Qtde",
                "Valor em Carteira": "Valor",
            },
            inplace=True
        )

        resultado.sort_values("Valor", ascending=False, inplace=True)

        return resultado

    if tipo == "Por Previsão de Faturamento":
        coluna_data = "Data Previsão Faturamento"

        if coluna_data not in df.columns:
            coluna_data = "Data Entrega"

        resultado = df.groupby(
            [coluna_data],
            as_index=False
        ).agg({
            "Pedido": "nunique",
            "Item": "nunique",
            "Saldo a Faturar": "sum",
            "Valor em Carteira": "sum",
        })

        resultado.rename(
            columns={
                coluna_data: "Data",
                "Pedido": "Qtd. Pedidos",
                "Item": "Qtd. Itens",
                "Saldo a Faturar": "Qtde",
                "Valor em Carteira": "Valor",
            },
            inplace=True
        )

        resultado.sort_values("Data", ascending=True, inplace=True)

        return resultado

    return pd.DataFrame()