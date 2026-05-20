import pandas as pd

from core.carteira_processor import obter_consolidacao
from core.formatters import formatar_moeda, formatar_numero


def exportar_excel_completo(caminho, state):
    if state.df_original is None:
        raise ValueError("Nenhum arquivo importado.")

    with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
        state.gerar_df_prog2().to_excel(
            writer,
            sheet_name="PROG 2",
            index=False
        )

        state.gerar_df_pedidos_ajustados().to_excel(
            writer,
            sheet_name="Pedidos Ajustados",
            index=False
        )

        state.gerar_df_pedidos_liberados().to_excel(
            writer,
            sheet_name="Pedidos Liberados",
            index=False
        )

        state.gerar_df_bloqueios().to_excel(
            writer,
            sheet_name="Bloqueios",
            index=False
        )

        state.gerar_df_carteira_com_bloqueios().to_excel(
            writer,
            sheet_name="Carteira Detalhada",
            index=False
        )

        obter_consolidacao(state.df_original, "Por Item").to_excel(
            writer,
            sheet_name="Por Item",
            index=False
        )

        obter_consolidacao(state.df_original, "Por Pedido").to_excel(
            writer,
            sheet_name="Por Pedido",
            index=False
        )

        obter_consolidacao(state.df_original, "Por Cliente").to_excel(
            writer,
            sheet_name="Por Cliente",
            index=False
        )

        obter_consolidacao(state.df_original, "Por Grupo de Faturamento").to_excel(
            writer,
            sheet_name="Por Grupo",
            index=False
        )

        obter_consolidacao(state.df_original, "Por Previsão de Faturamento").to_excel(
            writer,
            sheet_name="Por Previsao",
            index=False
        )


def exportar_csv(caminho, df):
    if df is None:
        raise ValueError("Nenhum dado para exportar.")

    df.to_csv(
        caminho,
        index=False,
        sep=";",
        encoding="utf-8-sig"
    )


def preparar_dataframe_exportacao(df, identificador):
    df_saida = df.copy()
    identificador = str(identificador).lower()

    if (
        "itens liberados do prog 2" in identificador
        or "prog2_itens_liberados" in identificador
        or "itens_liberados" in identificador
    ):
        colunas_remover = [
            "Qtd. Pedidos",
            "Qtd. Clientes",
            "Valor Liberado",
            "VLR. ITEM",
        ]

        df_saida.drop(
            columns=[coluna for coluna in colunas_remover if coluna in df_saida.columns],
            inplace=True
        )

        ordem_preferida = [
            "Item",
            "Descrição Item",
            "Qtde Liberada",
        ]

        colunas_existentes = [
            coluna for coluna in ordem_preferida
            if coluna in df_saida.columns
        ]

        outras_colunas = [
            coluna for coluna in df_saida.columns
            if coluna not in colunas_existentes
        ]

        df_saida = df_saida[colunas_existentes + outras_colunas]

    elif (
        "pedidos liberados do prog 2" in identificador
        or "prog2_pedidos_liberados" in identificador
        or "pedidos_liberados" in identificador
    ):
        colunas_remover = [
            "Cliente",
            "Qtd. Itens Liberados",
            "Valor Total Liberado",
            "VLR. PEDIDO",
        ]

        df_saida.drop(
            columns=[coluna for coluna in colunas_remover if coluna in df_saida.columns],
            inplace=True
        )

        ordem_preferida = [
            "Pedido",
            "Grupo",
            "Cliente Original",
            "Data Entrega",
            "Qtde Liberada",
        ]

        colunas_existentes = [
            coluna for coluna in ordem_preferida
            if coluna in df_saida.columns
        ]

        outras_colunas = [
            coluna for coluna in df_saida.columns
            if coluna not in colunas_existentes
        ]

        df_saida = df_saida[colunas_existentes + outras_colunas]

    return df_saida


def exportar_dataframe_excel(caminho, df, sheet_name="Dados"):
    if df is None or df.empty:
        raise ValueError("Nenhum dado para exportar.")

    df_exportar = preparar_dataframe_exportacao(df, sheet_name)

    with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
        df_exportar.to_excel(
            writer,
            sheet_name=sheet_name[:31],
            index=False
        )

        worksheet = writer.sheets[sheet_name[:31]]

        for coluna_cells in worksheet.columns:
            tamanho_maximo = 0
            letra_coluna = coluna_cells[0].column_letter

            for cell in coluna_cells:
                valor = "" if cell.value is None else str(cell.value)
                tamanho_maximo = max(tamanho_maximo, len(valor))

            worksheet.column_dimensions[letra_coluna].width = min(tamanho_maximo + 2, 50)


def preparar_dataframe_pdf(df, titulo):
    df_pdf = preparar_dataframe_exportacao(df, titulo)
    titulo_normalizado = str(titulo).lower()

    if "itens liberados do prog 2" in titulo_normalizado:
        df_pdf.rename(
            columns={
                "Item": "ITEM",
                "Descrição Item": "DESCRICAO ITEM",
                "Qtde Liberada": "QTDE",
            },
            inplace=True
        )

    elif "pedidos liberados do prog 2" in titulo_normalizado:
        df_pdf.rename(
            columns={
                "Pedido": "PEDIDO",
                "Grupo": "GF",
                "Cliente Original": "DESCRICAO CLIENTE",
                "Data Entrega": "ENTREGA",
                "Qtde Liberada": "QTDE",
            },
            inplace=True
        )

    return df_pdf


