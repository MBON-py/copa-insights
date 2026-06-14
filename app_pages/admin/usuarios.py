import pandas as pd
import streamlit as st

from core import session
from core.constants import Perfil
from repositories.supabase_client import get_client
from services import profile_service

st.title("Usuários")
st.caption("Gerencie participantes e administradores do bolão (PDR §6).")

profile = session.get_profile()
if profile is None:
    st.stop()

client = get_client()

usuarios = profile_service.list_all(client)

st.subheader("Usuários cadastrados")
if not usuarios:
    st.info("Nenhum usuário cadastrado ainda.")
else:
    tabela = pd.DataFrame(
        [
            {
                "Nome": u.nome_completo,
                "E-mail": u.email,
                "Telefone": u.telefone,
                "Perfil": u.perfil.value.capitalize(),
                "Status": "🟢 Ativo" if u.ativo else "⚪ Inativo",
            }
            for u in usuarios
        ]
    )
    st.dataframe(tabela, width="stretch", hide_index=True)

st.subheader("Gerenciar usuário")
if not usuarios:
    st.info("Cadastre usuários antes de gerenciar perfis e status.")
else:
    opcoes = {u.id: f"{u.nome_completo} ({u.email})" for u in usuarios}
    user_id = st.selectbox("Usuário", options=list(opcoes.keys()), format_func=lambda i: opcoes[i])
    usuario = next(u for u in usuarios if u.id == user_id)

    st.caption(
        f"Perfil atual: **{usuario.perfil.value.capitalize()}** · "
        f"Status: **{'Ativo' if usuario.ativo else 'Inativo'}**"
    )

    eh_voce_mesmo = usuario.id == profile.id
    if eh_voce_mesmo:
        st.caption("Você não pode alterar seu próprio status ou perfil.")

    if usuario.perfil == Perfil.PARTICIPANTE:
        rotulo_perfil, novo_perfil = "Promover a administrador", Perfil.ADMINISTRADOR
    else:
        rotulo_perfil, novo_perfil = "Rebaixar a participante", Perfil.PARTICIPANTE

    with st.container(horizontal=True):
        rotulo_ativo = "Desativar" if usuario.ativo else "Ativar"
        if st.button(rotulo_ativo, disabled=eh_voce_mesmo):
            atualizado = profile_service.set_ativo(client, profile.id, usuario.id, not usuario.ativo)
            st.success(f"Usuário {'ativado' if atualizado.ativo else 'desativado'} com sucesso.")
            st.rerun()

        if st.button(rotulo_perfil, disabled=eh_voce_mesmo):
            try:
                atualizado = profile_service.set_perfil(client, profile.id, usuario.id, novo_perfil)
            except RuntimeError:
                st.error(
                    "Alteração de perfil requer a SUPABASE_SERVICE_ROLE_KEY configurada no .env."
                )
            else:
                st.success(f"Perfil de {atualizado.nome_completo} atualizado para {atualizado.perfil.value}.")
                st.rerun()

    st.caption(
        "Alterações de perfil (promover/rebaixar administrador) só têm efeito "
        "nas permissões do usuário após ele entrar novamente — a sessão atual "
        "dele continua com o perfil anterior até o token de acesso ser renovado."
    )
