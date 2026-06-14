from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from core import flags, session
from core.formatting import status_badge
from repositories.supabase_client import get_client
from services import matches_service, predictions_service, profile_service, ranking_service

_FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")

st.title("Correção histórica")

profile = session.get_profile()
if profile is None:
    st.stop()

client = get_client()

st.subheader("Corrigir palpite de participante")
st.caption(
    "O administrador pode inserir ou corrigir o palpite de um participante "
    "para qualquer jogo, mesmo após o início da partida (PDR §12). Se o "
    "jogo já estiver finalizado, a pontuação do palpite é recalculada na hora."
)

participantes = profile_service.list_all(client)
matches = matches_service.get_matches(client)

if not participantes or not matches:
    st.info("Cadastre participantes e jogos antes de usar a correção histórica.")
else:
    opcoes_participantes = {p.id: f"{p.nome_completo} ({p.email})" for p in participantes}
    user_id = st.selectbox(
        "Participante", options=list(opcoes_participantes.keys()), format_func=lambda i: opcoes_participantes[i]
    )

    opcoes_jogos = {
        m.id: (
            f"{flags.confronto(m.selecao_1, m.selecao_2)} · "
            f"{m.data_hora.astimezone(_FUSO_HORARIO).strftime('%d/%m/%Y %H:%M')} · {status_badge(m.status)}"
        )
        for m in matches
    }
    match_id = st.selectbox("Jogo", options=list(opcoes_jogos.keys()), format_func=lambda i: opcoes_jogos[i])
    match = next(m for m in matches if m.id == match_id)

    palpite_existente = predictions_service.get_palpite(client, user_id, match_id)
    if palpite_existente is not None:
        data_padrao = palpite_existente.data_aposta.astimezone(_FUSO_HORARIO)
        gols_1_padrao = palpite_existente.gols_selecao_1
        gols_2_padrao = palpite_existente.gols_selecao_2
    else:
        data_padrao = datetime.now(_FUSO_HORARIO)
        gols_1_padrao = 0
        gols_2_padrao = 0

    with st.form("correcao_palpite_form"):
        col1, col2 = st.columns(2)
        with col1:
            gols_1 = st.number_input(
                match.selecao_1, min_value=0, step=1, value=gols_1_padrao, key=f"correcao_gols_1_{user_id}_{match_id}"
            )
        with col2:
            gols_2 = st.number_input(
                match.selecao_2, min_value=0, step=1, value=gols_2_padrao, key=f"correcao_gols_2_{user_id}_{match_id}"
            )

        col3, col4 = st.columns(2)
        with col3:
            data_palpite = st.date_input(
                "Data do palpite", value=data_padrao.date(), key=f"correcao_data_{user_id}_{match_id}"
            )
        with col4:
            hora_palpite = st.time_input(
                "Hora do palpite", value=data_padrao.time(), key=f"correcao_hora_{user_id}_{match_id}"
            )

        salvar = st.form_submit_button("Salvar palpite", type="primary")

    if salvar:
        data_aposta = datetime.combine(data_palpite, hora_palpite, tzinfo=_FUSO_HORARIO)
        palpite = predictions_service.set_palpite_admin(client, profile.id, user_id, match_id, gols_1, gols_2, data_aposta)
        if palpite.pontos is not None:
            st.success(f"Palpite salvo. Pontuação recalculada: {palpite.pontos} ponto(s).")
        else:
            st.success("Palpite salvo.")
        st.rerun()

st.subheader("Recalcular ranking")
st.caption(
    "Reaplica a pontuação de todos os palpites com base nos resultados "
    "oficiais cadastrados. Use após corrigir resultados ou importar dados "
    "históricos (PDR §14)."
)
if st.button("Recalcular ranking"):
    ranking_service.recalculate_ranking(client, profile.id)
    st.success("Ranking recalculado com sucesso.")
