"""Back In Time: escritura de un perfil con su propia API (así también reescribe el crontab)."""
from __future__ import annotations

import json
import os
import subprocess

from . import CopiaDetectada
from .backintime import API, leer, ruta_config
from .backintime_modos import MODOS, REPETIDO
from .comun import respaldar

PYTHON = '/usr/bin/python3'
DIA, HORA_U, DIA_U = 20, 10, 20

# Corre con el Python del sistema, que trae dbus y la API de Back In Time.
SCRIPT = '''
import json, sys
d = json.loads(sys.argv[1])
sys.path.insert(0, d["api"])
import config
cfg = config.Config(config_path=d["config"])
pid = d["perfil"]
cfg.setScheduleMode(d["modo"], pid)
if d["modo"] == 25:
    cfg.setScheduleRepeatedPeriod(d["periodo"], pid)
    cfg.setScheduleRepeatedUnit(d["unidad"], pid)
cfg.setInclude([(r, t) for r, t in d["incluir"]], pid)
cfg.setExclude(d["excluir"], pid)
cfg.save()
if d["automatizar"]:
    cfg.setup_automation()
'''


def modo(c: CopiaDetectada, actual: int) -> tuple[int, int, int]:
    """(modo, periodo, unidad) de Back In Time para la frecuencia pedida."""
    if not c.activa:
        return 0, 1, DIA_U
    minutos = c.frecuencia_min
    if minutos is None:
        return (actual or DIA), 1, DIA_U
    inverso = {v: k for k, v in MODOS.items() if k != 19}
    if minutos in inverso:
        return inverso[minutos], 1, DIA_U
    if minutos % 1440 == 0:
        return REPETIDO, minutos // 1440, DIA_U
    return REPETIDO, max(1, round(minutos / 60)), HORA_U


def datos(c: CopiaDetectada, automatizar: bool = True) -> dict:
    pid = c.id.split(':', 1)[1]
    ruta = ruta_config()
    actual = int(leer(ruta).get(f'profile{pid}.schedule.mode', '0') or 0)
    elegido, periodo, unidad = modo(c, actual)
    incluir = [[r, 1 if os.path.isfile(r) else 0] for r in c.carpetas]
    return {'api': API, 'config': str(ruta), 'perfil': pid, 'modo': elegido, 'periodo': periodo,
            'unidad': unidad, 'incluir': incluir, 'excluir': list(c.excluir),
            'automatizar': automatizar}


def guardar(c: CopiaDetectada, automatizar: bool = True) -> None:
    """Respalda la config (.bak-<epoch>) y aplica los cambios; lanza RuntimeError si falla."""
    if not os.path.isdir(API):
        raise RuntimeError('Back In Time no está instalado en este equipo')
    carga = datos(c, automatizar)
    respaldar(carga['config'])
    hecho = subprocess.run([PYTHON, '-I', '-c', SCRIPT, json.dumps(carga)],
                           capture_output=True, text=True, timeout=60, check=False)
    if hecho.returncode != 0:
        raise RuntimeError(f'Back In Time no aceptó los cambios: {hecho.stderr.strip()[-300:]}')
