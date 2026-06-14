from supabase import Client

from core.constants import StatusJogo
from models.match import Match


def list_all(client: Client) -> list[Match]:
    """Lista todos os jogos, ordenados por data/hora."""
    response = client.table("matches").select("*").order("data_hora").execute()
    return [Match.model_validate(row) for row in response.data]


def replace_all(client: Client, rows: list[dict]) -> tuple[int, list[Match]]:
    """Apaga todos os jogos cadastrados e insere os jogos do CSV (PDR §10).

    A FK predictions.match_id possui ON DELETE CASCADE, portanto apagar os
    jogos remove em cascata os palpites e placares já lançados. Usado para
    reimportar o calendário do zero a cada upload do CSV de importação
    inicial, evitando duplicação. Retorna a quantidade de jogos removidos e
    os jogos inseridos.
    """
    removidos = len(list_all(client))
    client.table("matches").delete().neq("id", 0).execute()

    response = client.table("matches").insert(rows).execute()
    return removidos, [Match.model_validate(row) for row in response.data]


def update_result(client: Client, match_id: int, gols_1: int, gols_2: int) -> Match:
    """Atualiza o placar oficial e marca o jogo como Finalizado (PDR §11)."""
    response = (
        client.table("matches")
        .update({"gols_selecao_1": gols_1, "gols_selecao_2": gols_2, "status": StatusJogo.FINALIZADO.value})
        .eq("id", match_id)
        .execute()
    )
    return Match.model_validate(response.data[0])
