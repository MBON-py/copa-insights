import re
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
from supabase import Client
from supabase_auth.errors import AuthApiError

from core import flags
from core.csv_utils import ERRO_LEITURA_CSV, ler_csv, normalizar
from models.match import Match
from repositories import matches_repo, predictions_repo, profiles_repo
from repositories.supabase_client import get_admin_client
from services import audit_service, ranking_service

_FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")

_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_COLUNAS_PARTICIPANTES = ["nome", "email", "telefone"]
_COLUNAS_PALPITES = ["email", "selecao_1", "selecao_2", "gols_selecao_1", "gols_selecao_2", "data_aposta"]
_COLUNAS_RESULTADOS = ["selecao_1", "selecao_2", "gols_selecao_1", "gols_selecao_2"]

_FORMATOS_DATA_HORA = ["%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M", "%Y-%m-%d", "%d/%m/%Y"]


@dataclass
class ImportPreview:
    rows: list[dict[str, Any]]
    preview: pd.DataFrame
    errors: list[str]


@dataclass
class ImportResult:
    sucesso: int
    erros: list[str]


def _parse_data_hora(texto: str) -> datetime | None:
    for formato in _FORMATOS_DATA_HORA:
        try:
            return datetime.strptime(texto, formato).replace(tzinfo=_FUSO_HORARIO)
        except ValueError:
            continue
    return None


def _find_match(matches: list[Match], selecao_1: str, selecao_2: str) -> Match | None:
    chave = (normalizar(selecao_1), normalizar(selecao_2))
    candidatos = [m for m in matches if (normalizar(m.selecao_1), normalizar(m.selecao_2)) == chave]
    return candidatos[0] if len(candidatos) == 1 else None


# --------------------------------------------------------------------- #
# Participantes históricos
# --------------------------------------------------------------------- #


def parse_participantes_csv(client: Client, file: BytesIO) -> ImportPreview:
    """Lê e valida o CSV de participantes históricos (PDR §16).

    Colunas esperadas: nome, email, telefone.
    """
    df = ler_csv(file)
    if df is None:
        return ImportPreview([], pd.DataFrame(), [ERRO_LEITURA_CSV])

    colunas_faltantes = [c for c in _COLUNAS_PARTICIPANTES if c not in df.columns]
    if colunas_faltantes:
        return ImportPreview(
            [], pd.DataFrame(), [f"Colunas obrigatórias ausentes no CSV: {', '.join(colunas_faltantes)}."]
        )

    existentes = profiles_repo.list_all(client)
    emails_existentes = {p.email.lower() for p in existentes}
    telefones_existentes = {p.telefone for p in existentes}

    rows: list[dict[str, Any]] = []
    preview_records: list[dict[str, Any]] = []
    errors: list[str] = []
    emails_no_arquivo: set[str] = set()
    telefones_no_arquivo: set[str] = set()

    for indice, linha in df.iterrows():
        numero_linha = int(indice) + 2
        erros_linha: list[str] = []

        nome = linha["nome"].strip()
        email = linha["email"].strip().lower()
        telefone = linha["telefone"].strip()

        if not nome:
            erros_linha.append("nome vazio")
        if not email or not _EMAIL_REGEX.match(email):
            erros_linha.append(f"e-mail inválido: '{email}'")
        elif email in emails_existentes:
            erros_linha.append(f"e-mail já cadastrado: '{email}'")
        elif email in emails_no_arquivo:
            erros_linha.append(f"e-mail duplicado no arquivo: '{email}'")

        if not telefone:
            erros_linha.append("telefone vazio")
        elif telefone in telefones_existentes:
            erros_linha.append(f"telefone já cadastrado: '{telefone}'")
        elif telefone in telefones_no_arquivo:
            erros_linha.append(f"telefone duplicado no arquivo: '{telefone}'")

        if erros_linha:
            errors.append(f"Linha {numero_linha}: {'; '.join(erros_linha)}")
            continue

        emails_no_arquivo.add(email)
        telefones_no_arquivo.add(telefone)
        rows.append({"nome": nome, "email": email, "telefone": telefone})
        preview_records.append({"Nome": nome, "E-mail": email, "Telefone": telefone})

    return ImportPreview(rows, pd.DataFrame(preview_records), errors)


