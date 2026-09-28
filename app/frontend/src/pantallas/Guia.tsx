/**
 * Guía de uso de la app (reescrita sobre la app real, 26-sep-2026).
 *
 * Escrita en lenguaje simple y sin jerga para el operador. Cada afirmación sale de lo que
 * la app muestra hoy: Hoy con su franja y sus órdenes, la tabla de Productos, la ficha del
 * producto, Resultados con la caja, Trabajos como única puerta de aprobación. Los colores
 * de decisión son los tokens oficiales (`estado-*`), nunca una paleta aparte.
 */
import { Tarjeta, Chip } from "../componentes/ui";

export function Guia() {
  return (
    <div className="mx-auto max-w-5xl space-y-8 pb-12">
      <header className="border-b border-border pb-5">
        <h1 className="text-2xl font-semibold">Guía de Uso del Sistema</h1>
        <p className="mt-2 text-base text-muted-foreground">
          Todo lo que necesitás saber para operar VitalCom en el día a día. Sin tecnicismos ni código.
        </p>
      </header>

      {/* ── SECCIÓN 1: PANTALLAS Y BOTONES ── */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/15 text-sm font-bold text-primary">
            1
          </span>
          <h2 className="text-lg font-semibold">¿Qué hace cada pantalla y botón?</h2>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <Tarjeta className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Hoy — tu día en un vistazo</h3>
              <Chip tono="dato">Pantalla principal</Chip>
            </div>
            <p className="text-sm text-muted-foreground">
              Es la primera pantalla al abrir la app. La franja de arriba te dice en números grandes
              qué te toca hoy: cuántas órdenes piden <strong>escalar</strong>, <strong>pausar</strong>{" "}
              o <strong>renovar</strong>, y cuántas siguen midiendo. Cada orden muestra lo que de
              verdad importa: el <strong>CPA observado contra el break-even</strong>. El resto
              (veredicto y definiciones) queda plegado para no tapar el número.
            </p>
            <div className="rounded-lg bg-muted/50 p-2.5 text-xs text-muted-foreground">
              <strong className="text-foreground">Acción clave:</strong> si una orden dice «Listo
              para revisión», el botón te lleva a Trabajos, que es donde se aprueba de verdad, orden
              por orden. También avisa acá si Trabajos te espera o si la data está vieja.
            </div>
          </Tarjeta>

          <Tarjeta className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Productos</h3>
              <Chip tono="neutro">El portafolio</Chip>
            </div>
            <p className="text-sm text-muted-foreground">
              Una tabla con todos tus productos: en qué fase van, cuál es su paso actual, qué los
              frena y hace cuántos días no se actualiza su data («Nd de rezago»).
            </p>
            <div className="rounded-lg bg-muted/50 p-2.5 text-xs text-muted-foreground">
              <strong className="text-foreground">Acción clave:</strong> hacé clic en el nombre de un
              producto para abrir su ficha completa.
            </div>
          </Tarjeta>

          <Tarjeta className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Ficha del producto</h3>
              <Chip tono="dato">Resumen · Fase 1 · 2 · 3 · 4</Chip>
            </div>
            <p className="text-sm text-muted-foreground">
              Cada producto tiene su ficha con pestañas. El <strong>Resumen</strong> muestra dónde
              está parado, qué falta para avanzar y el recorrido completo. Las pestañas de fase
              traen el trabajo específico: armado de la FASE 1, tablero de conceptos de la FASE 2,
              la reescritura del flujo del bot en la FASE 3 o el plan de escalado de la FASE 4.
            </p>
          </Tarjeta>

          <Tarjeta className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Resultados</h3>
              <Chip tono="bien">La plata del negocio</Chip>
            </div>
            <p className="text-sm text-muted-foreground">
              La contabilidad real: venta bruta entregada, márgenes y resultado neto, la tendencia en
              el tiempo y cuánto deja cada venta por producto. El bloque{" "}
              <strong>«Caja de la ventana»</strong> muestra la plata que entró de verdad a la
              cartera de Dropi — distinta de la cohorte, que mide si la pauta rindió. Lo marcado{" "}
              <strong>PRELIMINAR</strong> todavía está madurando: un cohorte necesita sus días de
              entrega antes de leerse como definitivo.
            </p>
            <div className="rounded-lg bg-muted/50 p-2.5 text-xs text-muted-foreground">
              <strong className="text-foreground">Para que salga la caja:</strong> cargá el export de
              Dropi de la ventana; sin historial de cartera, la app te lo dice y no inventa números.
            </div>
          </Tarjeta>

          <Tarjeta className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Trabajos</h3>
              <Chip tono="neutro">La sala de máquinas</Chip>
            </div>
            <p className="text-sm text-muted-foreground">
              Cada tarea que el sistema corre en vivo, con su bitácora al detalle. Cuando algo espera
              tu aprobación o tu respuesta, lo ves acá — y el aviso aparece tanto en Hoy como en la
              insignia junto a Ajustes.
            </p>
            <div className="rounded-lg bg-muted/50 p-2.5 text-xs text-muted-foreground">
              <strong className="text-foreground">Regla dura:</strong> esta es la única pantalla desde
              la que se aprueban acciones en Meta, orden por orden. Nada se ejecuta sin tu clic.
            </div>
          </Tarjeta>

          <Tarjeta className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Órdenes</h3>
              <Chip tono="aviso">El detalle del motor</Chip>
            </div>
            <p className="text-sm text-muted-foreground">
              La versión extendida de las órdenes del día: los relojes del motor, los ganadores
              coronados y las llamadas literales a Meta de cada orden. Si hay conjuntos gastando en
              Meta que todavía no tienen su fila de registro, aparecen arriba en una tarjeta ámbar.
            </p>
          </Tarjeta>

          <Tarjeta className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Fases 1, 2, 3 y 4</h3>
              <Chip tono="bien">El método</Chip>
            </div>
            <ul className="space-y-1.5 text-sm text-muted-foreground">
              <li>
                • <strong className="text-foreground">FASE 1 (Ángulos):</strong> seis ángulos de
                venta con un mismo concepto fijo, para descubrir qué dolor compra la gente. Se
                desbloquea con evidencia de venta por ángulo.
              </li>
              <li>
                • <strong className="text-foreground">FASE 2 (Conceptos):</strong> toma el ángulo
                ganador y le testea diez conceptos visuales, con prompts listos para copiar y
                generar las imágenes. Se desbloquea cuando un concepto gana en 2 de 2 pruebas
                seguidas (~3 días de la 1-1-5).
              </li>
              <li>
                • <strong className="text-foreground">FASE 3 (Flujo LucidBot):</strong> ángulo y
                concepto ya validados, mismo presupuesto — se reescribe el flujo del bot hacia el
                ganador (CAMBIO_BOT) y se mide el cierre hasta llegar al piso.
              </li>
              <li>
                • <strong className="text-foreground">FASE 4 (Escalado):</strong> se desbloquea con
                el CAMBIO_BOT registrado más ≥30 mensajes con cierre ≥10 % desde ese cambio
                (PROHIBIDO_ESCALAR_CIERRE_BAJO); recién ahí se compra volumen con la campaña CBO
                1-1-7.
              </li>
            </ul>
          </Tarjeta>

          <Tarjeta className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Ajustes y pantallas internas</h3>
              <Chip tono="neutro">Cuentas y entradas</Chip>
            </div>
            <p className="text-sm text-muted-foreground">
              En <strong className="text-foreground">Ajustes</strong> viven las cuentas de Meta, las
              FanPages y las puertas a las pantallas internas: Órdenes, Trabajos, Salud, esta Guía y
              el alta de un producto nuevo. Desde acá también se abre la carpeta del sistema.
            </p>
          </Tarjeta>

          <Tarjeta className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Nuevo producto</h3>
              <Chip tono="bien">Alta en 3 pasos</Chip>
            </div>
            <p className="text-sm text-muted-foreground">
              Subís la foto del envase, la descripción (con ingredientes y dosis para que los textos
              de anuncios salgan convincentes) y el costo en quetzales; al instante ves la tabla de
              precios para Guatemala y el break-even. Después podés transcribir los videos del
              producto para que el motor construya sus ángulos.
            </p>
          </Tarjeta>

          <Tarjeta className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Salud y respaldos</h3>
              <Chip tono="dato">Frescura de la data</Chip>
            </div>
            <p className="text-sm text-muted-foreground">
              <strong className="text-foreground">Salud:</strong> de un vistazo, qué archivos de
              datos están frescos, tibios o faltan, quién es su dueño y con qué comando se
              regeneran.
            </p>
            <p className="text-sm text-muted-foreground">
              <strong className="text-foreground">Respaldos:</strong> el sistema guarda copias{" "}
              <code className="rounded bg-muted px-1">.zip</code> fechadas de la carpeta{" "}
              <code className="rounded bg-muted px-1">PRODUCTOS/</code> en tus Documentos (
              <code className="rounded bg-muted px-1">VITALCOM_RESPALDOS</code>).
            </p>
          </Tarjeta>
        </div>
      </section>

      {/* ── SECCIÓN 2: ESTADOS ── */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-estado-seguir/15 text-sm font-bold text-estado-seguir">
            2
          </span>
          <h2 className="text-lg font-semibold">¿Qué significa cada estado?</h2>
        </div>
        <p className="text-sm text-muted-foreground">
          Los colores de decisión son siempre los mismos en toda la app — un color, un significado.
        </p>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <div className="space-y-1 rounded-lg border border-estado-escalar/40 bg-estado-escalar/10 p-3.5">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-estado-escalar" />
              <strong className="text-sm text-estado-escalar">ESCALAR (+20%)</strong>
            </div>
            <p className="text-xs text-muted-foreground">
              La evidencia alcanza y el costo por venta está por debajo del techo. El motor recomienda
              subir el presupuesto.
            </p>
          </div>

          <div className="space-y-1 rounded-lg border border-estado-pausar/40 bg-estado-pausar/10 p-3.5">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-estado-pausar" />
              <strong className="text-sm text-estado-pausar">PAUSAR</strong>
            </div>
            <p className="text-xs text-muted-foreground">
              Gastó de más sin vender lo suficiente y la evidencia ya alcanza para cortar. Se apaga
              para proteger la caja.
            </p>
          </div>

          <div className="space-y-1 rounded-lg border border-estado-seguir/40 bg-estado-seguir/10 p-3.5">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-estado-seguir" />
              <strong className="text-sm text-estado-seguir">SEGUIR MIDIENDO</strong>
            </div>
            <p className="text-xs text-muted-foreground">
              Todavía no hay evidencia para decidir: se mantiene el presupuesto tal cual. El motor
              dice cuántas ventas faltan.
            </p>
          </div>

          <div className="space-y-1 rounded-lg border border-estado-renovar/40 bg-estado-renovar/10 p-3.5">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-estado-renovar" />
              <strong className="text-sm text-estado-renovar">RENOVAR</strong>
            </div>
            <p className="text-xs text-muted-foreground">
              El ángulo sigue vendiendo pero el anuncio se cansó. Se cambia el creativo, no se apaga
              el ángulo.
            </p>
          </div>

          <div className="space-y-1 rounded-lg border border-border bg-muted/30 p-3.5">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />
              <strong className="text-sm">LISTO</strong>
            </div>
            <p className="text-xs text-muted-foreground">
              Todos los requisitos del paso están cumplidos. Podés ejecutarlo con el botón principal.
            </p>
          </div>

          <div className="space-y-1 rounded-lg border border-border bg-muted/30 p-3.5">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-rose-400" />
              <strong className="text-sm">BLOQUEADO</strong>
            </div>
            <p className="text-xs text-muted-foreground">
              Falta un insumo indispensable (la cuenta, el page_id, una imagen…). La app te dice
              exactamente cuál es y quién lo produce.
            </p>
          </div>
        </div>
      </section>

      {/* ── SECCIÓN 3: RESOLUCIÓN DE PROBLEMAS ── */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-estado-pausar/15 text-sm font-bold text-estado-pausar">
            3
          </span>
          <h2 className="text-lg font-semibold">¿Qué hacer si algo falla o se detiene?</h2>
        </div>

        <div className="space-y-3">
          <Tarjeta>
            <h3 className="text-sm font-semibold">1. Un trabajo en Trabajos quedó en rojo o falló</h3>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
              Hacé clic sobre el trabajo en la lista para ver el detalle de la bitácora. Casi siempre
              son micro-cortes de internet al consultar Meta o archivos en uso. Usá{" "}
              <strong className="text-foreground">«Reintentar»</strong>.
            </p>
          </Tarjeta>

          <Tarjeta>
            <h3 className="text-sm font-semibold">2. Hoy dice que las órdenes se calcularon sobre datos viejos</h3>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
              El banner rojo aparece cuando la data tiene más de 2 días de rezago. Refrescá la data
              antes de actuar: una decisión sobre data vieja es una decisión a ciegas. El botón del
              banner encola la recolección y el progreso se sigue en Trabajos.
            </p>
          </Tarjeta>

          <Tarjeta>
            <h3 className="text-sm font-semibold">3. Aparece la franja rosa «META FALSO»</h3>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
              Es el modo de prueba del sistema: nada de lo que aprobés llega a Meta de verdad. Sirve
              para ensayar el flujo completo sin gastar plata.
            </p>
          </Tarjeta>

          <Tarjeta>
            <h3 className="text-sm font-semibold">4. Un producto no me deja publicar porque está BLOQUEADO</h3>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
              Entrá al producto. Encontrarás una tarjeta de color con el dato exacto que falta:
              <br />• Si falta la <strong className="text-foreground">cuenta</strong>: elegí una
              cuenta activa del selector.
              <br />• Si falta el <strong className="text-foreground">page_id</strong>: pegá el ID
              numérico de tu FanPage de Facebook.
              <br />• Si faltan <strong className="text-foreground">imágenes</strong>: usá el botón
              de subida con el nombre que la app te indica.
            </p>
          </Tarjeta>

          <Tarjeta>
            <h3 className="text-sm font-semibold">5. Aparecen «Conjuntos de Meta sin registrar» en Órdenes</h3>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
              Son conjuntos que ya gastan en Meta pero todavía no tienen su fila de registro en el
              sistema. Su gasto ya cuenta en el producto; la fila la da de alta la etapa que la
              produce, para que el motor pueda atribuir bien lo que pasa ahí.
            </p>
          </Tarjeta>

          <Tarjeta>
            <h3 className="text-sm font-semibold">6. Regla de oro: ¿Puedo tocar Meta directamente?</h3>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
              <strong className="text-foreground">
                Evitá renombrar campañas, conjuntos o anuncios directo en el Administrador de Meta.
              </strong>{" "}
              El sistema cruza las ventas por el nombre exacto de cada anuncio. Si cambiás los
              nombres a mano, el motor no puede atribuir las ventas y las métricas quedan
              descalzadas.
            </p>
          </Tarjeta>

          <Tarjeta>
            <h3 className="text-sm font-semibold">7. ¿Cómo vuelvo a levantar la app si reinicio la computadora?</h3>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
              Doble clic en <code className="rounded bg-muted px-1">iniciar.bat</code> en la carpeta
              raíz del sistema. Levanta los servidores, recompila la pantalla si el código cambió y
              abre tu navegador en{" "}
              <code className="rounded bg-muted px-1">http://localhost:8000</code>.
            </p>
          </Tarjeta>
        </div>
      </section>
    </div>
  );
}
