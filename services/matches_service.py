from dataclasses import dataclass
from datetime import date, datetime, time
from io import BytesIO
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
from supabase import Client

from core.constants import Etapa
from core.csv_utils import ERRO_LEITURA_CSV, ler_csv, normalizar
from models.match import Match
from repositories import matches_repo
from services import audit_service

_FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")

_COLUNAS_OBRIGATORIAS = ["selecao_1", "selecao_2", "data", "horario", "etapa"]

_FORMATOS_DATA = ["%Y-%m-%d", "%d/%m/%Y"]
_FORMATOS_HORA = ["%H:%M", "%H:%M:%S"]

_ETAPAS_POR_NOME_NORMALIZADO = {normalizar(etapa.value): etapa for etapa in Etapa}


def _parse_data(texto: str) -> date | None:
    for formato in _FORMATOS_DATA:
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    return None


def _parse_hora(texto: str) -> time | None:
    for formato in _FORMATOS_HORA:
        try:
            return datetime.strptime(texto, formato).time()
        except ValueError:
            continue
    return None


@dataclass
class ImportPreview:
    rows: list[dict[str, Any]]
    preview: pd.DataFrame
    errors: list[str]


def parse_csv(file: BytesIO) -> ImportPreview:
    """Lê e valida o CSV de importação inicial dos jogos (PDR §10).

    Colunas esperadas (com ou sem acento): selecao_1, selecao_2, data,
    horario, grupo (opcional), etapa. `data` aceita `AAAA-MM-DD` ou
    `DD/MM/AAAA`; `horario` aceita `HH:MM` ou `HH:MM:SS`, interpretado no
    fuso America/Sao_Paulo.
    """
    df = ler_csv(file)
    if df is None:
        return ImportPreview([], pd.DataFrame(), [ERRO_LEITURA_CSV])

    colunas_faltantes = [c for c in _COLUNAS_OBRIGATORIAS if c not in df.columns]
    if colunas_faltantes:
        return ImportPreview(
            [], pd.DataFrame(), [f"Colunas obrigatórias ausentes no CSV: {', '.join(colunas_faltantes)}."]
        )

    rows: list[dict[str, Any]] = []
    preview_records: list[dict[str, Any]] = []
    errors: list[str] = []

    for indice, linha in df.iterrows():
        numero_linha = int(indice) + 2  # +1 (1-index) + 1 (linha de cabeçalho)
        erros_linha: list[str] = []

        selecao_1 = linha["selecao_1"].strip()
        selecao_2 = linha["selecao_2"].strip()
        if not selecao_1:
            erros_linha.append("seleção_1 vazia")
        if not selecao_2:
            erros_linha.append("seleção_2 vazia")

        etapa = _ETAPAS_POR_NOME_NORMALIZADO.get(normalizar(linha["etapa"]))
        if etapa is None:
            erros_linha.append(f"etapa inválida: '{linha['etapa']}'")

        data_texto = linha["data"].strip()
        hora_texto = linha["horario"].strip()
        data_parseada = _parse_data(data_texto)
        hora_parseada = _parse_hora(hora_texto)
        if data_parseada is None:
            erros_linha.append(f"data inválida: '{data_texto}'")
        if hora_parseada is None:
            erros_linha.append(f"horário inválido: '{hora_texto}'")

        grupo = linha["grupo"].strip() if "grupo" in df.columns else ""

        if erros_linha:
            errors.append(f"Linha {numero_linha}: {'; '.join(erros_linha)}")
            continue

        assert etapa is not None and data_parseada is not None and hora_parseada is not None
        data_hora = datetime.combine(data_parseada, hora_parseada, tzinfo=_FUSO_HORARIO)

        rows.append(
            {
                "selecao_1": selecao_1,
                "selecao_2": selecao_2,
                "data_hora": data_hora.isoformat(),
                "grupo": grupo or None,
                "etapa": etapa.value,
            }
        )
        preview_records.append(
            {
                "Seleção 1": selecao_1,
                "Seleção 2": selecao_2,
                "Data/hora": data_hora.strftime("%d/%m/%Y %H:%M"),
                "Grupo": grupo or "-",
                "Etapa": etapa.value,
            }
        )

    return ImportPreview(rows, pd.DataFrame(preview_records), errors)


def import_matches(client: Client, user_id: str, rows: list[dict[str, Any]]) -> list[Match]:
    """Apaga todos os jogos cadastrados e insere os jogos do CSV, registrando a importação na auditoria (PDR §18).

    Apagar os jogos remove em cascata os palpites e placares já lançados.
    Permite reenviar o CSV de importação inicial sem duplicar o calendário,
    sempre substituindo o conteúdo anterior pelo do arquivo enviado.
    """
    removidos, matches = matches_repo.replace_all(client, rows)
    audit_service.log_action(
        client, user_id, "importacao_jogos", {"jogos_removidos": removidos, "jogos_importados": len(matches)}
    )
    return matches


def get_matches(client: Client) -> list[Match]:
    """Lista todos os jogos cadastrados, ordenados por data/hora."""
    return matches_repo.list_all(client)


def set_result(client: Client, user_id: str, match_id: int, gols_1: int, gols_2: int) -> Match:
    """Registra o resultado oficial de um jogo, finalizando-o (PDR §11).

    A pontuação dos palpites desse jogo é recalculada automaticamente por
    trigger no banco quando o status muda para "Finalizado".
    """
    match = matches_repo.update_result(client, match_id, gols_1, gols_2)
    audit_service.log_action(
        client,
        user_id,
        "lancamento_resultado",
        {
            "match_id": match_id,
            "confronto": f"{match.selecao_1} x {match.selecao_2}",
            "gols_selecao_1": gols_1,
            "gols_selecao_2": gols_2,
        },
    )
    return match