def import_participantes_historicos(client: Client, user_id: str, rows: list[dict[str, Any]]) -> ImportResult:
    """Cria os participantes históricos via Supabase Auth (PDR §16).

    Cada participante é criado com uma senha temporária aleatória; o
    profile é criado automaticamente pelo trigger `handle_new_user` e o
    participante deve usar "recuperar senha" para definir a própria senha.
    """
    admin_client = get_admin_client()

    sucesso = 0
    erros: list[str] = []
    for row in rows:
        try:
            profiles_repo.create_user(admin_client, row["email"], row["nome"], row["telefone"])
        except AuthApiError as exc:
            erros.append(f"{row['email']}: {exc.message}")
            continue
        sucesso += 1

    audit_service.log_action(
        client, user_id, "importacao_participantes_historicos", {"quantidade": sucesso, "erros": len(erros)}
    )
    return ImportResult(sucesso=sucesso, erros=erros)


# --------------------------------------------------------------------- #
# Palpites históricos
# --------------------------------------------------------------------- #


def parse_palpites_csv(client: Client, file: BytesIO) -> ImportPreview:
    """Lê e valida o CSV de palpites históricos (PDR §12/§16).

    Colunas esperadas: email (participante), selecao_1 e selecao_2 (jogo,
    times conforme cadastrados em Admin > Jogos), gols_selecao_1,
    gols_selecao_2 e data_aposta (opcional; AAAA-MM-DD HH:MM, DD/MM/AAAA
    HH:MM, AAAA-MM-DD ou DD/MM/AAAA).
    """
    df = ler_csv(file)
    if df is None:
        return ImportPreview([], pd.DataFrame(), [ERRO_LEITURA_CSV])

    colunas_faltantes = [c for c in _COLUNAS_PALPITES if c not in df.columns]
    if colunas_faltantes:
        return ImportPreview(
            [], pd.DataFrame(), [f"Colunas obrigatórias ausentes no CSV: {', '.join(colunas_faltantes)}."]
        )

    matches = matches_repo.list_all(client)
    profiles_por_email = {p.email.lower(): p for p in profiles_repo.list_all(client)}

    rows: list[dict[str, Any]] = []
    preview_records: list[dict[str, Any]] = []
    errors: list[str] = []

    for indice, linha in df.iterrows():
        numero_linha = int(indice) + 2
        erros_linha: list[str] = []

        email = linha["email"].strip().lower()
        selecao_1 = linha["selecao_1"].strip()
        selecao_2 = linha["selecao_2"].strip()

        profile = profiles_por_email.get(email)
        if profile is None:
            erros_linha.append(f"participante não encontrado: '{email}'")

        match = _find_match(matches, selecao_1, selecao_2)
        if match is None:
            erros_linha.append(f"jogo não encontrado: '{selecao_1} x {selecao_2}'")

        try:
            gols_1 = int(linha["gols_selecao_1"].strip())
            gols_2 = int(linha["gols_selecao_2"].strip())
            if gols_1 < 0 or gols_2 < 0:
                raise ValueError
        except ValueError:
            erros_linha.append("placar inválido")
            gols_1 = gols_2 = 0

        texto_data = linha["data_aposta"].strip()
        data_aposta: datetime | None = None
        if texto_data:
            data_aposta = _parse_data_hora(texto_data)
            if data_aposta is None:
                erros_linha.append(f"data_aposta inválida: '{texto_data}'")

        if erros_linha:
            errors.append(f"Linha {numero_linha}: {'; '.join(erros_linha)}")
            continue

        assert profile is not None and match is not None
        row: dict[str, Any] = {
            "user_id": profile.id,
            "match_id": match.id,
            "gols_selecao_1": gols_1,
            "gols_selecao_2": gols_2,
        }
        if data_aposta is not None:
            row["data_aposta"] = data_aposta.isoformat()
        rows.append(row)
        preview_records.append(
            {
                "Participante": profile.nome_completo,
                "Confronto": flags.confronto(match.selecao_1, match.selecao_2),
                "Palpite": f"{gols_1} x {gols_2}",
                "Data do palpite": data_aposta.strftime("%d/%m/%Y %H:%M") if data_aposta else "-",
            }
        )

    return ImportPreview(rows, pd.DataFrame(preview_records), errors)


