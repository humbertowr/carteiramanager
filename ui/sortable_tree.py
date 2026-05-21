import re
from datetime import datetime


def _limpar_indicadores(texto):
    texto = "" if texto is None else str(texto).strip()
    texto = re.sub(r"^[✅☑☐⬜\s]+", "", texto).strip()
    return texto


def _converter_numero(texto):
    texto = _limpar_indicadores(texto)
    texto = texto.replace("R$", "").replace("%", "").strip()
    texto = re.sub(r"[^0-9,\.\-]", "", texto)

    if not texto or texto in {"-", ",", "."}:
        return None

    if "," in texto and "." in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")

    try:
        return float(texto)
    except ValueError:
        return None


def _converter_data(texto):
    texto = _limpar_indicadores(texto)

    for formato in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(texto, formato)
        except ValueError:
            pass

    return None


def _chave_ordenacao(valor):
    texto = _limpar_indicadores(valor)

    if texto == "":
        return (0, "")

    data = _converter_data(texto)
    if data is not None:
        return (1, data)

    numero = _converter_numero(texto)
    if numero is not None:
        return (2, numero)

    return (3, texto.upper())


def _valor_item(tabela, item_id, coluna):
    if coluna == "#0":
        return tabela.item(item_id, "text")

    return tabela.set(item_id, coluna)


def _ordenar(tabela, coluna):
    estado = getattr(tabela, "_sort_state", {})
    ascendente = not estado.get(coluna, False)
    estado = {coluna: ascendente}
    tabela._sort_state = estado

    pais = list(tabela.get_children(""))

    pais.sort(
        key=lambda item_id: _chave_ordenacao(_valor_item(tabela, item_id, coluna)),
        reverse=not ascendente,
    )

    for indice, item_id in enumerate(pais):
        tabela.move(item_id, "", indice)

    _atualizar_cabecalhos(tabela, coluna, ascendente)


def _atualizar_cabecalhos(tabela, coluna_ativa=None, ascendente=True):
    labels = getattr(tabela, "_sort_labels", {})

    for coluna in ["#0"] + list(tabela["columns"]):
        if coluna not in labels:
            continue

        texto = labels[coluna]

        if coluna == coluna_ativa:
            texto = f"{texto} {'↑' if ascendente else '↓'}"

        tabela.heading(
            coluna,
            text=texto,
            command=lambda c=coluna: _ordenar(tabela, c),
        )


def aplicar_ordenacao_treeview(tabela):
    """Ativa ordenação clicável nos cabeçalhos de uma Treeview.

    Ordena apenas os registros de primeiro nível. Em abas com pedidos agrupados,
    os itens continuam dentro do respectivo pedido.
    """
    labels = {}

    for coluna in ["#0"] + list(tabela["columns"]):
        try:
            texto = tabela.heading(coluna).get("text", coluna)
        except Exception:
            texto = coluna

        texto = str(texto).replace(" ↑", "").replace(" ↓", "")
        labels[coluna] = texto

    tabela._sort_labels = labels

    if not hasattr(tabela, "_sort_state"):
        tabela._sort_state = {}

    _atualizar_cabecalhos(tabela)
