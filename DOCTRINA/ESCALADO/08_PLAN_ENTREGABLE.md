## 7. FASE 3 — ENTREGABLE FIJO: `PRODUCTOS/[NOMBRE]/4_PLAN_ESCALADO.txt`

> El escalado necesita archivo y plantilla fija, igual que FASE 1: sin eso cada plan sale distinto.
> Historia: `_CONOCIMIENTO/POSTMORTEMS/ESCALADO_PLAYBOOK_historias.md` §7.

**ESQUEMA DE ARCHIVOS POR PRODUCTO (fijo, no cambia entre productos):**
| Archivo | Rol | Cuándo se crea |
|---|---|---|
| `1_HACER_MANUAL.txt` | lo que el operador ejecuta a mano (bot, prompts, copies, checklist) | FASE 1 |
| `2_DATA_PRODUCTO.txt` | memoria del producto (costeo, ángulos, avatar, resultados) | FASE 1 |
| `3_CAMPAÑA_META.txt` | llave técnica: IDs de campaña/conjuntos/anuncios/creativos y Post IDs | al crear por MCP |
| **`4_PLAN_ESCALADO.txt`** | **el plan de FASE 3** — se SOBRESCRIBE en cada ciclo de escalado | al declarar ganador |

⚠️ El slot `3_` es **solo** para IDs de Meta. Nunca meter ahí el plan de escalado (historia:
`_CONOCIMIENTO/POSTMORTEMS/ESCALADO_PLAYBOOK_historias.md` §7).

**PLANTILLA OBLIGATORIA de `4_PLAN_ESCALADO.txt`** (ETAPA-8 la llena; se sobrescribe, no se acumulan versiones):
```
[PRODUCTO] · PLAN DE ESCALADO FASE 3 · v[N] · [FECHA]
Cuenta madre · página · tasa · CPA Base Q.. · Break-Even Q..
CPA real semanal (LucidSales, del _FACT_VENTAS.csv) · integridad de ventana: X/7 días

0. VEREDICTO EN UNA LÍNEA: [escalar fuerte / escalar suave / solo renovar creativo / no escalar aún]
1. MATRIZ ÁNGULO × CUENTA (§5) — con clasificación VIAJA / LOCAL / MURIENDO y cuentas saturadas
2. APAGAR — lista exacta [campaña → conjunto] con gasto, ventas y motivo (conversación / ventas-tras-PD / sobre BE)
3. MATRIZ DE DUPLICACIÓN (§6) — tabla con ×N por cuenta + ventas y gasto proyectados + neto
4. SURFING +20% — a qué conjuntos, mañana 9-10 AM
5. POST ID / PUBLICACIÓN EN PÁGINA — IDs vigentes por ángulo ganador
6. CREATIVOS (§4) — el POR QUÉ ganó + brief de 3-5 conceptos nuevos para ETAPA-4
6b. BANCO DE MICROÁNGULOS (ETAPA-3, PASO 0 de fase-3-escalado) — los 8-12 MICROÁNGULOS del
    ángulo ganador con su frase de apertura, tal como los entregó ETAPA-3 (banco de copy de la
    expansión horizontal). Este bloque es lo que `flujo.py` verifica en `F3.plan` (T8-4,
    23-sep-2026): sin él, el output de ETAPA-3 no queda con ningún consumidor visible en disco.
7. PRECIO — subir gradual / mantener
8. ORDEN DE EJECUCIÓN — checklist numerado con [ ] para tildar
9. QUÉ APRENDIMOS — lo que NO volver a probar en este producto
```

**REGLAS DEL ENTREGABLE:**
- Se **sobrescribe** en cada ciclo y sube `v[N]`. Prohibido dejar `_V2`, `_SIMULACION`, `_COPIA` sueltos (misma regla que FASE 1).
- Todo número de VENTA sale de `PRODUCTOS/_FACT_VENTAS.csv` (la única que suma al P&L), nunca de una auditoría en prosa. Las señales de entrega (mensajes/clics/CPM) salen de `_FACT_ENTREGA.csv` y **no se suman al gasto** — reglas de lectura en `DOCTRINA/DATA_PLAYBOOK.md` §3.
- Si la ventana tiene días 🔴 en `_BITACORA_DATA.txt` → el plan se marca **PARCIAL** y no se declara ganador oficial ni se manda matar por ventas.
- El plan cierra actualizando `_GANANCIAS.txt` con el neto proyectado del movimiento.

---

