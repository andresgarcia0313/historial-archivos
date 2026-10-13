"""Uso del espacio del historial. Solo lee el catálogo, en una pasada secuencial: < 1 s con 50 mil versiones."""
from __future__ import annotations

import heapq
import os
import shutil
from datetime import datetime, timezone

from . import catalogo, estado
from .contrato_uso import Grupo, Uso
from .tipos import categoria_de

TOPE = 20
TODAS = 'SELECT ruta, tam, sello FROM versiones ORDER BY id'   # ORDER BY id: la última fila es la más reciente


def _fecha(sello: str | None) -> datetime | None:
    """'AAAA_MM_DD HH_MM_SS UTC' a hora local; None si falta o está dañado."""
    try:
        utc = datetime.strptime(sello, '%Y_%m_%d %H_%M_%S UTC').replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None
    return utc.astimezone().replace(tzinfo=None)


def carpeta_de(ruta: str, raices: list[str]) -> str:
    """Carpeta protegida más específica que contiene la ruta (raíces de la más larga a la más corta)."""
    for raiz in raices:
        if ruta.startswith(raiz.rstrip(os.sep) + os.sep):
            return raiz
    return 'otros'


def _espacio(cfg) -> tuple[int, int]:
    if not estado.conectado(cfg):
        return 0, 0
    disco = shutil.disk_usage(cfg.destino)
    return disco.free, disco.total


def _por_ruta_y_mes(filas) -> tuple[dict, dict]:
    """Por ruta [bytes, versiones, tam de la última]; por mes [bytes, rutas, versiones]."""
    por_ruta, meses = {}, {}
    for ruta, tam, sello in filas:
        r = por_ruta.get(ruta)
        if r is None:
            por_ruta[ruta] = [tam, 1, tam]
        else:
            r[0] += tam
            r[1] += 1
            r[2] = tam
        m = meses.get(sello[:7])
        if m is None:
            m = meses[sello[:7]] = [0, set(), 0]
        m[0] += tam
        m[1].add(ruta)
        m[2] += 1
    return por_ruta, meses


def _grupos(acumulado: dict) -> list[Grupo]:
    """{nombre: [bytes, archivos, versiones]} a Grupos de mayor a menor."""
    return sorted((Grupo(n, *v) for n, v in acumulado.items()), key=lambda g: (-g.bytes, g.nombre))


def _sumar(acumulado: dict, clave: str, tam: int, versiones: int) -> None:
    a = acumulado.get(clave) or acumulado.setdefault(clave, [0, 0, 0])
    a[0], a[1], a[2] = a[0] + tam, a[1] + 1, a[2] + versiones


def uso(cfg) -> Uso:
    libre, total = _espacio(cfg)
    resultado = Uso(0, 0, 0, 0, libre, total, None, None)
    cat = catalogo.abrir(cfg, crear=False)
    if cat is None:
        return resultado
    try:
        filas = cat.db.execute(TODAS).fetchall()
    finally:
        cat.db.close()
    if not filas:
        return resultado
    por_ruta, meses = _por_ruta_y_mes(filas)
    raices = sorted({os.path.normpath(c) for c in cfg.carpetas}, key=len, reverse=True)
    por_categoria, por_carpeta = {}, {}
    for ruta, (tam, versiones, _) in por_ruta.items():
        _sumar(por_categoria, categoria_de(ruta), tam, versiones)
        _sumar(por_carpeta, carpeta_de(ruta, raices), tam, versiones)
    sellos = [f[2] for f in filas]
    resultado.primera, resultado.ultima = _fecha(min(sellos)), _fecha(max(sellos))
    resultado.bytes_copias, resultado.versiones = sum(m[0] for m in meses.values()), len(filas)
    resultado.bytes_actual, resultado.archivos = sum(r[2] for r in por_ruta.values()), len(por_ruta)
    resultado.por_categoria, resultado.por_carpeta = _grupos(por_categoria), _grupos(por_carpeta)
    resultado.por_mes = [Grupo(m.replace('_', '-'), b, len(r), v) for m, (b, r, v) in sorted(meses.items())]
    archivos = [(ruta, r[0], r[1]) for ruta, r in por_ruta.items()]
    resultado.mas_grandes = heapq.nsmallest(TOPE, archivos, key=lambda a: (-a[1], a[0]))
    resultado.mas_versionados = heapq.nsmallest(TOPE, archivos, key=lambda a: (-a[2], -a[1], a[0]))
    return resultado
