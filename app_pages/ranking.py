import pandas as pd
import streamlit as st

from core import session
from core.formatting import formatar_reais
from repositories.supabase_client import get_client
from services import ranking_service

_MEDALHAS = {1: "🥇", 2: "🥈", 3: "🥉"}

st.title("Classificação")

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

st.subheader("Premiação atual")
if not premiacao.vencedores:
    st.info("Ainda não há participantes no ranking.")
else:
    for posicao, nome, valor in premiacao.vencedores:
        st.markdown(f"**{posicao}º lugar** — {nome} — {formatar_reais(valor)}")

st.subheader("Classificação geral")
if not ranking:
    st.info("Nenhum participante no ranking ainda.")
else:
    tabela = pd.DataFrame(
        [
            {
                "Posição": f"{_MEDALHAS.get(entry.posicao, '')} {entry.posicao}º".strip(),
                "Nome": entry.nome_completo,
                "Pontos": entry.pontos_total,
                "Placares exatos": entry.placares_exatos,
                "Acertos de vencedor": entry.acertos_vencedor,
            }
            for entry in ranking
        ]
    )

    def _destacar_minha_linha(row: pd.Series) -> list[str]:
        if ranking[row.name].user_id == profile.id:
            return ["background-color: #E3F6EC"] * len(row)
        return [""] * len(row)

    st.dataframe(tabela.style.apply(_destacar_minha_linha, axis=1), width="stretch", hide_index=True)
