from supabase import Client

from models.ranking import RankingEntry


def list_ranking(client: Client) -> list[RankingEntry]:
    """Lista a classificação geral, ordenada pela posição (public.v_ranking)."""
    response = client.table("v_ranking").select("*").order("posicao").execute()
    return [RankingEntry.model_validate(row) for row in response.data]
