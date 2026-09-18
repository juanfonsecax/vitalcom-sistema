"""acciones.py — qué puede hacer la app, según `VISTAS/_MANIFIESTO.json` (bloque `acciones`).

Es el ÚNICO lugar que sabe qué es una acción (diseño Hito 3, §3.1). Hace cuatro cosas:
  1. Carga el manifiesto y le pide su validación a `gen_app.py --validar-manifiesto`: la app
     no re-implementa las 21 reglas, solo lee el veredicto.
  2. Valida los parámetros que manda el operador contra el vocabulario cerrado del manifiesto.
  3. **Resuelve el argv** de una acción de tipo `script`: la lista de tokens que el runner corre,
     sin shell. Ningún literal de comando vive fuera del manifiesto.
  4. Consulta la precondición (`nodo_listo`) preguntándole a `flujo.py`, nunca calculándola.

No ejecuta nada y no escribe nada. Ejecutar es de `workflows.py`.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import contratos
from .config import base, python_del_sistema, ruta

MANIFIESTO = ("VISTAS", "_MANIFIESTO.json")
GEN_APP = ("Ads", "_TOOLS", "gen_app.py")
PREFIJO_TEMPORAL = "vitalcom-subida-"
_MARCADOR = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
_FASE = re.compile(r"^F\d+\.")


class ErrorDeAccion(Exception):
    """Una acción rechazada, con el código HTTP y el `codigo` del contrato (diseño §2.5)."""

    def __init__(self, http: int, codigo: str, detalle: str, **extra: Any) -> None:
        super().__init__(detalle)
        self.http = http
        self.codigo = codigo
        self.detalle = detalle
        self.extra = extra

    def cuerpo(self) -> dict[str, Any]:
        return {"detail": self.detalle, "codigo": self.codigo, **self.extra}


@dataclass
class EstadoManifiesto:
    """`ok` (acciones válidas) · `sin_acciones` (manifiesto v6) · `invalido` (+ problemas)."""

    estado: str
    version: int | None = None
    problemas: list[str] = field(default_factory=list)
    bloque: dict[str, Any] = field(default_factory=dict)

    def lista(self) -> list[dict[str, Any]]:
        return list(self.bloque.get("lista", []))


_cache: dict[str, Any] = {"clave": None, "estado": None}


def _clave_de_cache() -> tuple[str, int, int] | None:
    archivo = ruta(*MANIFIESTO)
    if not archivo.is_file():
        return None
    datos = archivo.stat()
    return (str(base()), datos.st_mtime_ns, datos.st_size)


def _validar_con_gen_app() -> tuple[bool, list[str]]:
    """`gen_app.py --validar-manifiesto --json`: el veredicto es del script, no nuestro."""
    guion = ruta(*GEN_APP)
    if not guion.is_file():
        return False, [f"falta {Path(*GEN_APP)}: no puedo validar el manifiesto"]
    completado = subprocess.run(
        [python_del_sistema(), str(guion), "--validar-manifiesto", "--json"],
        cwd=str(ruta()), capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=60,
    )
    try:
        veredicto = json.loads(completado.stdout)
    except json.JSONDecodeError:
        detalle = (completado.stderr or completado.stdout or "sin salida").strip()
        return False, [f"gen_app.py --validar-manifiesto no devolvió JSON: {detalle[-300:]}"]
    return bool(veredicto.get("ok")), list(veredicto.get("problemas") or [])


def cargar() -> EstadoManifiesto:
    """El manifiesto vigente. Se relee y revalida solo cuando cambia su `mtime`."""
    clave = _clave_de_cache()
    if clave is not None and _cache["clave"] == clave:
        return _cache["estado"]

    archivo = ruta(*MANIFIESTO)
    if clave is None:
        estado = EstadoManifiesto("invalido", problemas=[f"falta {Path(*MANIFIESTO)}"])
    else:
        try:
            contenido = json.loads(archivo.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as error:
            estado = EstadoManifiesto("invalido", problemas=[f"el manifiesto no se puede leer: {error}"])
        else:
            version = contenido.get("version")
            bloque = contenido.get("acciones")
            if not isinstance(version, int) or version < 7 or not isinstance(bloque, dict):
                estado = EstadoManifiesto("sin_acciones", version=version if isinstance(version, int) else None)
            else:
                valido, problemas = _validar_con_gen_app()
                estado = (
                    EstadoManifiesto("ok", version=version, bloque=bloque)
                    if valido else EstadoManifiesto("invalido", version=version, problemas=problemas)
                )
    _cache["clave"], _cache["estado"] = clave, estado
    return estado


def olvidar_cache() -> None:
    """Para las pruebas: que el próximo `cargar()` relea el disco."""
    _cache["clave"], _cache["estado"] = None, None


def _exigir_manifiesto_valido() -> EstadoManifiesto:
    estado = cargar()
    if estado.estado == "invalido":
        raise ErrorDeAccion(
            503, "MANIFIESTO_INVALIDO",
            "El manifiesto de acciones no es válido: el sistema no ofrece ninguna acción hasta arreglarlo.",
            problemas=estado.problemas,
        )
    return estado


def declaradas() -> list[dict[str, Any]]:
    """Las acciones con botón (`visibilidad: boton`). Vacío si el manifiesto es v6."""
    return [a for a in _exigir_manifiesto_valido().lista() if a.get("visibilidad") == "boton"]


def buscar(accion_id: str, *, interna_ok: bool = False) -> dict[str, Any]:
    """La acción declarada con ese id. No declarada o interna (desde la API) → 403."""
    estado = _exigir_manifiesto_valido()
    for accion in estado.lista():
        if accion["id"] == accion_id:
            if accion.get("visibilidad") == "interna" and not interna_ok:
                raise ErrorDeAccion(
                    403, "ACCION_INTERNA",
                    f"«{accion_id}» es una acción interna del runner: no se pide desde la pantalla.",
                )
            return accion
    raise ErrorDeAccion(
        403, "ACCION_NO_DECLARADA",
        f"«{accion_id}» no está declarada en el manifiesto de acciones: la app no la ejecuta.",
    )


def tras_escribir() -> list[str]:
    """Los ids de las acciones que el runner corre después de toda unidad que escribe."""
    return list(cargar().bloque.get("tras_escribir", []))


def sha_del_manifiesto() -> str:
    """Huella del manifiesto con el que arrancó un trabajo (queda en el sello)."""
    return hashlib.sha256(ruta(*MANIFIESTO).read_bytes()).hexdigest()


def por_id_para_el_runner(accion_id: str) -> dict[str, Any]:
    """Para `workflows.py`: cualquier acción declarada, interna o no."""
    return buscar(accion_id, interna_ok=True)


# ── parámetros ────────────────────────────────────────────────────────────────

def _invalido(campo: str, mensaje: str) -> ErrorDeAccion:
    return ErrorDeAccion(422, "PARAMETRO_INVALIDO", f"«{campo}»: {mensaje}", campo=campo)


def _en_la_carpeta_de_subidas(valor: str) -> bool:
    """Está dentro de una carpeta que creó `subidas.py` en el temporal del sistema operativo."""
    try:
        archivo = Path(valor).resolve()
    except (OSError, ValueError):
        return False
    temporal = Path(tempfile.gettempdir()).resolve()
    return (
        archivo.is_file()
        and archivo.parent.parent == temporal
        and archivo.parent.name.startswith(PREFIJO_TEMPORAL)
    )


def _validar_uno(nombre: str, especificacion: dict[str, Any], valor: Any) -> Any:
    tipo = especificacion["tipo"]
    if tipo == "bandera":
        if not isinstance(valor, bool):
            raise _invalido(nombre, "tiene que ser verdadero o falso.")
        return valor

    if isinstance(valor, bool) or not isinstance(valor, (str, int, float)):
        raise _invalido(nombre, "tiene que ser un texto.")
    texto = str(valor)
    # Un valor que arranca con «-» podría leerse como una bandera del script: nunca pasa.
    if texto.startswith("-"):
        raise _invalido(nombre, "no puede empezar con «-».")
    if not texto.strip():
        raise _invalido(nombre, "está vacío.")

    if tipo == "producto_key":
        if texto not in {fila["producto_key"] for fila in contratos.productos()}:
            raise _invalido(nombre, f"«{texto}» no tiene fila en _DIM_PRODUCTOS.csv.")
    elif tipo == "cuenta_alias":
        if texto not in {fila["cuenta_alias"] for fila in contratos.cuentas()}:
            raise _invalido(nombre, f"«{texto}» no está en _DIM_CUENTAS.csv.")
    elif tipo == "enum":
        if texto not in especificacion.get("valores", []):
            raise _invalido(nombre, f"«{texto}» no es una de las opciones: {especificacion.get('valores')}.")
    elif tipo == "texto":
        if not re.fullmatch(especificacion["patron"], texto):
            raise _invalido(nombre, "no tiene el formato que el sistema espera.")
    elif tipo == "archivo_temporal":
        if not _en_la_carpeta_de_subidas(texto):
            raise _invalido(nombre, "el archivo no salió de una subida de la pantalla.")
    return texto


def validar_parametros(accion: dict[str, Any], recibidos: dict[str, Any]) -> dict[str, Any]:
    """Parámetros faltantes, sobrantes o inválidos → 422. Devuelve los valores ya validados."""
    declarados = accion.get("parametros", {})
    sobrantes = sorted(set(recibidos) - set(declarados))
    if sobrantes:
        raise _invalido(sobrantes[0], "la acción no lleva ese parámetro.")
    valores: dict[str, Any] = {}
    for nombre, especificacion in declarados.items():
        if nombre not in recibidos or recibidos[nombre] is None:
            if especificacion.get("requerido"):
                raise _invalido(nombre, "falta.")
            continue
        valores[nombre] = _validar_uno(nombre, especificacion, recibidos[nombre])
    return valores


# ── argv ──────────────────────────────────────────────────────────────────────

class ArgvIncompleto(RuntimeError):
    """Un `{marcador}` del comando no tiene valor: el runner no corre una orden a medias."""


def resolver(accion: dict[str, Any], valores: dict[str, Any],
             reservados: dict[str, str] | None = None) -> list[str]:
    """El argv literal de una acción `script`. Sin shell: cada elemento es un token."""
    if accion.get("ejecutor_tipo") != "script" or not accion.get("comando"):
        raise ArgvIncompleto(f"«{accion.get('id')}» no es una acción de script.")
    contexto: dict[str, str] = {k: str(v) for k, v in valores.items() if not isinstance(v, bool)}
    contexto.update(reservados or {})

    def _sustituir(token: str) -> str:
        def _por(coincidencia: re.Match[str]) -> str:
            nombre = coincidencia.group(1)
            if nombre not in contexto:
                raise ArgvIncompleto(f"falta el valor de {{{nombre}}} para «{accion['id']}».")
            return contexto[nombre]

        return _MARCADOR.sub(_por, token)

    argv = [_sustituir(token) for token in accion["comando"]]
    argv[0] = python_del_sistema() if argv[0] == "python" else argv[0]
    for nombre, especificacion in accion.get("parametros", {}).items():
        bandera = especificacion.get("bandera")
        if not bandera or nombre not in valores:
            continue
        if especificacion["tipo"] == "bandera":
            if valores[nombre]:
                argv.append(bandera)
        else:
            argv += [bandera, str(valores[nombre])]
    return argv


# ── precondición: el nodo tiene que estar listo, lo dice flujo.py ─────────────

def _sin_prefijo_de_fase(nodo: str) -> str:
    return _FASE.sub("", nodo)


def es_el_mismo_nodo(nodo_de_la_accion: str, nodo_actual: str) -> bool:
    """`F2.plan` == `F2.plan`; `ciclo.motor` == `F2.ciclo.motor` (el ciclo cambia de prefijo)."""
    if nodo_de_la_accion == nodo_actual:
        return True
    return nodo_de_la_accion.startswith("ciclo.") and _sin_prefijo_de_fase(nodo_actual) == nodo_de_la_accion


def situacion_del_nodo(accion: dict[str, Any], flujo: dict[str, Any]) -> dict[str, Any]:
    """Lo que `flujo.py` dijo del producto, tal cual, para decidir si la acción está disponible."""
    nodo = accion.get("nodo")
    listo = bool(
        nodo
        and es_el_mismo_nodo(nodo, flujo.get("nodo_actual", ""))
        and flujo.get("estado") == "LISTO_PARA_EJECUTAR"
    )
    return {
        "listo": listo,
        "nodo_actual": flujo.get("nodo_actual"),
        "estado": flujo.get("estado"),
        "bloqueantes": flujo.get("bloqueantes", []),
    }


def exigir_nodo_listo(accion: dict[str, Any], valores: dict[str, Any]) -> None:
    if accion.get("precondicion") != "nodo_listo":
        return
    situacion = situacion_del_nodo(accion, contratos.flujo(valores["producto_key"]))
    if not situacion["listo"]:
        raise ErrorDeAccion(
            409, "NODO_NO_LISTO",
            "El producto no está en ese paso o el paso todavía está bloqueado.",
            nodo_actual=situacion["nodo_actual"], estado=situacion["estado"],
            bloqueantes=situacion["bloqueantes"],
        )


# ── lo que se le muestra a la pantalla ────────────────────────────────────────

CAMPOS_PUBLICOS = (
    "id", "rotulo", "nodo", "ejecutor_tipo", "parametros", "requiere_confirmacion", "aprobacion",
    "toca_meta", "escribe", "habilitada", "motivo", "tiempo_max_s", "datos_del_operador",
)


def publica(accion: dict[str, Any]) -> dict[str, Any]:
    return {campo: accion.get(campo) for campo in CAMPOS_PUBLICOS}


def _filtrar_por_nodo(acciones: list[dict[str, Any]], nodo: str | None) -> list[dict[str, Any]]:
    if not nodo:
        return acciones
    return [
        a for a in acciones
        if a.get("nodo") and (es_el_mismo_nodo(a["nodo"], nodo) or es_el_mismo_nodo(a["nodo"], _sin_prefijo_de_fase(nodo)))
    ]


def listar(nodo: str | None = None, producto_key: str | None = None) -> list[dict[str, Any]]:
    """`GET /api/acciones`. Con `producto_key`, cada acción suma `disponible` y `por_que`."""
    acciones = _filtrar_por_nodo(declaradas(), nodo)
    salida: list[dict[str, Any]] = []
    flujo_del_producto = contratos.flujo(producto_key) if producto_key else None
    for accion in acciones:
        fila = publica(accion)
        if flujo_del_producto is not None:
            if not accion.get("habilitada"):
                fila.update(disponible=False, por_que={"motivo": accion.get("motivo")})
            elif accion.get("precondicion") == "nodo_listo":
                situacion = situacion_del_nodo(accion, flujo_del_producto)
                fila.update(
                    disponible=situacion["listo"],
                    por_que={"nodo_actual": situacion["nodo_actual"], "estado": situacion["estado"],
                             "bloqueantes": situacion["bloqueantes"]},
                )
            else:
                fila.update(disponible=True, por_que=None)
        salida.append(fila)
    return salida