def titulo_pdf_formatado(titulo):
    titulo_normalizado = str(titulo).lower()

    if "itens liberados do prog 2" in titulo_normalizado:
        return "ITENS PRIORIDADE SEPARACAO"

    if "pedidos liberados do prog 2" in titulo_normalizado:
        return "PEDIDOS PRIORIDADE SEPARACAO"

    return str(titulo).upper()


def formatar_valor_pdf(valor, coluna):
    if pd.isna(valor):
        return ""

    coluna_normalizada = str(coluna).upper()

    if isinstance(valor, float):
        if "VLR" in coluna_normalizada or "VALOR" in coluna_normalizada:
            return formatar_moeda(valor).replace("R$", "").strip()

        return formatar_numero(valor)

    if isinstance(valor, int):
        if "VLR" in coluna_normalizada or "VALOR" in coluna_normalizada:
            return formatar_moeda(valor).replace("R$", "").strip()

        return str(valor)

    return str(valor)


def peso_coluna_pdf(coluna):
    coluna_normalizada = str(coluna).upper()

    if coluna_normalizada == "ITEM":
        return 1.15

    if "DESCRICAO ITEM" in coluna_normalizada:
        return 5.30

    if "DESCRICAO CLIENTE" in coluna_normalizada:
        return 4.60

    if coluna_normalizada == "PEDIDO":
        return 1.10

    if coluna_normalizada == "GF":
        return 0.55

    if "ENTREGA" in coluna_normalizada:
        return 1.10

    if "QTDE" in coluna_normalizada or "QTD" in coluna_normalizada:
        return 0.90

    return 1.00


def alinhamento_coluna_pdf(coluna):
    coluna_normalizada = str(coluna).upper()

    if "QTDE" in coluna_normalizada or "QTD" in coluna_normalizada:
        return "RIGHT"

    if coluna_normalizada == "GF":
        return "CENTER"

    return "LEFT"


def exportar_dataframe_pdf(caminho, df, titulo="Relatório"):
    if df is None or df.empty:
        raise ValueError("Nenhum dado para exportar.")

    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    except ImportError as erro:
        raise ImportError(
            "A biblioteca reportlab não está instalada. Rode: pip install reportlab"
        ) from erro

    df_pdf = preparar_dataframe_pdf(df, titulo)

    estilos = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        "TituloRelatorio",
        parent=estilos["Title"],
        alignment=TA_CENTER,
        fontName="Courier-Bold",
        fontSize=14,
        leading=17,
        spaceAfter=10,
    )

    quantidade_colunas = len(df_pdf.columns)

    if quantidade_colunas <= 3:
        fonte_tabela = 8.5
        leading_tabela = 10.5
    elif quantidade_colunas <= 5:
        fonte_tabela = 7.2
        leading_tabela = 8.8
    else:
        fonte_tabela = 6.2
        leading_tabela = 7.8

    estilo_texto = ParagraphStyle(
        "TextoTabela",
        parent=estilos["BodyText"],
        fontName="Courier",
        fontSize=fonte_tabela,
        leading=leading_tabela,
    )

    estilo_cabecalho = ParagraphStyle(
        "CabecalhoTabela",
        parent=estilos["BodyText"],
        fontName="Courier-Bold",
        fontSize=fonte_tabela,
        leading=leading_tabela,
    )

    documento = SimpleDocTemplate(
        caminho,
        pagesize=A4,
        rightMargin=0.8 * cm,
        leftMargin=0.8 * cm,
        topMargin=1.0 * cm,
        bottomMargin=0.8 * cm,
    )

    elementos = [
        Paragraph(titulo_pdf_formatado(titulo), estilo_titulo),
        Spacer(1, 0.10 * cm),
    ]

    colunas = list(df_pdf.columns)

    dados = [
        [Paragraph(str(coluna), estilo_cabecalho) for coluna in colunas]
    ]

    for _, linha in df_pdf.iterrows():
        dados.append([
            Paragraph(formatar_valor_pdf(linha[coluna], coluna), estilo_texto)
            for coluna in colunas
        ])

    largura_total = A4[0] - (1.6 * cm)

    pesos = [
        peso_coluna_pdf(coluna)
        for coluna in colunas
    ]

    soma_pesos = sum(pesos) if pesos else 1

    larguras = [
        largura_total * (peso / soma_pesos)
        for peso in pesos
    ]

    tabela = Table(
        dados,
        colWidths=larguras,
        repeatRows=1,
        splitByRow=True,
    )

    estilos_tabela = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.white),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Courier-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Courier"),
        ("FONTSIZE", (0, 0), (-1, -1), fonte_tabela),
        ("TOPPADDING", (0, 0), (-1, 0), 4),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
        ("TOPPADDING", (0, 1), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("BOX", (0, 0), (-1, 0), 0.75, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.75, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]

    for indice, coluna in enumerate(colunas):
        alinhamento = alinhamento_coluna_pdf(coluna)
        estilos_tabela.append(("ALIGN", (indice, 0), (indice, -1), alinhamento))

    tabela.setStyle(TableStyle(estilos_tabela))

    elementos.append(tabela)

    documento.build(elementos)