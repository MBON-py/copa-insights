from typing import Any

from supabase import Client

from models.audit import AuditLogEntry
from repositories import audit_repo


def log_action(client: Client, user_id: str, acao: str, detalhe: dict[str, Any]) -> None:
    """Registra uma ação administrativa para fins de auditoria (PDR §18)."""
    audit_repo.log(client, user_id, acao, detalhe)


def get_audit_log(client: Client) -> list[AuditLogEntry]:
    """Retorna o histórico de auditoria, do mais recente para o mais antigo (PDR §18)."""
    return audit_repo.list_all(client)
