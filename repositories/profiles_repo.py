import secrets

from supabase import Client

from core.constants import Perfil
from models.profile import Profile


def get_by_id(client: Client, user_id: str) -> Profile | None:
    """Busca o profile do usuário pelo id (auth.uid())."""
    response = client.table("profiles").select("*").eq("id", user_id).execute()
    if not response.data:
        return None
    return Profile.model_validate(response.data[0])


def list_all(client: Client) -> list[Profile]:
    """Lista todos os profiles, ordenados por nome (uso administrativo)."""
    response = client.table("profiles").select("*").order("nome_completo").execute()
    return [Profile.model_validate(row) for row in response.data]


def update_telefone(client: Client, user_id: str, telefone: str) -> Profile:
    """Atualiza o telefone do profile e retorna o registro atualizado."""
    response = (
        client.table("profiles").update({"telefone": telefone}).eq("id", user_id).execute()
    )
    return Profile.model_validate(response.data[0])


def update_ativo(client: Client, user_id: str, ativo: bool) -> Profile:
    """Ativa ou desativa um participante (PDR §6). Requer perfil administrador (RLS)."""
    response = client.table("profiles").update({"ativo": ativo}).eq("id", user_id).execute()
    return Profile.model_validate(response.data[0])


def update_perfil(admin_client: Client, user_id: str, perfil: Perfil) -> Profile:
    """Promove ou rebaixa um usuário entre `administrador` e `participante` (PDR §6).

    Atualiza `app_metadata.perfil` no Supabase Auth — fonte da autorização
    usada pelas policies de RLS — e o campo `perfil` em `profiles`, usado
    pela navegação do app. Requer a `service_role key`.
    """
    admin_client.auth.admin.update_user_by_id(user_id, {"app_metadata": {"perfil": perfil.value}})
    response = admin_client.table("profiles").update({"perfil": perfil.value}).eq("id", user_id).execute()
    return Profile.model_validate(response.data[0])


def create_user(admin_client: Client, email: str, nome_completo: str, telefone: str) -> str:
    """Cria um usuário via Supabase Auth (importação histórica, PDR §16).

    O profile correspondente é criado automaticamente pelo trigger
    `handle_new_user`. Retorna uma senha temporária aleatória; o
    participante deve usar "recuperar senha" para definir a própria senha.
    """
    response = admin_client.auth.admin.create_user(
        {
            "email": email,
            "password": secrets.token_urlsafe(18),
            "email_confirm": True,
            "user_metadata": {"nome_completo": nome_completo, "telefone": telefone},
        }
    )
    assert response.user is not None
    return response.user.id
