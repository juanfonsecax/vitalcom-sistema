"""modelos.py — la forma de lo que la app sirve, para que el frontend no redefina campos.

Los modelos son deliberadamente permisivos (`extra="allow"`): el dueño de cada contrato es
el motor, y si `flujo.py` o `decidir.py` agregan un campo, la app lo pasa sin romperse.
Lo que sí se fija es lo que la pantalla necesita para dibujar.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class Base(BaseModel):
    model_config = ConfigDict(extra="allow")


class Producto(Base):
    """Fila de `_DIM_PRODUCTOS.csv` + fase y nodo vigentes de `_ESTADO_FLUJO.csv`."""

    producto_key: str
    nombre_display: str = ""
    estado: str = ""
    cuenta_alias: str = ""
    moneda: str = ""
    # Los montos viajan como el CSV los escribe: texto, sin convertir ni redondear.
    costo_q: str = ""
    precio_base_q: str = ""
    cpa_base_q: str = ""
    cpa_be_q: str = ""
    campaign_id: str = ""
    fase_bitacora: str = ""  # la columna `fase` del CSV; quedó como bitácora
    # Derivado por flujo.py (esto es lo que manda):
    fase: str | None = None
    nodo_actual: str | None = None
    estado_flujo: str | None = None
    bloqueantes: int | None = None
    siguiente_ejecutor: str | None = None
    evaluado_el: str | None = None


class Requisito(Base):
    dato: str = ""
    ok: bool = False
    observado: str = ""
    dueno: str = ""
    regla: str = ""


class Nodo(Base):
    id: str
    titulo: str = ""
    ejecutor: str = ""
    ejecutor_tipo: str = ""
    como: str = ""
    estado: str = ""
    cumplido: bool = False
    ciclo: bool = False
    secuencia: list[Any] = []
    produce: list[Requisito] = []
    avisos: list[Any] = []


class Flujo(Base):
    """Salida de `flujo.py <pk> --json`, la vista completa del producto en el grafo."""

    producto_key: str
    nombre: str = ""
    estado_producto: str = ""
    fase: str = ""
    fase_titulo: str = ""
    nodo_actual: str = ""
    estado: str = ""
    ejecutor: str = ""
    como: str = ""
    evaluado_el: str = ""
    bloqueantes: list[Requisito] = []
    falta_para_cumplir: list[Requisito] = []
    entradas: list[Any] = []
    nodos: list[Nodo] = []
    avisos: list[Any] = []
    ordenes: list[Any] = []
    avance: dict[str, Any] | None = None
    motor: dict[str, Any] | None = None


class Salud(Base):
    """`VISTAS/_ESTADO.json`: frescura por vista, calculada por gen_app.py."""

    generado: str = ""
    version: int | None = None
    secciones: list[Any] = []
    vistas: list[Any] = []
    salud: dict[str, Any] | None = None


class Decisiones(Base):
    """`_DECISIONES.json`: lo que dictó `decidir.py`. La app no lo reinterpreta."""

    generado: str = ""
    datos_desde: str = ""
    datos_hasta: str = ""
    rezago_dias: int | None = None
    motor: str = ""
    ventana_dias: int | None = None
    resumen_acciones: dict[str, int] = {}
    productos: list[Any] = []


class Escalera(Base):
    unidades: int
    precio: float
    costo_pedido: float


class Costeo(Base):
    """Salida de `costear.py --json`. Las cifras salen de `_DIM_COSTEO.csv`, nunca de acá."""

    costo_ingresado: float
    fila_usada: float
    criterio_de_fila: str = ""
    precio_1u: float | None = None
    cpa_objetivo: float | None = None
    cpa_base: float | None = None
    cpa_break_even: float | None = None
    valor_envio: float | None = None
    utilidad_esperada: float | None = None
    escalera: list[Escalera] = []
    arranque: dict[str, Any] = {}
    fuente: str = ""
    origen_escalera: str = ""
