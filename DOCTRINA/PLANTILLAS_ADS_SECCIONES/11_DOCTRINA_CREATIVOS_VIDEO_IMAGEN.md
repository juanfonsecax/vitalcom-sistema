## DOCTRINA DE CREATIVOS (VIDEO vs IMAGEN) — qué formato va en cada fase

> **Este archivo es el dueño** de la regla de formato del creativo de Meta por fase. La citan
> `etapa-2` y `etapa-9`.

**En FASE 1 los videos de competencia son DATA, no creativo.** `etapa-0`, `etapa-1b` y `etapa-2` los
minan para ángulos, hooks, lenguaje real, señales de compra y objeciones. El video que sostiene un
ángulo queda registrado como su ORIGEN (`VIDEO_COMPETENCIA` en el `_PLAN.json`), nunca como su
creativo.

| Fase | Formato del creativo | Regla |
|---|---|---|
| **FASE 1 · ángulos** | **IMAGEN en los 6 conjuntos** | Prompt de Control (`04_PROMPT_CONTROL_FASE1.md`), concepto fijo `C2_BENEFICIOS` variante `ligera`, 1 creativo por conjunto. `gen_plan.py --validar` bloquea un plan de F1 con un conjunto que no sea IMAGEN. |
| **FASE 2 · conceptos** | IMAGEN o VIDEO | El VIDEO es un concepto más dentro de la tanda de 10 de `etapa-9`. Un video de competencia se lava antes de subirlo (`Ads/_TOOLS/LAVADO.md`). |
| **FASE 4 · escalado** | el creativo validado | Se replica por Post ID; no se produce un formato nuevo. |

- **Ningún ángulo de FASE 1 se pausa ni se descarta por no tener video:** todos van en imagen.
- **Confound de formato.** Cuando un video le gana a una imagen no se sabe si ganó el ángulo o el
  formato. En FASE 1 no puede pasar (todo imagen). En FASE 2, `etapa-9` lo ataca bajando el contenido
  del video ganador a piezas IMAGEN independientes.
- **Variación agresiva o de choque** (`02_ENFOQUE_AGRESIVO.md`): no va en FASE 1, porque el concepto
  es fijo en los 6 conjuntos y cambiar la ejecución visual junto con el ángulo vuelve el resultado no
  atribuible. En FASE 2 puede ser uno de los 10 conceptos, con su compliance («ahuyenta / aleja»,
  nunca «elimina / mata») y render propio.

**Dos sistemas de creativo, no confundir:**
- **(a) ADS DE TESTEO:** la imagen (o el video lavado en FASE 2) que va en la campaña de Meta.
- **(b) INFOGRAFÍAS DEL BOT:** las imágenes dentro del flujo de WhatsApp (IMAGEN 1 beneficios,
  IMAGEN 2 modo de uso e ingredientes, IMAGEN 3 confianza, IMAGEN 4 anti-imitación opcional), de
  `DOCTRINA/PLANTILLAS_INFOGRAFIAS_FLUJO.md` y `DOCTRINA/PLANTILLAS_INFOGRAFIAS_OPCIONALES.md`, sobre
  el motor de `DOCTRINA/PLANTILLAS_INFOGRAFIAS.md`.
