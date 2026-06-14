from pydantic import BaseModel, Field

from core.constants import Etapa


class MatchAccuracy(BaseModel):
    match_id: int
    selecao_1: str
    selecao_2: str
    etapa: Etapa
    total_palpites: int
    placares_exatos: int
    # A coluna `acertos_vencedor` em v_match_accuracy conta pontos >= 1, ou
    # seja, inclui os placares exatos — representa o total de acertos do jogo.
    acertos_totais: int = Field(alias="acertos_vencedor")


class PredictionDistribution(BaseModel):
    match_id: int
    gols_selecao_1: int
    gols_selecao_2: int
    quantidade: int
