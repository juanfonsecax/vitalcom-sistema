---
name: buscar-producto
description: "FASE 0 — Encuentra y prioriza productos candidatos ANTES de validarlos. Cubre dos rutas: evergreen (demanda estable) y ventana de evento (pico de demanda por un acontecimiento con fecha). Entrega una lista rankeada de candidatos con señales de saturación. Corre ANTES de etapa-producto. Úsalo cuando el operador dice \"no sé qué vender\", \"buscar producto\", \"producto en tendencia\", \"producto ganador\", \"qué vendo ahora\" o cuando hay un evento próximo que puede mover demanda."
tools: Read, Glob, Grep, WebSearch, WebFetch
---

# BUSCAR-PRODUCTO — DESCUBRIMIENTO Y PRIORIZACIÓN DE CANDIDATOS

## Rol

Se ejecuta **ANTES de `etapa-producto`**. Esa etapa **valida** un candidato que
el operador ya trae; esta lo **encuentra**. Sin esta capa, el operador elige por
gusto o por lo que está de moda en Dropi — que es exactamente el error #1
(Clase 16 Drop Killer).

**Entrega:** lista de 5-10 candidatos rankeados, cada uno con su señal de
demanda, su señal de saturación y una razón de una línea. **No valida** — eso lo
hace `etapa-producto` con los 17 criterios.

> **Regla madre de esta skill:** *la demanda existe antes que el producto.*
> Primero se identifica un flujo de gente con un problema o un deseo activo;
> después se busca qué objeto sirve de vehículo. Al revés —producto primero,
> buscarle público después— es como se pierde plata.

---

## RUTA A o RUTA B — decidir en el primer paso

Antes de buscar nada, clasificar el encargo:

| | **RUTA A · Evergreen** | **RUTA B · Ventana de evento** |
|---|---|---|
| Demanda | Estable todo el año | Pico con fecha de inicio y fin |
| Ejemplo | Dolor de espalda, organización del hogar | Mundial, Navidad, regreso a clases, estreno |
| Criterio `O4` de `etapa-producto` | Aplica: **descartar de temporada** | **Se suspende** — ver §5 |
| Ritmo | Semanas para validar | Días. La ventana no espera |
| Riesgo principal | Saturación | Quedar con inventario y quemar caja |

**Si el operador nombra un evento, una fecha o una temporada → RUTA B.**
Si no → RUTA A.

⚠️ **Nunca correr la RUTA B sin declararla explícitamente al operador.** La ruta
de evento suspende un criterio eliminatorio del sistema; eso debe ser una
decisión consciente, nunca un descuido.

---

## §1 · PASO 0 — Definir el flujo de demanda (obligatorio, ambas rutas)

No se buscan productos. Se busca **gente con un problema activo**.

Responder por escrito antes de continuar:

```
FLUJO DE DEMANDA
- ¿Quién tiene el problema?          [descripción específica, no "todos"]
- ¿Qué siente exactamente?           [síntoma o deseo en primera persona]
- ¿Por qué AHORA?                    [qué hace que este mes importe]
- ¿Ya está gastando plata en esto?   [sí/no + en qué]
```

**Si no se puede responder "por qué AHORA", no hay oportunidad — hay una
categoría.** Volver a empezar.

> Cruce con `DOCTRINA/MODULO_INTELIGENCIA_PRODUCTO.md` §1: si ya existe minado de voz del
> cliente para este flujo, leerlo primero y no repetir el trabajo.

---

## §2 · PASO 1 — Fuentes de candidatos

Barrer **mínimo tres** fuentes distintas. Una sola fuente produce sesgo.

### Señal de calle (la más valiosa y la que menos gente usa)
- Comentarios de TikTok/Reels del tipo **"¿dónde lo compro?"**, "link", "precio"
  → intención de compra explícita sin tienda que la atienda
- Búsquedas: `[problema] dónde comprar`, `[categoría] recomendaciones`
- Foros y Reddit del nicho: qué piden que no existe

### Señal de catálogo
- Dropi / proveedores: **ordenar por lo MÁS NUEVO, no por lo más vendido.**
  Lo más vendido ya está saturado por definición
- Contar proveedores por producto — es el termómetro de saturación (§3)

