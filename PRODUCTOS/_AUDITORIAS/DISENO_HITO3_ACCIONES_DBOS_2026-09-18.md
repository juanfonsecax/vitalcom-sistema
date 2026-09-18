# DISEÑO · HITO 3 · Acciones declaradas + runner DBOS · 18-sep-2026

> Diseño hecho en Opus (handoff §6.1) para que una sesión de Sonnet lo implemente sin tener que
> decidir nada de fondo. Manda `CLAUDE.md`, después `_ROADMAP/HOJA_DE_RUTA_APP.md`, después el
> handoff `HANDOFF_2026-09-18_APP_HITO3.md`, después este documento. Si algo de acá choca con
> esos tres, se para y se avisa al operador.
>
> **No se tocó código.** Este documento es la única salida de la sesión de diseño.

---

## 0 · Resumen: las decisiones en una tabla

| # | Tema | Decisión |
|---|---|---|
| D1 | De dónde salen las acciones de los nodos | Se **declaran explícitamente** en el manifiesto (regla 2.3 de la hoja), una por nodo, y `gen_app.py` **exige la biyección** con `DOCTRINA/FLUJO.json`: cada nodo tiene exactamente una acción, con el mismo `ejecutor_tipo`, el mismo `name` y (si es script) el mismo `cmd`. Si divergen, el manifiesto es inválido. No se inventan aparte y no se pueden desincronizar. |
| D2 | Forma del bloque | `acciones` es un objeto: `schema`, configuración común (`claude`, `tras_escribir`) y `lista` de acciones. `version` del manifiesto pasa a **7**. |
| D3 | Acciones no expuestas | Los scripts que el runner usa por dentro (refrescar flujo, barrido CSV, gen_app, paquete y verificación de publicación, registrar evento, alta) también se declaran, con `visibilidad: "interna"`. El runner **solo** ejecuta ids del manifiesto; un `.py` literal en el código del runner es un defecto con prueba. |
| D4 | 403 | `POST /api/acciones/{id}` devuelve **403** si el id no está en el manifiesto **o** es `interna`. Una acción declarada pero `habilitada: false` devuelve **409** con su motivo. |
| D5 | Confirmación | Dos cosas distintas: `requiere_confirmacion` (el POST debe traer `confirmado: true`: el operador vio qué escribe y cuánto tarda) y `aprobacion: "por_orden"` (el workflow se detiene en `DBOS.recv` antes de cada orden que toca Meta). Toda acción `mcp` o `toca_meta` exige ambas. |
| D6 | Nodos de Claude | **Un nodo = una llamada headless.** DBOS no orquesta las etapas de adentro de una skill: la skill es la dueña de su secuencia y de sus paralelos. Si el proceso muere a mitad, **no** se re-ejecuta sola: queda `INTERRUMPIDO` con rastro y el operador reintenta (invariante 5: rerun completo, nunca parche parcial). |
| D7 | Cola | **Dos colas DBOS.** `trabajos` (concurrencia 8, deduplicada por producto) para los workflows padre, que pueden esperar aprobación horas sin bloquear a nadie; `escritura` (concurrencia **1**, global) para cada unidad que escribe. Cada unidad además toma el **lock de archivo** (`Cola`) con latido. Esperar una aprobación nunca retiene el turno de escritura. |
| D8 | Lock | La `Cola` actual caduca un candado a los 15 min por `mtime`: con una FASE 1 de 40 min, otro escritor lo borraría en plena escritura. Se cambia a **latido** (el dueño toca el archivo cada 30 s; caduca a los 120 s sin latido) y a **espera bloqueante con tope** para el runner. |
| D9 | `application_version` | Constante escrita a mano en `workflows.py` (`"wf-1"`), **no** el hash del código. Se sube solo cuando cambia la lista de pasos de un workflow; una prueba compara la lista de pasos contra la versión y falla si cambió sin subirla. |
| D10 | Meta idempotente | Todo paso que escribe en Meta **empieza con un snapshot fresco dentro del mismo paso** y regenera el paquete contra ese snapshot (`gen_publicacion.py --snapshot`, que marca `omitir`). El runner verifica que lo que va a ejecutar sea **subconjunto** de lo aprobado; si aparece algo nuevo, para y pide aprobación otra vez. Las aprobaciones **caducan**. |
| D11 | Bitácora de corridas | La escribe el runner, append-only, **solo** bajo `PRODUCTOS/_AUDITORIAS/app_runs/`, desde un módulo nuevo `bitacora.py` con prueba estructural (igual que `subidas.py`). `app_runs/` va a `.gitignore`. |
| D12 | Preguntas de las skills | Headless no puede preguntar. El prompt obliga a terminar con `PREGUNTA_OPERADOR: …`; el workflow la publica, espera la respuesta con `DBOS.recv` y continúa con `claude -p --resume <session_id>`. |
| D13 | Qué se habilita en el Hito 3 | Todo el mecanismo, **pero ninguna acción que toque Meta queda habilitada**: `F1/F2/F3.publicar`, `F1/F2.activar` y `ciclo.ordenes` se declaran con `habilitada: false` y su motivo. Se habilitan en Hitos 4-5, en Opus (handoff §6.2). |

---

## 1 · Lo que encontré en el código y la doctrina que condiciona el diseño

Cosas verificadas leyendo el repo el 18-sep-2026, no supuestas. Cada una cambia algo del diseño.

1. **`gen_app.py` no tiene prueba.** No existe `Ads/_TOOLS/test_gen_app.py`. El handoff pide validar
   el bloque "con su test": ese test es nuevo y cubre también la validación de v6 que ya existe.
2. **`escrituras.Cola` caduca el candado a los 15 min por `mtime`** (`TIEMPO_MAXIMO_LOCK`). Con
   corridas de Claude largas, un segundo escritor lo borraría con el primero todavía escribiendo.
   → D8.
