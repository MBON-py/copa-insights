from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLogEntry(BaseModel):
    id: int
    user_id: str | None
    nome_completo: str | None
    acao: str
    detalhe: dict[str, Any] | None
    created_at: datetime