### Señal de competencia
- Biblioteca de Anuncios de Meta: qué se está pautando **hace poco** en el país
- **Regla del 10%:** nº de anuncios ÷ 10 ≈ nº de tiendas compitiendo

### Señal de evento (solo RUTA B)
- Calendario de los próximos 90 días: deportivo, escolar, comercial, cultural
- Google Trends del término del evento: **la curva de subida es la ventana**
- Qué se agotó o se disparó en el mismo evento del ciclo anterior

**Salida del paso:** 15-25 candidatos crudos. Todavía no filtrar por gusto.

---

## §3 · PASO 2 — Filtro de descarte (rápido y sin piedad)

Descartar de inmediato el candidato que cumpla **cualquiera**:

| Descarte | Umbral | Por qué |
|---|---|---|
| Saturación en catálogo | **>10 proveedores** en Dropi | Guerra de precios |
| Saturación en pauta | **>20 tiendas** (regla del 10%) | Guerra de precios |
| Mercado tradicional | Se consigue en farmacia, súper o esquina | Lo compran allá |
| Frágil o pesado | — | Se rompe o el flete come el margen |
| Variaciones complejas | Tallas, colores múltiples | Devoluciones y errores de despacho |
| Sin stock verificable | — | Se vende lo que no hay |

**Excepción única a la saturación** (regla del 10%, Clase 5): se puede entrar en
un producto saturado **solo si** existe un ángulo que nadie está usando, **o**
nadie lo vende por WhatsApp/COD (público distinto al de landing = mercado sin
explotar). Si se invoca la excepción, **escribir cuál es el ángulo virgen.**
Sin ángulo escrito, no hay excepción.

**Salida:** 5-10 candidatos sobrevivientes.

---

## §4 · PASO 3 — Ranking de candidatos

Puntuar cada sobreviviente de 0 a 3 en cinco ejes. **No es la validación de los
17 criterios** — es priorización para decidir a cuál dedicarle la validación.

| Eje | 0 | 3 |
|---|---|---|
| **Intensidad del dolor** | Curiosidad | Duele hoy y no lo deja dormir |
| **Efecto WOW** | Se explica con palabras | Se entiende en 3 segundos de video |
| **Hueco de mercado** | Todos lo pautan | Demanda visible, nadie la atiende |
| **Margen proyectado** | < 3 USD tras gastos | Holgado con espacio para combos |
| **Facilidad de demostración** | No se puede mostrar | El video se graba solo |

**Score = suma / 15.** Ordenar de mayor a menor.

**Desempate:** gana el que tenga **evidencia externa de intención de compra**
(comentarios de "¿dónde lo compro?", búsquedas, gente preguntando precio) sobre
el que solo tiene una hipótesis del operador. *El mercado decide, no tu gusto.*

---

## §5 · RUTA B — Reglas específicas de la ventana de evento

Solo si se declaró RUTA B en el paso inicial.

### Por qué se suspende el criterio `O4` ("no de temporada")

`O4` existe para proteger de productos que mueren y dejan inventario. En una
jugada de evento eso **no se elimina: se administra** con las tres reglas de
abajo. Si no se pueden cumplir las tres, **`O4` vuelve a aplicar y el candidato
se descarta.**

### Las tres reglas de la ventana

**① Mapear la ventana antes de comprar nada.**

```
VENTANA
- Inicio de la curva:   [fecha en que la demanda empieza a subir]
- Pico:                 [fecha]
- Muerte:               [fecha en que el producto deja de venderse]
- Lead time proveedor:  [días desde el pedido hasta tener stock]
- DÍAS ÚTILES REALES = muerte − hoy − lead time
```

**Si `DÍAS ÚTILES REALES < 14` → no entrar.** No alcanza a testear ángulo,
corregir y escalar. Entrar tarde a una ventana es la forma más rápida de
perder plata en este modelo.

**② Sin inventario propio, o el mínimo posible.** COD + proveedor que despacha
es lo que hace viable la jugada de evento: el riesgo de quedar con producto
muerto se transfiere. Si hay que comprar inventario por adelantado, **comprar
para la mitad de la proyección** y reponer con la venta.

**③ Fecha de apagado escrita desde el día 1.** Definir *hoy* el día en que se
apaga la pauta y se deja de despachar. Sin fecha escrita, la caída de la curva
se descubre tarde, con pedidos que ya no llegan a tiempo.

