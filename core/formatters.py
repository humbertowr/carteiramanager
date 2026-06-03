import pandas as pd


def normalizar_texto(valor):
    if pd.isna(valor):
        return ""

    texto = str(valor).strip()

    if texto.lower() in ["nan", "none"]:
        return ""

    return texto


def converter_numero_br(serie):
    serie = serie.astype(str)
    serie = serie.str.strip()
    serie = serie.str.replace("R$", "", regex=False)
    serie = serie.str.replace(" ", "", regex=False)

    def tratar_valor(valor):
        if valor in ["", "nan", "None", "NaN"]:
            return 0

        if "," in valor:
            valor = valor.replace(".", "")
            valor = valor.replace(",", ".")

        try:
            return float(valor)
        except ValueError:
            return 0

    return serie.apply(tratar_valor)


def converter_valor_digitado(texto):
    texto = str(texto).strip()

    if not texto:
        return 0

    texto = texto.replace("R$", "")
    texto = texto.replace(" ", "")

    if "," in texto:
        texto = texto.replace(".", "")
        texto = texto.replace(",", ".")

    try:
        return float(texto)
    except ValueError:
        return 0


def formatar_moeda(valor):
    try:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def formatar_numero(valor):
    try:
        return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0,00"


def formatar_data(valor):
    try:
        if valor is None or pd.isna(valor):
            return ""
        data = pd.to_datetime(valor, dayfirst=True, errors="coerce")
        if pd.isna(data):
            return str(valor)
        return data.strftime("%d/%m/%Y")
    except Exception:
        return str(valor or "")


def formatar_data_hora(valor):
    try:
        if valor is None or pd.isna(valor):
            return ""
        data = pd.to_datetime(valor, dayfirst=True, errors="coerce")
        if pd.isna(data):
            return str(valor)
        return data.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(valor or "")
