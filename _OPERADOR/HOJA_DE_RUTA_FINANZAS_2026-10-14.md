# Hoja de ruta — tarjetas por BM y Colombia en AMG 3 (para el ejecutor)

Sigue a `_OPERADOR/HOJA_DE_RUTA_FINANZAS_2026-10-13.md`: **sus reglas para el ejecutor siguen vigentes**
(Python del sistema, sin stash ni cambio de rama, TDD, commits sin firma de IA, no push). Esta hoja
**reemplaza** los valores de tarjetas que se te pasaron ayer.

Ya hecho por el orquestador: cartera de Dropi de julio y agosto cargada (`7c68368`). No la vuelvas a cargar.

---

## TAREA A — Dimensión tarjeta → BM → mercado

Archivo nuevo `PRODUCTOS/_DIM_TARJETAS_MERCADO.csv` (NO reescribir `_DIM_TARJETAS.csv`: lo regenera
`conciliar_facturacion.py`). Columnas:
`banco,ultimos4,bm,mercado,uso,cuentas_publicitarias,estado,confirmado_por,fecha,notas`
(`cuentas_publicitarias` separadas por `|`).

Filas confirmadas por el operador el 2026-10-14 (una tarjeta por BM):

| banco | ultimos4 | bm | mercado | uso | cuentas_publicitarias | estado |
|---|---|---|---|---|---|---|
| MERCURY | 4232 | AMG 2 | GT | PAUTA | GTR0\|GTR1\|GTR2\|GTR18 | ACTIVA |
| MERCURY | 9736 | AMG 5 | GT | PAUTA | GTR7 | ACTIVA |
| MERCURY | 0237 | AMG 9 | GT | PAUTA | GTR13\|GTR14\|GTR15\|GTR16\|GTR17 | ACTIVA |
| MERCURY | 9893 | AMG 3 | CO | PAUTA | GTR3\|GTR9\|GTR10 | ACTIVA |
| MERCURY | 1077 | AMG 4 | SIN_USO | PAUTA | GTR4\|GTR5 | RESERVA |
| MERCURY | 2190 | AMG 8 | SIN_USO | PAUTA | GTR11\|GTR12 | RESERVA |
| MERCURY | 9282 |  | COMPARTIDO | SOFTWARE |  | ACTIVA |

- Nota del operador: la cuenta que dijo "G18" se registra como `GTR18`. Si en `_DIM_CUENTAS.csv` existe con
  otro alias, usar ese y avisar.
- AMG 1 está en pesos y no se usa: no lleva fila.
- Tarjetas viejas vistas fallando en Mercury Credit (••2479, ••8931, ••1193, ••2187, ••4895, ••1766): fila
  con `estado = MUERTA`, `mercado` vacío, `notas = "cargos fallidos en Mercury Credit sep-oct 2026"`.
  ••4895 es la de Anthropic y ••2187/••1766 las de LucidBot: `uso = SOFTWARE`.
- Test: el archivo carga, cada `ultimos4` es único, `mercado` ∈ {GT, CO, COMPARTIDO, SIN_USO, ""}.
- Una línea en `DOCTRINA/DATA_PLAYBOOK.md` donde se listan las dimensiones.

**Commit:** `chore(finanzas): card to BM and market dimension`

---

## TAREA B — Colombia en AMG 3

1. En `PRODUCTOS/_DIM_CUENTAS.csv`, revisar GTR3 (id `581490137794343`, USD, ya accesible por MCP y por
   `bajar_meta_insights.py`) y, si existen, GTR9 y GTR10. Marcarlas con mercado CO siguiendo el formato de
   las filas existentes. Si GTR9/GTR10 no tienen fila, **no inventar sus IDs**: dejarlas fuera y avisar.
2. Correr `~/AppData/Local/Python/bin/python Ads/_TOOLS/bajar_meta_insights.py --dry-run` y confirmar que
   GTR3 sigue leyéndose sin error.
3. Buscar dónde decide el sistema la cuenta de un producto de Colombia (`Ads/_TOOLS/mercado.py`,
   `cargar_cuenta.py`, `_DIM_PRODUCTOS.csv` columna `cuenta_alias`). **Solo reportar** qué habría que cambiar
   para pasar OVULOS_PURITY y GAFAS a GTR3. No cambiarlo: mover un producto vivo de cuenta es decisión del
   operador y tiene su propio camino (`cargar_cuenta.py`, eventos, alias).

**Commit (si cambió `_DIM_CUENTAS.csv`):** `chore(cuentas): assign AMG 3 accounts to Colombia`

---

## TAREA C — Mercury (cuando el operador pase el CSV)

Igual que la Tarea 2 de la hoja anterior, con estas reglas extra que ya se conocen:
- Mercury tiene dos tipos de cuenta en el export: `Checking ••6842` / `Checking ••4742` (débito) y
  `Mercury Credit` (crédito). Guardar en `_FACT_BANCO.csv` cuál es (`cuenta`).
- Excluir `Failed` y `Pending`; reportar cuántos.
- **No son gasto:** `Transfer In`, `Transfer Out`, `Credit Account Payment`, `Credit Cashback Deposit`
  (movimientos entre cuentas propias). Marcarlos como `tipo = INTERNO`.
- `Dropi … ACH In` = llegada de un retiro de cartera de Dropi: `tipo = ENTRADA`, lo empareja
  `registrar_transferencia_fx.py`.
- `Intl. Transaction Fee` = comisión bancaria: entra como gasto con su propia clasificación en
  `_DIM_GASTOS.csv` (`NEGOCIO_FIJO`, categoría `comision_bancaria`, mercado COMPARTIDO).
- Cada cargo de Facebook se asigna a mercado con `_DIM_TARJETAS_MERCADO.csv` (Tarea A).

**Commit:** `feat(finanzas): ingest Mercury transactions with the card of each charge`

---

## TAREA D — Julio sin extracto de Relay

El operador confirmó que en julio no usaba Relay. El aviso de `faltantes` de julio en
`gen_pl_mensual.py` hoy pide "cargá el extracto": cambiarlo para que diga que julio se pagó por otro medio
y que los gastos fijos de julio no están medidos. Regla: un parámetro en `_PARAMETROS_FINANZAS.csv`
(`banco_desde = 2026-08-01`); antes de esa fecha el faltante es informativo, no un pedido.

**Commit:** `fix(finanzas): July had no Relay statement to ask for`

---

## Al terminar

Marcar en `odd/tasks/dashboard-finanzas-mensual.md` lo hecho (con hash y verificación), reportar en
pocas líneas y parar. Lo que queda esperando al operador: el CSV de Mercury (Tarea C).