### El activo real de una ventana de evento

**No es el producto: es el ángulo y el sistema.** Terminada la ventana, lo que
queda y se reutiliza es el avatar, la voz del cliente y la estructura de oferta
que convirtió — nunca el objeto. Al cerrar una RUTA B, **archivar el ángulo
ganador en `_CONOCIMIENTO/`** para la siguiente ventana.

⚠️ **Riesgo legal — chequeo obligatorio antes de continuar.** Los eventos
grandes tienen propiedad intelectual agresivamente protegida (marcas, logos,
mascotas, nombres oficiales, personajes, escudos). Antes de aprobar un candidato
de RUTA B, responder por escrito:

```
CHEQUEO DE PROPIEDAD INTELECTUAL
- ¿El producto reproduce marca, logo, mascota, escudo o personaje registrado?  [sí/no]
- ¿Usa el nombre oficial del evento?                                            [sí/no]
- ¿Existe licenciatario oficial de esta categoría?                              [sí/no]
```

**Cualquier "sí" → el candidato queda MARCADO EN ROJO.** Se le informa al
operador con la consecuencia concreta: un producto que infringe PI no se puede
mostrar, no se puede escalar en pauta sin riesgo de baja de cuenta, y **no se
puede usar como caso de estudio público después**. Se recomienda buscar el
vehículo no infractor del mismo flujo de demanda — la demanda del evento es
real y legal; reproducir la marca es lo que no lo es.

---

## §6 · OUTPUT

```
══════════════════════════════════════════════════════════
BÚSQUEDA DE PRODUCTO — [fecha]
RUTA: [A · Evergreen] / [B · Ventana de evento: NOMBRE]
══════════════════════════════════════════════════════════

FLUJO DE DEMANDA
Quién:        [...]
Qué siente:   [...]
Por qué AHORA:[...]
Ya gasta en:  [...]

FUENTES BARRIDAS: [lista]  ·  CANDIDATOS CRUDOS: [N]

DESCARTADOS: [N]
- [producto] → [motivo del descarte]

──────────────────────────────────────────────────────────
CANDIDATOS RANKEADOS
──────────────────────────────────────────────────────────
#1 · [PRODUCTO]                                score X.XX
    Dolor [0-3] · WOW [0-3] · Hueco [0-3] · Margen [0-3] · Demo [0-3]
    Proveedores en Dropi: [N]  ·  Tiendas pautando: [N]
    Evidencia de intención: [cita o dato concreto + fuente]
    Por qué este: [1 línea]
    [Solo RUTA B] Días útiles reales: [N]  ·  PI: [🟢 limpio / 🔴 marcado]

#2 · [...]

──────────────────────────────────────────────────────────
RECOMENDACIÓN
Validar primero: [#1]
Razón: [1 línea]
SIGUIENTE PASO → correr `etapa-producto` sobre [#1]
══════════════════════════════════════════════════════════
```

---

## Reglas duras

- **No inventar datos de mercado.** Si no se pudo contar proveedores o
  anunciantes, escribir `sin dato` y decirlo en el output. Un número inventado
  contamina toda la cadena de decisión aguas abajo.
- **No recomendar el más vendido de Dropi.** Nunca. Está saturado por
  definición.
- **Evidencia externa > opinión del operador.** Una cita real de alguien
  preguntando dónde comprarlo vale más que cualquier corazonada.
- **Esta skill no valida.** Entrega candidatos rankeados. El veredicto APTO/NO
  APTO es de `etapa-producto` con los 17 criterios. No saltarse ese paso.
- **RUTA B nunca es implícita.** Suspender `O4` es una decisión declarada.
- **PI marcada en rojo se informa siempre**, aunque el operador ya haya decidido.

---

## Conexión

```
buscar-producto  →  etapa-producto  →  ETAPA-1 (costeo)  →  ETAPA-0
   (encuentra)        (valida 17)         (cuesta)          (arranca)
```

El ángulo ganador de una RUTA B cerrada se archiva en `_CONOCIMIENTO/` y
alimenta `DOCTRINA/MODULO_INTELIGENCIA_PRODUCTO.md` para la siguiente ventana.