3. **La carpeta real (`VITALCOM_BASE`) está en la rama vieja y tiene el manifiesto v6.** Hasta que
   se mergee `feat/app-web` y se regenere allá, la app que lee la carpeta real **no ve ninguna
   acción**. Comportamiento definido: manifiesto sin bloque `acciones` ⇒ `GET /api/acciones` vacío,
   todo `POST /api/acciones/*` ⇒ 403, y un aviso en Salud ("el manifiesto de la carpeta del sistema
   es v6: sin acciones"). Las pruebas del Hito 3 usan un **fixture** de sistema, no la carpeta real.
4. **`_DECISIONES.json` no trae órdenes ejecutables.** Cada celda trae `estado` y `accion_sugerida`
   en prosa ("NO SUBIR PRESUPUESTO … Opciones: (A) … (B) …"), sin `ad_id`/`adset_id`, sin valor
   destino. Para ejecutar `ciclo.ordenes` falta un script que convierta la celda en una orden
   literal (`gen_ordenes.py`, con test) y otro que la verifique contra Meta (`verificar_orden.py`).
   → `nodo.ciclo.ordenes` queda `habilitada: false` con ese motivo. Es trabajo del Hito 5, en Opus.
5. **Nada genera hoy la orden de ACTIVAR** (qué campaña, a qué hora, con qué evento). Mismo
   tratamiento para `F1.activar` y `F2.activar`.
6. **`ads_creative_upload_media` con `LOCAL_FILE` abre un widget** (skill `publicar-meta`, paso 3).
   En headless no hay quien lo elija. Spike pendiente antes de habilitar cualquier `publicar`.
7. **`etapa-render` conduce el Chrome del operador** con `mcp__claude-in-chrome__*`. Que ese
   conector exista en una corrida headless no está verificado. → `nodo.F2.conceptos` queda
   deshabilitada hasta un spike corto (mismo formato que el spike B).
8. **`registrar_evento.py` no deduplica.** Si el proceso muere entre que escribe la fila y que DBOS
   registra el paso, al retomar escribiría la fila dos veces. → el runner firma cada evento en
   `--fuente` con `app job=<id> orden=<n>` y, antes de registrar, busca esa firma en `_EVENTOS.csv`
   (lectura de texto; no toca el script).
9. **El `{cuenta}` de FLUJO.json es el alias normalizado sin espacios** (`GTR7`), y `_DIM_PRODUCTOS`
   guarda `GTR 7`. La app no normaliza: la cuenta se elige de las filas de `_DIM_CUENTAS.csv` y
   viaja tal cual; el script la interpreta.
10. **Los nodos del ciclo aparecen en `flujo.py` con prefijo de fase** (`F2.ciclo.motor`), pero en
    FLUJO.json su id es `ciclo.motor`. El id de acción usa el de FLUJO.json: `nodo.ciclo.motor`.
    El endpoint quita el prefijo de fase al comparar contra el nodo actual (`nodo_actual` sin
    `F<n>.` si el nodo es de ciclo).
11. **Dentro de una corrida headless los hooks sí corren** (spike A: `SessionStart` y
    `PostToolUse`). Fuera, no. Por eso después de toda unidad que escribe, el runner corre
    `tras_escribir` (barrido CSV + `flujo.py --todo` + `gen_app.py`), venga de un script o de Claude.

---

## 2 · PARTE A — el bloque `acciones` del manifiesto v7

### 2.1 Esquema: nivel del bloque

```json
"acciones": {
  "schema": "acciones/1",
  "reservados": ["run_dir", "tmp", "hoy", "job_id"],
  "claude": {
    "servidor_meta": "claude_ai_META_MCP",
    "herramientas_base": ["Task", "Agent", "Skill", "Read", "Glob", "Grep", "Bash", "Write", "Edit"],
    "marca_pregunta": "PREGUNTA_OPERADOR:",
    "respuesta_max_horas": 24,
    "prompt_nodo": [
      "Sos el orquestador de VITALCOM corriendo desde la app, sin operador en línea (trabajo {job_id}).",
      "Ejecutá SOLO el nodo {nodo} del producto {producto_key}.",
      "Primero corré `python Ads/_TOOLS/flujo.py {producto_key}`. Si el nodo actual no es {nodo} o está BLOQUEADO, no ejecutes nada: devolvé los bloqueantes y terminá.",
      "Ejecutalo con su ejecutor declarado ({ejecutor}), según CLAUDE.md y su skill o su archivo de etapa.",
      "Si necesitás una decisión del operador, no la asumas: terminá tu respuesta con una línea que empiece con `PREGUNTA_OPERADOR:` seguida de la pregunta y las opciones."
    ]
  },
  "tras_escribir": ["sistema.barrido_csv", "sistema.refrescar_flujo", "sistema.gen_app"],
  "lista": [ /* §2.3 */ ]
}
```

- `reservados`: placeholders que llena el runner, nunca el operador. `{run_dir}` = carpeta de la
  corrida en `app_runs/`; `{tmp}` = carpeta temporal del SO de esa corrida; `{hoy}` = fecha
  sellada en el primer paso del workflow (ver §3.4, determinismo); `{job_id}`.
- `claude.prompt_nodo`: se une con saltos de línea y se rellena con `{job_id}`, `{nodo}`,
  `{producto_key}`, `{ejecutor}` (el texto que ya devuelve `flujo.py` en `ejecutor`). Es el
  "prompt mínimo" de la hoja §Hito 3: la doctrina la carga Claude Code desde `CLAUDE.md`, no la
  repite la app.

### 2.2 Esquema: cada acción

| Campo | Tipo | Obligatorio | Significado |
|---|---|---|---|
| `id` | str `^[a-z]+(\.[A-Za-z0-9_-]+)+$` | sí | `nodo.<id de FLUJO.json>` para nodos; `producto.*`, `sistema.*`, `publicacion.*`, `evento.*` para el resto. |
| `rotulo` | str | sí | Texto del botón, en lenguaje del operador. |
| `nodo` | str \| null | sí | Id del nodo en FLUJO.json (sin prefijo de fase) o `null`. |
| `ejecutor_tipo` | `script`\|`subagente`\|`skill`\|`mcp`\|`operador` | sí | Igual al de FLUJO.json si `nodo` no es null. |
| `name` | str \| null | subagente/skill | Igual al `ejecutor.name` de FLUJO.json. |
| `comando` | list[str] \| null | script | argv literal con placeholders `{x}`. **Nunca** shell. Null para los demás tipos. |
| `salida` | `json`\|`texto` | script | Si el runner debe parsear stdout como JSON (`{"ok": false, "detalle": …}` ⇒ fallo). |
| `parametros` | obj | sí (puede ser `{}`) | `{nombre: {tipo, requerido, valores?, patron?, bandera?}}` — ver 2.2.1. |
| `requiere_confirmacion` | bool | sí | El POST debe traer `confirmado: true`. |
| `aprobacion` | `ninguna`\|`por_orden` | sí | `por_orden` ⇒ el workflow espera `DBOS.recv` antes de cada orden. |
| `toca_meta` | bool | sí | Escribe en Meta (aunque el ejecutor sea una skill, como `publicar-meta`). |
| `herramientas` | list[str] | Claude | `allowedTools` extra sobre `herramientas_base` (p. ej. `WebSearch`). Nunca `mcp__*`. |
| `herramientas_meta` | `{lectura: [...], escritura: [...]}` | si `toca_meta` | Nombres **exactos** de Meta (sin prefijo; el runner antepone `mcp__<servidor_meta>__`). `escritura` solo se pasa en el paso aprobado. |
| `ordenes` | obj \| null | si `toca_meta` y habilitada | De dónde salen las órdenes y quién las verifica (2.2.2). |
| `escribe` | list[str] | sí | Rutas o prefijos relativos a la base. `[]` = no escribe (no pasa por la cola de escritura). |
| `idempotente` | bool | script | `true` ⇒ si el proceso muere a mitad, se re-ejecuta sola al retomar. `false` ⇒ `INTERRUMPIDO`, reintento manual. Claude y Meta: siempre `false` (Meta se protege por D10). |
| `precondicion` | `nodo_listo`\|`ninguna` | sí | `nodo_listo`: el endpoint consulta `flujo.py <pk> --json --sin-escribir` y exige que el nodo actual sea este y esté `LISTO_PARA_EJECUTAR`. |
| `visibilidad` | `boton`\|`interna` | sí | `interna` ⇒ 403 desde la API; solo la usa el runner. |
| `habilitada` | bool | sí | `false` ⇒ 409 con `motivo`. |
| `motivo` | str | si `habilitada: false` | Qué falta, con el nombre de su dueño. |
| `tiempo_max_s` | int | sí | Tope duro del subproceso. |
| `presupuesto_usd` | number | Claude | `--max-budget-usd` (tope de seguridad; con la suscripción es cuota, no dinero). |
| `datos_del_operador` | list[{dato, accion}] | operador (opcional en otros) | Por cada `dato` de `requiere`/`produce` del nodo, la acción escritora que lo carga (o `null`: "hoy se carga a mano en <dueño>"). |

#### 2.2.1 Tipos de parámetro (vocabulario cerrado)

| `tipo` | Qué acepta | Cómo lo valida el endpoint (sin calcular nada) |
|---|---|---|
| `producto_key` | una clave | Existe tal cual en `_DIM_PRODUCTOS.csv` (lectura de `contratos.productos()`). |
| `cuenta_alias` | un alias | Existe tal cual en la columna `cuenta_alias` de `_DIM_CUENTAS.csv`. |
| `enum` | uno de `valores` | Pertenencia a la lista declarada. |
| `texto` | texto libre | `fullmatch` contra `patron` (obligatorio). |
| `archivo_temporal` | una ruta | Está dentro de la carpeta temporal que creó `subidas.py` para ese pedido. |
| `bandera` | bool | Sin valor: si es `true` se agrega `bandera` sola. |

- Un parámetro **sin** `bandera` debe aparecer como `{nombre}` en `comando`.
- Un parámetro **con** `bandera` no aparece en `comando`: si viene con valor, el runner agrega
  `[bandera, valor]` al final (o solo `bandera` si es tipo `bandera`). Así caben los opcionales de
  `alta_producto.py` sin un `if` en el código.
- La sustitución es por token y **no** hay shell (`subprocess.run(lista)`), así que un valor con
  espacios no puede partir el comando. Igual, `texto` exige `patron`.

#### 2.2.2 `ordenes` (solo acciones que tocan Meta)

```json
"ordenes": {
  "tipo": "paquete_publicacion",
  "generador": "publicacion.paquete",
  "verificador": "publicacion.verificar",
  "evento": "LANZAMIENTO",
  "caduca_horas": 12
}
```

- `tipo`: `paquete_publicacion` (una orden = un paquete de `gen_publicacion.py`, todas sus
  llamadas; todo nace PAUSED) · `decision` (una orden = una orden literal de `gen_ordenes.py`,
  Hito 5) · `activacion` (Hito 4/5).
- `generador` y `verificador`: ids de acciones `script` internas. `evento`: lo que se registra con
  `evento.registrar` al verificar.
- `caduca_horas`: una aprobación vale ese tiempo desde que el operador la da. Si el proceso se cae
  y retoma después, la orden pasa a `CADUCADA` y no se ejecuta (invariante 13: una orden sobre
  data vieja es el error de ventana del 06-sep).

> **Unidad de aprobación de una publicación = el paquete completo**, mostrado llamada por llamada.
> Razón: todo nace PAUSED (no gasta) y la skill ya exige parar al primer fallo; aprobar 40
> `ads_create_*` de a una no protege nada que el paquete no proteja. Para `decision` y
> `activacion` (que sí mueven plata) la unidad es **una orden**. Ver §5, punto a confirmar 1.

### 2.3 La lista completa propuesta para v7

Los 14 nodos de FLUJO.json (F1: 4 · F2: 5 · F3: 2 · ciclo: 3) + 8 internas/independientes.

```json
"lista": [
  {"id": "nodo.F1.congelar_inputs", "rotulo": "Cargar lo que el producto necesita",
   "nodo": "F1.congelar_inputs", "ejecutor_tipo": "operador", "name": null, "comando": null,
   "parametros": {"producto_key": {"tipo": "producto_key", "requerido": true}},
   "requiere_confirmacion": false, "aprobacion": "ninguna", "toca_meta": false,
   "escribe": [], "precondicion": "ninguna", "visibilidad": "boton", "habilitada": true,
   "tiempo_max_s": 0,
   "datos_del_operador": [
     {"dato": "fila del producto en _DIM_PRODUCTOS.csv", "accion": "producto.alta"},
     {"dato": "COSTO_PROVEEDOR_Q", "accion": "producto.alta"},
     {"dato": "≥6 transcripciones TXT", "accion": "producto.transcribir"},
     {"dato": "carpeta de media del producto (imagen del frasco)", "accion": "producto.alta"}]},

  {"id": "nodo.F1.paquete", "rotulo": "Armar FASE 1 (ángulos, copy, bot y plan)",
   "nodo": "F1.paquete", "ejecutor_tipo": "skill", "name": "fase-1-angulos", "comando": null,
   "parametros": {"producto_key": {"tipo": "producto_key", "requerido": true}},
   "requiere_confirmacion": true, "aprobacion": "ninguna", "toca_meta": false,
   "herramientas": ["WebSearch", "WebFetch"],
   "escribe": ["PRODUCTOS/", "Ads/"], "idempotente": false,
   "precondicion": "nodo_listo", "visibilidad": "boton", "habilitada": true,
   "tiempo_max_s": 5400, "presupuesto_usd": 30},

  {"id": "nodo.F1.publicar", "rotulo": "Publicar FASE 1 en Meta (PAUSED)",
   "nodo": "F1.publicar", "ejecutor_tipo": "skill", "name": "publicar-meta", "comando": null,
   "parametros": {"producto_key": {"tipo": "producto_key", "requerido": true},
                  "cuenta": {"tipo": "cuenta_alias", "requerido": true}},
   "requiere_confirmacion": true, "aprobacion": "por_orden", "toca_meta": true,
   "herramientas_meta": {
     "lectura": ["ads_get_ad_accounts", "ads_get_ad_entities", "ads_get_user_pages", "ads_get_ad_account_pages", "ads_get_ad_images"],
     "escritura": ["ads_create_campaign", "ads_create_ad_set", "ads_create_creative", "ads_create_ad"]},
   "ordenes": {"tipo": "paquete_publicacion", "generador": "publicacion.paquete",
               "verificador": "publicacion.verificar", "evento": "LANZAMIENTO", "caduca_horas": 12},
   "escribe": ["Ads/_INGESTA/META/", "PRODUCTOS/_DIM_CREATIVOS.csv", "PRODUCTOS/_EVENTOS.csv"],
   "idempotente": false, "precondicion": "nodo_listo", "visibilidad": "boton",
   "habilitada": false,
   "motivo": "Se habilita en el Hito 4, en Opus: falta el spike de ads_creative_upload_media (LOCAL_FILE abre un widget) en headless.",
   "tiempo_max_s": 1800, "presupuesto_usd": 10},

  {"id": "nodo.F1.activar", "rotulo": "Activar FASE 1 a las 4 AM",
   "nodo": "F1.activar", "ejecutor_tipo": "mcp", "name": null, "comando": null,
   "parametros": {"producto_key": {"tipo": "producto_key", "requerido": true}},
   "requiere_confirmacion": true, "aprobacion": "por_orden", "toca_meta": true,
   "herramientas_meta": {"lectura": ["ads_get_ad_entities"], "escritura": ["ads_activate_entity"]},
   "ordenes": null, "escribe": ["PRODUCTOS/_EVENTOS.csv"], "idempotente": false,
   "precondicion": "nodo_listo", "visibilidad": "boton", "habilitada": false,
   "motivo": "Ningún script genera la orden de activación (campaña, hora, evento) ni la verifica. Hito 4/5, en Opus.",
   "tiempo_max_s": 600, "presupuesto_usd": 3},

  {"id": "nodo.F2.etapa-11", "rotulo": "Diagnosticar el cierre del bot",
   "nodo": "F2.etapa-11", "ejecutor_tipo": "subagente", "name": "etapa-11", "comando": null,
   "parametros": {"producto_key": {"tipo": "producto_key", "requerido": true}},
   "requiere_confirmacion": true, "aprobacion": "ninguna", "toca_meta": false, "herramientas": [],
   "escribe": ["PRODUCTOS/"], "idempotente": false, "precondicion": "nodo_listo",
   "visibilidad": "boton", "habilitada": true, "tiempo_max_s": 2400, "presupuesto_usd": 10},

  {"id": "nodo.F2.conceptos", "rotulo": "Fabricar y renderizar los 10 conceptos",
   "nodo": "F2.conceptos", "ejecutor_tipo": "subagente", "name": "etapa-9", "comando": null,
   "parametros": {"producto_key": {"tipo": "producto_key", "requerido": true}},
   "requiere_confirmacion": true, "aprobacion": "ninguna", "toca_meta": false, "herramientas": [],
   "escribe": ["PRODUCTOS/", "Ads/"], "idempotente": false, "precondicion": "nodo_listo",
   "visibilidad": "boton", "habilitada": false,
   "motivo": "etapa-render conduce el Chrome del operador; no está verificado que claude-in-chrome exista en una corrida headless (spike pendiente).",
   "tiempo_max_s": 5400, "presupuesto_usd": 25},

  {"id": "nodo.F2.plan", "rotulo": "Copy único, flujos A/B y plan de las 3 campañas",
   "nodo": "F2.plan", "ejecutor_tipo": "subagente", "name": "etapa-6", "comando": null,
   "parametros": {"producto_key": {"tipo": "producto_key", "requerido": true}},
   "requiere_confirmacion": true, "aprobacion": "ninguna", "toca_meta": false, "herramientas": [],
   "escribe": ["PRODUCTOS/"], "idempotente": false, "precondicion": "nodo_listo",
   "visibilidad": "boton", "habilitada": true, "tiempo_max_s": 3600, "presupuesto_usd": 20},

  {"id": "nodo.F2.publicar", "rotulo": "Publicar las campañas de conceptos (PAUSED)",
   "nodo": "F2.publicar", "ejecutor_tipo": "skill", "name": "publicar-meta", "comando": null,
   "parametros": {"producto_key": {"tipo": "producto_key", "requerido": true},
                  "cuenta": {"tipo": "cuenta_alias", "requerido": true},
                  "brazo": {"tipo": "enum", "valores": ["A", "B", "C"], "requerido": true}},
   "requiere_confirmacion": true, "aprobacion": "por_orden", "toca_meta": true,
   "herramientas_meta": {
     "lectura": ["ads_get_ad_accounts", "ads_get_ad_entities", "ads_get_user_pages", "ads_get_ad_account_pages", "ads_get_ad_images"],
     "escritura": ["ads_create_campaign", "ads_create_ad_set", "ads_create_creative", "ads_create_ad"]},
   "ordenes": {"tipo": "paquete_publicacion", "generador": "publicacion.paquete",
               "verificador": "publicacion.verificar", "evento": "LANZAMIENTO", "caduca_horas": 12},
   "escribe": ["Ads/_INGESTA/META/", "PRODUCTOS/_DIM_CREATIVOS.csv", "PRODUCTOS/_EVENTOS.csv"],
   "idempotente": false, "precondicion": "nodo_listo", "visibilidad": "boton",
   "habilitada": false, "motivo": "Igual que nodo.F1.publicar: Hito 4, en Opus.",
   "tiempo_max_s": 1800, "presupuesto_usd": 10},

  {"id": "nodo.F2.activar", "rotulo": "Activar las campañas de conceptos a las 4 AM",
   "nodo": "F2.activar", "ejecutor_tipo": "mcp", "name": null, "comando": null,
   "parametros": {"producto_key": {"tipo": "producto_key", "requerido": true}},
   "requiere_confirmacion": true, "aprobacion": "por_orden", "toca_meta": true,
   "herramientas_meta": {"lectura": ["ads_get_ad_entities"], "escritura": ["ads_activate_entity"]},
   "ordenes": null, "escribe": ["PRODUCTOS/_EVENTOS.csv", "PRODUCTOS/_TESTEOS.csv"], "idempotente": false,
   "precondicion": "nodo_listo", "visibilidad": "boton", "habilitada": false,
   "motivo": "Igual que nodo.F1.activar, más el A/B de flujo (CAMBIO_BOT + gemelos + test_id). Hito 4/5, en Opus.",
   "tiempo_max_s": 600, "presupuesto_usd": 3},

  {"id": "nodo.F3.plan", "rotulo": "Microángulos y plan 1-1-7",
   "nodo": "F3.plan", "ejecutor_tipo": "subagente", "name": "etapa-6", "comando": null,
   "parametros": {"producto_key": {"tipo": "producto_key", "requerido": true}},
   "requiere_confirmacion": true, "aprobacion": "ninguna", "toca_meta": false,
   "herramientas": ["WebSearch", "WebFetch"],
   "escribe": ["PRODUCTOS/"], "idempotente": false, "precondicion": "nodo_listo",
   "visibilidad": "boton", "habilitada": true, "tiempo_max_s": 3600, "presupuesto_usd": 20},

  {"id": "nodo.F3.publicar", "rotulo": "Publicar el 1-1-7 CBO (PAUSED)",
   "nodo": "F3.publicar", "ejecutor_tipo": "skill", "name": "publicar-meta", "comando": null,
   "parametros": {"producto_key": {"tipo": "producto_key", "requerido": true},
                  "cuenta": {"tipo": "cuenta_alias", "requerido": true}},
   "requiere_confirmacion": true, "aprobacion": "por_orden", "toca_meta": true,
   "herramientas_meta": {
     "lectura": ["ads_get_ad_accounts", "ads_get_ad_entities", "ads_get_user_pages", "ads_get_ad_account_pages", "ads_get_ad_images"],
     "escritura": ["ads_create_campaign", "ads_create_ad_set", "ads_create_creative", "ads_create_ad"]},
   "ordenes": {"tipo": "paquete_publicacion", "generador": "publicacion.paquete",
               "verificador": "publicacion.verificar", "evento": "LANZAMIENTO", "caduca_horas": 12},
   "escribe": ["Ads/_INGESTA/META/", "PRODUCTOS/_DIM_CREATIVOS.csv", "PRODUCTOS/_EVENTOS.csv"],
   "idempotente": false, "precondicion": "nodo_listo", "visibilidad": "boton",
   "habilitada": false, "motivo": "Igual que nodo.F1.publicar: Hito 6, en Opus.",
   "tiempo_max_s": 1800, "presupuesto_usd": 10},

  {"id": "nodo.ciclo.datos", "rotulo": "Traer las ventas de LucidSales",
   "nodo": "ciclo.datos", "ejecutor_tipo": "skill", "name": "recopilar-lucidsales", "comando": null,
   "parametros": {}, "requiere_confirmacion": false, "aprobacion": "ninguna", "toca_meta": false,
   "herramientas": [], "escribe": ["PRODUCTOS/_FACT_VENTAS.csv", "Ads/_INGESTA/"],
   "idempotente": false, "precondicion": "ninguna", "visibilidad": "boton", "habilitada": true,
   "tiempo_max_s": 1200, "presupuesto_usd": 5},

  {"id": "nodo.ciclo.motor", "rotulo": "Correr el motor de decisión",
   "nodo": "ciclo.motor", "ejecutor_tipo": "script", "name": null,
   "comando": ["python", "Ads/_TOOLS/gen_decisiones.py"], "salida": "texto",
   "parametros": {}, "requiere_confirmacion": false, "aprobacion": "ninguna", "toca_meta": false,
   "escribe": ["PRODUCTOS/_DECISIONES.json", "warehouse/"], "idempotente": true,
   "precondicion": "ninguna", "visibilidad": "boton", "habilitada": true, "tiempo_max_s": 900},

  {"id": "nodo.ciclo.ordenes", "rotulo": "Ejecutar las órdenes del motor",
   "nodo": "ciclo.ordenes", "ejecutor_tipo": "mcp", "name": null, "comando": null,
   "parametros": {"producto_key": {"tipo": "producto_key", "requerido": true}},
   "requiere_confirmacion": true, "aprobacion": "por_orden", "toca_meta": true,
   "herramientas_meta": {"lectura": ["ads_get_ad_entities"], "escritura": ["ads_update_entity"]},
   "ordenes": null, "escribe": ["PRODUCTOS/_EVENTOS.csv"], "idempotente": false,
   "precondicion": "ninguna", "visibilidad": "boton", "habilitada": false,
   "motivo": "_DECISIONES.json trae la orden en prosa, sin entidad ni valor destino. Falta gen_ordenes.py (orden literal) y verificar_orden.py (contra Meta), ambos con test. Hito 5, en Opus.",
   "tiempo_max_s": 600, "presupuesto_usd": 3},

  {"id": "producto.alta", "rotulo": "Dar de alta el producto", "nodo": null,
   "ejecutor_tipo": "script", "name": null,
   "comando": ["python", "Ads/_TOOLS/alta_producto.py", "--nombre", "{nombre}", "--costo", "{costo}",
               "--descripcion-archivo", "{descripcion}", "--imagen", "{imagen}", "--json"],
   "salida": "json",
   "parametros": {
     "nombre": {"tipo": "texto", "patron": "^[^\\r\\n]{2,80}$", "requerido": true},
     "costo": {"tipo": "texto", "patron": "^[0-9]{1,5}([.,][0-9]{1,2})?$", "requerido": true},
     "descripcion": {"tipo": "archivo_temporal", "requerido": true},
     "imagen": {"tipo": "archivo_temporal", "requerido": true},
     "clave": {"tipo": "texto", "patron": "^[A-Z0-9_]{2,40}$", "requerido": false, "bandera": "--clave"},
     "cuenta": {"tipo": "cuenta_alias", "requerido": false, "bandera": "--cuenta"},
     "moneda": {"tipo": "enum", "valores": ["GTQ", "USD", "COP"], "requerido": false, "bandera": "--moneda"},
     "tasa": {"tipo": "texto", "patron": "^[0-9]{1,5}([.,][0-9]{1,4})?$", "requerido": false, "bandera": "--tasa"},
     "color_envase": {"tipo": "texto", "patron": "^[^\\r\\n]{1,40}$", "requerido": false, "bandera": "--color-envase"},
     "color_hex": {"tipo": "texto", "patron": "^#[0-9A-Fa-f]{6}$", "requerido": false, "bandera": "--color-hex"},
     "marca": {"tipo": "texto", "patron": "^[^\\r\\n]{1,60}$", "requerido": false, "bandera": "--marca"},
     "formato": {"tipo": "texto", "patron": "^[^\\r\\n]{1,40}$", "requerido": false, "bandera": "--formato"},
     "dry_run": {"tipo": "bandera", "requerido": false, "bandera": "--dry-run"}},
   "requiere_confirmacion": false, "aprobacion": "ninguna", "toca_meta": false,
   "escribe": ["PRODUCTOS/_DIM_PRODUCTOS.csv", "PRODUCTOS/_DIM_ENVASE.csv", "PRODUCTOS/", "Ads/"],
   "idempotente": false, "precondicion": "ninguna", "visibilidad": "interna", "habilitada": true,
   "tiempo_max_s": 120},

  {"id": "producto.transcribir", "rotulo": "Pasar los videos a texto", "nodo": null,
   "ejecutor_tipo": "script", "name": null,
   "comando": ["python", "Ads/_TOOLS/transcribir_videos.py", "--producto", "{producto_key}", "--modelo", "{modelo}", "--json"],
   "salida": "json",
   "parametros": {"producto_key": {"tipo": "producto_key", "requerido": true},
                  "modelo": {"tipo": "enum", "valores": ["tiny", "base", "small", "medium"], "requerido": true}},
   "requiere_confirmacion": false, "aprobacion": "ninguna", "toca_meta": false,
   "escribe": ["Ads/1.2 Transcripcion videos/"], "idempotente": true,
   "precondicion": "ninguna", "visibilidad": "boton", "habilitada": true, "tiempo_max_s": 3600},

  {"id": "sistema.barrido_csv", "rotulo": "Validar los CSV que cambiaron", "nodo": null,
   "ejecutor_tipo": "script", "name": null, "comando": ["python", "Ads/_TOOLS/hook_csv.py", "--barrido"],
   "salida": "texto", "parametros": {}, "requiere_confirmacion": false, "aprobacion": "ninguna",
   "toca_meta": false, "escribe": ["PRODUCTOS/.hook_csv_mtimes.json"], "idempotente": true,
   "precondicion": "ninguna", "visibilidad": "interna", "habilitada": true, "tiempo_max_s": 300},

  {"id": "sistema.refrescar_flujo", "rotulo": "Re-evaluar el flujo", "nodo": null,
   "ejecutor_tipo": "script", "name": null, "comando": ["python", "Ads/_TOOLS/flujo.py", "--todo", "--silencioso"],
   "salida": "texto", "parametros": {}, "requiere_confirmacion": false, "aprobacion": "ninguna",
   "toca_meta": false,
   "escribe": ["PRODUCTOS/_FLUJO.json", "PRODUCTOS/_ESTADO_FLUJO.csv", "PRODUCTOS/_EVENTOS.csv", "VISTAS/FLUJO.html"],
   "idempotente": true, "precondicion": "ninguna", "visibilidad": "interna", "habilitada": true,
   "tiempo_max_s": 600},

  {"id": "sistema.gen_app", "rotulo": "Regenerar las vistas", "nodo": null,
   "ejecutor_tipo": "script", "name": null, "comando": ["python", "Ads/_TOOLS/gen_app.py"],
   "salida": "texto", "parametros": {}, "requiere_confirmacion": false, "aprobacion": "ninguna",
   "toca_meta": false,
   "escribe": ["VISTAS/_ESTADO.json", "VISTAS/APP.html", "VISTAS/PANEL.html", "PRODUCTOS/_LANZADOR.json"],
   "idempotente": true, "precondicion": "ninguna", "visibilidad": "interna", "habilitada": true,
   "tiempo_max_s": 600},

  {"id": "publicacion.paquete", "rotulo": "Generar el paquete de publicación contra el snapshot", "nodo": null,
   "ejecutor_tipo": "script", "name": null,
   "comando": ["python", "Ads/_TOOLS/gen_publicacion.py", "--producto", "{producto_key}", "--fase", "{fase}",
               "--brazo", "{brazo}", "--cuenta", "{cuenta}",
               "--snapshot", "Ads/_INGESTA/META/snapshot_{cuenta}.json", "--json", "--salida", "{run_dir}/paquete.json"],
   "salida": "json",
   "parametros": {"producto_key": {"tipo": "producto_key", "requerido": true},
                  "fase": {"tipo": "enum", "valores": ["1", "2", "3"], "requerido": true},
                  "brazo": {"tipo": "enum", "valores": ["UNICO", "A", "B", "C"], "requerido": true},
                  "cuenta": {"tipo": "cuenta_alias", "requerido": true}},
   "requiere_confirmacion": false, "aprobacion": "ninguna", "toca_meta": false,
   "escribe": [], "idempotente": true, "precondicion": "ninguna", "visibilidad": "interna",
   "habilitada": true, "tiempo_max_s": 300},

  {"id": "publicacion.verificar", "rotulo": "Verificar Meta contra el paquete y escribir los ad_id", "nodo": null,
   "ejecutor_tipo": "script", "name": null,
   "comando": ["python", "Ads/_TOOLS/verificar_publicacion.py", "--producto", "{producto_key}", "--fase", "{fase}",
               "--brazo", "{brazo}", "--snapshot", "Ads/_INGESTA/META/snapshot_{cuenta}.json", "--escribir"],
   "salida": "texto",
   "parametros": {"producto_key": {"tipo": "producto_key", "requerido": true},
                  "fase": {"tipo": "enum", "valores": ["1", "2", "3"], "requerido": true},
                  "brazo": {"tipo": "enum", "valores": ["UNICO", "A", "B", "C"], "requerido": true},
                  "cuenta": {"tipo": "cuenta_alias", "requerido": true}},
   "requiere_confirmacion": false, "aprobacion": "ninguna", "toca_meta": false,
   "escribe": ["PRODUCTOS/_DIM_CREATIVOS.csv"], "idempotente": true, "precondicion": "ninguna",
   "visibilidad": "interna", "habilitada": true, "tiempo_max_s": 300},

  {"id": "evento.registrar", "rotulo": "Registrar el evento", "nodo": null,
   "ejecutor_tipo": "script", "name": null,
   "comando": ["python", "Ads/_TOOLS/registrar_evento.py", "--producto", "{producto_key}", "--evento", "{evento}",
               "--motivo", "{motivo}", "--fuente", "{fuente}"],
   "salida": "texto",
   "parametros": {"producto_key": {"tipo": "producto_key", "requerido": true},
                  "evento": {"tipo": "enum", "valores": ["LANZAMIENTO", "PAUSA", "CAMBIO_PRESUPUESTO", "CAMBIO_CREATIVO", "ORDEN_REVOCADA"], "requerido": true},
                  "motivo": {"tipo": "texto", "patron": "^[^\\r\\n]{3,300}$", "requerido": true},
                  "fuente": {"tipo": "texto", "patron": "^[^\\r\\n]{3,300}$", "requerido": true},
                  "cuenta": {"tipo": "cuenta_alias", "requerido": false, "bandera": "--cuenta"},
                  "campana": {"tipo": "texto", "patron": "^[^\\r\\n]{1,120}$", "requerido": false, "bandera": "--campana"},
                  "conjunto": {"tipo": "texto", "patron": "^[^\\r\\n]{1,160}$", "requerido": false, "bandera": "--conjunto"},
                  "antes": {"tipo": "texto", "patron": "^[0-9.]{0,12}$", "requerido": false, "bandera": "--antes"},
                  "despues": {"tipo": "texto", "patron": "^[0-9.]{0,12}$", "requerido": false, "bandera": "--despues"}},
   "requiere_confirmacion": false, "aprobacion": "ninguna", "toca_meta": false,
   "escribe": ["PRODUCTOS/_EVENTOS.csv"], "idempotente": false, "precondicion": "ninguna",
   "visibilidad": "interna", "habilitada": true, "tiempo_max_s": 60}
]
```

Notas sobre la lista:
- `nodo.F1.congelar_inputs` no se "ejecuta": es un formulario. `POST` sobre ella devuelve **409
  `ES_DEL_OPERADOR`** con la lista `datos_del_operador` para que la pantalla ofrezca los escritores.
  `producto.alta` es `interna` porque su puerta es el endpoint multipart que ya existe
  (`POST /api/productos`), que por dentro pasa a ejecutar esta acción por el runner (§3.8).
- Los `escribe` con prefijo (`"PRODUCTOS/"`) son honestos: una skill puede tocar cualquier cosa
  bajo `PRODUCTOS/`. Sirven para mostrarle al operador qué puede cambiar y para decidir que pasa por
  la cola de escritura; no son un sandbox (el sandbox real de Claude es `allowedTools`).
- `evento.registrar` queda con el enum mínimo que usa el runner. Se amplía cuando el Hito 5 lo pida.
- Ningún `presupuesto_usd`/`tiempo_max_s` de esta lista está medido: son topes de seguridad
  iniciales. Se ajustan con la primera corrida real de cada uno (la bitácora guarda `costo_usd` y
  duración).

### 2.4 Cómo lo valida `gen_app.py`

**Cambio a `gen_app.py`** (el único a un script existente en este hito, autorizado por el handoff
§5.1): una función `validar_acciones(m, flujo)` que se llama desde `leer_manifiesto()` cuando
`version >= 7`, y un modo nuevo **`--validar-manifiesto [--json]`** que solo valida y sale 0/1
(no mira fuentes ni escribe; `--verificar` sigue igual). Con `--json` imprime
`{"ok": bool, "version": 7, "problemas": [...], "avisos": [...]}`. Las acciones **no** se
copian a `_ESTADO.json` ni a `APP.html` (la app vieja no las usa).

Reglas (cada una con su caso en `test_gen_app.py`, sobre un manifiesto y un FLUJO de fixture):

| Regla | Falla si… |
|---|---|
| V1 | `version >= 7` y falta `acciones`, o `acciones.schema != "acciones/1"`, o falta `lista`. |
| V2 | Un `id` se repite o no cumple el patrón. |
| V3 | Un campo obligatorio falta o hay un campo que el contrato no conoce (igual que `CAMPOS_VISTA`). |
| V4 | `ejecutor_tipo` fuera de `script|subagente|skill|mcp|operador`. |
| V5 | `nodo` no existe en FLUJO.json (fases + ciclo), o su `ejecutor.tipo` ≠ `ejecutor_tipo`, o su `ejecutor.name` ≠ `name`, o (script) su `cmd` ≠ `comando` (comparando `{pk}` como `{producto_key}`). |
| V6 | Un nodo de FLUJO.json no tiene exactamente una acción con ese `nodo` (**completitud**: un nodo nuevo en el grafo obliga a declarar su acción). |
| V7 | `script` sin `comando`, o `comando[0] != "python"`, o `comando[1]` no es un `Ads/_TOOLS/*.py` que exista, o algún token contiene `--bare`, `--dangerously-skip-permissions` o `shell`. |
| V8 | Tipos que no son `script` con `comando` no nulo; `subagente`/`skill` sin `name` o sin `presupuesto_usd`. |
| V9 | Un `{x}` de `comando` no está en `parametros` (sin `bandera`) ni en `reservados`; o un parámetro sin `bandera` no aparece en `comando`. |
| V10 | Un parámetro con `tipo` fuera del vocabulario, `enum` sin `valores`, `texto` sin `patron` o con un `patron` que no compila. |
| V11 | `ejecutor_tipo == "mcp"` o `toca_meta` y (`requiere_confirmacion` no es `true` o `aprobacion != "por_orden"`). **La regla del handoff: mcp ⇒ requiere_confirmacion.** |
| V12 | `herramientas_meta` no vacío y `toca_meta` es `false`; o `toca_meta` sin `herramientas_meta.escritura`; o cualquier `herramientas` contiene `mcp__` o `*`. |
| V13 | `toca_meta`, `habilitada` y `ordenes` nulo; o `ordenes.generador`/`verificador` no es una acción `script` declarada. |
| V14 | Una ruta de `escribe` es absoluta, contiene `..`, o empieza por `DOCTRINA/`, `.claude/` o `app/` (la app nunca reescribe doctrina ni se reescribe a sí misma); o no empieza por `PRODUCTOS/`, `Ads/`, `VISTAS/` o `warehouse/`. |
| V15 | `subagente`/`skill` con `escribe` vacío (Claude siempre puede escribir: tiene que pasar por la cola). |
| V16 | `visibilidad == "interna"` con `nodo` no nulo (un nodo siempre tiene botón). |
| V17 | `operador` con `datos_del_operador` cuyo `dato` no coincide literal con un `dato` de `requiere`/`produce` del nodo, o cuya `accion` no es un `script` declarado. Un `accion: null` es **aviso**, no error. |
| V18 | `habilitada: false` sin `motivo`. |
| V19 | Un id de `tras_escribir` no es una acción `script`, `interna`, `idempotente`. |

`python Ads/_TOOLS/flujo.py --validar` sigue siendo el que garantiza que los `name` de agentes y
skills existen: por V5, si la acción coincide con FLUJO.json y FLUJO.json valida, la acción valida.

**Gate:** `test_gen_app.py` entra a la lista del gate §2.6 (serán 16 `test_*.py`).

### 2.5 Contrato de la API de acciones

La app carga el manifiesto de `VITALCOM_BASE` al arrancar y cada vez que cambia su `mtime`, y lo
hace validar con `gen_app.py --validar-manifiesto --json` (la app no re-implementa las reglas;
solo parsea la estructura con Pydantic para tiparla). Estado en memoria: `ok` / `sin_acciones`
(v6) / `invalido` (+ problemas).

#### `GET /api/acciones?nodo=&producto_key=`
200 → `[{id, rotulo, nodo, ejecutor_tipo, parametros, requiere_confirmacion, aprobacion,
toca_meta, escribe, habilitada, motivo, tiempo_max_s, datos_del_operador}]`, solo `visibilidad:
"boton"`. Con `producto_key`, cada una suma `disponible: bool` y `por_que` (el `estado` y los
`bloqueantes` que devuelve `flujo.py` para ese nodo, tal cual). Con manifiesto inválido → 503.

#### `POST /api/acciones/{accion_id}`
Request:
```json
{"parametros": {"producto_key": "TINNIDROP"},
 "confirmado": true,
 "job_id": "3f2a…(32 hex, lo genera el frontend al abrir el diálogo)"}
```
Orden de validación y respuestas (la primera que falla corta):

| # | Condición | Código | `codigo` en el cuerpo |
|---|---|---|---|
| 1 | Manifiesto inválido | 503 | `MANIFIESTO_INVALIDO` (+ `problemas`) |
| 2 | Id no declarado, o manifiesto v6 sin acciones | **403** | `ACCION_NO_DECLARADA` |
| 3 | Acción `interna` | **403** | `ACCION_INTERNA` |
| 4 | `habilitada: false` | 409 | `ACCION_DESHABILITADA` (+ `motivo`) |
| 5 | `ejecutor_tipo == "operador"` | 409 | `ES_DEL_OPERADOR` (+ `datos_del_operador`) |
| 6 | Parámetro faltante, sobrante o inválido (§2.2.1) | 422 | `PARAMETRO_INVALIDO` (+ campo) |
| 7 | `requiere_confirmacion` y `confirmado` no es `true` | 428 | `FALTA_CONFIRMACION` (+ `escribe`, `tiempo_max_s`, `toca_meta`) |
| 8 | Claude: `claude auth status` sin sesión, o `ANTHROPIC_API_KEY`/`CLAUDE_CODE_OAUTH_TOKEN` en el entorno | 503 | `CLAUDE_SIN_SESION` / `CLAUDE_CREDENCIAL_PROHIBIDA` |
| 9 | `precondicion: nodo_listo` y `flujo.py <pk> --json --sin-escribir` no dice nodo actual = este y `LISTO_PARA_EJECUTAR` | 409 | `NODO_NO_LISTO` (+ `nodo_actual`, `estado`, `bloqueantes` tal cual) |
| 10 | Ya hay un trabajo activo para ese producto (o para esa acción global) | 409 | `YA_EN_CURSO` (+ `job_id` existente) |
| — | Mismo `job_id` que un trabajo ya creado | 202 | mismo cuerpo que la primera vez, `repetido: true` |
| — | OK | **202** | ver abajo |

```json
{"job_id": "3f2a…", "accion_id": "nodo.F2.plan", "estado": "ENCOLADO",
 "url_estado": "/api/trabajos/3f2a…", "url_eventos": "/api/trabajos/3f2a…/eventos"}
```

- El 403 es la compuerta de la regla 2.3: **ningún camino** del runner ejecuta algo que no salga
  de una acción declarada, y la API no expone las internas.
- Todos los errores usan el mismo cuerpo: `{"detail": "<frase para el operador>", "codigo": "…"}`.
- Esto reemplaza la lista blanca fija de `escrituras.py` (handoff §5.1).

---

## 3 · PARTE B — el runner (`workflows.py`, `claude.py`, `bitacora.py`)

### 3.1 Piezas y responsabilidades

| Módulo | Hace | No hace |
|---|---|---|
| `acciones.py` (nuevo) | Carga y tipa el manifiesto, pide la validación a `gen_app.py`, valida parámetros, **resuelve el argv** (placeholders + banderas). Único lugar que sabe qué es una acción. | No ejecuta nada. |
| `workflows.py` (nuevo) | DBOS: configuración, colas, workflows padre por tipo, unidades de escritura, aprobaciones, estado publicado con `set_event`. | No arma comandos a mano: todo argv sale de `acciones.resolver()`. Ningún literal `.py`. |
| `claude.py` (nuevo) | Único que invoca Claude Code headless (handoff §5.2 entero). | No decide qué herramientas: las recibe de la acción. |
| `bitacora.py` (nuevo) | Crea la carpeta de la corrida y escribe los logs **append-only**, solo bajo `PRODUCTOS/_AUDITORIAS/app_runs/`. | Nada fuera de esa carpeta (prueba estructural). |
| `escrituras.py` (cambia) | `Cola` con latido y espera bloqueante; `refrescar_estado_derivado` desaparece (pasa a `tras_escribir`). `dar_de_alta`/`transcribir` pasan a ser llamadas al runner. | — |
| `sse.py` (nuevo) | `GET /api/trabajos/{id}/eventos`. | — |

### 3.2 Configuración de DBOS

```python
APP_VERSION = "wf-1"   # se sube SOLO si cambia la lista de pasos de un workflow (ver 3.7)

DBOS(config={
    "name": "vitalcom-app",
    "system_database_url": f"sqlite:///{datos_de_la_app() / 'dbos.sqlite'}",
    "application_version": APP_VERSION,
})
```
- `datos_de_la_app()` = `VITALCOM_DATOS` o `%LOCALAPPDATA%\VitalCom\` (fuera del repo, fuera del
  worktree; lo crea `config.py` al arrancar). Nunca dentro de `SISTEMA/`.
- `DBOS.launch()` en el `lifespan` de FastAPI (al arrancar recupera los PENDING de esta versión);
  `DBOS.destroy()` al cerrar. Las pruebas usan una SQLite temporal por sesión de pytest.
- Antes de escribir, **leer `docs.dbos.dev` para la versión instalada (3.0.0)**: nombres exactos de
  `Queue`, `SetEnqueueOptions(deduplication_id=…)`, `DBOS.set_event/get_event`,
  `DBOS.fork_workflow`, `DBOS.list_workflows`, `DBOS.list_workflow_steps`. El diseño usa solo esas
  primitivas; si alguna no existe con ese nombre, se reemplaza por su equivalente sin cambiar la
  forma.

### 3.3 Las dos colas y el lock ("un escritor a la vez")

```
POST /api/acciones/X ──► cola `trabajos` (concurrencia 8, deduplication_id = producto_key | accion_id)
                           │  workflow PADRE: sella, espera aprobaciones/respuestas, decide el estado
                           │  (no escribe nada él mismo)
                           ▼  enqueue + get_result()
                         cola `escritura` (concurrencia 1, global: vive en la SQLite de DBOS)
                           │  workflow UNIDAD: toma el lock de archivo con latido, ejecuta UN
                           │  comando (script o Claude), corre `tras_escribir`, suelta el lock
                           ▼
                         MOTOR (Ads/_TOOLS/*.py · Claude Code headless)
```

- **Por qué dos colas:** si el workflow que espera una aprobación ocupara el turno de escritura,
  una publicación esperando al operador trabaría toda la app durante horas. El padre espera sin
  turno; solo la unidad que escribe lo toma. Así "dos jobs que escriben se serializan" se cumple
  en la unidad, que es donde se escribe.
- **Deduplicación por producto:** `deduplication_id = producto_key` (o el `accion_id` si la acción
  no lleva producto) en la cola `trabajos`. Un segundo trabajo sobre el mismo producto mientras hay
  uno activo → `DBOSQueueDeduplicatedError` → 409 `YA_EN_CURSO`. Evita dos corridas de Claude
  pisándose el mismo paquete.
- **El lock de archivo sigue**, dentro de cada unidad: protege contra escritores que no pasan por
  DBOS (otra instancia de la app, una prueba, un script corrido a mano que adopte `Cola`).
  - `Cola(esperar=True, tope_s=tiempo_max_s)`: espera con sondeo cada 2 s en vez de fallar.
  - **Latido:** mientras la unidad corre, un hilo toca el `mtime` del candado cada 30 s. Un candado
    sin latido por **120 s** se considera de un proceso muerto y se borra. Se elimina
    `TIEMPO_MAXIMO_LOCK = 15 min`.
  - El candado guarda `{"pid", "job_id", "desde"}` para que la pantalla diga quién escribe.
  - El modo actual (`esperar=False` → `SistemaOcupado`) se conserva para quien lo use.
- **Qué NO cubre:** una sesión interactiva de Claude Code escribiendo en la misma carpeta a la vez.
  No usa el candado. Se documenta en la pantalla Trabajos ("si tenés una sesión de Claude abierta
  trabajando en el sistema, esperá a que termine").

### 3.4 Determinismo y el primer paso de todo padre

DBOS re-ejecuta el cuerpo del workflow al retomar y reemplaza cada paso ya hecho por su resultado
guardado. Por eso **nada no determinista vive fuera de un paso**: ni la fecha, ni leer el
manifiesto, ni `uuid`.

Todo padre empieza con el paso `sellar(job_id, accion_id, parametros)` que devuelve y deja
guardado:
```json
{"job_id": "…", "accion": { /* la acción completa, copiada del manifiesto de ese momento */ },
 "manifiesto_sha": "…", "hoy": "2026-09-18", "iniciado": "2026-09-18T10:15:02-06:00",
 "run_dir": "PRODUCTOS/_AUDITORIAS/app_runs/2026-09/20260918-101502_nodo.F2.plan_TINNIDROP_3f2a1c9e",
 "argv": ["python", "…"]}
