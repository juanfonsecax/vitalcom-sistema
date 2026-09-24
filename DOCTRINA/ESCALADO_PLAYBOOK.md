# ESCALADO_PLAYBOOK — ÍNDICE (T2 p2-simplificacion, 24-sep-2026)

> Este archivo dejó de llevar la doctrina completa: es un ÍNDICE. El texto original (verbatim, sin
> reescribir ni una palabra) vive partido por sección en `DOCTRINA/ESCALADO/`, un archivo por
> encabezado `##` del documento original — así cada consumidor cita solo el archivo de la sección
> que usa, en vez de heredar el playbook entero para citar un solo párrafo.
> Prueba de que el texto no cambió: `Ads/_TOOLS/test_split_doctrina.py` reconstruye el original
> byte a byte a partir de estos 11 archivos y lo compara contra su sha256 congelado.

**Compañero obligatorio, sin partir:** `DOCTRINA/CALENDARIO_ESCALADO.md` (el CUÁNDO — ritmo de
gates día 0→3→6→7+). Este índice y sus secciones son el QUÉ.

| # | Archivo | Contenido | Quién lo lee |
|---|---|---|---|
| 0 | `DOCTRINA/ESCALADO/00_INTRO_FILOSOFIA.md` | Regla de recencia de clases + §0 Filosofía (Progresiva/Agresiva) | lectura humana / onboarding |
| 1 | `DOCTRINA/ESCALADO/01_TIMING.md` | §1 Timing y fases — cuándo se decide qué | `etapa-7` |
| 2 | `DOCTRINA/ESCALADO/02_PRESUPUESTO_DECISION.md` | §1.5 Presupuesto de Decisión (PD) — cuánto gasto antes de que "0 ventas" cuente | `decidir.py` (doctrina que lo justifica; los umbrales viven en el CSV) |
| 3 | `DOCTRINA/ESCALADO/03_SENALES_DECISION.md` | §2 Señales de decisión (umbrales de diagnóstico) | `etapa-7` |
| 4 | `DOCTRINA/ESCALADO/04_PALANCAS.md` | §3 Palancas de escalado, en orden | `etapa-7`, `etapa-11`, `fase-2-conceptos` |
| 5 | `DOCTRINA/ESCALADO/05_REPLICAR_GANADOR.md` | §4 Replicar el creativo ganador (el porqué, no el creativo) | `etapa-7` |
| 6 | `DOCTRINA/ESCALADO/06_SATURACION_CUENTA.md` | §5 Saturación por cuenta (matriz ángulo×cuenta) | `etapa-7` |
| 7 | `DOCTRINA/ESCALADO/07_MATRIZ_DUPLICACION.md` | §6 Matriz de duplicación — cuánto volumen y dónde | `etapa-7` |
| 8 | `DOCTRINA/ESCALADO/08_PLAN_ENTREGABLE.md` | §7 Entregable fijo `4_PLAN_ESCALADO.txt` (plantilla) | `etapa-6`, `etapa-7`, `etapa-guardar-producto`, `fase-3-escalado`, `generar-conceptos` |
| 9 | `DOCTRINA/ESCALADO/09_EXPLORACION_PARALELA.md` | §7b Exploración de ángulos nuevos mientras se escala (F3.exploracion) | `fase-3-escalado` |
| 10 | `DOCTRINA/ESCALADO/10_METRICAS_TESTEO.md` | §8 Métricas de evaluación de testeo (umbrales canónicos) | `etapa-6`, `etapa-7`, `etapa-10`, `etapa-11` |

Los valores vigentes de PD y umbrales de testeo (§§1.5/8) viven en
`PRODUCTOS/_PARAMETROS_DECISION.csv` y los ejecuta `Ads/_TOOLS/decidir.py` — si el texto y el CSV
difieren, manda el CSV y `verificar_guia_madre.py` lo canta.
