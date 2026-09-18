"""main.py — la API de solo lectura del Hito 1 y el servidor del frontend compilado.

Hito 1: la app NO escribe nada. No hay endpoint que corra un comando libre; lo único que se
ejecuta es `flujo.py --json --sin-escribir`, que es lectura. Las acciones que escriben llegan
en el Hito 3, declaradas en `VISTAS/_MANIFIESTO.json` y detrás de una cola con lock.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import contratos
from .config import base
from .modelos import Decisiones, Flujo, Producto, Salud

app = FastAPI(
    title="VitalCom",
    version="0.1.0",
    summary="La pantalla del sistema VITALCOM Guatemala (solo lectura, Hito 1).",
)

# En desarrollo el frontend corre en Vite (5173) y la API en 8000. En producción los sirve
# el mismo proceso y no hace falta CORS, pero dejarlo no abre nada: la API es de lectura y
# escucha en localhost.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/productos", response_model=list[Producto], tags=["productos"])
def listar_productos() -> list[Producto]:
    """El portafolio: la fila del CSV más la fase y el nodo vigentes del estado derivado.

    La fase que se sirve es la de `_ESTADO_FLUJO.csv` (derivada). La columna `fase` de
    `_DIM_PRODUCTOS.csv` viaja aparte, como `fase_bitacora`, para que nadie las confunda.
    """
    estados = contratos.estado_flujo()
    salida: list[Producto] = []
    for fila in contratos.productos():
        clave = fila["producto_key"]
        estado = estados.get(clave, {})
        bloqueantes = estado.get("bloqueantes") or ""
        salida.append(
            Producto(
                **{campo: valor for campo, valor in fila.items() if campo != "fase"},
                fase_bitacora=fila.get("fase", ""),
                fase=estado.get("fase") or None,
                nodo_actual=estado.get("nodo_actual") or None,
                estado_flujo=estado.get("estado") or None,
                bloqueantes=int(bloqueantes) if bloqueantes.isdigit() else None,
                siguiente_ejecutor=estado.get("siguiente_ejecutor") or None,
                evaluado_el=estado.get("evaluado_el") or None,
            )
        )
    return salida


@app.get("/api/productos/{producto_key}", response_model=Flujo, tags=["productos"])
def detalle_producto(producto_key: str) -> Flujo:
    """El recorrido completo del producto en el grafo, tal como lo evalúa `flujo.py`."""
    claves = {fila["producto_key"] for fila in contratos.productos()}
    if producto_key not in claves:
        raise HTTPException(
            status_code=404,
            detail=f"«{producto_key}» no tiene fila en _DIM_PRODUCTOS.csv (invariante 8).",
        )
    return Flujo(**contratos.flujo(producto_key))


@app.get("/api/decisiones", response_model=Decisiones, tags=["decisiones"])
def listar_decisiones() -> Decisiones:
    """Las órdenes vigentes de `decidir.py`. La app las muestra; no las recalcula."""
    return Decisiones(**contratos.decisiones())


@app.get("/api/salud", tags=["sistema"], response_model=Salud)
def estado_del_sistema() -> Salud:
    """Qué vista está fresca y quién la produce, según `gen_app.py`."""
    return Salud(**contratos.salud())


@app.get("/api/sistema", tags=["sistema"])
def donde_corre() -> dict[str, str]:
    """Sobre qué carpeta está corriendo la app. Evita el error del worktree (hoja §1.2)."""
    return {"base": str(base())}


@app.exception_handler(contratos.ContratoAusente)
def _contrato_ausente(_request, exc: contratos.ContratoAusente):  # type: ignore[no-untyped-def]
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=503, content={"detail": str(exc)})


# El frontend compilado, si ya existe. Va al final para no tapar /api.
DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{ruta_spa:path}", include_in_schema=False)
    def spa(ruta_spa: str) -> FileResponse:
        archivo = DIST / ruta_spa
        if ruta_spa and archivo.is_file():
            return FileResponse(archivo)
        return FileResponse(DIST / "index.html")
