"""Back In Time: equivalencia entre schedule.mode y minutos o texto legible."""
from __future__ import annotations

from .comun import texto_frecuencia

MODOS = {2: 5, 4: 10, 7: 30, 10: 60, 12: 120, 14: 240, 16: 360, 18: 720, 19: 1440, 20: 1440,
         30: 10080, 40: 43200}
ESPECIALES = {1: 'Al iniciar el equipo', 27: 'Al conectar la unidad', 80: 'Anual'}
UNIDADES = {10: 60, 20: 1440, 30: 10080, 40: 43200}
REPETIDO = 25


def _entero(cfg: dict[str, str], clave: str, defecto: int) -> int:
    try:
        return int(cfg.get(clave) or defecto)
    except ValueError:
        return defecto


def modo_actual(cfg: dict[str, str], p: str) -> int:
    return _entero(cfg, f'{p}.schedule.mode', 0)


def frecuencia(cfg: dict[str, str], p: str) -> tuple[int | None, str]:
    """(minutos, texto) del perfil p ('profileN'); minutos None si no es un intervalo."""
    modo = modo_actual(cfg, p)
    if modo == REPETIDO:
        periodo = _entero(cfg, f'{p}.schedule.repeatedly.period', 1)
        unidad = _entero(cfg, f'{p}.schedule.repeatedly.unit', 20)
        minutos = periodo * UNIDADES.get(unidad, 1440)
        return minutos, texto_frecuencia(minutos)
    if modo in ESPECIALES:
        return None, ESPECIALES[modo]
    minutos = MODOS.get(modo)
    return minutos, texto_frecuencia(minutos)
