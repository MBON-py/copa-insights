from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import streamlit as st

from core import session
from repositories.supabase_client import get_client
from services import predictions_service, ranking_service

_FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")

st.title("Meu desempenho")

profile = session.get_profile()
if profile is None:
    st.stop()

client = get_client()

ranking = ranking_service.get_ranking(client)
entrada = next((entry for entry in ranking if entry.user_id == profile.id), None)

if entrada is None:
    st.info("Esta página está disponível apenas para participantes.")
    st.stop()

with st.container(horizontal=True):
    st.metric("Pontos totais", entrada.pontos_total, border=True)
    st.metric("Posição", f"{entrada.posicao}º", border=True)
    st.metric("Placares exatos", entrada.placares_exatos, border=True)
    st.metric("Acertos de vencedor", entrada.acertos_vencedor, border=True)

st.subheader("Evolução da pontuação")
evolucao = predictions_service.get_evolucao_pontuacao(client, profile.id)
if not evolucao:
    st.info("Nenhum jogo encerrado com palpite registrado ainda.")
else:
    tabela = pd.DataFrame(
        [
            {
                "Jogo": indice + 1,
                "Confronto": item.confronto,
                "Data/hora": item.data_hora.astimezone(_FUSO_HORARIO).strftime("%d/%m/%Y %H:%M"),
                "Pontos": item.pontos,
                "Pontos acumulados": item.pontos_acumulados,
            }
            for indice, item in enumerate(evolucao)
        ]
    )
    figura = px.line(
        tabela,
        x="Jogo",
        y="Pontos acumulados",
        markers=True,
        hover_data=["Confronto", "Data/hora", "Pontos"],
    )
    st.plotly_chart(figura)