```
Al retomar, el padre usa **esta** copia: si el manifiesto cambió entre la caída y el reinicio, el
trabajo sigue con la definición con la que arrancó.

### 3.5 Los workflows por tipo de ejecutor

Nombres de estado que ve el operador (salen de lo que el workflow publica con
`DBOS.set_event("estado", …)` y del estado de DBOS):

`ENCOLADO` · `CORRIENDO` · `ESPERA_APROBACION` · `ESPERA_RESPUESTA` · `EXITO` · `SIN_CUMPLIR`
(Claude terminó bien pero `flujo.py` dice que el nodo sigue pendiente) · `RECHAZADO` ·
`CADUCADO` · `FALLIDO` · `INTERRUMPIDO` (murió a mitad de un paso no idempotente; hay rastro) ·
`CSV_INVALIDO` (terminó, pero el barrido encontró un CSV malo) · `CANCELADO` · `OTRA_VERSION`.

#### (a) La unidad de escritura — `wf_unidad(job_id, n, spec)` en la cola `escritura`

```python
@DBOS.workflow()
def wf_unidad(job_id, n, spec):          # spec: {tipo: script|claude, argv|claude_args, idempotente, escribe}
    r = paso_ejecutar(job_id, n, spec)   # bajo Cola(esperar=True) con latido
    if spec["escribe"]:
        r["tras"] = paso_tras_escribir(job_id, n)   # barrido → flujo --todo → gen_app, bajo el lock
    return r

