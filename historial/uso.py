"""Uso del espacio del historial. Solo lee el catálogo (agregados en SQLite): rápido con 50 mil versiones."""
from __future__ import annotations

import os
import shutil
from datetime import datetime, timezone

from . import catalogo, estado
from .contrato_uso import Grupo, Uso
from .tipos import categoria_de

TOPE = 20
TODAS = 'SELECT ruta, tam, substr(sello, 1, 7), sello FROM versiones ORDER BY id'   # recorrido secuencial


def _fecha(sello: str | None) -> datetime | None:
    """'AAAA_MM_DD HH_MM_SS UTC' a hora local; None si falta o está dañado."""
    try:
        utc = datetime.strptime(sello, '%Y_%m_%d %H_%M_%S UTC').replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None
    return utc.astimezone().replace(tzinfo=None)


def _sumar(grupos: dict, clave: str, tam: int, versiones: int) -> None:
    g = grupos.get(clave)
    if g is None:
        grupos[clave] = Grupo(clave, tam, 1, versiones)
    else:
        g.bytes += tam
        g.archivos += 1
        g.versiones += versiones


def carpeta_de(ruta: str, raices: list[str]) -> str:
    """Carpeta protegida más específica que contiene la ruta; 'otros' si ninguna."""
    for raiz in raices:
        if ruta.startswith(raiz.rstrip(os.sep) + os.sep):
            return raiz
    return 'otros'


def _espacio(cfg) -> tuple[int, int]:
    if not estado.conectado(cfg):
        return 0, 0
    disco = shutil.disk_usage(cfg.destino)
    return disco.free, disco.total


def _mayor_a_menor(grupos: dict) -> list[Grupo]:
    return sorted(grupos.values(), key=lambda g: (-g.bytes, g.nombre))


def _agregar(filas, resultado: Uso) -> tuple[dict, dict]:
    """Una pasada: por ruta [bytes, versiones, tam de la última] y por mes [bytes, rutas, versiones]."""
    por_ruta, meses = {}, {}
    for ruta, tam, mes, _ in filas:
        r = por_ruta.get(ruta)
        if r is None:
            por_ruta[ruta] = [tam, 1, tam]
        else:
            r[0] += tam
            r[1] += 1
            r[2] = tam                         # ORDER BY id: la última fila es la versión más reciente
        m = meses.get(mes)
        if m is None:
            meses[mes] = m = [0, set(), 0]
        m[0] += tam
        m[1].add(ruta)
        m[2] += 1
    resultado.bytes_copias = sum(tam for _, tam, _, _ in filas)
    resultado.versiones = len(filas)
    sellos = [f[3] for f in filas]
    resultado.primera, resultado.ultima = (_fecha(min(sellos)), _fecha(max(sellos))) if sellos else (None, None)
    return por_ruta, meses


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
    por_ruta, meses = _agregar(filas, resultado)
    raices = sorted({os.path.normpath(c) for c in cfg.carpetas}, key=len, reverse=True)
    por_categoria, por_carpeta, archivos = {}, {}, []
    for ruta, (tam, versiones, ultimo) in por_ruta.items():
        resultado.bytes_actual += ultimo
        _sumar(por_categoria, categoria_de(ruta), tam, versiones)
        _sumar(por_carpeta, carpeta_de(ruta, raices), tam, versiones)
        archivos.append((ruta, tam, versiones))
    resultado.archivos = len(por_ruta)
    resultado.por_categoria = _mayor_a_menor(por_categoria)
    resultado.por_carpeta = _mayor_a_menor(por_carpeta)
    resultado.por_mes = [Grupo(m.replace('_', '-'), b, len(r), v) for m, (b, r, v) in sorted(meses.items())]
    resultado.mas_grandes = sorted(archivos, key=lambda a: (-a[1], a[0]))[:TOPE]
    resultado.mas_versionados = sorted(archivos, key=lambda a: (-a[2], -a[1], a[0]))[:TOPE]
    return resultado
