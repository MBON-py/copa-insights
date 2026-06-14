import streamlit as st

from core import session
from repositories.supabase_client import get_client
from services import auth_service, profile_service

st.title("Entrar")

if session.is_authenticated():
    profile = session.get_profile()
    st.success(f"Você já está logado como **{profile.nickname}**.")
    st.stop()

client = get_client()

# Links de confirmação de cadastro e recuperação de senha trazem os
# tokens no fragmento (#) da URL. st.query_params só lê a query string,
# então este script move o fragmento para lá antes de continuar.
st.iframe(
    """
    <script>
    const hash = window.parent.location.hash;
    if (hash && hash.includes('access_token')) {
        const hashParams = new URLSearchParams(hash.substring(1));
        const search = new URLSearchParams(window.parent.location.search);
        hashParams.forEach((value, key) => search.set(key, value));
        window.parent.location.replace(
            window.parent.location.pathname + '?' + search.toString()
        );
    }
    </script>
    """,
    height=1,
)

params = st.query_params
access_token = params.get("access_token")
refresh_token = params.get("refresh_token", "")
link_type = params.get("type")

if access_token:
    result = auth_service.set_recovery_session(client, access_token, refresh_token)
    if not result.success:
        st.error(result.message)
        st.query_params.clear()
    elif link_type == "recovery":
        st.subheader("Defina sua nova senha")
        with st.form("nova_senha_form"):
            nova_senha = st.text_input("Nova senha", type="password")
            confirmar_senha = st.text_input("Confirmar nova senha", type="password")
            salvar = st.form_submit_button("Salvar nova senha", type="primary")
        if salvar:
            if len(nova_senha) < 6:
                st.error("A senha deve ter pelo menos 6 caracteres.")
            elif nova_senha != confirmar_senha:
                st.error("As senhas não coincidem.")
            else:
                update_result = auth_service.update_password(client, nova_senha)
                if update_result.success:
                    auth_service.sign_out(client)
                    st.query_params.clear()
                    st.success(update_result.message)
                    if st.button("Ir para o login"):
                        st.rerun()
                else:
                    st.error(update_result.message)
        st.stop()
    else:
        user_response = client.auth.get_user()
        profile = (
            profile_service.get_profile(client, user_response.user.id)
            if user_response and user_response.user
            else None
        )
        if profile is not None:
            session.set_profile(profile)
            st.query_params.clear()
            st.rerun()
        st.error("Não foi possível concluir a confirmação automaticamente. Faça login abaixo.")
        st.query_params.clear()

tab_entrar, tab_cadastrar, tab_recuperar = st.tabs(["Entrar", "Cadastrar", "Esqueci minha senha"])

with tab_entrar:
    with st.form("login_form"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar", type="primary")
    if entrar:
        if not email or not senha:
            st.error("Informe e-mail e senha.")
        else:
            result = auth_service.sign_in(client, email, senha)
            if not result.success:
                st.error(result.message)
            else:
                profile = profile_service.get_profile(client, result.user_id)
                if profile is None:
                    st.error("Não encontramos seu perfil. Tente novamente em alguns instantes.")
                else:
                    session.set_profile(profile)
                    st.rerun()

with tab_cadastrar:
    with st.form("cadastro_form"):
        nome_completo = st.text_input("Nome completo")
        apelido = st.text_input("Apelido", help="Como seu nome vai aparecer no ranking e nos dashboards.")
        telefone = st.text_input("Telefone")
        email_cadastro = st.text_input("E-mail", key="cadastro_email")
        senha_cadastro = st.text_input("Senha", type="password", key="cadastro_senha")
        confirmar_senha_cadastro = st.text_input(
            "Confirmar senha", type="password", key="cadastro_confirmar_senha"
        )
        cadastrar = st.form_submit_button("Cadastrar", type="primary")
    if cadastrar:
        if not all([nome_completo, apelido, telefone, email_cadastro, senha_cadastro]):
            st.error("Preencha todos os campos.")
        elif "@" not in email_cadastro:
            st.error("Informe um e-mail válido.")
        elif len(senha_cadastro) < 6:
            st.error("A senha deve ter pelo menos 6 caracteres.")
        elif senha_cadastro != confirmar_senha_cadastro:
            st.error("As senhas não coincidem.")
        else:
            result = auth_service.sign_up(client, email_cadastro, senha_cadastro, nome_completo, apelido, telefone)
            if result.success:
                st.success(result.message)
            else:
                st.error(result.message)

with tab_recuperar:
    with st.form("recuperar_form"):
        email_recuperar = st.text_input("E-mail cadastrado", key="recuperar_email")
        enviar = st.form_submit_button("Enviar link de recuperação", type="primary")
    if enviar:
        if not email_recuperar:
            st.error("Informe seu e-mail.")
        else:
            result = auth_service.request_password_reset(client, email_recuperar)
            st.success(result.message)
