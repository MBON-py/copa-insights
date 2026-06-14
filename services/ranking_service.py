from dataclasses import dataclass

from supabase import Client

from models.ranking import RankingEntry
from repositories import ranking_repo
from services import audit_service

VALOR_PARTICIPACAO = 10.0

PREMIOS = {1: 100.0, 2: 30.0, 3: 10.0}


@dataclass
class Premiacao:
    quantidade_participantes: int
    valor_arrecadado: float
    valor_distribuido: float
    vencedores: list[tuple[int, str, float]]


def get_ranking(client: Client) -> list[RankingEntry]:
    """Retorna a classificação geral, ordenada pela posição (PDR §14)."""
    return ranking_repo.list_ranking(client)


def recalculate_ranking(client: Client, user_id: str) -> None:
    """Reaplica a pontuação de todos os palpites com base nos resultados oficiais (PDR §14)."""
    client.rpc("recalculate_all_rankings", {}).execute()
    audit_service.log_action(client, user_id, "recalculo_ranking", {})


def get_premiacao(ranking: list[RankingEntry]) -> Premiacao:
    """Calcula arrecadação e distribuição da premiação (PDR §15).

    Cada posição premiada (1º/2º/3º) recebe o valor correspondente; em caso
    de empate, todos os participantes naquela posição recebem o prêmio
    integral. Posições "puladas" pelo empate (ex.: 1º, 1º, 3º) não têm
    prêmio de 2º lugar distribuído.
    """
    vencedores = [
        (entry.posicao, entry.nickname, PREMIOS[entry.posicao])
        for entry in ranking
        if entry.posicao in PREMIOS
    ]
    return Premiacao(
        quantidade_participantes=len(ranking),
        valor_arrecadado=len(ranking) * VALOR_PARTICIPACAO,
        valor_distribuido=sum(valor for _, _, valor in vencedores),
        vencedores=vencedores,
    )
