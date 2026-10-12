"""Catálogo SQLite. Una versión existe en el punto R si desde <= R <= hasta (hasta NULL = vigente)."""
from __future__ import annotations

import os
import shutil
import sqlite3
import time

from . import config, destino
from .api import Config

ESQUEMA = """
CREATE TABLE IF NOT EXISTS versiones(id INTEGER PRIMARY KEY AUTOINCREMENT, ruta TEXT NOT NULL,
  sello TEXT NOT NULL, tam INTEGER NOT NULL, mtime_ns INTEGER NOT NULL, archivo TEXT NOT NULL,
  desde INTEGER NOT NULL, hasta INTEGER);
CREATE INDEX IF NOT EXISTS i_versiones_ruta ON versiones(ruta);
CREATE TABLE IF NOT EXISTS ejecuciones(id INTEGER PRIMARY KEY AUTOINCREMENT, inicio REAL, fin REAL,
  copiados INTEGER DEFAULT 0, errores INTEGER DEFAULT 0, estado TEXT);
CREATE TABLE IF NOT EXISTS meta(clave TEXT PRIMARY KEY, valor TEXT);
"""


class Catalogo:
    def __init__(self, ruta) -> None:
        self.db = sqlite3.connect(ruta, timeout=60)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(ESQUEMA)

    def meta(self, clave: str, defecto=None):
        fila = self.db.execute('SELECT valor FROM meta WHERE clave=?', (clave,)).fetchone()
        return fila['valor'] if fila else defecto

    def poner_meta(self, clave: str, valor) -> None:
        self.db.execute('INSERT OR REPLACE INTO meta VALUES(?,?)', (clave, str(valor)))

    def iniciar(self) -> tuple[int, int | None]:
        """Abre una ejecución. Devuelve (id nuevo, id del punto anterior)."""
        self.db.execute("UPDATE ejecuciones SET estado='ok', fin=inicio WHERE estado='curso'")
        anterior = self.db.execute("SELECT MAX(id) FROM ejecuciones WHERE estado='ok'").fetchone()[0]
        nuevo = self.db.execute("INSERT INTO ejecuciones(inicio, estado) VALUES(?, 'curso')",
                                (time.time(),)).lastrowid
        return nuevo, anterior

    def terminar(self, punto: int, copiados: int, cerradas: int, errores: int) -> bool:
        """Cierra la ejecución; si no cambió nada no deja punto. Devuelve si dejó punto."""
        if copiados == 0 and cerradas == 0:
            self.db.execute('DELETE FROM ejecuciones WHERE id=?', (punto,))
            return False
        self.db.execute("UPDATE ejecuciones SET fin=?, copiados=?, errores=?, estado='ok' WHERE id=?",
                        (time.time(), copiados, errores, punto))
        return True

    def vigentes(self) -> dict[str, tuple[int, int, int]]:
        filas = self.db.execute('SELECT id, ruta, tam, mtime_ns FROM versiones WHERE hasta IS NULL')
        return {f['ruta']: (f['id'], f['tam'], f['mtime_ns']) for f in filas}

    def agregar(self, ruta: str, sello: str, tam: int, mtime_ns: int, archivo: str, desde: int) -> None:
        self.db.execute('INSERT INTO versiones(ruta, sello, tam, mtime_ns, archivo, desde) VALUES(?,?,?,?,?,?)',
                        (ruta, sello, tam, mtime_ns, archivo, desde))

    def cerrar(self, ids: list[int], hasta: int | None) -> None:
        self.db.executemany('UPDATE versiones SET hasta=? WHERE id=?', [(hasta, i) for i in ids])

    def exportar(self, ruta: str) -> None:
        """Copia consistente del catálogo (API de respaldo de SQLite) con reemplazo atómico."""
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        parcial = ruta + '.part'
        copia = sqlite3.connect(parcial)
        with copia:
            self.db.backup(copia)
        copia.close()
        os.replace(parcial, ruta)


def raiz_guardada(ruta) -> str:
    try:
        con = sqlite3.connect(ruta)
        fila = con.execute("SELECT valor FROM meta WHERE clave='raiz'").fetchone()
        con.close()
        return fila[0] if fila else ''
    except sqlite3.Error:
        return ''


def abrir(cfg: Config, crear: bool = True) -> Catalogo | None:
    """Abre el catálogo local; si falta usa el del destino. Cambiar de unidad aparta el anterior."""
    local = config.ruta_catalogo()
    if local.exists() and raiz_guardada(local) not in ('', destino.raiz_equipo(cfg)):
        if not crear:
            return None
        local.rename(local.with_name(f'catalogo.{int(time.time())}.sqlite'))
    if not local.exists():
        remoto = destino.catalogo_remoto(cfg)
        if not crear and not os.path.isfile(remoto):
            return None
        local.parent.mkdir(parents=True, exist_ok=True)
        if os.path.isfile(remoto):
            shutil.copyfile(remoto, local)
    local.parent.mkdir(parents=True, exist_ok=True)
    return Catalogo(local)
