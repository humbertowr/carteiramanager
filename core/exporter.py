from datetime import datetime

import pandas as pd
from openpyxl.styles import Border, Font, Side

from core.carteira_processor import obter_consolidacao
from core.formatters import formatar_numero


def exportar_excel_completo(caminho, state):
    if state.df_original is None:
        raise ValueError("Nenhum arquivo importado.")

    with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
        state.gerar_df_prog2().to_excel(writer, sheet_name="PROG 2", index=False)
        state.gerar_df_pedidos_ajustados().to_excel(writer, sheet_name="Pedidos Ajustados", index=False)
        state.gerar_df_pedidos_liberados().to_excel(writer, sheet_name="Pedidos Liberados", index=False)
        state.gerar_df_bloqueios().to_excel(writer, sheet_name="Bloqueios", index=False)
        state.gerar_df_carteira_com_bloqueios().to_excel(writer, sheet_name="Carteira Detalhada", index=False)

        obter_consolidacao(state.df_original, "Por Item").to_excel(writer, sheet_name="Por Item", index=False)
        obter_consolidacao(state.df_original, "Por Pedido").to_excel(writer, sheet_name="Por Pedido", index=False)
        obter_consolidacao(state.df_original, "Por Cliente").to_excel(writer, sheet_name="Por Cliente", index=False)
        obter_consolidacao(state.df_original, "Por Grupo de Faturamento").to_excel(writer, sheet_name="Por Grupo", index=False)
        obter_consolidacao(state.df_original, "Por Previsão de Faturamento").to_excel(writer, sheet_name="Por Previsao", index=False)


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

        borda_fina = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

        formato_moeda = '"R$" #,##0.00'
        colunas_moeda = set()

        for cell in worksheet[1]:
            if cell.value not in (None, ""):
                cell.font = Font(bold=True)
                cell.border = borda_fina

                cabecalho = str(cell.value).upper()
                if "VALOR" in cabecalho or cabecalho.startswith("VLR"):
                    colunas_moeda.add(cell.column)

        for row in worksheet.iter_rows(min_row=2, max_col=worksheet.max_column):
            linha_tem_conteudo = any(cell.value not in (None, "") for cell in row)
            if not linha_tem_conteudo:
                continue

            linha_total = str(row[0].value or "").strip().upper().startswith("TOTAL")

            for cell in row:
                cell.border = borda_fina

                if linha_total:
                    cell.font = Font(bold=True)

                if cell.column in colunas_moeda and cell.value not in (None, ""):
                    cell.number_format = formato_moeda

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

    if isinstance(valor, float):
        return formatar_numero(valor)

    if isinstance(valor, int):
        return str(valor)

    return str(valor)


def peso_coluna_pdf(coluna):
    coluna_normalizada = str(coluna).upper()

    if coluna_normalizada == "ITEM":
        return 1.25

    if "DESCRICAO ITEM" in coluna_normalizada:
        return 5.50

    if "DESCRICAO CLIENTE" in coluna_normalizada:
        return 4.30

    if coluna_normalizada == "PEDIDO":
        return 1.10

    if coluna_normalizada == "GF":
        return 0.55

    if "ENTREGA" in coluna_normalizada:
        return 1.10

    if "QTDE" in coluna_normalizada or "QTD" in coluna_normalizada:
        return 0.95

    return 1.00


def alinhamento_coluna_pdf(coluna):
    coluna_normalizada = str(coluna).upper()

    if "QTDE" in coluna_normalizada or "QTD" in coluna_normalizada:
        return "RIGHT"

    if coluna_normalizada == "GF":
        return "CENTER"

    return "LEFT"


def definir_fonte_pdf(df_pdf, titulo):
    titulo_normalizado = str(titulo).lower()
    quantidade_colunas = len(df_pdf.columns)

    if "itens liberados do prog 2" in titulo_normalizado:
        return 10.6, 12.6

    if quantidade_colunas <= 3:
        return 9.8, 11.8

    if quantidade_colunas <= 5:
        return 8.1, 9.8

    return 7.0, 8.6


def desenhar_rodape_pdf(canvas, doc, texto_rodape):
    canvas.saveState()

    canvas.setFont("Courier", 7)

    largura_pagina, _ = doc.pagesize

    y_rodape = 0.45 * 28.3464567

    canvas.drawRightString(
        largura_pagina - doc.rightMargin,
        y_rodape,
        texto_rodape
    )

    canvas.restoreState()


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
    data_geracao = datetime.now().strftime("%d/%m/%Y %H:%M")
    texto_rodape = f"Gerado em: {data_geracao}"

    estilos = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        "TituloRelatorio",
        parent=estilos["Title"],
        alignment=TA_CENTER,
        fontName="Courier-Bold",
        fontSize=15,
        leading=18,
        spaceAfter=5,
    )

    fonte_tabela, leading_tabela = definir_fonte_pdf(df_pdf, titulo)

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
        rightMargin=0.6 * cm,
        leftMargin=0.6 * cm,
        topMargin=0.9 * cm,
        bottomMargin=1.0 * cm,
    )

    elementos = [
        Paragraph(titulo_pdf_formatado(titulo), estilo_titulo),
        Spacer(1, 0.12 * cm),
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

    largura_total = A4[0] - (1.2 * cm)

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

    documento.build(
        elementos,
        onFirstPage=lambda canvas, doc: desenhar_rodape_pdf(canvas, doc, texto_rodape),
        onLaterPages=lambda canvas, doc: desenhar_rodape_pdf(canvas, doc, texto_rodape),
    )