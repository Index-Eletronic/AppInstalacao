from datetime import datetime


def limpar_cpf(cpf: str) -> str:
    return "".join(ch for ch in cpf if ch.isdigit())


def parse_qr_text(qr_text: str) -> dict:
    dados = {
        "ID": "",
        "Data": "",
        "Cliente": "",
        "Produto": "",
        "Projetista": ""
    }

    for linha in qr_text.splitlines():
        if "=" in linha:
            chave, valor = linha.split("=", 1)
            chave = chave.strip()
            valor = valor.strip()
            if chave in dados:
                dados[chave] = valor

    return dados


def parse_date(valor: str):
    if not valor:
        return None
    return datetime.strptime(valor, "%Y-%m-%d")