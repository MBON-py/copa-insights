from core.constants import StatusJogo

_STATUS_EMOJI = {
    StatusJogo.AGENDADO: "⚪",
    StatusJogo.EM_ANDAMENTO: "🟡",
    StatusJogo.FINALIZADO: "🟢",
}


def formatar_reais(valor: float) -> str:
    texto = f"{valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {texto}"


def status_badge(status: StatusJogo) -> str:
    """Retorna o status do jogo com um indicador visual (PDR §19)."""
    return f"{_STATUS_EMOJI[status]} {status.value}"
