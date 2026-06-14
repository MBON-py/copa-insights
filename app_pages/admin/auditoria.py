import json
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from core import session
from repositories.supabase_client import get_client
from services import audit_service

_FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")

st.title("Auditoria")
st.caption(
    "Trilha de importações, alterações de resultados e palpites, e "
    "reprocessamentos de ranking (PDR §18), do mais recente para o mais antigo."
)

profile = session.get_profile()
if profile is None:
    st.stop()

client = get_client()

entradas = audit_service.get_audit_log(client)

if not entradas:
    st.info("Nenhum registro de auditoria ainda.")
else:
    tabela = pd.DataFrame(
        [
            {
                "Data/hora": entrada.created_at.astimezone(_FUSO_HORARIO).strftime("%d/%m/%Y %H:%M"),
                "Usuário": entrada.nome_completo or "-",
                "Ação": entrada.acao,
                "Detalhe": json.dumps(entrada.detalhe, ensure_ascii=False) if entrada.detalhe else "-",
            }
            for entrada in entradas
        ]
    )
    st.dataframe(tabela, width="stretch", hide_index=True)
