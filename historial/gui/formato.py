"""Formato de tamaños y fechas para mostrar."""
from .qt import C
from .textos import idioma, t


def tam_humano(n: int) -> str:
    """465 GB, 12,3 MB, 0 B ... con base 1024 como el Explorador de Windows."""
    valor = float(n)
    for unidad in ('B', 'KB', 'MB', 'GB', 'TB'):
        if valor < 1024 or unidad == 'TB':
            break
        valor /= 1024
    decimales = 0 if unidad in ('B', 'KB') or valor >= 100 else 1
    texto = f'{valor:.{decimales}f}'
    if idioma() == 'es':
        texto = texto.replace('.', ',')
    return f'{texto} {unidad}'


def _qfecha(fecha):
    return C.QDateTime(C.QDate(fecha.year, fecha.month, fecha.day),
                       C.QTime(fecha.hour, fecha.minute, fecha.second))


def fecha_texto(fecha, largo: bool = False) -> str:
    """Fecha local legible en el idioma de la interfaz; '' si no hay fecha."""
    if fecha is None:
        return ''
    formato = t('fmt_larga' if largo else 'fmt_corta')
    return C.QLocale(idioma()).toString(_qfecha(fecha), formato)
