# Prompt de arranque — continuación de las mejoras visuales del dashboard VitalCom (v2)

> Cómo usar: abrí un chat nuevo en la carpeta SISTEMA y escribile:
> «Leé _OPERADOR/PROMPT_SESION_DASHBOARD.md y confirmame en 5 líneas que entendiste el estado.
> Esperá mis pedidos.» Este archivo es el contrato de la sesión y la memoria del trabajo.

---

Vas a trabajar conmigo en las mejoras **visuales y de usabilidad** del dashboard de mi sistema
(una app web local). Yo voy a ir recorriendo las pantallas y diciéndote qué cambiar. Tu trabajo
es ejecutar **sin romper nada** de lo que ya funciona: el sistema lleva meses de trabajo, maneja
plata real y su parte técnica ya está validada. La misión de esta etapa: que la app sea amigable
para un operador que no sabe de publicidad — cada pantalla debe responder «qué pasó, qué debo
hacer y a dónde voy».

## 1. Qué es el sistema (contexto mínimo)

- Negocio: dropshipping contra entrega (COD) en Guatemala, anuncios en Meta, ventas por WhatsApp
  con un bot (LucidBot).
- Método en 3 fases por producto: **FASE 1** testea 6 ÁNGULOS → **FASE 2** testea CONCEPTOS del
  ángulo ganador → **FASE 3** escala el concepto ganador.
- Los números y las decisiones NO los calcula la app: los calculan scripts de Python en
  `Ads/_TOOLS/` (`decidir.py` decide pausar/escalar, `flujo.py` ubica cada producto, `gen_pl.py`
  contabiliza). La data vive en CSV dentro de `PRODUCTOS/`.
- **La app solo LEE esos resultados, los muestra y dispara acciones ya declaradas.** Esa regla
  no se rompe nunca.
- Estados de decisión (vienen de `decidir.py`): `ESCALAR` (verde) · `PAUSAR` (rojo) ·
  `SEGUIR_MIDIENDO` (ámbar) · `RENOVAR` (violeta). Un color, un dueño.

## 2. DÓNDE ESTAMOS — estado al cierre de la sesión anterior (27-sep-2026)

- Rama activa: **`feat/dashboard-visual`**, con 11 commits ya hechos (ver `git log`). Resumen:
  identidad «espresso» cálida + amanecer superior (estilos.css) · Hoy convertida en cabina
  (tarjetas-resumen grandes con glow por estado, filetes de color por orden, CPA vs break-even
  como héroes, celebración al entrar a ESCALAR) · navegación de 5 entradas (Trabajos promovido
  al menú con su insignia; Órdenes enlazado desde Hoy) · un solo lenguaje visual en las 12
  pantallas (botones shadcn, chips de decisión con tokens, inputs unificados) · VISTA B «Caja
  de la ventana» en Resultados · «Conjuntos de Meta sin registrar» en Órdenes · Guía reescrita ·
  Resumen del producto reestructurado (qué falta → qué frena → estás acá → recorrido plegado) ·
  prompts de la galería de conceptos completos y copiables · pasada amigable en
  Productos/Resultados/Trabajos (CTA en vacíos, KPIs héroe, neto coloreado por signo, JSON de
  Meta plegado en el panel de aprobación).
- `main` quedó **intacta** en `a031da9` (respaldo total). Además existe la rama
  `respaldo-antes-de-reestructura` como punto intermedio.
- Verificación al cierre: **111/111 pruebas Vitest · 15/15 Playwright e2e · build limpio**.
- La captura de pantallas para comparaciones se hacía con una spec TEMPORAL (copiarla a
  `app/frontend/e2e/`, correr `pnpm exec playwright test <spec>` con la variable de entorno
  `ETIQUETA` para el prefijo del nombre, borrarla después — nunca commitearla) y salida a una
  carpeta temporal FUERA del repo.

## 3. Reglas de trabajo (fijadas por el operador)

1. **Seguís en `feat/dashboard-visual`.** No cambies de rama, no hagas merge ni push.
2. **Un pedido = un commit Conventional, en inglés, sin Co-Authored-By.**
3. Antes de cada commit: `pnpm test` y `pnpm build` desde `app/frontend`. Al final del día (o
   de cada bloque grande): la suite completa `pnpm exec playwright test`.
4. **Commiteá solo archivos de `app/frontend`.** Los CSV, `VISTAS/` y los reportes de
   LucidSales que aparecen modificados en el working tree son data del sistema: nunca se
   commitean.
5. Textos que expliquen decisiones del motor: **mostrá lo que manda la API**. Si falta un
   dato, anotalo como pendiente de backend; no lo escribas a mano en la UI.

## 4. Lo que NO podés hacer (sin mi permiso explícito, pedido por pedido)

1. No toques `app/backend/`, `Ads/`, `DOCTRINA/`, `PRODUCTOS/`, `.claude/`, `evals/`,
   `warehouse/`, ni CSV/JSON de datos. Tampoco `iniciar.bat`.
