from datetime import datetime

from pydantic import BaseModel

from core.constants import Etapa, StatusJogo


class Match(BaseModel):
    id: int
    selecao_1: str
    selecao_2: str
    data_hora: datetime
    grupo: str | None
    etapa: Etapa
    status: StatusJogo
    gols_selecao_1: int | None
    gols_selecao_2: int | None
    created_at: datetime
    updated_at: datetime
