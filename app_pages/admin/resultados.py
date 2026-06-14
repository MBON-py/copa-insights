from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from core import flags, session
from core.formatting import status_badge
from repositories.supabase_client import get_client
from services import matches_service

_FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")

st.title("Resultados oficiais")

profile = session.get_profile()
if profile is None:
    st.stop()

client = get_client()

matches = matches_service.get_matches(client)

st.subheader("Lançar resultado")
if not matches:
    st.info("Nenhum jogo cadastrado ainda.")
else:
    opcoes = {
        m.id: (
            f"{flags.confronto(m.selecao_1, m.selecao_2)} · "
            f"{m.data_hora.astimezone(_FUSO_HORARIO).strftime('%d/%m/%Y %H:%M')} · {status_badge(m.status)}"
        )
        for m in matches
    }
    match_id = st.selectbox("Jogo", options=list(opcoes.keys()), format_func=lambda i: opcoes[i])
    match = next(m for m in matches if m.id == match_id)

    with st.form("resultado_form"):
        col1, col2 = st.columns(2)
        with col1:
            gols_1 = st.number_input(
                match.selecao_1,
                min_value=0,
                step=1,
                value=match.gols_selecao_1 or 0,
                key=f"resultado_gols_1_{match.id}",
            )
        with col2:
            gols_2 = st.number_input(
                match.selecao_2,
                min_value=0,
                step=1,
                value=match.gols_selecao_2 or 0,
                key=f"resultado_gols_2_{match.id}",
            )
        salvar = st.form_submit_button("Salvar resultado oficial", type="primary")

    if salvar:
        matches_service.set_result(client, profile.id, match.id, gols_1, gols_2)
        st.success("Resultado salvo. O jogo foi marcado como Finalizado e a pontuação dos palpites foi recalculada.")
        st.rerun()

st.subheader("Jogos cadastrados")

if not matches:
    st.info("Nenhum jogo cadastrado ainda.")
else:
    tabela = pd.DataFrame(
        [
            {
                "Confronto": flags.confronto(m.selecao_1, m.selecao_2),
                "Data/hora": m.data_hora.astimezone(_FUSO_HORARIO).strftime("%d/%m/%Y %H:%M"),
                "Grupo": m.grupo or "-",
                "Etapa": m.etapa.value,
                "Status": status_badge(m.status),
                "Placar": (
                    f"{m.gols_selecao_1} x {m.gols_selecao_2}"
                    if m.gols_selecao_1 is not None and m.gols_selecao_2 is not None
                    else "-"
                ),
            }
            for m in matches
        ]
    )
    st.dataframe(tabela, width="stretch", hide_index=True)
