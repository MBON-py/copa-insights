import streamlit as st

from core import session
from repositories.supabase_client import get_client
from services import profile_service

st.title("Meu perfil")

profile = session.get_profile()
if profile is None:
    st.warning("Você precisa entrar para ver esta página.")
    st.stop()

client = get_client()

st.text_input("Nome completo", value=profile.nome_completo, disabled=True)
st.text_input("Apelido", value=profile.nickname, disabled=True)
st.text_input("E-mail", value=profile.email, disabled=True)
st.text_input("Perfil", value=profile.perfil.value.capitalize(), disabled=True)

with st.form("telefone_form"):
    telefone = st.text_input("Telefone", value=profile.telefone)
    salvar = st.form_submit_button("Salvar telefone", type="primary")

if salvar:
    if not telefone.strip():
        st.error("Informe um telefone válido.")
    else:
        updated_profile = profile_service.update_telefone(client, profile.id, telefone.strip())
        session.set_profile(updated_profile)
        st.success("Telefone atualizado com sucesso.")
