"""Página "Uso del espacio": cifras clave, uso por tipo y por carpeta, crecimiento por mes y limpieza filtrada."""
import os

from historial import api

from . import categorias
from .formato import fecha_texto, numero, tam_humano
from .pagina import Pagina
from .tarjetas import Rejilla
from .textos import t
from .trabajo import lanzar
from .uso_graficos import BarrasH, BarrasV
from .uso_limpiar import LimpiarFiltro
from .uso_tablas import Tablas
from .widgets import etiqueta

CIFRAS = ('cifra_copias', 'cifra_actual', 'cifra_libre', 'cifra_archivos', 'cifra_versiones', 'cifra_primera')


def _mes(nombre: str) -> str:
    """'2026-10' -> '10/26' (corto para que quepan muchos meses)."""
    anio, _, mes = nombre.partition('-')
    return f'{mes}/{anio[-2:]}' if mes else nombre


class UsoPagina(Pagina):
    def __init__(self, cfg, padre=None):
        super().__init__(t('pag_uso'), t('uso_texto'), padre)
        self.cfg, self.tarea = cfg, None
        self.estado = etiqueta('', 'gris')
        self.cifras = Rejilla({c: t(c) for c in CIFRAS})
        self.por_tipo, self.por_carpeta, self.por_mes = BarrasH(), BarrasH(), BarrasV()
        self.tablas = Tablas()
        self.limpieza = LimpiarFiltro(cfg)
        self.limpieza.limpiado.connect(lambda *_: self.al_mostrar())
        self.cuerpo.addWidget(self.estado)
        self.cuerpo.addWidget(self.cifras)
        self.detalle = [self.cifras]
        for titulo, widget in (('sec_por_tipo', self.por_tipo), ('sec_por_carpeta', self.por_carpeta),
                               ('sec_por_mes', self.por_mes), ('sec_detalle', self.tablas),
                               ('sec_limpiar_filtro', self.limpieza)):
            self.detalle += [self.seccion(t(titulo)), widget]
            self.cuerpo.addWidget(widget)
        self.cuerpo.addStretch(1)
        self._mostrar_detalle(False)

    def _mostrar_detalle(self, visible: bool) -> None:
        for w in self.detalle:
            w.setVisible(visible)

    def al_mostrar(self) -> None:
        """Calcula el uso en segundo plano; mientras tanto la página dice qué está haciendo."""
        if self.tarea is not None:
            return
        self.limpieza.cfg = self.cfg
        self.estado.setText(t('uso_calculando'))
        self.estado.setVisible(True)
        self.tarea = lanzar(self, lambda: api.uso(self.cfg), self.mostrar, self._fallo)

    def _fallo(self, motivo: str) -> None:
        self.tarea = None
        self.estado.setText(t('uso_fallo', motivo=motivo))

    def mostrar(self, u) -> None:
        self.tarea = None
        vacio = not u or not u.versiones
        self.estado.setText(t('uso_vacio') if vacio else '')
        self.estado.setVisible(vacio)
        self._mostrar_detalle(not vacio)
        if vacio:
            return
        c = self.cifras
        c['cifra_copias'].poner(tam_humano(u.bytes_copias))
        c['cifra_actual'].poner(tam_humano(u.bytes_actual))
        c['cifra_libre'].poner(tam_humano(u.libre), t('cifra_de', total=tam_humano(u.total)))
        c['cifra_archivos'].poner(numero(u.archivos))
        promedio = u.versiones / max(1, u.archivos)
        detalle = t('cifra_por_archivo') if promedio <= 1 else t('cifra_promedio', n=numero(promedio, 1))
        c['cifra_versiones'].poner(numero(u.versiones), detalle)
        ultima = t('cifra_ultima', fecha=fecha_texto(u.ultima)) if u.ultima else ''
        c['cifra_primera'].poner(fecha_texto(u.primera).split(' ')[0] or '-', ultima)
        self.por_tipo.poner([(categorias.nombre(g.nombre), g.bytes, tam_humano(g.bytes)) for g in u.por_categoria])
        self.por_carpeta.poner([(os.path.basename(g.nombre.rstrip('/')) or g.nombre, g.bytes, tam_humano(g.bytes))
                                for g in u.por_carpeta])
        self.por_mes.poner([(_mes(g.nombre), g.bytes, tam_humano(g.bytes)) for g in u.por_mes])
        self.tablas.poner(u.mas_grandes, u.mas_versionados)
        self.limpieza.poner([g.nombre for g in u.por_categoria], [g.nombre for g in u.por_carpeta])
