from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from core import flags, session
from repositories.supabase_client import get_client
from services import predictions_service

_FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")

st.title("Meus palpites")

profile = session.get_profile()
if profile is None:
    st.stop()

client = get_client()

abertos, encerrados = predictions_service.get_matches_with_predictions(client, profile.id)

st.subheader("Palpites em aberto")
if not abertos:
    st.info("Não há jogos disponíveis para palpite no momento.")
else:
    with st.form("palpites_form"):
        valores: dict[int, tuple[int, int]] = {}
        for item in abertos:
            match = item.match
            palpite = item.palpite
            detalhes = f"{match.data_hora.astimezone(_FUSO_HORARIO).strftime('%d/%m/%Y %H:%M')} · {match.etapa.value}"
            if match.grupo:
                detalhes += f" · Grupo {match.grupo}"

            with st.container(border=True):
                st.markdown(f"**{flags.confronto(match.selecao_1, match.selecao_2)}**")
                st.caption(detalhes)
                col1, col2 = st.columns(2)
                with col1:
                    gols_1 = st.number_input(
                        match.selecao_1,
                        min_value=0,
                        step=1,
                        value=palpite.gols_selecao_1 if palpite else 0,
                        key=f"gols_1_{match.id}",
                    )
                with col2:
                    gols_2 = st.number_input(
                        match.selecao_2,
                        min_value=0,
                        step=1,
                        value=palpite.gols_selecao_2 if palpite else 0,
                        key=f"gols_2_{match.id}",
                    )
            valores[match.id] = (gols_1, gols_2)

        salvar = st.form_submit_button("Salvar palpites", type="primary")

    if salvar:
        predictions_service.save_palpites(client, profile.id, valores)
        st.success("Palpites salvos com sucesso.")
        st.rerun()

st.subheader("Palpites encerrados")
if not encerrados:
    st.info("Nenhum jogo encerrado ainda.")
else:
    tabela = pd.DataFrame(
        [
            {
                "Confronto": flags.confronto(item.match.selecao_1, item.match.selecao_2),
                "Data/hora": item.match.data_hora.astimezone(_FUSO_HORARIO).strftime("%d/%m/%Y %H:%M"),
                "Meu palpite": (
                    f"{item.palpite.gols_selecao_1} x {item.palpite.gols_selecao_2}"
                    if item.palpite
                    else "Sem palpite"
                ),
                "Placar oficial": (
                    f"{item.match.gols_selecao_1} x {item.match.gols_selecao_2}"
                    if item.match.gols_selecao_1 is not None and item.match.gols_selecao_2 is not None
                    else "-"
                ),
                "Pontos": str(item.palpite.pontos) if item.palpite and item.palpite.pontos is not None else "-",
            }
            for item in encerrados
        ]
    )
    st.dataframe(tabela, width="stretch", hide_index=True)
