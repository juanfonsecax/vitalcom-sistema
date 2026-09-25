"""main.py — la API de la app y el servidor del frontend compilado.

La app no calcula y no escribe: **ejecuta al que escribe**. Las lecturas salen de los
contratos; todo cambio es una acción declarada en `VISTAS/_MANIFIESTO.json` que el runner
(`workflows.py`) ejecuta detrás de la cola de escritura. No hay ningún endpoint que corra un
comando libre.
"""

from __future__ import annotations

import asyncio
import uuid
from contextlib import ExitStack, asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from fastapi.responses import JSONResponse

from . import acciones, api_acciones, api_fase1, api_fases, api_ordenes, api_trabajos, claude, contratos, subidas, workflows
from .acciones import ErrorDeAccion
from .config import base
from .modelos import Costeo, Cuenta, Decisiones, FanPage, Flujo, Producto, Resultados, Salud

@asynccontextmanager
async def _ciclo_de_vida(_app: FastAPI):  # type: ignore[no-untyped-def]
    """Al arrancar, DBOS retoma los trabajos que quedaron a medias; al cerrar, se despide."""
    # DBOS es síncrono y no admite un event loop corriendo en su hilo: se lanza aparte.
    await asyncio.to_thread(workflows.iniciar)
    try:
        yield
    finally:
        await asyncio.to_thread(workflows.detener)


