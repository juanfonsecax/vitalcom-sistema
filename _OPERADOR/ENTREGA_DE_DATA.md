# ENTREGA DE DATA — QUÉ ARCHIVO PASO, CADA CUÁNTO Y PARA QUÉ

> **Qué es esto:** el contrato de entrada del sistema. Cinco fuentes, cinco cadencias distintas.
> Creado 2026-09-03 después de verificar las cuatro capas contra archivos reales.
>
> **Regla madre:** la cadencia de cada fuente no se elige por comodidad — se elige por **cada cuánto
> cambia la decisión que esa fuente alimenta**. Pasar Dropi todos los días no mejora nada (la COD
> madura ~10 días); no pasar Meta un día deja ciego el diagnóstico pre-clic de esa jornada.

---

## LA TABLA

| # | Fuente | Archivo que descargás | Cadencia | Sin esto no se puede |
|---|---|---|---|---|
| 1 | **LucidSales** | `report-AYER-AYER.xlsx` (1 solo día) | **DIARIA** — todas las noches | saber si vendiste. Es la ÚNICA fuente de ventas. |
| 2 | **Meta Ads Manager** | `Informe-*.xlsx` nivel **conjunto**, 1 solo día | **DIARIA** — misma corrida que el 1 | separar *"el anuncio no entrega"* de *"el bot no cierra"* |
| 3 | **Dropi — órdenes** | `ordenes_productos_*.xlsx`, rango **60 días móviles** | **SEMANAL** — lunes | saber cuánto de lo vendido llegó a entregarse (y cobrarse) |
| 4 | **Dropi — cartera** | `historial de cartera-*.xlsx` | **SEMANAL** — lunes, junto al 3 | ver la caja real: entradas por ganancia, salidas por devolución |
| 5 | **Banco (Relay)** | `Business-Checking-MES.pdf` | **MENSUAL** — día 1 o 2 | verificar que Meta cobre lo que dice, y cazar cargos nuevos |

> **Bonus ya existente (no cambia):** el **extracto de Facturación de Meta por cuenta** va
> **semanal, domingos**, según `DOCTRINA/DATA_PLAYBOOK.md` §5. Es la capa que responde
> *"¿lo que Meta COBRA = lo que Meta dice que GASTÉ?"*.

---

## POR QUÉ CADA CADENCIA ES ESA

### 1 · LucidSales — DIARIA, y no se puede bajar
Es la única fuente de VENTAS del sistema. De ahí salen el CPA, la ganancia y el ranking por ángulo.
Un día que falta **no es un día con cero ventas**: es un agujero, y la doctrina prohíbe declarar
ganador o matar un conjunto con días 🔴 en la ventana.
**Cumplimiento medido (26-ago → 01-sep): 7 de 7 días. Sin fallas.**

### 2 · Meta Ads Manager — DIARIA, y era el eslabón roto
Mide lo que pasa **antes del clic**: impresiones, clics de enlace, y qué fracción de esos clics se
convirtió en conversación. Sin esta capa, cuando un ángulo vende poco es imposible saber si el
anuncio no está entregando o si el bot no cierra — y ese fue exactamente el límite que frenó a
`etapa-11` con TINNIDROP.

> 🔴 **Lo que se descubrió el 03-sep:** vos venías bajando estos archivos, pero el sistema **no
> tenía cómo cargarlos**. La capa se llenaba sólo por el conector MCP de Meta, y desde que ese
> conector dejó de correr `_FACT_ENTREGA.csv` quedó congelada en el **25-ago**.
> Ya existe `Ads/_TOOLS/ingerir_meta.py`. Cargados los 6 días pendientes, la cobertura de TINNIDROP
> pasó de **53.8 % → 66.2 %** por mensajes y de **72.3 % → 87.3 %** por gasto.

**El export tiene que ser a nivel CONJUNTO y de UN SOLO DÍA.** Un export de varios días se carga
igual, pero no se puede desagregar después y no encadena con la serie diaria.

### 3 y 4 · Dropi — SEMANAL, nunca diaria
Este negocio es **contra entrega**: la venta de hoy se entrega en 2-5 días y se cobra después. Un
export diario de Dropi mide un cohorte inmaduro y **cambia solo** al día siguiente sin que haya
pasado nada nuevo. Con 60 días móviles el cohorte ya maduró y la tasa es estable.
**Verificado:** el export de 593 órdenes (01-jul → 01-sep) da 85.3 % de entrega sobre resueltos, y
el costo real de devolución (Q28.02) salió de 56 cobros del historial de cartera. Los dos archivos
van juntos: uno dice qué pasó con el paquete, el otro qué pasó con la plata.

### 5 · Banco — MENSUAL
Confirma el veredicto, no lo cambia. Sirve para dos cosas concretas:
- **¿Meta cobra de más?** Agosto: cobró **$1,871.89** contra **$1,978.22** de gasto trackeado —
  −5.4 %, que es el desfase normal de cobro (el cargo del 1-sep es gasto de agosto). Sin fuga.
- **¿Apareció un cargo nuevo?** Cada concepto del extracto tiene que existir en `_DIM_GASTOS.csv`.
  En agosto: 0 sin clasificar.

---

## CÓMO SE ENTREGA

Pasar los archivos por ruta, sin renombrarlos. El sistema los carga con:

```bash
python Ads/_TOOLS/ingerir_lucidsales.py --dir ~/Downloads
```

```bash
python Ads/_TOOLS/ingerir_meta.py --dir ~/Downloads
```

Los dos son **idempotentes**: tienen anti-duplicado por llave, hacen backup antes de escribir y
aceptan `--dry-run`. Pasar dos veces el mismo archivo no duplica nada — lo reporta como omitido.

---

## LO QUE FALTA HOY (03-sep-2026)

| Falta | Estado |
|---|---|
| Export de **Meta del 30-ago** | El de LucidSales de ese día sí llegó; el de Meta no. Es el único hueco de la semana. |
| **Export del flujo real de LucidBot** | Gate duro: `1_HACER_MANUAL.txt` declara que no es el bot cargado. Sin esto `etapa-5` no escribe. |
| **Export semanal de conversaciones de LucidBot** | `etapa-11`: *"el input más barato y de mayor retorno pendiente en todo el sistema"*. Sin chats se sabe DÓNDE se pierde la venta, nunca POR QUÉ. |

Las dos últimas son las que valen más. No hay herramienta que las reemplace.
