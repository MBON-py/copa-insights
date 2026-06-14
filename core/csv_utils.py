import unicodedata
from io import BytesIO, StringIO

import pandas as pd

ERRO_LEITURA_CSV = "Não foi possível ler o arquivo. Salve o CSV em UTF-8 ou Windows-1252."


def normalizar(texto: str) -> str:
    """Remove acentos/ordinais e normaliza espaços e caixa para comparação."""
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return sem_acento.replace("º", "").replace("°", "").strip().lower()


def ler_csv(file: BytesIO) -> pd.DataFrame | None:
    """Lê um CSV (UTF-8 ou Windows-1252) com colunas normalizadas, ou None se ilegível."""
    conteudo = file.read()
    texto = None
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            texto = conteudo.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if texto is None:
        return None

    df = pd.read_csv(StringIO(texto), sep=None, engine="python", dtype=str).fillna("")
    df.columns = [normalizar(col) for col in df.columns]
    return df