app = FastAPI(
    title="VitalCom",
    version="0.1.0",
    summary="La pantalla del sistema VITALCOM Guatemala.",
    lifespan=_ciclo_de_vida,
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
TOPE_DEL_ALTA_S = 120
TOPE_DEL_PL_S = 120
app.include_router(api_acciones.router)
app.include_router(api_trabajos.router)
app.include_router(api_trabajos.router_claude)
app.include_router(api_fase1.router)
app.include_router(api_ordenes.router)
app.include_router(api_fases.router)


@app.exception_handler(ErrorDeAccion)
def _accion_rechazada(_request, error: ErrorDeAccion) -> JSONResponse:  # type: ignore[no-untyped-def]
    return JSONResponse(status_code=error.http, content=error.cuerpo())


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
    return Salud(**contratos.salud(), meta_falso=claude.meta_falso())


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
def alta_de_producto(
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
    """Da de alta el producto: la acción `producto.alta` por el runner, y espera su resultado.

    La imagen y la descripción se guardan primero en una carpeta temporal; quien las mete
    en el sistema —y quien declara el packshot en `_DIM_ENVASE.csv`— es `alta_producto.py`.
    """
    opcionales = {"clave": clave, "cuenta": cuenta, "moneda": moneda, "tasa": tasa,
                  "color_envase": color_envase, "color_hex": color_hex, "marca": marca,
                  "formato": formato}
    try:
        with subidas.carpeta_temporal() as temporal:
            ruta_imagen = subidas.guardar(imagen.file, imagen.filename or "imagen", temporal)
            ruta_descripcion = subidas.guardar_texto(descripcion, temporal)
            accion = acciones.por_id_para_el_runner("producto.alta")
            valores = acciones.validar_parametros(accion, {
                "nombre": nombre, "costo": costo, "descripcion": str(ruta_descripcion),
                "imagen": str(ruta_imagen), "dry_run": dry_run,
                **{k: v for k, v in opcionales.items() if v.strip()},
            })
            job_id, _repetido = workflows.encolar(accion, valores, uuid.uuid4().hex)
            resultado = workflows.esperar_resultado(job_id, TOPE_DEL_ALTA_S)
    except subidas.SubidaRechazada as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if resultado is None:
        raise HTTPException(
            status_code=409,
            detail="El alta no alcanzó a terminar: hay otro cambio en curso. Probá de nuevo en un momento.",
        )
    unidad = resultado["unidades"][0]
    if resultado["estado"] != "EXITO":
        raise HTTPException(status_code=422, detail=unidad.get("detalle") or resultado["detalle"])
    return unidad["json"]


@app.post("/api/productos/{producto_key}/transcribir", tags=["productos"], status_code=410,
          include_in_schema=False)
def transcribir_videos(producto_key: str) -> dict:
    """Ya no existe: transcribir es la acción `producto.transcribir` (202 y progreso en vivo)."""
    raise HTTPException(status_code=410, detail="Usá POST /api/acciones/producto.transcribir.")


@app.get("/api/sistema", tags=["sistema"])
def donde_corre() -> dict[str, str]:
    """Sobre qué carpeta está corriendo la app. Evita el error del worktree (hoja §1.2)."""
    return {"base": str(base())}


@app.get("/api/cuentas", response_model=list[Cuenta], tags=["sistema"])
def listar_cuentas() -> list[Cuenta]:
    """Las cuentas publicitarias del portafolio (_DIM_CUENTAS.csv)."""
    return [Cuenta(**fila) for fila in contratos.cuentas()]


@app.get("/api/fanpages", response_model=list[FanPage], tags=["sistema"])
def listar_fanpages() -> list[FanPage]:
    """Las FanPages declaradas (_DIM_FANPAGES.csv). Lista vacía, nunca un error, cuando la
    carpeta sobre la que corre la app todavía no tiene ese archivo (T5)."""
    return [FanPage(**fila) for fila in contratos.fanpages()]


@app.get("/api/resultados", response_model=Resultados, tags=["resultados"])
def resultados() -> Resultados:
    """El P&L más reciente que dejó `gen_pl.py --json` (T4a): VISTA A/B, tal cual las decidió el
    script. 404 (no 503: es un estado normal de arranque, no una falla del sistema) cuando
    nadie cargó todavía el export de Dropi (DOCTRINA/CONTABILIDAD.md §5)."""
    try:
        return Resultados(**contratos.resultados())
    except contratos.ContratoAusente as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/api/resultados/historial", response_model=list[Resultados], tags=["resultados"])
def historial_de_resultados() -> list[Resultados]:
    """Todos los períodos que `gen_pl.py --json` dejó en `_AUDITORIAS/` (T4a), del más viejo al
    más nuevo: el gráfico de tendencia de la pantalla los lee de acá, nunca de una interpolación."""
    return [Resultados(**dato) for dato in contratos.historial_resultados()]


@app.post("/api/resultados/cargar", tags=["resultados"], status_code=201)
def cargar_resultados(
    dropi: UploadFile = File(..., description="export de órdenes de Dropi (--dropi, obligatorio)"),
    banco: UploadFile | None = File(None, description="extracto bancario de Relay, opcional"),
    cartera: UploadFile | None = File(None, description="historial de cartera de Dropi, opcional"),
    desde: str = Form(""),
    hasta: str = Form(""),
) -> dict:
    """Corre la acción `resultados.cargar_pl`: `gen_pl.py --json` sobre lo que sube el operador.

    Los archivos se guardan primero en carpetas temporales del sistema operativo (una por
    archivo, igual que el alta de producto) y quien los mete al sistema es `gen_pl.py`, que
    además escribe el `.txt` y el `.json` en `PRODUCTOS/_AUDITORIAS/`.
    """
    try:
        with ExitStack() as pila:
            ruta_dropi = subidas.guardar(
                dropi.file, dropi.filename or "dropi.xlsx", pila.enter_context(subidas.carpeta_temporal())
            )
            valores_crudos = {"dropi": str(ruta_dropi), "desde": desde, "hasta": hasta}
            if banco is not None:
                ruta_banco = subidas.guardar(
                    banco.file, banco.filename or "banco.pdf", pila.enter_context(subidas.carpeta_temporal())
                )
                valores_crudos["banco"] = str(ruta_banco)
            if cartera is not None:
                ruta_cartera = subidas.guardar(
                    cartera.file, cartera.filename or "cartera.xlsx", pila.enter_context(subidas.carpeta_temporal())
                )
                valores_crudos["cartera"] = str(ruta_cartera)
            accion = acciones.por_id_para_el_runner("resultados.cargar_pl")
            valores = acciones.validar_parametros(
                accion, {k: v for k, v in valores_crudos.items() if not isinstance(v, str) or v.strip()}
            )
            job_id, _repetido = workflows.encolar(accion, valores, uuid.uuid4().hex)
            resultado = workflows.esperar_resultado(job_id, TOPE_DEL_PL_S)
    except subidas.SubidaRechazada as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if resultado is None:
        raise HTTPException(
            status_code=409,
            detail="La carga no alcanzó a terminar: hay otro cambio en curso. Probá de nuevo en un momento.",
        )
    unidad = resultado["unidades"][0]
    if resultado["estado"] != "EXITO":
        raise HTTPException(status_code=422, detail=unidad.get("detalle") or resultado["detalle"])
    return unidad["json"]


@app.exception_handler(contratos.ContratoAusente)
def _contrato_ausente(_request, exc: contratos.ContratoAusente):  # type: ignore[no-untyped-def]
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
