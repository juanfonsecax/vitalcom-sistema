---
name: generar-imagenes-chatgpt
description: RENDERIZA los creativos en ChatGPT web conduciendo el Chrome logueado del operador. Toma el paquete de prompts que ya produjo armar_prompts_fase2.py (prompt + foto del producto + imagen de referencia del swipe), adjunta las 2 imágenes, envía, espera la generación, descarga el PNG con el nombre canónico y lo deja en Ads/MEDIA_[PRODUCTO]/. Úsala cuando el operador dice "generá las imágenes", "renderizá los conceptos", "bajá los creativos de FASE 2", "hacé las imágenes de [PRODUCTO]" o cuando _DIM_CREATIVOS.csv tiene filas en PENDIENTE_GENERAR. Requiere que el operador tenga sesión abierta en chatgpt.com.
tools: Read, Glob, Grep, Bash, Write
---

# GENERAR-IMAGENES-CHATGPT — EL RENDERIZADOR

## Rol

Cierra el hueco entre **el prompt** y **el archivo en disco**. `etapa-9` y
`generar-conceptos` entregan prompts resueltos; esta skill los convierte en PNG.

> **No inventa contenido.** No escribe copy, no elige conceptos, no decide qué
> generar. Recibe un paquete ya resuelto y lo renderiza. Si un prompt trae una
> variable sin resolver, **se detiene** — no la rellena.

## DE DÓNDE SALE CADA COSA (un dato, un dueño)

| Insumo | Dueño |
|---|---|
| El prompt resuelto y qué 2 imágenes lleva | `Ads/_TOOLS/armar_prompts_fase2.py` → `PROMPTS_FASE2_[ANGULO].txt` |
| El nombre del archivo de salida | El mismo paquete, línea `Guardar archivo generado como:` |
| La carpeta destino | `Ads/MEDIA_[PRODUCTO]/` (invariante 8 de `CLAUDE.md`) |
| El registro del creativo | `PRODUCTOS/_DIM_CREATIVOS.csv` — lo escribe `etapa-9`, **no esta skill** |
| Compliance de copy en el ad | `DOCTRINA/COPYWRITING_ADS.md` |

---

## REGLA DE ORO: TODO POR JAVASCRIPT, CASI NADA POR PANTALLA

Medido el 07-sep-2026 sobre 6 generaciones: **simular clicks y tecleo falla de
forma intermitente y silenciosa**; ejecutar JS en la página no falla y además no
gasta contexto en capturas.

| No hagas esto | Hacé esto |
|---|---|
| `computer type` para el prompt | `document.execCommand('insertText', …)` |
| `computer key Return` para enviar | click en `[data-testid="send-button"]` |
| `screenshot` para ver si terminó | leer el DOM por JS |
| `screenshot` para validar el texto | medir `innerText.length` por JS |

Los screenshots quedan solo para diagnosticar cuando algo ya falló.

---

## PRE-REQUISITOS

1. **Sesión abierta.** El operador debe tener `chatgpt.com` logueado en su Chrome.
   Esta skill **NO inicia sesión** y **NO pide credenciales**.
2. **Chrome conectado y ELEGIDO.** `list_connected_browsers`. Si hay más de uno,
   se pregunta con `AskUserQuestion` cuál usar — nunca elegir solo.

   > ⚠ **Esa pregunta se hace en la sesión principal, NO dentro de `etapa-render`.**
   > Los subagentes no tienen `AskUserQuestion`: si la etapa la necesita, se traba
   > sin poder preguntar (pasó el 07-sep-2026).
   >
   > **El orquestador elige el navegador ANTES de invocar la etapa** (`switch_browser`
   > o `select_browser`). Esa selección persiste a nivel de cuenta, así que la etapa
   > la hereda: **`etapa-render` no llama `list_connected_browsers` ni `select_browser`
   > — usa el navegador que ya está activo y arranca en `navigate`.**
   >
   > No sirve pasarle un `deviceId`: `list_connected_browsers` devuelve los nombres y
   > los ids pero **nunca dice cuál está seleccionado**, y `switch_browser` tampoco lo
   > devuelve. El único que sabe cuál es el bueno es el operador, en el momento de
   > hacer clic en Connect.
