"""Línea de órdenes: abre la GUI o ejecuta la copia (sin cargar Qt en --ejecutar)."""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys

from . import __version__, api, prioridad, registro


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog='historial-archivos', description='Historial de archivos')
    grupo = p.add_mutually_exclusive_group()
    grupo.add_argument('--restaurar', action='store_true', help='abre Restaurar archivos personales')
    grupo.add_argument('--versiones', metavar='RUTA', help='abre Versiones anteriores de un archivo o carpeta')
    grupo.add_argument('--ejecutar', action='store_true', help='hace una copia ahora (la usa el temporizador)')
    grupo.add_argument('--estado', action='store_true', help='imprime el estado en JSON')
    p.add_argument('--ahora', action='store_true', help='con --ejecutar: copia aunque esté desactivado')
    p.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    return p


def _ejecutar(ahora: bool) -> int:
    cfg = api.cargar_config()
    if not cfg.activo and not ahora:
        return 0
    prioridad.bajar()
    try:
        resumen = api.ejecutar(cfg)
    except Exception as error:                      # el registro debe mostrar también los fallos graves
        registro.anotar('ERROR', f'La copia falló: {error}')
        raise
    nivel = 'ADVERTENCIA' if resumen.errores else 'INFORMACIÓN'
    registro.anotar(nivel, f'Copia {resumen.punto_id}: revisados {resumen.revisados}, '
                           f'copiados {resumen.copiados} ({resumen.bytes_copiados} bytes), errores {len(resumen.errores)}')
    for error in resumen.errores[:50]:
        registro.anotar('ERROR', error)
    print(f'Revisados {resumen.revisados}, copiados {resumen.copiados}, errores {len(resumen.errores)}')
    for error in resumen.errores[:20]:
        print(error, file=sys.stderr)
    return 0


def _gui(modo: str, ruta: str | None) -> int:
    try:
        from historial.gui import app
    except ImportError as error:
        print(f'No se pudo cargar la interfaz gráfica: {error}', file=sys.stderr)
        return 1
    return app.main(modo, ruta) or 0


def principal(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.ejecutar:
        return _ejecutar(args.ahora)
    if args.estado:
        datos = dataclasses.asdict(api.estado(api.cargar_config()))
        print(json.dumps(datos, default=str, ensure_ascii=False, indent=2))
        return 0
    if args.versiones:
        return _gui('versiones', args.versiones)
    return _gui('restaurar' if args.restaurar else 'panel', None)


main = principal
