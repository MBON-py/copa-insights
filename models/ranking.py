from pydantic import BaseModel


class RankingEntry(BaseModel):
    user_id: str
    nome_completo: str
    pontos_total: int
    placares_exatos: int
    acertos_vencedor: int
    posicao: int