def import_palpites_historicos(client: Client, user_id: str, rows: list[dict[str, Any]]) -> ImportResult:
    """Importa palpites históricos e recalcula o ranking (PDR §16)."""
    predictions_repo.upsert_many(client, rows)
    audit_service.log_action(client, user_id, "importacao_palpites_historicos", {"quantidade": len(rows)})
    ranking_service.recalculate_ranking(client, user_id)
    return ImportResult(sucesso=len(rows), erros=[])


# --------------------------------------------------------------------- #
# Resultados históricos
# --------------------------------------------------------------------- #


def parse_resultados_csv(client: Client, file: BytesIO) -> ImportPreview:
    """Lê e valida o CSV de resultados históricos (PDR §16).

    Colunas esperadas: selecao_1 e selecao_2 (jogo, times conforme
    cadastrados em Admin > Jogos), gols_selecao_1, gols_selecao_2.
    """
    df = ler_csv(file)
    if df is None:
        return ImportPreview([], pd.DataFrame(), [ERRO_LEITURA_CSV])

    colunas_faltantes = [c for c in _COLUNAS_RESULTADOS if c not in df.columns]
    if colunas_faltantes:
        return ImportPreview(
            [], pd.DataFrame(), [f"Colunas obrigatórias ausentes no CSV: {', '.join(colunas_faltantes)}."]
        )

    matches = matches_repo.list_all(client)

    rows: list[dict[str, Any]] = []
    preview_records: list[dict[str, Any]] = []
    errors: list[str] = []

    for indice, linha in df.iterrows():
        numero_linha = int(indice) + 2
        erros_linha: list[str] = []

        selecao_1 = linha["selecao_1"].strip()
        selecao_2 = linha["selecao_2"].strip()
        match = _find_match(matches, selecao_1, selecao_2)
        if match is None:
            erros_linha.append(f"jogo não encontrado: '{selecao_1} x {selecao_2}'")

        try:
            gols_1 = int(linha["gols_selecao_1"].strip())
            gols_2 = int(linha["gols_selecao_2"].strip())
            if gols_1 < 0 or gols_2 < 0:
                raise ValueError
        except ValueError:
            erros_linha.append("placar inválido")
            gols_1 = gols_2 = 0

        if erros_linha:
            errors.append(f"Linha {numero_linha}: {'; '.join(erros_linha)}")
            continue

        assert match is not None
        rows.append({"match_id": match.id, "gols_selecao_1": gols_1, "gols_selecao_2": gols_2})
        preview_records.append(
            {"Confronto": flags.confronto(match.selecao_1, match.selecao_2), "Placar": f"{gols_1} x {gols_2}"}
        )

    return ImportPreview(rows, pd.DataFrame(preview_records), errors)


def import_resultados_historicos(client: Client, user_id: str, rows: list[dict[str, Any]]) -> ImportResult:
    """Importa resultados históricos; cada jogo é finalizado e o ranking é recalculado (PDR §16)."""
    for row in rows:
        matches_repo.update_result(client, row["match_id"], row["gols_selecao_1"], row["gols_selecao_2"])
    audit_service.log_action(client, user_id, "importacao_resultados_historicos", {"quantidade": len(rows)})
    ranking_service.recalculate_ranking(client, user_id)
    return ImportResult(sucesso=len(rows), erros=[])
