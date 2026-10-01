# Hoy agrupado + anuncios→checklist (mejoras visuales v3)

Estado: EN CURSO — rama `feat/dashboard-visual` (11 commits previos) · base verificada: 111/111 Vitest · 15/15 Playwright · build limpio
Espejo Engram: PENDIENTE (runtime actual sin herramientas mem_*; reintentar al cierre de sesión)

## Objetivo

Dos pedidos del operador sobre usabilidad, sin tocar lógica de datos:

1. **Hoy**: las tarjetas de estado de la cabina deben llevar a su grupo; la lista de
   órdenes pasa de grilla mixta a secciones rotuladas por estado (Pausar / Escalar /
   Renovar / Midiendo), con identidad de color por estado.
2. **Fase 1 · Anuncios**: el bloque «falta la pieza» pasa de texto plano a botón que
   lleva al tab Checklist y resalta el input exacto del archivo a subir. El preview de
   imagen/video ya existía (`pieza.url`) y se conserva.

## Diagnóstico (por qué «no salían» los ESCALAR)

Los 2 ESCALAR (CLEARSTEM, NUSAVA) SÍ están en `_DECISIONES.json` y SÍ se pintan en la
lista. Ambos traen `bloqueo_fase` (celda rentable pero producto en F2: no mover plata
en pleno testeo, invariante 6), y por diseño la celda bloqueada se pinta ámbar
(«Escalar bloqueado por fase»), no verde. El operador no los reconocía. La solución es
agrupación rotulada + navegación desde la cabina; el ámbar de bloqueo SE CONSERVA (es
metodología, regla 5 de la sesión).

## Fuera de alcance

- **F3=optimización de flujo / F4=escalado** (doctrina): requiere tocar
  `DOCTRINA/FLUJO.json` (no hay fase F4 declarada), `Ads/_TOOLS/flujo.py`
  (`TOKEN_FASE` llega a 3), `CLAUDE.md`, `.claude/agents/ETAPA-*.md`, skills
  `fase-3-escalado`, backend y plumbing de tabs del frontend. PENDIENTE DE PERMISO
  EXPLÍCITO del operador (se pregunta al cierre de este bloque).
- **«Ads funcionando»** (estado Meta ACTIVO/PAUSADO por anuncio): la API no lo entrega
  → pendiente de backend, no se pinta a mano (regla 5).
- No se cambia qué datos se piden a la API ni la lógica de aparición; no se toca
  backend; commits solo de `app/frontend`.

## Tareas

- [x] T1. `Hoy.tsx`: secciones por estado con id `seccion-<ESTADO>` (orden
  PAUSAR→ESCALAR→RENOVAR), header con badge de color del estado + conteo; «Siguen
  midiendo» colapsado pasa a controlado con id `seccion-MIDIENDO`. (delegado: writer)
- [x] T2. `Hoy.tsx`: `TarjetaResumen` acepta `alHacerClick` → botón con scroll suave al
  grupo; la tarjeta Midiendo también abre el colapsado. Tests nuevos en
  `pruebas/hoy.test.tsx`. (delegado: writer)
- [x] T3. `Fase1.tsx`: botón «Subirla en el Checklist» en el bloque «falta la pieza» con el
  archivo declarado; al llegar, scroll + resaltado (ring ámbar) del input exacto
  (`Subir archivo para <archivo>`). Test en `pruebas/fase1.test.tsx`. (delegado: writer)
- [x] T4. Verificación: Vitest 114/114 (3 nuevos), `pnpm build` limpio, Playwright 15/15,
  assess del diff tier medio (inflado por data sucia del sistema, no por el cambio).
- [ ] T5. Reporte al operador + pregunta de permisos para F4.

## Criterios de aceptación

- Click en «2 Escalar» baja suavemente al grupo Escalar; «3 Renovar» al suyo;
  «3 Midiendo» abre el colapsado y baja hasta él.
- La lista muestra grupos rotulados por estado; los ESCALAR bloqueados conservan el
  ámbar y su nota de fase plegada.
- En Fase 1, cada anuncio sin pieza tiene un botón que cambia al tab Checklist y
  resalta el input del archivo declarado; tras subir, el preview aparece en Anuncios
  (refetch existente).
- Vitest verde (≥111), Playwright 15/15, build limpio.

## Progreso / evidencia

- T1+T2 → commit `15b1482` feat(ui): group day orders by state and let summary cards jump
  to them (Hoy.tsx + hoy.test.tsx, 153+/34-).
- T3 → commit `3ec6147` feat(ui): jump from missing ad piece to its checklist upload row
  (Fase1.tsx + fase1.test.tsx, 148+/9-).
- Verificación: Vitest 114/114 · `pnpm build` limpio · Playwright 15/15. RDD off; sin
  ciclo de review nativo.
- T5: reporte al operador entregado; queda la pregunta abierta de permisos para F4
  (doctrina: F3=optimización de flujo, F4=escalado).
