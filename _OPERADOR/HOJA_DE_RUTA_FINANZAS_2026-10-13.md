# Hoja de ruta — cierre de finanzas y separación GT/CO (para el ejecutor)

Repositorio: `C:/Users/juand/Downloads/AGENTES LUCID/Profesional en Eccomerce gestion/SISTEMA`, rama `main`.
Contexto completo de lo ya hecho: `odd/tasks/dashboard-finanzas-mensual.md` (T1–T8 cerradas). Leelo
entero antes de empezar, junto con `CLAUDE.md` y `DOCTRINA/CONTABILIDAD.md`.

## Reglas para el ejecutor (no negociables)

1. **Python:** siempre `~/AppData/Local/Python/bin/python`. Nunca `python` del PATH (cae a un venv sin scipy).
   Tests del backend: `app/backend/.venv/Scripts/python -m pytest` desde `app/backend`.
   Frontend (desde `app/frontend`): `npx vitest run`, `npx tsc -b`, `npx vite build`.
2. **Git:** no cambiar de rama, no `git stash`, no `git add -A`. Agregar solo los archivos de la tarea.
   Hay archivos modificados de otras sesiones (`PRODUCTOS/*.csv`, `VISTAS/*`): no tocarlos ni revertirlos.
   Commits en inglés, Conventional Commits, **sin** líneas "Co-Authored-By" ni firmas de IA. No hacer push.
3. **TDD:** escribir el test primero, correrlo y ver que falla, recién ahí implementar y ver que pasa.
4. **CSV:** siempre con `csv.DictWriter` / `csv.writer`, nunca a mano. Un comando que solo mira no escribe:
   escribir exige `--escribir`.
5. **Fórmula única:** todo número del P&L sale de `gen_pl.calcular_vista_a`. No duplicar fórmulas.
6. **Falla conocida del entorno (ignorar):** los tests de `Ads/_TOOLS` corridos con pytest muestran un ítem
   extra que falla con `OSError: [WinError 6]`. Correrlos también con
   `~/AppData/Local/Python/bin/python -m unittest <modulo>` y reportar ese resultado.
7. **Código y textos de pantalla en español neutro**, como los archivos vecinos. Sin notas con fechas e
   historias de incidentes dentro del código: solo la regla vigente.
8. **Si algo no está claro o hay que decidir algo de negocio: parar y preguntar al operador.** No adivinar.
9. Al terminar cada tarea: marcarla en `odd/tasks/dashboard-finanzas-mensual.md` con el hash del commit y
   lo verificado, y reportar `<comando>: <resultado observado>`.

---

## TAREA 1 — Tasa de cambio hacia atrás (decisión ya tomada)

**Qué:** hoy un mes sin transferencias anteriores usa la tasa fija 7.62, que subestima la pauta (la tasa
real medida es 7.9079). Regla nueva en `Ads/_TOOLS/tasa_fx.py`: si un mes no tiene transferencia en su
ventana ni ninguna anterior, usa la **primera transferencia posterior** conocida, con regla
`PRIMERA_POSTERIOR`. Solo si no existe ninguna transferencia, usa el parámetro (`PARAMETRO`).

**Pasos:**
1. Test en `Ads/_TOOLS/test_tasa_fx.py`: mes sin transferencias previas y una posterior → tasa de la
   posterior, regla `PRIMERA_POSTERIOR`. Sin transferencias → `PARAMETRO`. Verlo fallar.
2. Implementar en `tasa_fx.py`. Agregar `PRIMERA_POSTERIOR` donde se listan las reglas (backend y
   frontend, si muestran el nombre de la regla).
3. Actualizar el párrafo de la regla en `DOCTRINA/CONTABILIDAD.md` (solo la regla vigente).

**Verificación:** `~/AppData/Local/Python/bin/python Ads/_TOOLS/gen_pl_mensual.py --mercado GT --json`
→ julio, agosto y septiembre con tasa ≈ 7.9079 y regla `PRIMERA_POSTERIOR`. Neto de septiembre ≈ Q630
menor que antes (era Q8,547.67). Tests: `test_tasa_fx`, `test_gen_pl`, `test_gen_pl_mensual`,
backend `tests/test_finanzas_mensual_api.py`, `vitest`.

**Commit:** `feat(finanzas): price months before the first transfer with the first later rate`

---

## TAREA 2 — Leer el export CSV de Mercury

**Necesita del operador:** el CSV de transacciones de Mercury (septiembre y octubre). Si todavía no está,
saltar a la Tarea 4 y volver después.

**Qué:** `Ads/_TOOLS/ingerir_banco.py` hoy lee PDFs de Relay. Agregar `--banco MERCURY` que lea el CSV de
Mercury y escriba en `PRODUCTOS/_FACT_BANCO.csv` con las mismas columnas, llenando `tarjeta` con los
últimos 4 dígitos de la tarjeta de cada cargo.

