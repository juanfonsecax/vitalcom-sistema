# SISTEMA VITALCOM GUATEMALA — punto de entrada

**La doctrina del sistema vive en un solo archivo: [`CLAUDE.md`](CLAUDE.md).** Leelo antes de
operar. Este archivo existe solo porque algunos clientes buscan `AGENTS.md` por convención.

## Rutas canónicas

| Qué | Dónde |
|---|---|
| Orquestador y doctrina | `CLAUDE.md` |
| Definiciones de las 16 etapas | `.claude/agents/ETAPA-*.md` |
| Skills invocables | `.claude/skills/` |
| Documentos dueños de cada tema | `DOCTRINA/` — cuál es cuál, en la tabla «MAPA DE ARCHIVOS» de `CLAUDE.md` |

Las etapas se invocan por su `name` (`etapa-0`, `etapa-4`, …), nunca por ruta de archivo.

> ⚠️ **No dupliques la doctrina acá.** Hasta el 2026-09-02 este archivo era una copia línea
> por línea de `CLAUDE.md` con las rutas reescritas, y mantener las dos versiones a mano
> garantizaba que divergieran. Un dato, un dueño.
