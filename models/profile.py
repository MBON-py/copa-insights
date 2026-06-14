from datetime import datetime

from pydantic import BaseModel

from core.constants import Perfil


class Profile(BaseModel):
    id: str
    nome_completo: str
    email: str
    telefone: str
    perfil: Perfil
    ativo: bool
    created_at: datetime
    updated_at: datetime
