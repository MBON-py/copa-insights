from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import streamlit as st

from core import flags, session
from repositories.supabase_client import get_client
from services import dashboard_service, matches_service

_FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")

st.title("Dashboard de jogos")

profile = session.get_profile()
if profile is None:
    st.stop()

client = get_client()

st.subheader("Acertos por jogo")
acertos = dashboard_service.get_match_accuracy(client)
if not acertos:
    st.info("Nenhum jogo finalizado ainda.")
else:
    tabela = pd.DataFrame(
        [
            {
                "Confronto": flags.confronto(item.match.selecao_1, item.match.selecao_2),
                "Taxa de acerto": item.taxa_acerto,
                "Acertos": item.match.acertos_totais,
                "Placares exatos": item.match.placares_exatos,
                "Total de palpites": item.match.total_palpites,
            }
            for item in acertos
        ]
    ).sort_values("Taxa de acerto", ascending=False)
    figura = px.bar(
        tabela,
        x="Taxa de acerto",
        y="Confronto",
        orientation="h",
        hover_data=["Acertos", "Placares exatos", "Total de palpites"],
    )
    figura.update_xaxes(tickformat=".0%")
    figura.update_yaxes(autorange="reversed", title=None)
    st.plotly_chart(figura)

st.subheader("Distribuição de palpites por partida")
matches = matches_service.get_matches(client)
if not matches:
    st.info("Nenhum jogo cadastrado ainda.")
else:
    matches_por_id = {match.id: match for match in matches}
    match_id = st.selectbox(
        "Jogo",
        options=list(matches_por_id.keys()),
        format_func=lambda mid: (
            f"{flags.confronto(matches_por_id[mid].selecao_1, matches_por_id[mid].selecao_2)} · "
            f"{matches_por_id[mid].data_hora.astimezone(_FUSO_HORARIO).strftime('%d/%m/%Y %H:%M')}"
        ),
    )

    distribuicao = dashboard_service.get_prediction_distribution(client, match_id)
    if not distribuicao:
        st.info("Nenhum palpite registrado para este jogo.")
    else:
        tabela = pd.DataFrame(
            [
                {
                    "Placar": f"{item.gols_selecao_1} x {item.gols_selecao_2}",
                    "Quantidade": item.quantidade,
                }
                for item in distribuicao
            ]
        ).sort_values("Quantidade", ascending=False)
        figura = px.bar(tabela, x="Placar", y="Quantidade")
        st.plotly_chart(figura)