3. **Las 2 imágenes existen en disco**, suma < 10 MB (límite de `file_upload`).

---

## EL FLUJO — 7 PASOS, TODOS EJECUTADOS Y MEDIDOS (07-sep-2026)

### 1 · Conectar y abrir pestaña propia
```
navigate → https://chatgpt.com     (crea el grupo de pestañas solo)
computer wait 10                    ← la página necesita hidratar
```
> **Esperar 10 s no es opcional.** Con 4 s, el primer intento escribió solo los
> caracteres acentuados del prompt (`áñóáéóó…`) y perdió todo el ASCII.

### 2 · Localizar el input de archivos
```
find "file input for attaching images"
```
Devuelve varios; **el bueno es siempre el primero** (`ref_206` en la práctica,
el del formulario principal). Los refs cambian entre sesiones — buscarlos
siempre, nunca hardcodearlos.

### 3 · Adjuntar las 2 imágenes EN ORDEN
```
file_upload {ref: <el primero>, paths: [<REFERENCIA>, <PRODUCTO>]}
```
**El orden es la semántica.** Primera = referencia visual del swipe;
segunda = foto real del producto. Invertirlas produce un anuncio del
producto del competidor.

> ⚠ **Nunca hacer click en el botón de adjuntar.** Abre el diálogo nativo de
> Windows, invisible para el agente, y deja la sesión colgada.

### 4 · Insertar el prompt — tres traducciones obligatorias

**(a) Las rutas de disco no significan nada para ChatGPT.** Reescribir
`IMAGEN 1 (Referencia visual): Ads/_SWIPE/…` como
**"IMAGEN 1 (la primera adjunta, referencia visual)"**.

**(b) Sin saltos de línea.** Aplanar a un párrafo con separadores (`. ` / ` / `).

**(c) El prompt se escribe en ASCII puro** (sin tildes ni ñ), y se le ordena al
modelo que la imagen sí lleve todos los acentos. Los caracteres especiales son
los que se corrompen al inyectarse. Cerrar el prompt con:

> `MUY IMPORTANTE: todo el texto de la imagen en espanol de Guatemala con voseo
> y CON TODOS LOS ACENTOS Y TILDES CORRECTOS, sin errores ortograficos.
> Replica fielmente todos los elementos de la IMAGEN 1: sellos, badges,
> certificaciones, estrellas, tarjetas de resena y cifras de respaldo. Si la
> referencia lleva un sello o un badge, el mio tambien lo lleva. Si la referencia
> muestra un numero de registro, usa EXACTAMENTE estos y ningun otro:
> MSPAS NS02026-GT3147 y FDA 30045469041. Si la referencia no muestra numero,
> el sello va sin numero.`

```js
const ta=document.querySelector('#prompt-textarea');
ta.focus();
document.execCommand('insertText', false, TXT);
await new Promise(r=>setTimeout(r,800));
({len:ta.innerText.length, thumbs:document.querySelectorAll('form img').length})
```

**Gate:** `len` debe coincidir con el largo esperado y `thumbs` debe ser **2**.
Si `len` es 0 o parcial, reintentar — **nunca enviar a ciegas**.

### 5 · Enviar por el botón, no por Enter
```js
const b=document.querySelector('[data-testid="send-button"]');
const ok=b&&!b.disabled; if(ok)b.click();
await new Promise(r=>setTimeout(r,2500));
({enviado:ok, path:location.pathname})
```
**Gate:** `path` tiene que pasar de `/` a `/c/…`. Si sigue en `/`, no se envió.
`Return` funcionó a veces y otras no; el botón funcionó siempre.

### 6 · Esperar (~2 a 2,5 min) y descargar con el nombre canónico
```js
const img=[...document.querySelectorAll('img')].find(i=>i.alt&&i.alt.startsWith('Imagen generada'));
if(!img){({listo:false, retoque:document.body.innerText.includes('retoque')})}
else{
  const r=await fetch(img.src); const b=await r.blob();
  const a=document.createElement('a');
  a.href=URL.createObjectURL(b); a.download='<NOMBRE_CANONICO>.png';
  document.body.appendChild(a); a.click();
  await new Promise(r=>setTimeout(r,4000));   // dejar que Chrome escriba
  a.remove();
  ({listo:true, ok:r.ok, bytes:b.size, alt:img.alt})
}
```
Estados intermedios: sin respuesta → arrancando · `retoque:true` → faltan ~30 s ·
`alt` que empieza en `Imagen generada:` → terminada. Sondear cada ~40 s.

