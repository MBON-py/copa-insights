from enum import StrEnum


class Perfil(StrEnum):
    ADMINISTRADOR = "administrador"
    PARTICIPANTE = "participante"


class Etapa(StrEnum):
    FASE_DE_GRUPOS = "Fase de Grupos"
    OITAVAS_DE_FINAL = "Oitavas de Final"
    QUARTAS_DE_FINAL = "Quartas de Final"
    SEMIFINAL = "Semifinal"
    DISPUTA_DE_3_LUGAR = "Disputa de 3º Lugar"
    FINAL = "Final"


class StatusJogo(StrEnum):
    AGENDADO = "Agendado"
    EM_ANDAMENTO = "Em andamento"
    FINALIZADO = "Finalizado"
