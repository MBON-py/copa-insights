from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from core import flags, session
from core.formatting import status_badge
from repositories.supabase_client import get_client
from services import matches_service

_FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")

st.title("Gestão de jogos")

profile = session.get_profile()
if profile is None:
    st.stop()

client = get_client()

st.subheader("Importação inicial via CSV")
st.caption(
    "Colunas esperadas: selecao_1, selecao_2, data (AAAA-MM-DD ou DD/MM/AAAA), "
    "horario (HH:MM), grupo (opcional) e etapa (Fase de Grupos, Segunda Fase, "
    "Oitavas de Final, Quartas de Final, Semifinal, Disputa de 3º Lugar ou Final). "
    "Reenviar o arquivo atualiza data/hora e grupo dos jogos já cadastrados "
    "(mesmo confronto e etapa) em vez de duplicá-los."
)

upload_key = f"upload_jogos_{st.session_state.get('_upload_jogos_versao', 0)}"
arquivo = st.file_uploader("Arquivo CSV", type=["csv"], key=upload_key)

if arquivo is not None:
    preview = matches_service.parse_csv(arquivo)

    if preview.errors:
        mensagens = "\n".join(f"- {erro}" for erro in preview.errors)
        st.error(f"Corrija os erros abaixo e envie o arquivo novamente:\n\n{mensagens}")
    elif not preview.rows:
        st.warning("Nenhuma linha encontrada no arquivo.")
    else:
        st.success(f"{len(preview.rows)} jogo(s) prontos para importar.")
        st.dataframe(preview.preview, width="stretch", hide_index=True)
        if st.button("Importar jogos", type="primary"):
            matches_service.import_matches(client, profile.id, preview.rows)
            st.session_state["_upload_jogos_versao"] = st.session_state.get("_upload_jogos_versao", 0) + 1
            st.success("Jogos importados/atualizados com sucesso.")
            st.rerun()

st.subheader("Jogos cadastrados")

matches = matches_service.get_matches(client)
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
