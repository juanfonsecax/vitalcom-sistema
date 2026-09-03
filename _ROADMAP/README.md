# _ROADMAP — decisiones pendientes (NO se carga en ninguna sesión)

> **Qué es esta carpeta:** el backlog. Ideas y análisis que **todavía no son parte del sistema**.
> Ningún agente lee esto. Nada de acá está implementado — si estuviera, viviría en su archivo dueño.
>
> **Regla:** cuando algo de acá se implementa, se **mueve a `_ARCHIVO/roadmap_cumplido/`** el mismo día.
> Un plan cumplido que se queda acá hace parecer pendiente algo que ya está hecho.

---

## Lo que queda abierto (2 archivos)

### `MEJORAS_FUTURAS.txt` — bitácora de ideas
Backlog personal del operador: variaciones, experimentos e ideas sueltas. Sin fecha de vencimiento.

### `ANALISIS_MENTOR_JULI_vs_SISTEMA_2026-07-03.md` — decisión pendiente
Contraste del sistema contra 3 transcripciones del mentor "Juli" (moda/dropshipping con IA).
Su cabecera lo dice: **"SOLO ANÁLISIS — nada implementado. Decisión de qué se implementa queda para Juan."**

Su propuesta principal (**P1 — pipeline de video UGC con IA**) sigue viva y conectada a dos cosas:
- `PLANTILLAS_VIDEO_IA.md` (acá, movido de la raíz el 2026-09-03) — **BORRADOR, NO INTEGRADO AL FLUJO**; ninguna etapa lo lee. Vive en `_ROADMAP/` porque eso es lo que es: backlog no implementado. En la raíz aparecía como huérfano en cada auditoría.
- La idea de extender la DOCTRINA DE CREATIVOS: que un ángulo virgen pueda salir como **VIDEO-IA** en vez de caer automático a IMAGEN — lo que atacaría el "confound de formato" documentado en `PLANTILLAS_ADS.md`.

**Para cerrarlo hay que decidir una cosa:** si se hace el piloto (1 producto, el ángulo ganador, medir CPA de video-IA vs imagen). Si sale que sí, se cablea a `PLANTILLAS_ADS.md` + `etapa-4` + `etapa-6` y este archivo se archiva. Si sale que no, se archiva igual.

---

## Archivado el 2026-09-02

| Archivo | Por qué se archivó |
|---|---|
| `ANALISIS_MENTOR_CALET_115_vs_SISTEMA_2026-08-21.md` | **Implementado.** La arquitectura de 3 fases vive en `CALENDARIO_ESCALADO.md` §1.7 y `.claude/agents/ETAPA-6.md`; la banda de edad en `ETAPA-6.md` → BANDA DE EDAD; la fábrica y el lector en `ETAPA-9.md`/`ETAPA-10.md`; la doctrina de origen quedó indexada en `_CONOCIMIENTO/MATRIZ_METODOLOGIA.md`. Lo único que **no** se implementó de ese documento es la `etapa-11` (optimizador de flujo) — sigue como brecha abierta en el choque C-10 de la matriz. |

## Archivado el 2026-08-01 (ya cumplido, en `_ARCHIVO/roadmap_cumplido/`)

| Archivo | Por qué se archivó |
|---|---|
| `PLAN_EXPANSION_MCP.txt` (56 KB, may-2026) | El MCP ya está en producción: `MCP_PLAYBOOK.md`, `etapa-6` crea campañas, `etapa-7` lee métricas. |
| `ANALISIS_SISTEMA_Y_PLAN_MCP_2026-06-21.md` | Era "plan aprobado para revisión, sin tocar archivos". Ya se ejecutó. |
| `REVISION_CRITICA_SISTEMA_2026-06-22.md` | Snapshot del 22-jun. Describe estructuras que ya no existen (`NusavaB12_CONTEXTO.txt`, `_ENTREGABLES.txt`, `skill pro/`), precios viejos (Q219/339/449) y el presupuesto $1.59 hoy deprecado. |
| `AUDITORIA_ETAPA-5_vs_LUCIDBOT.md` | Auditoría del 27-jun; `ETAPA-5.md` se actualizó después (10-jul). |
