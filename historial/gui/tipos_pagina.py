"""Página "Tipos de archivo": categorías que se copian y extensiones que nunca se copian (cfg.tipos y
cfg.extensiones_excluidas; lista de tipos vacía = todos)."""
from historial import api

from . import categorias
from .pagina import Pagina
from .qt import W
from .textos import t
from .widgets import etiqueta


def normalizar(texto: str) -> list[str]:
    """' .ISO, vmdk ;log ' -> ['iso', 'vmdk', 'log'] sin repetidos."""
    vistas = []
    for parte in texto.replace(';', ',').replace(' ', ',').split(','):
        ext = parte.strip().lstrip('.').lower()
        if ext and ext not in vistas:
            vistas.append(ext)
    return vistas


class TiposPagina(Pagina):
    def __init__(self, cfg, padre=None):
        super().__init__(t('pag_tipos'), t('tipos_texto'), padre)
        self.cfg = cfg
        self.todos = W.QCheckBox(t('tipos_todos'))
        self.casillas = {c: W.QCheckBox(categorias.nombre(c)) for c in categorias.ORDEN}
        tarjeta = W.QFrame()
        tarjeta.setObjectName('tarjeta')
        rejilla = W.QGridLayout(tarjeta)
        rejilla.setContentsMargins(16, 16, 16, 16)
        rejilla.setHorizontalSpacing(24)
        rejilla.setVerticalSpacing(4)
        for i, (categoria, casilla) in enumerate(self.casillas.items()):
            muestra = categorias.ejemplos(categoria)
            casilla.setToolTip(muestra)
            rejilla.addWidget(casilla, (i // 2) * 2, i % 2)
            rejilla.addWidget(etiqueta(muestra, 'gris'), (i // 2) * 2 + 1, i % 2)
        self.extensiones = W.QLineEdit()
        self.extensiones.setPlaceholderText(t('tipos_ext_ayuda'))
        self.extensiones.setAccessibleName(t('tipos_ext'))
        self.resultado = etiqueta('', 'gris')
        self.guardar = W.QPushButton(t('guardar'))
        self.guardar.setObjectName('primario')
        self.guardar.clicked.connect(self.aplicar)
        self.todos.toggled.connect(lambda marcado: tarjeta.setEnabled(not marcado))
        fila = W.QHBoxLayout()
        fila.addWidget(self.resultado, 1)
        fila.addWidget(self.guardar)
        self.cuerpo.addSpacing(8)
        self.cuerpo.addWidget(self.todos)
        self.cuerpo.addWidget(tarjeta)
        self.seccion(t('tipos_ext'))
        self.cuerpo.addWidget(self.extensiones)
        self.cuerpo.addWidget(etiqueta(t('tipos_ext_ayuda'), 'gris'))
        self.cuerpo.addSpacing(16)
        self.cuerpo.addLayout(fila)
        self.cuerpo.addStretch(1)
        self.al_mostrar()

    def al_mostrar(self) -> None:
        """Refleja la configuración guardada (vacía = todos los tipos marcados)."""
        elegidos = list(getattr(self.cfg, 'tipos', []) or [])
        self.todos.setChecked(not elegidos)
        for categoria, casilla in self.casillas.items():
            casilla.setChecked(not elegidos or categoria in elegidos)
        self.extensiones.setText(', '.join(getattr(self.cfg, 'extensiones_excluidas', []) or []))
        self.resultado.setText('')

    def elegidos(self) -> list[str]:
        if self.todos.isChecked():
            return []
        return [c for c, casilla in self.casillas.items() if casilla.isChecked()]

    def aplicar(self) -> None:
        tipos = self.elegidos()
        if not self.todos.isChecked() and not tipos:
            self.resultado.setText(t('tipos_ninguno'))
            return
        self.cfg.tipos = [] if len(tipos) == len(self.casillas) else tipos
        self.cfg.extensiones_excluidas = normalizar(self.extensiones.text())
        api.guardar_config(self.cfg)
        self.extensiones.setText(', '.join(self.cfg.extensiones_excluidas))
        self.resultado.setText(t('tipos_guardado'))