2. No calcules números de negocio en el frontend (CPA, ganancia, break-even, ganador,
   decisiones). Contar filas/tarjetas renderizadas está bien; derivar negocio, no.
3. No cambies qué datos se piden a la API ni la lógica de cuándo aparece algo. Si una
   pantalla filtra a propósito, primero investigá por qué y decime.
4. **No habilites acciones en Meta.** Aprobar/Rechazar viven SOLO en Trabajos, orden por
   orden, con las llamadas a la vista. En Hoy el botón solo ENLAZA a esa aprobación.
5. No borres información que la metodología exige mostrar —podés resumirla o plegarla, pero
   accesible—: el aviso de data vieja, el PRELIMINAR de Resultados, la nota de fase de una
   orden bloqueada, el paso actual de cada producto con su bloqueante y su dueño.
6. No cambies nombres de rutas/URLs ni instales/actualices dependencias sin preguntarme.

## 5. Reglas de diseño VIGENTES (reemplazan el «Linear gris» del prompt original)

- Solo modo oscuro (`index.html` fija `.dark`). **Contraste mínimo 4.5:1**: nunca
  `text-zinc-500`/`text-zinc-600` ni `opacity` sobre texto; secundario =
  `text-muted-foreground`.
- Tokens del tema antes que crudos (`bg-card`, `text-foreground`, `border-border`) — el modo
  claro algún día sale casi gratis.
- Neutros **espresso cálidos** + amanecer superior + filete de luz en tarjetas:
  vigentes, no revertirlos. Radios 1rem.
- Los 4 colores de decisión son sagrados. Índigo solo para lo interactivo. Los brillos
  (`.brillo-escalar` etc.) solo en protagonistas.
- Números-héroe: grandes, bold, `tabular-nums`, con pop al cambiar (patrón de Hoy:
  `key={valor}` + `motion-safe:animate-in zoom-in-95`).
- Movimiento sobrio y `motion-safe:` siempre: entrada escalonada, hover con elevación,
  nada de bucles persistentes.
- Jerarquía amigable: qué pasó → qué debo hacer → a dónde ir; CTA claro en cada pantalla,
  sin callejones sin salida; lo técnico (ids crudos, JSON, notas del motor) siempre
  accesible pero plegado o en letra chica.
- Español claro y amable (voseo), sin jerga en posición primaria, sin emojis.

## 6. Mapa de pantallas (`app/frontend/src/pantallas/`)

| Ruta | Archivo | Qué muestra (ya rediseñada) |
|---|---|---|
| Hoy `/` | `Hoy.tsx` | Cabina: tarjetas-resumen por estado con glow, órdenes con filete y héroes CPA/break-even, aviso de Trabajos pendientes, qué sigue por producto |
| Productos `/productos` | `Productos.tsx` | Portafolio con fase+(i), chips de estado, rezago visible, línea de orientación, CTA en vacío |
| Ficha `/producto/$clave` | `ProductoDetalle.tsx` | Header + Resumen reestructurado + pestañas F1/F2/F3 |
| Fase 1 | `Fase1.tsx` (monolito de 1450 líneas: no partirlo) | Armado, investigación, ángulos, anuncios, flujo bot, campaña, checklist |
| Fase 2 | `Fase2.tsx` | Ganador, carriles, fatiga, galería con prompts completos copiables |
| Fase 3 | `Fase3.tsx` | Gate 2de2, estructura CBO, expansión, reingreso |
| Resultados `/resultados` | `Resultados.tsx` | KPIs héroe (neto con color/glow por signo), tendencia, **Caja de la ventana**, economía unitaria, carga de Dropi |
| Ajustes `/ajustes` | `Ajustes.tsx` | Cuentas, FanPages y grid a las internas |
| Internas | `Ordenes.tsx` · `Trabajos.tsx` · `Salud.tsx` · `Guia.tsx` · `NuevoProducto.tsx` | Órdenes extendidas (con conjuntos sin registrar) · aprobaciones (JSON plegado) · frescura de data · guía reescrita · alta de producto |

## 7. Pendientes que decidís VOS (no de la app)

1. **«Mezclá»** cuando quieras que `main` adopte todo.
2. **Pendientes de backend**: marcador de ángulos con su desempeño (la API no entrega
   resultados por ángulo) e imagen de referencia del concepto en la galería (la API no la
   trae). El frontend los mostrará apenas existan; no se pintan a mano.
3. **Pendiente de doctrina**: Fase 3 = optimización del flujo del bot, Fase 4 = escalado
   (dueños: `CLAUDE.md`, `flujo.py`, las 15 etapas). Se define con el orquestador, no acá.

## 8. Primer paso de cada sesión

Confirmame en 5 líneas que entendiste el estado, corré `git status` y
`git branch --show-current` para verificar que seguimos en `feat/dashboard-visual`, y esperá
mis pedidos. Vamos ventana por ventana: yo recorro y te dicto qué mejorar.
