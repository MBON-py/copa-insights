from dataclasses import dataclass

from supabase import Client
from supabase_auth.errors import AuthApiError

from core.config import settings


@dataclass
class AuthResult:
    success: bool
    message: str = ""
    user_id: str | None = None


def sign_up(client: Client, email: str, password: str, nome_completo: str, telefone: str) -> AuthResult:
    """Cadastra um novo usuário. O profile é criado automaticamente por trigger."""
    try:
        client.auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {
                    "data": {"nome_completo": nome_completo, "telefone": telefone},
                    "email_redirect_to": settings.app_url,
                },
            }
        )
    except AuthApiError:
        return AuthResult(False, "Não foi possível concluir o cadastro. Verifique os dados informados.")
    return AuthResult(True, "Cadastro realizado com sucesso! Verifique seu e-mail para confirmar a conta antes de entrar.")


def sign_in(client: Client, email: str, password: str) -> AuthResult:
    """Autentica o usuário com e-mail e senha."""
    try:
        response = client.auth.sign_in_with_password({"email": email, "password": password})
    except AuthApiError:
        return AuthResult(False, "E-mail ou senha inválidos.")
    if response.user is None:
        return AuthResult(False, "E-mail ou senha inválidos.")
    return AuthResult(True, user_id=response.user.id)


def sign_out(client: Client) -> None:
    """Encerra a sessão do usuário no Supabase Auth."""
    client.auth.sign_out()


def request_password_reset(client: Client, email: str) -> AuthResult:
    """Envia o e-mail de recuperação de senha."""
    try:
        client.auth.reset_password_for_email(email, {"redirect_to": settings.app_url})
    except AuthApiError:
        pass
    return AuthResult(True, "Se o e-mail informado estiver cadastrado, enviaremos um link de recuperação.")


def set_recovery_session(client: Client, access_token: str, refresh_token: str) -> AuthResult:
    """Restaura a sessão a partir dos tokens recebidos no link de recuperação.

    access_token/refresh_token vêm da query string da URL (entrada não
    confiável): tokens malformados fazem set_session levantar exceções
    que não são AuthApiError (ex.: IndexError ao decodificar o JWT).
    """
    try:
        client.auth.set_session(access_token, refresh_token)
    except Exception:
        return AuthResult(False, "Link de recuperação inválido ou expirado. Solicite um novo.")
    return AuthResult(True)


def update_password(client: Client, new_password: str) -> AuthResult:
    """Atualiza a senha do usuário autenticado."""
    try:
        client.auth.update_user({"password": new_password})
    except AuthApiError:
        return AuthResult(False, "Não foi possível atualizar a senha. Solicite um novo link de recuperação.")
    return AuthResult(True, "Senha atualizada com sucesso. Faça login com a nova senha.")
