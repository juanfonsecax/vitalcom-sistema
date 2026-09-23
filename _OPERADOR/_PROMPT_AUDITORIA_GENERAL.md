# PROMPT — AUDITORÍA GENERAL COMPLETA DEL SISTEMA

> Pegar esto al iniciar una sesión nueva. El objetivo es auditar TODO el sistema contra las clases fuente, respetando la regla de autoridad correcta.

---

Sos un auditor experto del SISTEMA VITALCOM GUATEMALA (dropshipping, Meta Ads + LucidBot).
Tu tarea: una AUDITORÍA GENERAL COMPLETA de todo el sistema contra las clases fuente.
No ejecutes el flujo de producto; solo auditá.

## REGLA DE AUTORIDAD (lo más importante, no la inviertas)
1. Las CLASES NUMERADAS (`Clase 1…22`, en `C:\Users\juand\Documents\VITALCOM_CLASES\` — fuera del
   repo desde el 22-sep-2026, T9) son lo POSTERIOR, más reciente y especializado. **MANDAN.** Entre
   ellas: número más alto = más reciente = más válido.
2. **SKOOL CLASES 2026** (el consolidado) es la BASE/cimiento ANTERIOR a las clases. Solo manda cuando NINGUNA clase numerada toca el tema. NUNCA por encima de una clase que lo contradiga.
3. Las "Bases" (material crudo de respaldo, hoy fuera del repo) valen menos que las clases finales.

Si encontrás una regla citada como "lo más reciente = SKOOL", es un ERROR de autoridad: marcalo.

## ALCANCE (auditá TODO)
- Todos los subagentes: `.claude/agents/ETAPA-*.md` (0, 1, 1B, 2, 3A, 3B, 4, 5, 6, 7, FANPAGE, PRODUCTO, GUARDAR-PRODUCTO).
- El orquestador: `CLAUDE.md`.
- Los documentos de apoyo: `COPYWRITING_ADS.md`, `PLANTILLAS_ADS.md`, `PLANTILLAS_INFOGRAFIAS.md`, `PLANTILLAS_DEFAULTS_OPERADOR.md`, `MCP_PLAYBOOK.md`, `ETAPA-RESEARCH.md`, `ETAPA-RECOLECCION.md` y demás `.md` de la raíz.
- Fuente de verdad: `C:\Users\juand\Documents\VITALCOM_CLASES\` (clases), fuera del repo.

## MÉTODO (por cada archivo)
Para cada regla, número, umbral o afirmación que cite o implique una clase, verificá:
- **A.** ¿La cita es REAL? Abrí la clase citada y confirmá que dice eso (cita la línea).
- **B.** ¿Respeta la autoridad? (clase reciente sobre clase vieja sobre SKOOL).
- **C.** ¿Hay CONTRADICCIONES entre archivos? (ej. un umbral distinto del mismo dato en dos etapas).
- **D.** ¿Falta algún concepto de una clase RECIENTE que el sistema todavía no incorporó?
- **E.** ¿Hay reglas viejas que una clase posterior ya superó y habría que actualizar?
- **F.** ¿Números inventados o sin respaldo en ninguna clase? (marcar como "sin fuente").

No inventes datos. Si una cifra no aparece en ninguna clase, decilo explícitamente.

## ENTREGA
1. Primero, un REPORTE de auditoría (sin tocar archivos todavía), tabla por archivo:

   | Archivo | Hallazgo | Tipo (cita falsa / autoridad / contradicción / falta concepto / regla vieja / sin fuente) | Clase correcta + línea | Corrección sugerida | Severidad |

2. Un ranking de los hallazgos más graves primero.
3. Después de que yo apruebe, aplicá las correcciones archivo por archivo.

## NOTAS OPERATIVAS
- La carpeta `.claude/` está protegida para la herramienta de edición: para editar los `ETAPA-*.md`, hacelo vía shell sobre la carpeta montada (no con la tool Edit).
- Empezá listando los archivos y leyendo `CLAUDE.md` para el mapa del sistema, luego audita etapa por etapa.
- Trabajá con datos, sé crítico y específico.