@DBOS.step()
def paso_ejecutar(job_id, n, spec):
    marca = bitacora.marca(job_id, n)            # <run_dir>/<n>.inicio y <n>.fin
    if marca.inicio_sin_fin() and not spec["idempotente"]:
        raise PasoInterrumpido(n)                # se retomó después de una caída: NO repetir
    marca.iniciar()
    with Cola(esperar=True, tope_s=spec["tiempo_max_s"]):
        salida = correr_script(spec) if spec["tipo"] == "script" else claude.correr(spec)
    marca.terminar(salida.resumen())
    return salida.resumen()
```
- **Así se cumple "retoma o queda FALLIDO con rastro, nunca a medias sin rastro":** al retomar,
  DBOS re-ejecuta el paso interrumpido; el paso ve `<n>.inicio` sin `<n>.fin`. Si el comando es
  idempotente (`flujo.py --todo`, `gen_decisiones.py`, `transcribir_videos.py`,
  `verificar_publicacion.py`), lo corre de nuevo y el log muestra los dos intentos. Si no lo es
  (Claude, `alta_producto.py`, `registrar_evento.py`), levanta `PasoInterrumpido` → la unidad
  termina `INTERRUMPIDO` con el log parcial guardado, y el padre no avanza.
- `paso_tras_escribir` corre **también si el comando falló** (una escritura a medias igual cambió
  el disco): barrido primero; si el barrido sale con código 2 el estado final es `CSV_INVALIDO`
  aunque el comando haya salido 0. Es idempotente y se reintenta solo.
- `correr_script`: `subprocess.Popen(argv, cwd=base, sin shell)`, stdout y stderr línea a línea a
  `<run_dir>/<n>_<accion>.log`, tope `tiempo_max_s` (al vencer: se mata el árbol de procesos y es
  `FALLIDO`). `salida: "json"` ⇒ parsea stdout; `{"ok": false}` o exit ≠ 0 ⇒ fallo con el
  `detalle` del script, no uno nuestro.
- El pid del subproceso se guarda en memoria por `job_id` para que `cancelar` lo pueda matar
  (`taskkill /T /F` en Windows): la cancelación de DBOS por sí sola solo actúa entre pasos.

#### (b) `script` — `wf_script(job_id)`

```
sellar → estado CORRIENDO → enqueue wf_unidad(n=1, spec del argv) → get_result
       → si la acción tiene nodo: paso_leer_flujo (flujo.py <pk> --json --sin-escribir)
       → EXITO | SIN_CUMPLIR | FALLIDO | INTERRUMPIDO | CSV_INVALIDO
