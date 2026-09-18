"""main.py — la API de la app y el servidor del frontend compilado.

La app no calcula y no escribe: **ejecuta al que escribe**. Las lecturas salen de los
contratos; los dos cambios que existen hoy (dar de alta un producto y transcribir sus
videos) los hace un script de `Ads/_TOOLS/` con su propio test, detrás de la cola de
`escrituras.py`. No hay ningún endpoint que corra un comando libre.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import contratos, escrituras, subidas
from .config import base
from .modelos import Costeo, Decisiones, Flujo, Producto, Salud

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
    allow_methods=["GET", "POST"],
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


@app.get("/api/costeo/{costo_q}", response_model=Costeo, tags=["productos"])
def costeo(costo_q: str) -> Costeo:
    """La tabla de precios de Guatemala para un costo, tal como la devuelve `costear.py`.

    La app no calcula ni un centavo: pregunta y muestra. Si el costo cae entre dos filas de
    `_DIM_COSTEO.csv`, el script toma la superior y lo dice en `criterio_de_fila`
    (invariante 2).
    """
    try:
        return Costeo(**contratos.costear(costo_q))
    except contratos.ContratoAusente as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/api/productos", tags=["productos"], status_code=201)
async def alta_de_producto(
    nombre: str = Form(..., description="cómo se llama el producto"),
    costo: str = Form(..., description="costo del PEDIDO COMPLETO en quetzales"),
    descripcion: str = Form(..., description="la descripción extensa del operador"),
    imagen: UploadFile = File(..., description="la foto limpia del producto: el packshot"),
    clave: str = Form(""),
    cuenta: str = Form(""),
    moneda: str = Form("GTQ"),
    tasa: str = Form(""),
    color_envase: str = Form(""),
    color_hex: str = Form(""),
    marca: str = Form(""),
    formato: str = Form(""),
    dry_run: bool = Form(False),
) -> dict:
    """Da de alta el producto con `alta_producto.py` y re-evalúa el flujo.

    La imagen y la descripción se guardan primero en una carpeta temporal; quien las mete
    en el sistema —y quien declara el packshot en `_DIM_ENVASE.csv`— es el script.
    """
    campos = {
        "nombre": nombre, "costo": costo, "clave": clave, "cuenta": cuenta, "moneda": moneda,
        "tasa": tasa, "color_envase": color_envase, "color_hex": color_hex, "marca": marca,
        "formato": formato,
    }
    try:
        with subidas.carpeta_temporal() as temporal:
            ruta_imagen = subidas.guardar(imagen.file, imagen.filename or "imagen", temporal)
            ruta_descripcion = subidas.guardar_texto(descripcion, temporal)
            return escrituras.dar_de_alta(campos, ruta_imagen, ruta_descripcion, dry_run=dry_run)
    except subidas.SubidaRechazada as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except escrituras.SistemaOcupado as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except escrituras.ErrorDeEscritura as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/api/productos/{producto_key}/transcribir", tags=["productos"])
def transcribir_videos(producto_key: str, modelo: str = "small") -> dict:
    """Pasa a texto los videos del producto con `transcribir_videos.py`, en esta máquina."""
    try:
        return escrituras.transcribir(producto_key, modelo=modelo)
    except escrituras.SistemaOcupado as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except escrituras.ErrorDeEscritura as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


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
