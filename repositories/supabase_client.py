from functools import lru_cache

import streamlit as st
from supabase import Client, ClientOptions, create_client

from core.config import settings

_SESSION_KEY = "_supabase_client"


def get_client() -> Client:
    """Cliente Supabase isolado por sessão do Streamlit (RLS aplicado).

    Cada sessão de navegador tem seu próprio `Client`, pois o estado de
    autenticação (`auth`) é mutável e não pode ser compartilhado entre
    usuários. O fluxo "implicit" é usado para que o link de recuperação
    de senha retorne os tokens diretamente na URL, sem depender de um
    code_verifier persistido entre páginas.
    """
    if _SESSION_KEY not in st.session_state:
        st.session_state[_SESSION_KEY] = create_client(
            settings.supabase_url,
            settings.supabase_key,
            options=ClientOptions(flow_type="implicit"),
        )
    return st.session_state[_SESSION_KEY]


def clear_client() -> None:
    """Remove o cliente da sessão atual (usado no logout)."""
    st.session_state.pop(_SESSION_KEY, None)


@lru_cache
def get_admin_client() -> Client:
    """Cliente Supabase com service_role key, somente para fluxos administrativos."""
    if not settings.supabase_service_role_key:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY não configurada")
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
