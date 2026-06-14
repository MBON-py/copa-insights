import truststore

# Usa o repositório de certificados do sistema operacional para validar TLS,
# em vez do bundle do certifi. Necessário em redes corporativas com
# inspeção de TLS, que injetam um CA root que só o SO confia.
truststore.inject_into_ssl()

import streamlit as st

from core import session
from core.config import settings
from core.constants import Perfil
from repositories.supabase_client import clear_client, get_client
from services import auth_service

st.set_page_config(page_title=settings.app_name, page_icon=":material/sports_soccer:", layout="wide")

if not session.is_authenticated():
    pages = {
        "": [
            st.Page("app_pages/login.py", title="Entrar", icon=":material/login:"),
        ],
    }
else:
    profile = session.get_profile()

    pages = {
        "": [
            st.Page("app_pages/perfil.py", title="Meu perfil", icon=":material/person:"),
        ],
        "Bolão": [
            st.Page("app_pages/palpites.py", title="Meus palpites", icon=":material/sports_soccer:"),
            st.Page("app_pages/ranking.py", title="Classificação", icon=":material/leaderboard:"),
        ],
        "Dashboards": [
            st.Page("app_pages/dashboard_geral.py", title="Geral", icon=":material/dashboard:"),
            st.Page("app_pages/dashboard_participante.py", title="Meu desempenho", icon=":material/insights:"),
            st.Page("app_pages/dashboard_jogos.py", title="Jogos", icon=":material/bar_chart:"),
        ],
    }

    if profile.perfil == Perfil.ADMINISTRADOR:
        pages["Admin"] = [
            st.Page("app_pages/admin/jogos.py", title="Jogos", icon=":material/sports:"),
            st.Page("app_pages/admin/resultados.py", title="Resultados", icon=":material/edit_note:"),
            st.Page("app_pages/admin/usuarios.py", title="Usuários", icon=":material/group:"),
            st.Page("app_pages/admin/importacao_historica.py", title="Importação histórica", icon=":material/upload_file:"),
            st.Page("app_pages/admin/correcao_historica.py", title="Correção histórica", icon=":material/history:"),
            st.Page("app_pages/admin/auditoria.py", title="Auditoria", icon=":material/fact_check:"),
        ]

page = st.navigation(pages, position="top")

with st.sidebar:
    st.markdown(f"## :material/sports_soccer: {settings.app_name}")
    st.caption("Bolão da Copa do Mundo 2026")

if session.is_authenticated():
    profile = session.get_profile()
    with st.sidebar:
        st.markdown(f"**{profile.nome_completo}**")
        st.caption(f"{profile.email} · {profile.perfil.value.capitalize()}")
        if st.button("Sair", icon=":material/logout:", width="stretch"):
            auth_service.sign_out(get_client())
            session.clear()
            clear_client()
            st.rerun()

page.run()
