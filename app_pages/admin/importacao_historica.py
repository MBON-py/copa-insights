import streamlit as st

from core import session
from repositories.supabase_client import get_client
from services import import_service

st.title("Importação histórica")
st.caption("Disponível apenas para administradores (PDR §16). Valida duplicidades, exibe erros e relatório de importação, e permite reprocessar o arquivo após corrigi-lo.")

profile = session.get_profile()
if profile is None:
    st.stop()

client = get_client()


def _exibir_erros(preview: import_service.ImportPreview) -> None:
    mensagens = "\n".join(f"- {erro}" for erro in preview.errors)
    st.error(f"Corrija os erros abaixo e envie o arquivo novamente:\n\n{mensagens}")


def _exibir_resultado(resultado: import_service.ImportResult, rotulo: str) -> None:
    if resultado.erros:
        mensagens = "\n".join(f"- {erro}" for erro in resultado.erros)
        st.warning(f"{resultado.sucesso} {rotulo} importado(s). {len(resultado.erros)} erro(s):\n\n{mensagens}")
    else:
        st.success(f"{resultado.sucesso} {rotulo} importado(s) com sucesso.")


# --------------------------------------------------------------------- #
# Participantes
# --------------------------------------------------------------------- #

st.subheader("Participantes")
st.caption(
    "Colunas esperadas: nome, email, telefone. Cada participante é criado com "
    "uma senha temporária; ele deve usar 'Esqueci minha senha' na tela de "
    "login para definir a própria senha."
)

versao_participantes = st.session_state.get("_upload_participantes_versao", 0)
arquivo_participantes = st.file_uploader(
    "Arquivo CSV de participantes", type=["csv"], key=f"upload_participantes_{versao_participantes}"
)

if arquivo_participantes is not None:
    preview = import_service.parse_participantes_csv(client, arquivo_participantes)
    if preview.errors:
        _exibir_erros(preview)
    elif not preview.rows:
        st.warning("Nenhuma linha encontrada no arquivo.")
    else:
        st.success(f"{len(preview.rows)} participante(s) prontos para importar.")
        st.dataframe(preview.preview, width="stretch", hide_index=True)
        if st.button("Importar participantes", type="primary"):
            try:
                resultado = import_service.import_participantes_historicos(client, profile.id, preview.rows)
            except RuntimeError:
                st.error("Importação de participantes requer a SUPABASE_SERVICE_ROLE_KEY configurada no .env.")
            else:
                st.session_state["_upload_participantes_versao"] = versao_participantes + 1
                _exibir_resultado(resultado, "participante(s)")
                st.rerun()

# --------------------------------------------------------------------- #
# Palpites históricos
# --------------------------------------------------------------------- #

st.subheader("Palpites históricos")
st.caption(
    "Colunas esperadas: email (participante já cadastrado), selecao_1 e "
    "selecao_2 (jogo, conforme cadastrado em Admin > Jogos), "
    "gols_selecao_1, gols_selecao_2 e data_aposta (opcional; AAAA-MM-DD "
    "HH:MM, DD/MM/AAAA HH:MM, AAAA-MM-DD ou DD/MM/AAAA). O ranking é "
    "recalculado automaticamente após a importação."
)

versao_palpites = st.session_state.get("_upload_palpites_versao", 0)
arquivo_palpites = st.file_uploader(
    "Arquivo CSV de palpites históricos", type=["csv"], key=f"upload_palpites_{versao_palpites}"
)

if arquivo_palpites is not None:
    preview = import_service.parse_palpites_csv(client, arquivo_palpites)
    if preview.errors:
        _exibir_erros(preview)
    elif not preview.rows:
        st.warning("Nenhuma linha encontrada no arquivo.")
    else:
        st.success(f"{len(preview.rows)} palpite(s) prontos para importar.")
        st.dataframe(preview.preview, width="stretch", hide_index=True)
        if st.button("Importar palpites", type="primary"):
            resultado = import_service.import_palpites_historicos(client, profile.id, preview.rows)
            st.session_state["_upload_palpites_versao"] = versao_palpites + 1
            _exibir_resultado(resultado, "palpite(s)")
            st.rerun()

# --------------------------------------------------------------------- #
# Resultados históricos
# --------------------------------------------------------------------- #

st.subheader("Resultados históricos")
st.caption(
    "Colunas esperadas: selecao_1 e selecao_2 (jogo, conforme cadastrado em "
    "Admin > Jogos), gols_selecao_1, gols_selecao_2. Cada jogo é marcado "
    "como Finalizado e o ranking é recalculado automaticamente."
)

versao_resultados = st.session_state.get("_upload_resultados_versao", 0)
arquivo_resultados = st.file_uploader(
    "Arquivo CSV de resultados históricos", type=["csv"], key=f"upload_resultados_{versao_resultados}"
)

if arquivo_resultados is not None:
    preview = import_service.parse_resultados_csv(client, arquivo_resultados)
    if preview.errors:
        _exibir_erros(preview)
    elif not preview.rows:
        st.warning("Nenhuma linha encontrada no arquivo.")
    else:
        st.success(f"{len(preview.rows)} resultado(s) prontos para importar.")
        st.dataframe(preview.preview, width="stretch", hide_index=True)
        if st.button("Importar resultados", type="primary"):
            resultado = import_service.import_resultados_historicos(client, profile.id, preview.rows)
            st.session_state["_upload_resultados_versao"] = versao_resultados + 1
            _exibir_resultado(resultado, "resultado(s)")
            st.rerun()
