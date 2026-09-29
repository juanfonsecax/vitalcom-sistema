"""El mercado de cada producto viaja en la API: mercado, moneda_local y simbolo (D1 multi-mercado).

La app no resuelve nada por su cuenta: usa `Ads/_TOOLS/mercado.py`. Un producto sin mercado NO se
sirve con un valor por defecto: la API responde 503 diciendo qué falta.
"""

from __future__ import annotations

import csv


def _csv(base, nombre):
    with (base / "PRODUCTOS" / nombre).open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def test_la_lista_trae_mercado_moneda_local_y_simbolo(cliente, base_declarada):
    mercados = {m["mercado"]: m for m in _csv(base_declarada, "_DIM_MERCADOS.csv")}
    filas = {f["producto_key"]: f for f in _csv(base_declarada, "_DIM_PRODUCTOS.csv")}
    servidos = cliente.get("/api/productos").json()
    assert servidos
    for producto in servidos:
        esperado = mercados[filas[producto["producto_key"]]["mercado"]]
        assert producto["mercado"] == filas[producto["producto_key"]]["mercado"]
        assert producto["moneda_local"] == esperado["moneda"]
        assert producto["simbolo"] == esperado["simbolo"]
    por_clave = {p["producto_key"]: p for p in servidos}
    assert por_clave["OVULOS_PURITY"]["moneda_local"] == "COP"
    assert por_clave["TINNIDROP"]["moneda_local"] == "GTQ"
    # `moneda` sigue siendo la de la cuenta publicitaria, no la de venta.
    assert por_clave["TINNIDROP"]["moneda"] == filas["TINNIDROP"]["moneda"]


def test_el_detalle_trae_el_mercado_del_producto(cliente_juguete):
    detalle = cliente_juguete.get("/api/productos/TINNIDROP")
    assert detalle.status_code == 200, detalle.text
    cuerpo = detalle.json()
    assert (cuerpo["mercado"], cuerpo["moneda_local"], cuerpo["simbolo"]) == ("GT", "GTQ", "Q")


def test_los_mercados_salen_con_su_perfil(cliente):
    perfiles = {m["mercado"]: m for m in cliente.get("/api/mercados").json()}
    assert perfiles["GT"]["moneda"] == "GTQ" and perfiles["GT"]["persona"] == "voseo"
    assert perfiles["CO"]["moneda"] == "COP" and perfiles["CO"]["registro_sanitario"] == "registro INVIMA"
    assert perfiles["GT"]["tasa_moneda_por_usd"] and perfiles["CO"]["tasa_moneda_por_usd"]


def test_un_producto_sin_mercado_no_se_sirve_con_un_default(cliente_juguete, sistema_de_juguete):
    ruta = sistema_de_juguete / "PRODUCTOS" / "_DIM_PRODUCTOS.csv"
    with ruta.open(encoding="utf-8", newline="") as fh:
        filas = list(csv.DictReader(fh))
    filas[0]["mercado"] = ""
    with ruta.open("w", encoding="utf-8", newline="") as fh:
        escritor = csv.DictWriter(fh, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)
    for url in ("/api/productos", "/api/productos/TINNIDROP"):
        respuesta = cliente_juguete.get(url)
        assert respuesta.status_code == 503, (url, respuesta.text)
        assert "mercado" in respuesta.text
