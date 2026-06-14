from dataclasses import dataclass

from supabase import Client

from models.dashboard import MatchAccuracy, PredictionDistribution
from repositories import dashboard_repo


@dataclass
class AcertoJogo:
    match: MatchAccuracy
    taxa_acerto: float


def get_match_accuracy(client: Client) -> list[AcertoJogo]:
    """Retorna os acertos por jogo finalizado, com a taxa de acerto (PDR §17)."""
    rows = dashboard_repo.list_match_accuracy(client)
    return [
        AcertoJogo(
            match=row,
            taxa_acerto=row.acertos_totais / row.total_palpites if row.total_palpites else 0.0,
        )
        for row in rows
    ]


def get_prediction_distribution(client: Client, match_id: int) -> list[PredictionDistribution]:
    """Retorna a distribuição de placares apostados para um jogo (PDR §17)."""
    return dashboard_repo.list_prediction_distribution(client, match_id)