Verificar `ok:true` y `bytes` > 500 000.

### 7 · Confirmar en disco ANTES de cerrar o navegar

**Buscar por FECHA, nunca por nombre.** Chrome ignora el atributo `a.download` en estos
blobs y guarda con el nombre que le pone ChatGPT (`ChatGPT Image 8 sept 2026, 10_39_17.png`).
El nombre canónico se lo ponemos nosotros al mover:

```bash
P=$(ls -t "$HOME/Downloads"/*.png 2>/dev/null | head -1)
[ -n "$P" ] && [ -z "$(find "$P" -mmin +3)" ] && mv "$P" "Ads/MEDIA_<PRODUCTO>/<NOMBRE>.png"
```
(el `find -mmin +3` descarta un PNG viejo que ya estuviera en Downloads: si el más reciente
no bajó en los últimos 3 minutos, la descarga no ocurrió.)

> 🔴 **Esto costó tres corridas el 08-sep-2026.** El paso hacía
> `test -f "$HOME/Downloads/<NOMBRE>.png"`, con el nombre canónico. Como Chrome guardaba con
> otro nombre, el test daba falso y `etapa-render` reportaba "descarga bloqueada, diálogo
> nativo de Windows" — dos veces, con cuatro métodos distintos probados en vano. **El archivo
> estaba en Downloads desde el principio.** CN01 se dio por perdida y se recuperó a mano.
> Si el `fetch` devolvió `ok:true` y bytes, el archivo bajó: buscalo por fecha antes de
> declarar cualquier bloqueo.
> ⚠ **Se perdió una generación entera por saltarse esto.** El `a.click()` inicia
> una descarga asíncrona: si se cierra la pestaña o se navega antes de que Chrome
> escriba el archivo, **el blob muere y hay que regenerar** (2,5 min y una
> generación de la cuota). Confirmar el archivo, después navegar.

Después, abrir la imagen con `Read` y pasarla por el gate de abajo.

---

## DOCTRINA: SE REPLICA EL DISPOSITIVO DEL GANADOR, COMPLETO

**El sistema se basa en copiar la estructura que ya vendió en el mercado GT.**
Si la pieza de referencia lleva un sello de certificación, un badge de garantía,
tarjetas de reseña con estrellas o cifras de respaldo, **la nuestra los lleva
también**. Ese elemento está ahí porque le funcionó al que lo pauta, y quitarlo
es cambiar el concepto que se está testeando — justo lo que la FASE 2 no permite.

Los productos del portafolio **tienen MSPAS, FDA y garantía**. El sello no es un
adorno inventado: es un dato real que la pieza debe mostrar tan visible como lo
muestra el competidor.

> **No es tarea de esta skill decidir si un elemento del concepto "se puede"
> poner.** Su trabajo es que la ejecución salga fiel y sin defectos.

### Los números de registro: manda la referencia

Igual que todo lo demás, el número lo decide **la IMAGEN 1**:

| La pieza de referencia… | Entonces la nuestra… |
|---|---|
| muestra un número de registro | lleva **el nuestro, el real** |
| muestra el sello sin número | lleva el sello **sin número** |

Los números reales aplican a **todo el portafolio** y viven en
`DOCTRINA/PLANTILLAS_DEFAULTS_OPERADOR.md`:

- `[REG_MSPAS]` = **NS02026-GT3147**
- `[REG_FDA]` = **30045469041**

**Esos son los únicos que se escriben.** El 07-sep el modelo, por su cuenta,
inventó `No. NS02025-GT2599` — un número que no es de nadie. Si en una pieza
aparece un registro que no coincide con los de arriba, se regenera. No es una
restricción de concepto: es que el número tiene un valor correcto y hay que
usar ese.

---

## GATE DE CALIDAD — OBLIGATORIO, UNA POR UNA

Esto no filtra el concepto: filtra la **ejecución**. Son defectos que hacen que
la pieza se vea barata o que el ad sea rechazado por algo evitable.

