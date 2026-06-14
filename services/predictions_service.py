from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from supabase import Client

from core import flags
from models.match import Match
from models.prediction import Prediction
from repositories import matches_repo, predictions_repo
from services import audit_service


@dataclass
class MatchComPalpite:
    match: Match
    palpite: Prediction | None


@dataclass
class PontoEvolucao:
    data_hora: datetime
    confronto: str
    pontos: int
    pontos_acumulados: int


def get_matches_with_predictions(client: Client, user_id: str) -> tuple[list[MatchComPalpite], list[MatchComPalpite]]:
    """Retorna (jogos em aberto, jogos encerrados) com o palpite do usuário, se houver.

    Um jogo está "em aberto" enquanto `data_hora` ainda não chegou (trava por
    horário, espelhando as policies de RLS de predictions).
    """
    matches = matches_repo.list_all(client)
    palpites_por_jogo = {p.match_id: p for p in predictions_repo.list_by_user(client, user_id)}
    agora = datetime.now(timezone.utc)

    abertos: list[MatchComPalpite] = []
    encerrados: list[MatchComPalpite] = []
    for match in matches:
        item = MatchComPalpite(match=match, palpite=palpites_por_jogo.get(match.id))
        if match.data_hora > agora:
            abertos.append(item)
        else:
            encerrados.append(item)
    return abertos, encerrados


def get_evolucao_pontuacao(client: Client, user_id: str) -> list[PontoEvolucao]:
    """Retorna a evolução da pontuação acumulada do participante, em ordem cronológica (PDR §17)."""
    _, encerrados = get_matches_with_predictions(client, user_id)
    pontuados = [item for item in encerrados if item.palpite is not None and item.palpite.pontos is not None]
    pontuados.sort(key=lambda item: item.match.data_hora)

    evolucao: list[PontoEvolucao] = []
    acumulado = 0
    for item in pontuados:
        pontos = item.palpite.pontos
        acumulado += pontos
        evolucao.append(
            PontoEvolucao(
                data_hora=item.match.data_hora,
                confronto=flags.confronto(item.match.selecao_1, item.match.selecao_2),
                pontos=pontos,
                pontos_acumulados=acumulado,
            )
        )
    return evolucao


def get_palpite(client: Client, user_id: str, match_id: int) -> Prediction | None:
    """Busca o palpite de um usuário para um jogo específico, se existir."""
    return predictions_repo.get_by_user_and_match(client, user_id, match_id)


def save_palpites(client: Client, user_id: str, valores: dict[int, tuple[int, int]]) -> list[Prediction]:
    """Cria ou atualiza os palpites informados (match_id -> (gols_1, gols_2))."""
    rows = [
        {"user_id": user_id, "match_id": match_id, "gols_selecao_1": gols_1, "gols_selecao_2": gols_2}
        for match_id, (gols_1, gols_2) in valores.items()
    ]
    return predictions_repo.upsert_many(client, rows)


def set_palpite_admin(
    client: Client,
    admin_user_id: str,
    target_user_id: str,
    match_id: int,
    gols_1: int,
    gols_2: int,
    data_aposta: datetime | None = None,
) -> Prediction:
    """Insere ou corrige o palpite de um participante para um jogo (PDR §12).

    Recalcula a pontuação desse palpite (caso o jogo já esteja finalizado) e
    registra a correção na auditoria (PDR §18).
    """
    row: dict[str, Any] = {
        "user_id": target_user_id,
        "match_id": match_id,
        "gols_selecao_1": gols_1,
        "gols_selecao_2": gols_2,
    }
    if data_aposta is not None:
        row["data_aposta"] = data_aposta.isoformat()

    predictions_repo.upsert_many(client, [row])
    client.rpc("recalculate_match_predictions", {"p_match_id": match_id}).execute()

    audit_service.log_action(
        client,
        admin_user_id,
        "correcao_palpite_historico",
        {
            "user_id": target_user_id,
            "match_id": match_id,
            "gols_selecao_1": gols_1,
            "gols_selecao_2": gols_2,
        },
    )

    palpite = predictions_repo.get_by_user_and_match(client, target_user_id, match_id)
    assert palpite is not None
    return palpite
