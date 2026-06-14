"""Bandeiras (emoji) por seleção, para identidade visual (PDR §19)."""

from core.csv_utils import normalizar

# Nome da seleção (normalizado via core.csv_utils.normalizar) -> código ISO 3166-1 alpha-2.
_PAISES_ISO: dict[str, str] = {
    # CONMEBOL
    "brasil": "BR",
    "argentina": "AR",
    "uruguai": "UY",
    "colombia": "CO",
    "equador": "EC",
    "paraguai": "PY",
    "chile": "CL",
    "peru": "PE",
    "bolivia": "BO",
    "venezuela": "VE",
    # UEFA
    "alemanha": "DE",
    "franca": "FR",
    "espanha": "ES",
    "italia": "IT",
    "inglaterra": "GB",
    "portugal": "PT",
    "holanda": "NL",
    "paises baixos": "NL",
    "belgica": "BE",
    "croacia": "HR",
    "suica": "CH",
    "polonia": "PL",
    "servia": "RS",
    "dinamarca": "DK",
    "suecia": "SE",
    "noruega": "NO",
    "ucrania": "UA",
    "republica tcheca": "CZ",
    "tchequia": "CZ",
    "austria": "AT",
    "irlanda": "IE",
    "hungria": "HU",
    "romenia": "RO",
    "grecia": "GR",
    "turquia": "TR",
    "russia": "RU",
    "eslovaquia": "SK",
    "eslovenia": "SI",
    "finlandia": "FI",
    "islandia": "IS",
    "bosnia e herzegovina": "BA",
    "macedonia do norte": "MK",
    "albania": "AL",
    "montenegro": "ME",
    "bulgaria": "BG",
    "israel": "IL",
    "georgia": "GE",
    # CONCACAF
    "mexico": "MX",
    "estados unidos": "US",
    "eua": "US",
    "canada": "CA",
    "costa rica": "CR",
    "jamaica": "JM",
    "panama": "PA",
    "honduras": "HN",
    "el salvador": "SV",
    "trinidad e tobago": "TT",
    "haiti": "HT",
    "curacao": "CW",
    # CAF
    "marrocos": "MA",
    "senegal": "SN",
    "camaroes": "CM",
    "nigeria": "NG",
    "gana": "GH",
    "argelia": "DZ",
    "tunisia": "TN",
    "egito": "EG",
    "costa do marfim": "CI",
    "africa do sul": "ZA",
    "mali": "ML",
    "cabo verde": "CV",
    "guine": "GN",
    "zambia": "ZM",
    "mocambique": "MZ",
    "angola": "AO",
    "republica democratica do congo": "CD",
    # AFC
    "japao": "JP",
    "coreia do sul": "KR",
    "coreia do norte": "KP",
    "australia": "AU",
    "arabia saudita": "SA",
    "ira": "IR",
    "catar": "QA",
    "iraque": "IQ",
    "emirados arabes unidos": "AE",
    "jordania": "JO",
    "uzbequistao": "UZ",
    "china": "CN",
    "india": "IN",
    "vietna": "VN",
    "tailandia": "TH",
    "indonesia": "ID",
    "oma": "OM",
    "kuwait": "KW",
    "bahrein": "BH",
    # OFC
    "nova zelandia": "NZ",
    "fiji": "FJ",
    "nova caledonia": "NC",
}


def _bandeira_iso(codigo: str) -> str:
    """Converte um código ISO 3166-1 alpha-2 no emoji de bandeira correspondente."""
    return "".join(chr(0x1F1E6 + ord(letra) - ord("A")) for letra in codigo)


def bandeira(nome: str) -> str:
    """Retorna o emoji de bandeira da seleção, ou "" se o nome não for reconhecido."""
    codigo = _PAISES_ISO.get(normalizar(nome))
    if codigo is None:
        return ""
    return _bandeira_iso(codigo)


def confronto(selecao_1: str, selecao_2: str) -> str:
    """Formata "Seleção 1 x Seleção 2" prefixando bandeiras quando reconhecidas."""
    nome_1 = f"{bandeira(selecao_1)} {selecao_1}".strip()
    nome_2 = f"{bandeira(selecao_2)} {selecao_2}".strip()
    return f"{nome_1} x {nome_2}"