| Revisar | Detalle |
|---|---|
| **EL ENVASE** | Que el frasco de la pieza sea el del packshot que se adjuntó: mismo color, misma marca impresa, misma forma. Si no coincide, se regenera aunque el texto esté perfecto — **un envase equivocado no es un defecto estético, es otro producto**. Esto mira el ENVASE, no la paleta de la pieza: el fondo, las hojas o lo que pida el concepto van del color que corresponda |
| **Ortografía** | El defecto más frecuente: ~1 falta cada 2 imágenes, siempre en palabras largas — `Desinfilaman` (por Desinflaman), `RESISTENCUA` (por RESISTENCIA). Leer TODO el texto de la pieza, palabra por palabra |
| **Voseo** | El defecto típico está en el CTA y los cierres: `¡Empieza hoy!` en vez de `¡Empezá hoy!`. Parte viene de los prompts fuente, no del modelo |
| **Tildes perdidas en MAYÚSCULAS** | Efecto secundario de escribir el prompt en ASCII: el modelo repone casi todas las tildes, pero se le escapan las de palabras cortas en mayúscula del CTA — salió `PEDI EL TUYO` con `AQUÍ` bien acentuado al lado. Revisar el botón de WhatsApp letra por letra |
| **Número de registro equivocado** | Si la pieza muestra un registro, tiene que ser `NS02026-GT3147` (MSPAS) o `30045469041` (FDA). Cualquier otro número lo inventó el modelo — se regenera |
| **Paleta contra el avatar** | Si `_DIM_CREATIVOS.csv` fija paleta azul para un avatar masculino, una pieza rosa se regenera — la nota del propio CSV dice que el rosa espanta a ese avatar |
| **Fidelidad al dispositivo** | Que el canónico se haya cumplido: si es CN05 tienen que estar las 5 filas; si es CN04, la escalera tiene que SER el anuncio, no un bloque adentro |
| **Proporción** | ~1122×1402 (4:5). Si vuelve cuadrada, se repite |
| **Antes/después de rostro** | Solo como AVISO al entregar, no como bloqueo: Meta restringe ese formato en salud y belleza, así que esperá más rechazos en `CN01_ANTES_DESPUES` y `CN02_TIMELINE`. Si el swipe ganador lo usa, se lanza igual y se mide |

---

## LOTES

**Secuencial, un chat por concepto.** ChatGPT Go encola las generaciones: abrir
pestañas en paralelo no acelera y hace perder qué imagen es de qué concepto.

Ciclo por concepto: `navigate` → `find` → `file_upload` → insertar → enviar →
esperar → descargar → **confirmar en disco** → siguiente.
Presupuestar **~2,5 min por imagen** (5 conceptos ≈ 15 min).

> **Mejora pendiente de medir (NO VERIFICADO):** un **Proyecto** de ChatGPT con
> la foto del producto fija en sus archivos, para no resubirla en cada concepto.

---

## LÍMITES DUROS

1. **No inicia sesión.** Nunca escribir contraseñas ni códigos 2FA.
2. **No resuelve CAPTCHAs.** Si aparece uno, detenerse y avisar.
3. **No instala nada.** En particular **no** `chrome-use` /
   `agent-browser-stealth`: su función es falsificar el token de Cloudflare
   Turnstile y pide una extensión con acceso a todo el Chrome del operador
   —incluido Meta Ads y el banco. Auditado y descartado el 07-sep-2026.
4. **Una pestaña propia**, creada por la skill y cerrada al terminar —
   después de confirmar las descargas.
5. **No escribe en `_DIM_CREATIVOS.csv`.** Ese es el dueño de `etapa-9`.

---

## SALIDA

Reportar por concepto, con el gate explícito:

```
CONCEPTO  ARCHIVO                              BYTES      GATE
CN10      CLEARSTEM_F2_CN10_RESISTENCIA_.png   1 895 262  OK
CN01      CLEARSTEM_F2_CN01_RESISTENCIA_.png   2 121 817  BLOQUEA: No. de registro inventado
CN02      CLEARSTEM_F2_CN02_RESISTENCIA_.png   2 075 958  CORREGIR: "Desinfilaman"
```

Y decir explícitamente **qué falta**: los conceptos no generados y por qué.
