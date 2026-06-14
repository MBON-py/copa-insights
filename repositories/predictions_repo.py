from typing import Any

from supabase import Client

from models.prediction import Prediction


def list_by_user(client: Client, user_id: str) -> list[Prediction]:
    """Lista todos os palpites de um usuário."""
    response = client.table("predictions").select("*").eq("user_id", user_id).execute()
    return [Prediction.model_validate(row) for row in response.data]


def get_by_user_and_match(client: Client, user_id: str, match_id: int) -> Prediction | None:
    """Busca o palpite de um usuário para um jogo específico, se existir."""
    response = (
        client.table("predictions").select("*").eq("user_id", user_id).eq("match_id", match_id).execute()
    )
    if not response.data:
        return None
    return Prediction.model_validate(response.data[0])


def upsert_many(client: Client, rows: list[dict[str, Any]]) -> list[Prediction]:
    """Cria ou atualiza palpites (um por usuário/jogo)."""
    response = client.table("predictions").upsert(rows, on_conflict="user_id,match_id").execute()
    return [Prediction.model_validate(row) for row in response.data]
