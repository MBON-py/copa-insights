from typing import Any

from supabase import Client

from models.audit import AuditLogEntry


def log(client: Client, user_id: str, acao: str, detalhe: dict[str, Any]) -> None:
    """Registra uma ação administrativa em audit_log."""
    client.table("audit_log").insert(
        {"user_id": user_id, "acao": acao, "detalhe": detalhe}
    ).execute()


def list_all(client: Client) -> list[AuditLogEntry]:
    """Lista o histórico de auditoria, do mais recente para o mais antigo (PDR §18)."""
    response = (
        client.table("audit_log")
        .select("id, user_id, acao, detalhe, created_at, profiles(nome_completo)")
        .order("created_at", desc=True)
        .execute()
    )
    return [
        AuditLogEntry.model_validate({**row, "nome_completo": (row.get("profiles") or {}).get("nome_completo")})
        for row in response.data
    ]