```
(`nodo.ciclo.motor`, `producto.transcribir`, y `producto.alta` vía `POST /api/productos`.)

#### (c) `subagente` / `skill` — `wf_claude(job_id)`

```
sellar
→ paso_preparar_prompt  (prompt_nodo rellenado; allowedTools = herramientas_base + herramientas;
                         NUNCA herramientas de Meta en este workflow)
→ unidad n=1: claude.correr(prompt, allowed, presupuesto, tiempo)          [cola escritura]
→ bucle mientras el texto final tenga PREGUNTA_OPERADOR (máx. 5 vueltas):
      set_event("pendiente", {"tipo": "pregunta", "texto": …, "n": k})
      estado ESPERA_RESPUESTA
      r = DBOS.recv(f"respuesta:{k}", timeout_seconds = respuesta_max_horas·3600)
      si r es None → CADUCADO (la corrida queda en la bitácora; reintentar arranca de cero)
      unidad n=k+1: claude.correr(resume=session_id, prompt=r["texto"])     [cola escritura]
→ paso_leer_flujo: flujo.py <pk> --json --sin-escribir (después de tras_escribir)
→ EXITO si el nodo quedó CUMPLIDO · SIN_CUMPLIR con `falta_para_cumplir` tal cual · FALLIDO si
  claude devolvió is_error / subtype ≠ success