**Pasos:**
1. Abrir el CSV real y anotar sus columnas exactas (fecha, descripción, monto, estado, tarjeta). **No
   suponer los nombres de columna.**
2. Solo movimientos con estado completado/settled. Los `Failed` y `Pending` no entran (reportar cuántos
   quedaron fuera).
3. Fixture sintético mínimo en el test (sin datos personales reales) con un cargo de Facebook, un
   depósito y un cargo fallido. Ver fallar, implementar, ver pasar.
4. Re-ingerir el mismo archivo debe dejar `_FACT_BANCO.csv` idéntico (idempotente).
5. Correr con `--escribir` sobre el archivo real.
6. Correr `Ads/_TOOLS/registrar_transferencia_fx.py` (sin `--escribir` primero) y confirmar que el
   depósito de USD 11,381 empareja con el retiro de cartera 6450689 (Q90,000). Si empareja, correr con
   `--escribir` para completar la fecha de llegada.

**Verificación:** el total de cargos a Facebook por mes en Mercury cuadra con lo que muestra la app.
`test_ingerir_banco`, `test_tasa_fx`.

**Commit:** `feat(finanzas): ingest Mercury transactions with the card of each charge`

---

## TAREA 3 — Tarjeta → mercado (separar Guatemala y Colombia)

**Necesita del operador:** qué tarjeta de Mercury paga qué cuenta publicitaria y de qué mercado es.
Tarjetas vistas: ••0237, ••9736, ••4232 (Facebook) y ••9282 (LucidBot).

**Qué:** nuevo `PRODUCTOS/_DIM_TARJETAS.csv` con columnas
`banco,tarjeta,mercado,uso,cuentas_publicitarias,confirmado_por,fecha,notas` (`mercado` = GT | CO | COMPARTIDO).
En `gen_pl_mensual.py`, los cargos del banco con tarjeta conocida se asignan a su mercado. Los de tarjeta
sin fila en la dimensión salen en `faltantes`, nunca se reparten por adivinanza. Los de Relay (sin tarjeta)
siguen como hoy.

**Pasos:**
1. Test: un cargo de Facebook con tarjeta de CO no aparece en el P&L de GT; uno con tarjeta desconocida
   sale en `faltantes`. Ver fallar, implementar, ver pasar.
2. Llenar `_DIM_TARJETAS.csv` solo con lo que confirme el operador.
3. Ver con `--mercado CO` que Colombia ya muestra lo que cobró el banco a sus tarjetas.

**Commit:** `feat(finanzas): assign bank charges to a market by card`

---

## TAREA 4 — Cuentas publicitarias de Colombia en la contingencia

**Necesita del operador:** los IDs de las cuentas publicitarias nuevas de Colombia, y que les dé acceso al
usuario del sistema (System User con permiso de solo lectura `ads_read`) para que
`bajar_meta_insights.py` pueda leerlas.

**Pasos:**
1. Agregar cada cuenta nueva en `PRODUCTOS/_DIM_CUENTAS.csv`, siguiendo el formato de las filas
   existentes, con su mercado CO y su moneda.
2. Correr `~/AppData/Local/Python/bin/python Ads/_TOOLS/bajar_meta_insights.py --dry-run` y confirmar que
   las cuentas nuevas aparecen sin error. Si dice que no tiene acceso, parar y avisar al operador.
3. Confirmar en `Ads/_TOOLS/mercado.py --producto <PRODUCTO_CO>` que los productos de Colombia apuntan a
   las cuentas nuevas.
4. No crear campañas ni tocar Meta: publicar es otra skill y requiere confirmación del operador.

**Commit:** `chore(cuentas): register Colombia ad accounts in the contingency setup`

---

## TAREA 5 — Suite completa del backend

**Qué:** la suite completa del backend nunca terminó en esta sesión (tarda mucho). Correrla con tiempo largo
y separar lo que falla.

**Pasos:**
1. `app/backend/.venv/Scripts/python -m pytest tests -q -x --timeout=0` desde `app/backend`
   (si `--timeout` no existe, quitarlo). Dejarla correr hasta el final.
2. Para cada falla, revisar si también falla en el commit `5e59c38` (anterior a todos estos cambios) con
   `git worktree add --detach <carpeta temporal> 5e59c38`. Borrar el worktree al terminar.
3. Si una falla es nueva, arreglarla con su test. Si ya fallaba antes, solo listarla.
4. Fallas ya conocidas que no son de esta línea de trabajo: `db/test_db.py` (columna
   `voz_cliente.producto_key` en el Postgres local, viene de otra sesión). Solo reportar.

**Commit (solo si hubo arreglos):** `fix(app): <lo que se arregló>`

---

## Al terminar todo

Reportar al operador en pocas líneas:
- qué tareas quedaron hechas, con sus commits;
- la tabla de `gen_pl_mensual.py --mercado GT --json` (mes, neto, pauta USD, tasa, regla);
- lo que quedó esperando datos del operador.

No hacer push: lo decide el operador.
