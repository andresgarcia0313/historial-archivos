"""Etiquetas de las listas de frecuencia, retención y limpieza (iguales a las de Windows)."""
from .textos import t

PRED_FRECUENCIA = 60
PRED_LIMPIAR = 365


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
    """Opciones de Limpieza: "Hace más de 1 año (predeterminado)"; None = todas menos la última."""
    if dias is None:
        return t('limpiar_todos')
    return t('hace_mas', tiempo=texto_conservar(dias)) + (t('predeterminado') if dias == PRED_LIMPIAR else '')