```
- **El veredicto no lo da el texto de Claude, lo da `flujo.py`.** Un subagente que "dice" que
  terminó pero no produjo lo que el nodo exige queda `SIN_CUMPLIR` con la lista de lo que falta.
  Ejemplo esperado: `nodo.F2.etapa-11` termina en `SIN_CUMPLIR` porque su `produce` es un
  `CAMBIO_BOT` que registra el operador al aplicar el cambio, y la pantalla lo dice así.
- Entre vueltas de pregunta, el padre **no** retiene el turno de escritura (cada vuelta es una
  unidad aparte).
- `--resume <session_id>` en modo `-p` hay que confirmarlo con una corrida corta al implementar
  (no está en el spike). Si no funciona, la respuesta se pasa como una corrida nueva con el prompt
  del nodo + "respuesta del operador a tu pregunta anterior: …" y se documenta.

#### (d) `operador`

No hay workflow: el `POST` devuelve 409 `ES_DEL_OPERADOR` con `datos_del_operador` (§2.5). La
pantalla ofrece, por cada dato faltante, la acción escritora declarada (`producto.transcribir`,
el alta) o dice "hoy se carga a mano en <dueño>" cuando la acción es `null`. Cuando el operador usa
esa acción, es un trabajo `script` normal.

> Faltan escritores declarados para `cuenta_alias` y `page_id` (bloqueantes de `F1.publicar`) y
> para el costo de un producto que ya tiene fila. Se agregan como scripts nuevos con test cuando el
> Hito 4 los necesite; hasta entonces el manifiesto los declara con `accion: null`.

#### (e) Acciones que tocan Meta — `wf_meta(job_id)` (mecanismo completo en el Hito 3, todas deshabilitadas)

El dueño del **cómo** sigue siendo la skill `publicar-meta` (sus 5 pasos). El workflow solo pone
el **cuándo** y la compuerta de aprobación entre el paso 2 y el 3.

```
sellar
→ M1 unidad: claude.correr(lectura)   "publicar-meta paso 1: pre-flight y volcado del snapshot"
          allowedTools = base + mcp__claude_ai_META_MCP__<lectura...>   (NINGUNA de escritura)
          → si Meta dice que la cuenta no tiene MCP (is_ads_mcp_enabled=false): FALLIDO
            "esta cuenta se pauta a mano" (lo dice Meta, no el init del conector)
