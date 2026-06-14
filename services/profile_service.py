from supabase import Client

from core.constants import Perfil
from models.profile import Profile
from repositories import profiles_repo
from repositories.supabase_client import get_admin_client
from services import audit_service


def get_profile(client: Client, user_id: str) -> Profile | None:
    return profiles_repo.get_by_id(client, user_id)


def list_all(client: Client) -> list[Profile]:
    return profiles_repo.list_all(client)


def update_telefone(client: Client, user_id: str, telefone: str) -> Profile:
    return profiles_repo.update_telefone(client, user_id, telefone)


def set_ativo(client: Client, admin_user_id: str, target_user_id: str, ativo: bool) -> Profile:
    """Ativa ou desativa um participante e registra a ação na auditoria (PDR §6/§18)."""
    profile = profiles_repo.update_ativo(client, target_user_id, ativo)
    acao = "ativacao_usuario" if ativo else "desativacao_usuario"
    audit_service.log_action(client, admin_user_id, acao, {"user_id": target_user_id})
    return profile


def set_perfil(client: Client, admin_user_id: str, target_user_id: str, perfil: Perfil) -> Profile:
    """Promove ou rebaixa um usuário entre `administrador` e `participante` (PDR §6/§18).

    Requer a `service_role key` (`SUPABASE_SERVICE_ROLE_KEY`); levanta
    `RuntimeError` se ela não estiver configurada.
    """
    admin_client = get_admin_client()
    profile = profiles_repo.update_perfil(admin_client, target_user_id, perfil)
    audit_service.log_action(client, admin_user_id, "alteracao_perfil", {"user_id": target_user_id, "perfil": perfil.value})
    return profile
