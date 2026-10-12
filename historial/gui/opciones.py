"""Etiquetas de las listas de frecuencia y de retención (iguales a las de Windows)."""
from .textos import t

PRED_FRECUENCIA = 60
PRED_CONSERVAR = 0


def _meses(n: int) -> str:
    return t('un_mes') if n == 1 else t('meses', n=n)


def texto_frecuencia(minutos: int) -> str:
    if minutos == 1440:
        texto = t('diariamente')
    elif minutos == 60:
        texto = t('cada_hora')
    elif minutos > 60:
        texto = t('cada_horas', n=minutos // 60)
    else:
        texto = t('cada_min', n=minutos)
    return texto + (t('predeterminado') if minutos == PRED_FRECUENCIA else '')


def texto_conservar(dias: int) -> str:
    if dias == -1:
        return t('hasta_espacio')
    if dias == 0:
        return t('siempre') + t('predeterminado')
    if dias >= 365:
        anios = round(dias / 365)
        return t('un_anio') if anios == 1 else t('anios', n=anios)
    return _meses(round(dias / 30))


def texto_limpiar(dias) -> str:
    """Opciones del diálogo Limpiar versiones; None = todas menos la más reciente."""
    return t('limpiar_todos') if dias is None else texto_conservar(dias)
