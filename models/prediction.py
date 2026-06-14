from datetime import datetime

from pydantic import BaseModel


class Prediction(BaseModel):
    id: int
    user_id: str
    match_id: int
    gols_selecao_1: int
    gols_selecao_2: int
    pontos: int | None
    data_aposta: datetime
    created_at: datetime
    updated_at: datetime
