from supabase import Client

from models.dashboard import MatchAccuracy, PredictionDistribution


def list_match_accuracy(client: Client) -> list[MatchAccuracy]:
    """Lista os acertos por jogo finalizado (public.v_match_accuracy)."""
    response = client.table("v_match_accuracy").select("*").execute()
    return [MatchAccuracy.model_validate(row) for row in response.data]


def list_prediction_distribution(client: Client, match_id: int) -> list[PredictionDistribution]:
    """Lista a distribuição de placares apostados para um jogo (public.v_match_prediction_distribution)."""
    response = (
        client.table("v_match_prediction_distribution")
        .select("*")
        .eq("match_id", match_id)
        .execute()
    )
    return [PredictionDistribution.model_validate(row) for row in response.data]
