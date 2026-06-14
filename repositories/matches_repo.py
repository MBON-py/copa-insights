from supabase import Client

from core.constants import StatusJogo
from models.match import Match


def list_all(client: Client) -> list[Match]:
    """Lista todos os jogos, ordenados por data/hora."""
    response = client.table("matches").select("*").order("data_hora").execute()
    return [Match.model_validate(row) for row in response.data]


def insert_many(client: Client, rows: list[dict]) -> list[Match]:
    """Insere jogos em lote (importação inicial via CSV)."""
    response = client.table("matches").insert(rows).execute()
    return [Match.model_validate(row) for row in response.data]


def update_result(client: Client, match_id: int, gols_1: int, gols_2: int) -> Match:
    """Atualiza o placar oficial e marca o jogo como Finalizado (PDR §11)."""
    response = (
        client.table("matches")
        .update({"gols_selecao_1": gols_1, "gols_selecao_2": gols_2, "status": StatusJogo.FINALIZADO.value})
        .eq("id", match_id)
        .execute()
    )
    return Match.model_validate(response.data[0])
