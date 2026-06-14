import pandas as pd
import plotly.express as px
import streamlit as st

from core import session
from core.formatting import formatar_reais
from repositories.supabase_client import get_client
from services import ranking_service

_MEDALHAS = {1: "🥇", 2: "🥈", 3: "🥉"}

st.title("Dashboard geral")

profile = session.get_profile()
if profile is None:
    st.stop()

client = get_client()

ranking = ranking_service.get_ranking(client)
premiacao = ranking_service.get_premiacao(ranking)

with st.container(horizontal=True):
    st.metric("Participantes", premiacao.quantidade_participantes, border=True)
    st.metric("Valor arrecadado", formatar_reais(premiacao.valor_arrecadado), border=True)
    st.metric("Valor distribuído", formatar_reais(premiacao.valor_distribuido), border=True)

st.subheader("Top 3")
top3 = [entry for entry in ranking if entry.posicao <= 3]
if not top3:
    st.info("Ainda não há participantes no ranking.")
else:
    premios = {posicao: valor for posicao, _, valor in premiacao.vencedores}
    with st.container(horizontal=True):
        for entry in top3:
            with st.container(border=True):
                st.markdown(f"#### {_MEDALHAS.get(entry.posicao, '')} {entry.posicao}º lugar")
                st.markdown(f"**{entry.nome_completo}**")
                st.caption(f"{entry.pontos_total} pontos")
                st.markdown(formatar_reais(premios.get(entry.posicao, 0.0)))

st.subheader("Ranking geral")
if not ranking:
    st.info("Nenhum participante no ranking ainda.")
else:
    tabela = pd.DataFrame([{"Nome": entry.nome_completo, "Pontos": entry.pontos_total} for entry in ranking])
    figura = px.bar(tabela, x="Pontos", y="Nome", orientation="h")
    figura.update_yaxes(autorange="reversed", title=None)
    st.plotly_chart(figura)
