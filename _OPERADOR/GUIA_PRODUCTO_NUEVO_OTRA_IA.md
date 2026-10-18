# LANZAR UN PRODUCTO NUEVO (FASE 1) CON LA OTRA IA

Creada 2026-09-30. Escrita para OpenCode; sirve para cualquier IA que no sea Claude Code.

## Antes de empezar: lo que tenés que tener listo

1. Nombre del producto y mercado: GT o CO.
2. Costo del producto en la moneda del mercado.
3. Al menos 6 transcripciones `.txt` de videos de competencia, en su carpeta dentro de
   `Ads/1.2 Transcripcion videos/`.
4. Foto limpia del producto (el packshot).
5. Un `.txt` con la descripción extensa del producto (ingredientes, dosis, modo de uso).
6. La cuenta publicitaria y la FanPage donde va a correr, si ya las sabés.

## Por qué hace falta este prompt

OpenCode lee las skills de `.claude/skills/` y las reglas de `AGENTS.md` (que remite a
`CLAUDE.md`), pero no corre las etapas de `.claude/agents/` como subagentes: hay que decirle que
las lea como instrucciones. Las copias viejas que tenía en `.agents/skills/` (anteriores a la
limpieza) se mandaron a la papelera el 30-sep para que no vea dos versiones de cada skill.

## El prompt (copiar completo y pegarlo en la otra IA)

```
Vas a lanzar la FASE 1 (testeo de 6 ÁNGULOS) de un producto nuevo del SISTEMA VITALCOM.
Raíz del proyecto: la carpeta SISTEMA (la que tiene CLAUDE.md).

FUENTE DE VERDAD (lee estos, en este orden, antes de hacer nada):
  1. CLAUDE.md                                    — orquestador, invariantes 1 a 13
  2. .claude/skills/fase-1-angulos/SKILL.md       — la secuencia de FASE 1
  3. .claude/agents/ETAPA-<X>.md                  — cada etapa, cuando le toque
Las etapas NO son subagentes tuyos: son instrucciones que lees y ejecutas tú.

CÓMO SE CORRE
  - Las etapas son instrucciones: para cada una, lee su .claude/agents/ETAPA-<X>.md y ejecuta
    su proceso con su formato de output exacto. Pásale solo los inputs que declara, y pasa su
    output COMPLETO a la siguiente (invariante 3). Si falta un input, DETENTE y dime cuál.
  - El paso que toca lo dice el código, no tú:
        python Ads/_TOOLS/flujo.py <PRODUCTO_KEY>
    Ejecuta el nodo que devuelve, con el ejecutor que nombra. Si dice BLOQUEADO, produce lo
    que falta con el dueño que nombra y vuelve a correrlo.

PASO 0 — ALTA DEL PRODUCTO (una sola vez, primero con --dry-run y me muestras la salida):
    python Ads/_TOOLS/alta_producto.py --nombre "<NOMBRE>" --costo <COSTO> --mercado <GT|CO> \
        --moneda USD --tasa <TASA> --descripcion-archivo "<RUTA .txt>" --imagen "<RUTA FOTO>" --dry-run
  --moneda es la moneda con que Meta COBRA la cuenta publicitaria: hoy todas cobran en USD.
  --tasa es moneda local por USD: GT 7.62 · CO 3152.5. No dejes los valores por defecto.
  Cuando yo confirme, el mismo comando sin --dry-run.

REGLAS NUEVAS DE LA LIMPIEZA (ya están en los .md de .claude, te las repito porque son críticas):
  - etapa-4 ESCRIBE PRODUCTOS/<carpeta>/INFOGRAFIAS.md con marcadores <<INFOGRAFIA:1>>,
    <<INFOGRAFIA:2>>, <<INFOGRAFIA:3>> (y 4 si la pedí). Los prompts no se repiten en el chat.
  - etapa-5 ESCRIBE PRODUCTOS/<carpeta>/BLOQUES_BOT.md con los 9 marcadores <<BLOQUE:nombre>>
    (descripcion, modo_de_uso, caracteristicas, contenido, testimonios, audio, m2, faq_venta,
    faq_postventa), en la persona del mercado: voseo en GT, tuteo en CO.
    <<BLOQUE:propuestas_valor>> NO va ahí: va al output y de ahí a 2_DATA_PRODUCTO.txt.
  - <carpeta> es el slug_carpeta de PRODUCTOS/_DIM_PRODUCTOS.csv. Nunca la adivines.
  - etapa-guardar-producto: primero escribe 2_DATA_PRODUCTO.txt (primera línea = encabezado
    único), después corre
        python Ads/_TOOLS/gen_manual.py <PRODUCTO_KEY> --escribir
    1_HACER_MANUAL.txt NUNCA se tipea ni se edita a mano. Si gen_manual dice BLOQUEADO, cada
    línea nombra el dato y su dueño: se produce ese dato y se vuelve a correr.
  - Al cerrar: python Ads/_TOOLS/verificar_producto.py <PRODUCTO_KEY> tiene que salir PASA.

PROHIBIDO
  - Editar a mano cualquier CSV de PRODUCTOS/. Cada dato tiene su escritor: alta_producto.py,
    cargar_cuenta.py, cargar_page_id.py, cambiar_costo.py, cargar_moneda_cuenta.py,
    referencia_f1.py --elegir, verificar_voz.py --agregar-json. Si no hay escritor para algo,
    DETENTE y avísame.
  - Inventar cifras de costeo: salen de python Ads/_TOOLS/costear.py (invariante 2).
  - Publicar o activar nada en Meta. La publicación la confirmo yo, orden por orden.
  - Correr scripts con --escribir que no pida el paso actual, o hacer git push.

AL TERMINAR CADA ETAPA: dime en 3 líneas qué produjo, dónde quedó y qué sigue según flujo.py.
AL TERMINAR LA FASE 1: la salida de verificar_producto.py, la de
  python Ads/_TOOLS/gen_manual.py <PRODUCTO_KEY> --validar (tiene que decir LISTO) y la ruta
  del manual generado.
```

## Si algo sale raro

Si la otra IA se detiene, o dice algo que no cuadra con este documento, traé su mensaje a
Claude tal cual antes de seguir.
