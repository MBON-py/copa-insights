"""Promove um usuário existente a administrador.

Uso (uma única vez, para criar o primeiro administrador do bolão):

    python scripts/bootstrap_admin.py usuario@example.com

Requer SUPABASE_SERVICE_ROLE_KEY configurada no .env.
"""

import sys

import truststore

truststore.inject_into_ssl()

from repositories.supabase_client import get_admin_client


def promover_admin(email: str) -> None:
    client = get_admin_client()

    response = client.table("profiles").select("id, perfil").eq("email", email).execute()
    if not response.data:
        raise SystemExit(f"Usuário não encontrado: {email}")

    user_id = response.data[0]["id"]

    client.auth.admin.update_user_by_id(user_id, {"app_metadata": {"perfil": "administrador"}})
    client.table("profiles").update({"perfil": "administrador"}).eq("id", user_id).execute()
    print(f"Usuário {email} promovido a administrador.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python scripts/bootstrap_admin.py <email>")
    promover_admin(sys.argv[1])