→ M2 unidad: publicacion.paquete  (gen_publicacion.py --snapshot … --salida {run_dir}/paquete.json)
          exit 1 ⇒ FALLIDO con los bloqueantes y sus dueños (invariante 4)
→ paso_firmar_orden: orden = {tipo, llamadas no omitidas [n, tool, args], manifiesto}, sha256 del
          JSON canónico (sort_keys, sin espacios) = hash de la orden
→ set_event("pendiente", {"tipo": "aprobacion", "orden_id": 1, "hash": h, "orden": …})
  estado ESPERA_APROBACION
  a = DBOS.recv("aprobacion:1", timeout_seconds = caduca_horas·3600)
  · None                      → CADUCADO
  · a.decision == RECHAZADA   → RECHAZADO (+ evento ORDEN_REVOCADA si la orden venía del motor)
  · a.hash != h               → se ignora ese mensaje y se sigue esperando (aprobó otra cosa)
  · APROBADA con hash == h    → paso_sellar_aprobacion: {aprobada_el, valida_hasta, nota}
→ M3 unidad (la única con herramientas de ESCRITURA):
      dentro del MISMO paso, en este orden:
      1. si ahora > valida_hasta → CADUCADO, sin llamar a nada
      2. Claude (lectura): snapshot fresco  → 3. gen_publicacion.py --snapshot (regenera)
      4. el runner compara: llamadas no omitidas del paquete nuevo ⊆ llamadas de la orden aprobada
         (misma tupla n/tool/args). Si aparece una que no estaba → para: PENDIENTE de nueva
         aprobación (vuelve a set_event/recv con la orden nueva). Si ya no queda ninguna → nada
         que llamar.
      5. Claude (lectura + escritura exacta): "ejecutá EN ORDEN solo estas llamadas, literales,
         sustituyendo {{variables}}; parar al primer error (publicar-meta paso 3)"
→ M4 unidad: Claude (lectura) snapshot fresco → publicacion.verificar (--escribir los ad_id)
          exit 1 ⇒ FALLIDO "no activar: la secuencia quedó a medias" (se puede reintentar:
          M3 retomará sin duplicar)
→ M5 unidad: evento.registrar con --fuente "… · confirmado operador · app job=<id> orden=1",
          solo si esa firma no está ya en _EVENTOS.csv
→ paso_leer_flujo → EXITO | SIN_CUMPLIR
```

Para `ordenes.tipo = decision` (Hito 5) la forma es la misma con una orden por celda: `recv` por
orden, y M3 = leer la entidad → si ya está en el valor destino no se llama nada → si no,
`ads_update_entity` → M4 = `verificar_orden.py` (nuevo). Cada orden aprobada o rechazada por
separado (invariante 13, decisión del 09-sep-2026).

**Por qué es idempotente aunque DBOS repita el paso (al-menos-una-vez, spike C):** M3 re-ejecutado
vuelve a sacar un snapshot y a regenerar el paquete, así que lo ya creado sale `omitir: true` y no
se vuelve a llamar. Lo que no puede pasar es ejecutar algo que el operador no vio (paso 4) ni
ejecutar tarde algo que vio hace días (paso 1).

**Candados que no dependen del modelo:**
- `allowedTools` de M1, M4 y de todo `wf_claude` no incluye **ninguna** herramienta de escritura de
  Meta. Solo M3 las recibe, por nombre exacto (spike B: `dontAsk` no autoriza MCP y el comodín fue
  rechazado; bien, porque así no hay forma de colarlas).
- M3 no existe en el historial de un trabajo sin un `paso_sellar_aprobacion` antes. Prueba.

### 3.6 Aprobación y respuesta: `DBOS.send` / `DBOS.recv`

- El padre publica lo pendiente con `DBOS.set_event(job_id, "pendiente", {...})` y lo limpia al
  resolverlo (`set_event("pendiente", None)`). La API lo lee con `DBOS.get_event(job_id,
  "pendiente", timeout_seconds=0)`.
- `POST /api/trabajos/{job_id}/aprobaciones/{orden_id}`
  ```json
  {"decision": "APROBADA", "hash": "<el que mostró la pantalla>", "nota": ""}
  ```
  - 404 si el trabajo no existe · 409 `NO_ESPERA_ESA_ORDEN` si lo pendiente no es esa orden ·
    409 `HASH_DISTINTO` si el hash no coincide con el pendiente (no se envía nada) · 202 si se
    hizo `DBOS.send(job_id, {...}, topic=f"aprobacion:{orden_id}")`.
  - El botón **Aprobar** solo existe en la pantalla que muestra la orden completa (cada llamada con
    sus argumentos). El hash viaja desde lo que se mostró: lo que se aprueba es lo que se vio.
- `POST /api/trabajos/{job_id}/respuesta`  `{"n": 1, "texto": "…"}` → `DBOS.send(job_id, …,
  topic=f"respuesta:{n}")`. Mismos 404/409.
- La `recv` siempre tiene tope (`caduca_horas`, `respuesta_max_horas`). Nada queda esperando para
  siempre.

### 3.7 `application_version` y la pantalla de trabajos viejos

- `APP_VERSION` es una constante escrita a mano. DBOS solo retoma workflows PENDING de la misma
  versión; con el hash automático del código, cualquier arreglo después de una caída dejaría el
  trabajo huérfano (spike C, consecuencia 2).
- **Cuándo se sube:** cuando cambia el orden o la cantidad de pasos (`@DBOS.step`, `recv`,
  `set_event`, `enqueue`) de algún workflow, porque DBOS reemplaza pasos por posición.
- **Prueba `test_version_de_workflows`:** `workflows.py` declara `PASOS = {"wf_script": [...],
  "wf_claude": [...], "wf_meta": [...], "wf_unidad": [...]}` y la prueba (1) compara esa lista
  contra los pasos que de verdad llama cada workflow (recorriendo el AST) y (2) compara
  `sha256(PASOS)` contra un valor fijado junto a `APP_VERSION`. Si cambió la lista sin subir la
  versión, falla con el mensaje "subí APP_VERSION".
- **Trabajos de otra versión:** `GET /api/trabajos` marca `OTRA_VERSION` a los PENDING cuya
  `app_version` no es la actual. La pantalla ofrece dos botones: **Marcar fallido** (cancela en
  DBOS, deja la bitácora) y **Empezar de nuevo** (trabajo nuevo con los mismos parámetros). No se
  ofrece "continuar": ya no es el mismo código.
- **Reintentar** un trabajo `INTERRUMPIDO`/`FALLIDO` de la versión actual:
  `DBOS.fork_workflow(job_id, start_step=<paso que falló>)` → trabajo nuevo que reusa los
  resultados de los pasos anteriores (el sello y, en Meta, el paquete y la aprobación **no**: una
  aprobación no se hereda; si el paso que falló es posterior a la aprobación, el fork arranca desde
  la firma de la orden y se vuelve a pedir). El id del paso se obtiene de
  `DBOS.list_workflow_steps(job_id)`.

### 3.8 `claude.py` — contrato

```python
@dataclass
class ResultadoClaude:
    ok: bool                 # subtype == "success" y not is_error
    subtype: str
    session_id: str
    texto_final: str
    pregunta: str | None     # lo que siga a PREGUNTA_OPERADOR:, si está
    costo_equivalente_usd: float | None   # "equivalente": con la suscripción no se cobra
    num_turns: int | None
    duracion_s: float

def estado_sesion() -> dict            # `claude auth status` → {"logueado": bool, "detalle": str}
def correr(*, prompt: str, herramientas: list[str], presupuesto_usd: float,
           tiempo_max_s: int, log: Path, resume: str | None = None) -> ResultadoClaude
```
Todo lo del handoff §5.2, sin cambios: resolución del binario (`VITALCOM_CLAUDE_EXE` → PATH →
`~/.local/bin/claude.exe` → carpeta del escritorio, la más nueva); falla si ve
`ANTHROPIC_API_KEY` o `CLAUDE_CODE_OAUTH_TOKEN`; quita las `CLAUDE*`/`ANTHROPIC*` heredadas;
`-p … --output-format stream-json --verbose --include-hook-events --permission-mode dontAsk
--allowedTools … --max-budget-usd N` (+ `--resume <id>` si corresponde); nunca `--bare`;
`cwd = base()`. Cada línea de stdout va tal cual a `<run_dir>/<n>_claude.jsonl`.

Para las pruebas: `VITALCOM_CLAUDE_CMD` (lista JSON, p. ej. `["python", "tests/fake_claude.py"]`)
tiene prioridad sobre el binario. `fake_claude.py` emite un stream-json guionado (éxito, pregunta,
error, dormir N s, llamar a una herramienta Meta de lectura/escritura "falsa" escribiendo en un
archivo) según variables de entorno. Ninguna prueba llama al Claude real ni a Meta.

### 3.9 Bitácora de la corrida (`app_runs/`)

```
PRODUCTOS/_AUDITORIAS/app_runs/2026-09/20260918-101502_nodo.F2.plan_TINNIDROP_3f2a1c9e/
  trabajo.json        el sello (§3.4) + estado final + resumen por unidad (lo reescribe solo bitacora.py)
  1.inicio / 1.fin    marcas de la unidad 1
  1_claude.jsonl      salida completa de Claude
  2_gen_publicacion.log
  paquete.json        (lo escribe gen_publicacion.py vía {run_dir}: es el motor, no la app)
  aprobaciones.jsonl  cada aprobación/rechazo con hash, hora y nota (append-only)
