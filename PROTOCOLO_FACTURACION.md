# PROTOCOLO DE FACTURACIÓN — QUÉ PASAR, CUÁNDO Y CÓMO

> Creado 16-ago-2026 a pedido del operador. Responde: *"¿qué exactamente te paso para que esto corra siempre igual?"*
> Dueño de la doctrina de data: `DATA_PLAYBOOK.md` → "CAPA DE FACTURACIÓN". Este archivo es **solo el checklist de entrega**.

---

## LA REGLA DE ORO

**Extracto > pantallazo.** Un pantallazo se lee bien pero **nunca prueba que esté completo**.
El 16-ago los pantallazos de Nu cubrían 7 de 15 días y aun así destaparon Q1,600 de gasto no registrado — imaginate lo que falta en los 8 días que no se veían.
Si la app deja exportar (CSV/Excel/PDF), **siempre exportar**. El pantallazo es el plan B, no el plan A.

---

## CADA DOMINGO (la corrida semanal)

| # | Qué | De dónde | Formato ideal | Para qué sirve |
|---|---|---|---|---|
| 1 | **Extracto de Facturación de Meta**, una por cuenta (las 6) | Administrador comercial → Facturación → Transacciones | CSV o captura completa | Es lo ÚNICO que dice **qué tarjeta pagó cada cargo** y cuál fue **rechazado**. Sin esto no hay conciliación. |
| 2 | **Saldo "gastado sin facturar"** de cada cuenta | misma pantalla, arriba | un número por cuenta | Es lo que hace **cerrar la ecuación** y lo que convierte la conciliación de la semana siguiente en una verificación real |
| 3 | **Export de Relay** (transacciones de la semana) | Relay → Receipts / Transactions | CSV | Relay **ya etiqueta cada cargo con su BM** (AMG2 · Amg 8 · Amg 9 · Gtr7). Resuelve solo el mapa tarjeta→BM |
| 4 | **Export de Ads Manager nivel conjunto** de **GTR13** y **CP1** | Ads Manager → exportar | CSV/xlsx | Son las 2 cuentas **sin MCP**. Concentran casi toda la fuga de cobertura |
| 5 | **Export de LucidSales** de cada día que falte | LucidSales → Métricas de Facebook Ads | xlsx, **1 día por archivo** | El P&L. Nunca agregado: un agregado no se descompone |

## CADA MES (el cierre)

| # | Qué | Para qué |
|---|---|---|
| 6 | **Extracto bancario completo** — Nu (COP) y el de las tarjetas USD | Verifica que lo que Meta dice que cobró **salió de verdad de tu plata**, y mide la tasa COP real |
| 7 | **Export de órdenes de Dropi** (xlsx con PRECIO FLETE / PROVEEDOR / ESTATUS) | Refresca tasa de entrega y fletes |

---

## SI TIENE QUE SER PANTALLAZO — EL MÉTODO DEL SOLAPE

El método que usó el operador el 16-ago **es correcto y se conserva** (APR-046):

> En cada captura, la **última fila** de la pantalla anterior aparece repetida como **primera** de la siguiente. Eso prueba que no quedó ningún movimiento en el hueco entre capturas.

Cómo se deduplica sin romper nada:

- ✅ **Por el código del cargo** (`Facebk *Grdauyd4n2`). Es único por transacción y aparece literal en el banco. Deduplicación exacta, riesgo cero.
- ✅ En Relay, por (fecha + monto + **etiqueta de cuenta** + comercio) — Relay no muestra código.
- 🔴 **NUNCA por (fecha, monto) a secas.** Dos cargos legítimos pueden coincidir en ambos y se borraría uno real.

**Lo que sí o sí debe verse en la captura:** fecha · monto · **de qué cuenta/BM es** · y —si el banco lo muestra— el código del cargo. Si la captura corta la etiqueta de cuenta, el cargo entra como `POR_ATRIBUIR` y no se puede usar para conciliar.

**No hace falta** que digas a mano a qué tarjeta o BM corresponde cada cargo: Relay ya lo etiqueta y el extracto de Meta también. Decirlo a mano es justo el camino que llevó al error del 15-ago (US$117.88 atribuidos a una cuenta fantasma, APR-030).

---

## LO QUE SE ESCRIBE CON ESO

| Archivo | Qué guarda |
|---|---|
| `_FACT_FACTURACION.csv` | un cargo por fila (COBRO · RECHAZO · CREDITO · **COMISION_FX**), llave = código de Meta |
| `_FACT_SALDOS.csv` | saldo sin facturar por cuenta y corte — `estado=OBSERVADO` |
| `_DIM_TARJETAS.csv` | tarjeta → BM, salud (cobros OK / rechazos / veredicto). **Se autocompleta** |
| `_DIM_BM.csv` | Business Manager → cuentas publicitarias |
| `_FACT_PAUTA_REAL.csv` | gasto trackeado vs gasto real, por cuenta |

Y se corre: `python Ads/_TOOLS/conciliar_facturacion.py [ini] [fin]`

---

## LO QUE YA SABEMOS Y NO HAY QUE VOLVER A DISCUTIR

1. **Meta no cobra por día ni por rango.** Cobra al cruzar umbrales acumulados. Comparar "gasté del 1 al 15" contra "me cobraron del 1 al 15" **siempre** descuadra y no es sobrecobro (APR-025).
2. **La tarjeta es de un Business Manager, no de una cuenta.** Un BM puede tener 3 cuentas y su tarjeta paga cualquiera (APR-040).
3. **La comisión de cambio del Nu es 0.45% fijo** de cada cargo, y nunca estuvo en el P&L (APR-044).
4. **El riesgo grande no es que Meta cobre de más** — es el gasto que Meta cobra y el P&L no ve, porque *infla* la ganancia en vez de bajarla (APR-042).
5. **Una ecuación que cierra con un parámetro despejado de ella misma no prueba nada** (APR-041).
