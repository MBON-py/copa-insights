from collections import defaultdict

from supabase import Client

from core.constants import StatusJogo
from core.csv_utils import normalizar
from models.match import Match


def list_all(client: Client) -> list[Match]:
    """Lista todos os jogos, ordenados por data/hora."""
    response = client.table("matches").select("*").order("data_hora").execute()
    return [Match.model_validate(row) for row in response.data]


def upsert_many(client: Client, rows: list[dict]) -> list[Match]:
    """Insere jogos novos e atualiza data/hora e grupo dos já cadastrados (PDR §10).

    Cada linha é casada com um jogo existente por (selecao_1, selecao_2,
    etapa) normalizados; se houver exatamente um jogo correspondente, sua
    `data_hora`/`grupo` são atualizados (status e placar são preservados).
    Caso contrário (jogo novo, ou chave ambígua), a linha é inserida. Evita
    duplicar o calendário quando o CSV de importação inicial é reenviado.
    """
    existentes: dict[tuple[str, str, str], list[Match]] = defaultdict(list)
    for match in list_all(client):
        chave = (normalizar(match.selecao_1), normalizar(match.selecao_2), normalizar(match.etapa.value))
        existentes[chave].append(match)

    novos: list[dict] = []
    resultado: list[Match] = []
    for row in rows:
        chave = (normalizar(row["selecao_1"]), normalizar(row["selecao_2"]), normalizar(row["etapa"]))
        candidatos = existentes.get(chave, [])
        if len(candidatos) == 1:
            response = (
                client.table("matches")
                .update({"data_hora": row["data_hora"], "grupo": row["grupo"]})
                .eq("id", candidatos[0].id)
                .execute()
            )
            resultado.append(Match.model_validate(response.data[0]))
        else:
            novos.append(row)

    if novos:
        response = client.table("matches").insert(novos).execute()
        resultado.extend(Match.model_validate(row) for row in response.data)

    return resultado


def update_result(client: Client, match_id: int, gols_1: int, gols_2: int) -> Match:
    """Atualiza o placar oficial e marca o jogo como Finalizado (PDR §11)."""
    response = (
        client.table("matches")
        .update({"gols_selecao_1": gols_1, "gols_selecao_2": gols_2, "status": StatusJogo.FINALIZADO.value})
        .eq("id", match_id)
        .execute()
    )
    return Match.model_validate(response.data[0])