```
- Decisión del handoff §5.2 ("decidirlo y dejarlo con test"): **la escribe el runner, declarada**.
  `bitacora.py` es el único módulo nuevo con permiso de escribir; prueba estructural: solo abre
  archivos bajo `app_runs/` (modo `a` o `x`, o reescritura atómica de `trabajo.json`), nunca un
  CSV, nunca `json.dump` fuera de esa carpeta. `test_la_app_no_escribe_en_el_sistema` suma
  `bitacora.py` a sus excepciones acotadas, igual que `subidas.py`.
- `PRODUCTOS/_AUDITORIAS/app_runs/` va a `.gitignore` (salida cruda y pesada; el informe de un
  hito sigue siendo un `.md` versionado).
- Verificar al implementar que `gen_grafo.py --comparar` no la cuente; si la cuenta, excluirla
  con test (regla §2.6 de la hoja).

### 3.10 Endpoints de trabajos

| Método y ruta | Qué devuelve |
|---|---|
| `GET /api/trabajos?estado=&producto_key=&limite=50` | Lista (más nuevos primero): `job_id, accion_id, rotulo, producto_key, estado, iniciado, terminado, app_version, otra_version, pendiente` (tipo, sin el detalle). De `DBOS.list_workflows` + `get_event`. |
| `GET /api/trabajos/{id}` | Lo anterior + `sello`, `unidades` (estado, duración, `costo_equivalente_usd`), `pendiente` completo (la orden o la pregunta), `resultado` (p. ej. `falta_para_cumplir` de `flujo.py`), `run_dir`. |
| `GET /api/trabajos/{id}/eventos` (SSE) | `event: estado` `{estado, unidad, detalle}` · `event: linea` `{unidad, texto, tipo}` · `event: pendiente` `{…}` · `event: fin` `{estado, resultado}`. `id:` = `<unidad>:<offset de bytes>`; con `Last-Event-ID` sigue desde ahí. Sondea cada 1 s el estado de DBOS y el crecimiento de los logs; cierra al `fin`. Para Claude, `linea` resume cada evento del stream-json (un `tool_use` de `Task` con `subagent_type=etapa-2` ⇒ "arrancó etapa-2"); el JSON crudo queda en la bitácora. |
| `POST /api/trabajos/{id}/aprobaciones/{orden_id}` | §3.6. |
| `POST /api/trabajos/{id}/respuesta` | §3.6. |
| `POST /api/trabajos/{id}/reintentar` | 202 con el `job_id` nuevo (fork, §3.7) · 409 si no está en `FALLIDO`/`INTERRUMPIDO`/`CADUCADO`. |
| `POST /api/trabajos/{id}/cancelar` | Mata el subproceso vivo (si hay) y `DBOS.cancel_workflow`. Estado `CANCELADO`; `tras_escribir` corre igual. |
| `GET /api/claude/estado` | `estado_sesion()` + si la credencial prohibida está en el entorno. La pantalla lo muestra antes de ofrecer botones de Claude. |

**Cambios a endpoints que ya existen:**
- `POST /api/productos` (multipart) se queda: guarda los archivos en el temporal (`subidas.py`),
  arranca `wf_script` con `producto.alta` y **espera** el resultado (`handle.get_result()`, tope
  120 s) dentro del `with carpeta_temporal()`, para que los archivos existan mientras el script
  corre. Respuesta igual que hoy (201 con la salida del script); 409 si la cola de escritura no
  la tomó en el tope.
- `POST /api/productos/{pk}/transcribir` se reemplaza por `POST /api/acciones/producto.transcribir`
  (202 + progreso en vivo; transcribir tarda minutos). La ruta vieja devuelve 410 con el nuevo
  camino, o se borra junto con su uso en el frontend.

---

## 4 · Pruebas del Hito 3 (qué prueba cada criterio de aceptación)

Todas sobre un **sistema de fixture** (copia mínima: `DOCTRINA/FLUJO.json` de juguete,
`VISTAS/_MANIFIESTO.json` v7 de juguete, `PRODUCTOS/*.csv` mínimos y scripts falsos en
`Ads/_TOOLS/`), con `VITALCOM_BASE` apuntando ahí, SQLite de DBOS temporal y `fake_claude.py`.
`config.base.cache_clear()` en un `finally` (trampa 4 del handoff).

| Prueba | Criterio |
|---|---|
| `test_accion_no_declarada_403` · `test_accion_interna_403` · `test_manifiesto_v6_todo_403` | Acción no declarada → 403 (hoja, Hito 3). |
| `test_deshabilitada_409_con_motivo` · `test_operador_409_con_escritores` · `test_falta_confirmacion_428` · `test_parametro_invalido_422` · `test_nodo_no_listo_409` | Contrato §2.5. |
| `test_dos_escrituras_se_serializan` | Dos trabajos con un script falso que anota `inicio/fin` con marca de tiempo y duerme 2 s: los intervalos no se solapan. |
| `test_mismo_producto_409_ya_en_curso` | Deduplicación de la cola `trabajos`. |
| `test_caida_script_idempotente_retoma` | Proceso hijo (patrón del spike C) que muere con `os._exit` a mitad de la unidad; al relanzar, el trabajo termina `EXITO` y el log tiene los dos intentos. |
| `test_caida_claude_queda_interrumpido` | Igual con `fake_claude.py`: al relanzar, `INTERRUMPIDO` con `1.inicio` sin `1.fin` y el `.jsonl` parcial. Nunca `PENDING` para siempre. |
| `test_lock_con_latido` | Un candado con latido no se borra a los 150 s simulados; uno sin latido sí. |
| `test_meta_no_ejecuta_sin_aprobacion` | `wf_meta` con fake: sin `send` no hay llamada de escritura; `RECHAZADA` → ninguna; hash distinto → ninguna; timeout → `CADUCADO`. |
| `test_meta_reintento_no_duplica` | M3 re-ejecutado con un snapshot falso que ya tiene la campaña: la llamada sale `omitir` y no se llama. |
| `test_meta_llamada_nueva_pide_reaprobacion` | El paquete regenerado trae una llamada que no estaba: vuelve a `ESPERA_APROBACION`. |
| `test_aprobacion_caducada_no_ejecuta` | `valida_hasta` vencido al retomar M3 → `CADUCADO`, sin llamadas. |
| `test_escritura_meta_solo_en_m3` | Ningún `allowedTools` de otro paso ni de `wf_claude` contiene una herramienta de escritura de Meta. |
| `test_evento_no_se_duplica` | M5 repetido con la firma ya presente en `_EVENTOS.csv`: no llama a `registrar_evento.py`. |
| `test_version_de_workflows` | §3.7. |
| `test_claude_*` | Credencial prohibida → error claro; env sin `CLAUDE*`/`ANTHROPIC*`; nunca `--bare`; `--resume` solo con `session_id`. |
| Estructurales (`test_sin_aritmetica.py`) | Ningún literal `.py` en `workflows.py`/`escrituras.py`/`acciones.py` (todo argv sale del manifiesto; reemplaza la lista blanca de `test_los_cambios_pasan_por_un_script_del_motor`); nunca `shell=True`; `bitacora.py` solo escribe bajo `app_runs/`; la regla sin aritmética sigue verde (el hash y las comparaciones de hora no mencionan conceptos de negocio). |
| `Ads/_TOOLS/test_gen_app.py` | V1-V19 + que el `_MANIFIESTO.json` real del worktree valide. |

Más el gate §2.6 completo en verde, como siempre.

---

## 5 · Decisiones cerradas (operador de acuerdo, 18-sep-2026) y lo que vuelve a Opus

Las tres salen de reglas que el sistema ya tenía; no son preguntas abiertas. El operador las
confirmó el 18-sep-2026. La sesión de implementación no las reabre.

1. **La unidad de aprobación de una publicación es el paquete entero**, mostrado llamada por
   llamada. Sale de `publicar-meta`: todo nace PAUSED, no gasta, y la activación es aparte.
   Pausar, escalar y activar mueven plata y se aprueban **de a una orden** (invariante 13).
2. **Una aprobación caduca a las 12 h** (`caduca_horas`). Es la misma lógica que el requisito
   de FLUJO.json de tener el snapshot de Meta con edad máxima de 1 día y que el rezago de
   invariante 13: no se ejecuta algo aprobado sobre un estado viejo. El lanzamiento igual queda
   PAUSED y con `start_time` a las 4 AM.
3. **Un nodo de Claude que se cae a mitad no se repite solo**: queda `INTERRUMPIDO` y se reintenta
   completo (invariante 5: rerun completo, nunca parche parcial).

**No se implementa en el Hito 3; vuelve a Opus** (handoff §6):
- Habilitar `F1/F2/F3.publicar`: spike de `ads_creative_upload_media` en headless.
- Habilitar `F2.conceptos`: spike de `claude-in-chrome` en headless.
- `gen_ordenes.py` y `verificar_orden.py` (Hito 5) y el generador de la orden de activación.
- Los escritores de `cuenta_alias`, `page_id` y del costo de un producto con fila.

---

## 6 · Lista de trabajo para la sesión de implementación (Sonnet)

En este orden; cada punto cierra con sus pruebas en verde antes del siguiente.

1. `Ads/_TOOLS/test_gen_app.py` cubriendo la validación v6 que ya existe (sin cambiar
   `gen_app.py`). Verde.
2. `gen_app.py`: `validar_acciones()` (V1-V19) + `--validar-manifiesto [--json]`, con sus casos
   en `test_gen_app.py`. `flujo.py --validar` y el resto del gate siguen verdes.
3. `VISTAS/_MANIFIESTO.json` → v7 con el bloque de §2.1 y §2.3 y una línea nueva en `_leeme`.
   `python Ads/_TOOLS/gen_app.py --validar-manifiesto` sale 0. (Es el manifiesto del worktree; la
   carpeta real se actualiza al mergear, con confirmación del operador.)
4. `app/backend`: `acciones.py` + `GET/POST /api/acciones` con los 403/409/422/428/503, todavía
   sin DBOS (el POST válido puede devolver 501 hasta el punto 6). Pruebas de §4 del contrato.
5. `escrituras.Cola` con latido y espera; `bitacora.py`; `.gitignore` con `app_runs/`.
6. `dbos` en `pyproject.toml` (**parar el servidor antes de `uv sync`**, trampa 1);
   `workflows.py` (`wf_unidad`, `wf_script`) + `APP_VERSION` + `test_version_de_workflows`;
   `POST /api/acciones` real; migrar alta y transcribir.
7. `claude.py` + `fake_claude.py` + `wf_claude` (con preguntas). Una corrida corta real de
   `--resume` en modo `-p` para confirmar §3.5(c).
8. `wf_meta` completo contra fakes, **sin** habilitar ninguna acción Meta en el manifiesto.
9. `sse.py`, endpoints de trabajos, pantalla **Trabajos** (lista, estado, log en vivo, aprobar /
   rechazar con la orden a la vista, responder, reintentar, cancelar, trabajos de otra versión).
   Tipos del frontend regenerados del OpenAPI.
10. Gate §2.6 completo, commit y push en `feat/app-web`, PR a `main`. **Merge solo con
    confirmación del operador.**
