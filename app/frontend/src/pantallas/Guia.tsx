/**
 * Guía de uso de una página dentro de la app (Hito 7).
 *
 * Escrita en lenguaje simple, directo y sin jerga técnica para el operador.
 * Explica qué hace cada pantalla y botón, el significado de cada estado y qué hacer si algo falla.
 */
import { Tarjeta, Chip } from "../componentes/ui";

export function Guia() {
  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-12">
      <header className="border-b border-zinc-800 pb-5">
        <h1 className="text-3xl font-bold tracking-tight text-zinc-100">Guía de Uso del Sistema</h1>
        <p className="mt-2 text-base text-zinc-400">
          Todo lo que necesitás saber para operar VitalCom en el día a día. Sin tecnicismos ni código.
        </p>
      </header>

      {/* ── SECCIÓN 1: PANTALLAS Y BOTONES ── */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-sky-500/20 text-sm font-bold text-sky-400">
            1
          </span>
          <h2 className="text-xl font-semibold text-zinc-200">¿Qué hace cada pantalla y botón?</h2>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <Tarjeta className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-sky-300">Portafolio (Inicio)</h3>
              <Chip tono="bien">Vista General</Chip>
            </div>
            <p className="text-sm text-zinc-300">
              Es tu panel de control central. Muestra cada producto activo, en qué fase se encuentra, si está listo para avanzar o si tiene algún bloqueo que requiere tu atención.
            </p>
            <div className="rounded bg-zinc-950/60 p-2.5 text-xs text-zinc-400">
              <strong>Acción clave:</strong> Hacé clic en la tarjeta de cualquier producto para ver su ficha completa, acceder a sus fases y resolver bloqueantes.
            </div>
          </Tarjeta>

          <Tarjeta className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-amber-300">Órdenes de hoy</h3>
              <Chip tono="aviso">Decisiones Diarias</Chip>
            </div>
            <p className="text-sm text-zinc-300">
              Todas las mañanas el motor analiza las ventas y el gasto de Meta. Aquí aparecen las recomendaciones: si conviene <strong>subir presupuesto</strong> (+20%), <strong>pausar</strong> un anuncio que gasta de más o <strong>renovar</strong> un creativo que se cansó.
            </p>
            <div className="rounded bg-zinc-950/60 p-2.5 text-xs text-zinc-400">
              <strong>Regla dura:</strong> Nada se ejecuta en Meta sin tu clic en <em>Aprobar</em> orden por orden. Si no estás de acuerdo, podés <em>Rechazar</em>.
            </div>
          </Tarjeta>

          <Tarjeta className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-emerald-300">Nuevo producto</h3>
              <Chip tono="bien">Alta de Producto</Chip>
            </div>
            <p className="text-sm text-zinc-300">
              Asistente simple de 3 pasos: subís la foto del envase, pegás la descripción del producto y colocás el costo en Quetzales. Al instante ves la tabla de precios para Guatemala (1u, 2u, 3u y punto de equilibrio).
            </p>
            <div className="rounded bg-zinc-950/60 p-2.5 text-xs text-zinc-400">
              <strong>Consejo:</strong> Incluí en la descripción los ingredientes, dosis y registros sanitarios para que los textos de anuncios salgan más convincentes.
            </div>
          </Tarjeta>

          <Tarjeta className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-indigo-300">Trabajos</h3>
              <Chip tono="neutro">Procesos en Vivo</Chip>
            </div>
            <p className="text-sm text-zinc-300">
              Es la sala de máquinas. Muestra en vivo cada tarea que el sistema corre en segundo plano (investigación, armado de campañas, copias de seguridad).
            </p>
            <div className="rounded bg-zinc-950/60 p-2.5 text-xs text-zinc-400">
              <strong>Si algo espera tu acción:</strong> Aparece una insignia naranja arriba con el número de aprobaciones pendientes.
            </div>
          </Tarjeta>

          <Tarjeta className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-purple-300">Fases 1, 2 y 3</h3>
              <Chip tono="bien">Ciclo de Campañas</Chip>
            </div>
            <ul className="space-y-1.5 text-xs text-zinc-300">
              <li>• <strong>FASE 1 (Ángulos):</strong> 6 ángulos de venta × 1 concepto fijo ($2.99/conjunto) para descubrir por qué la gente compra.</li>
              <li>• <strong>FASE 2 (Conceptos):</strong> Toma el ángulo ganador y le testea 10 conceptos visuales con prompts listos para copiar y generar imágenes.</li>
              <li>• <strong>FASE 3 (Escalado):</strong> Campaña centralizada CBO 1-1-7 cuando un concepto demostró ganar en 2 de 2 pruebas seguidas.</li>
            </ul>
          </Tarjeta>

          <Tarjeta className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-cyan-300">Salud & Copias de Seguridad</h3>
              <Chip tono="bien">Protección de Datos</Chip>
            </div>
            <p className="text-sm text-zinc-300">
              <strong>Salud:</strong> Muestra si los archivos de ventas o reportes están frescos o si tienen más de 1 día de rezago.
            </p>
            <p className="text-sm text-zinc-300">
              <strong>Copias de seguridad:</strong> Cada madrugada el sistema empaqueta toda la carpeta <code>PRODUCTOS/</code> en un archivo <code>.zip</code> fechado dentro de tus Documentos (<code>VITALCOM_RESPALDOS</code>), manteniendo siempre los últimos 30 días.
            </p>
          </Tarjeta>
        </div>
      </section>

      {/* ── SECCIÓN 2: ESTADOS ── */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-amber-500/20 text-sm font-bold text-amber-400">
            2
          </span>
          <h2 className="text-xl font-semibold text-zinc-200">¿Qué significa cada estado?</h2>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <div className="rounded-lg border border-emerald-800/40 bg-emerald-950/20 p-3.5 space-y-1">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />
              <strong className="text-sm text-emerald-300">LISTO</strong>
            </div>
            <p className="text-xs text-zinc-400">
              El producto tiene todos los requisitos cumplidos. Podés avanzar a la siguiente etapa haciendo clic en el botón principal.
            </p>
          </div>

          <div className="rounded-lg border border-rose-800/40 bg-rose-950/20 p-3.5 space-y-1">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-rose-400" />
              <strong className="text-sm text-rose-300">BLOQUEADO</strong>
            </div>
            <p className="text-xs text-zinc-400">
              Falta un insumo indispensable (ej. seleccionar cuenta de Meta, ID de FanPage o WhatsApp). La app te dice exactamente cuál es.
            </p>
          </div>

          <div className="rounded-lg border border-sky-800/40 bg-sky-950/20 p-3.5 space-y-1">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-sky-400" />
              <strong className="text-sm text-sky-300">SEGUIR MIDIENDO</strong>
            </div>
            <p className="text-xs text-zinc-400">
              El anuncio está activo pero aún faltan ventas para tener certeza estadística. Se mantiene el presupuesto sin tocarlo.
            </p>
          </div>

          <div className="rounded-lg border border-teal-800/40 bg-teal-950/20 p-3.5 space-y-1">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-teal-400" />
              <strong className="text-sm text-teal-300">ESCALAR (+20%)</strong>
            </div>
            <p className="text-xs text-zinc-400">
              El anuncio es rentable y su costo por compra está bien por debajo del break-even. Se recomienda subir presupuesto de a poco.
            </p>
          </div>

          <div className="rounded-lg border border-amber-800/40 bg-amber-950/20 p-3.5 space-y-1">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-amber-400" />
              <strong className="text-sm text-amber-300">RENOVAR</strong>
            </div>
            <p className="text-xs text-zinc-400">
              El ángulo de venta es ganador, pero la imagen se agotó (la audiencia ya la vio mucho). Cambiamos el anuncio sin apagar el ángulo.
            </p>
          </div>

          <div className="rounded-lg border border-red-800/40 bg-red-950/20 p-3.5 space-y-1">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-red-400" />
              <strong className="text-sm text-red-300">PAUSAR</strong>
            </div>
            <p className="text-xs text-zinc-400">
              El anuncio gastó lo suficiente sin generar ventas rentables. Conviene apagarlo para proteger el presupuesto del negocio.
            </p>
          </div>
        </div>
      </section>

      {/* ── SECCIÓN 3: RESOLUCIÓN DE PROBLEMAS ── */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-rose-500/20 text-sm font-bold text-rose-400">
            3
          </span>
          <h2 className="text-xl font-semibold text-zinc-200">¿Qué hacer si algo falla o se detiene?</h2>
        </div>

        <div className="space-y-3">
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-4">
            <h3 className="text-sm font-semibold text-zinc-200">1. Un trabajo en la pantalla «Trabajos» quedó en rojo o falló</h3>
            <p className="mt-1 text-xs text-zinc-400 leading-relaxed">
              Hacé clic sobre el trabajo en la lista para ver el detalle de salida. La gran mayoría de veces se debe a micro-cortes de internet al consultar Meta o archivos en uso. Hacé clic en el botón <strong>«Reintentar»</strong>.
            </p>
          </div>

          <div className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-4">
            <h3 className="text-sm font-semibold text-zinc-200">2. El producto no me deja publicar porque dice «BLOQUEADO»</h3>
            <p className="mt-1 text-xs text-zinc-400 leading-relaxed">
              Entrá al producto. Verás una tarjeta de color con el dato exacto que falta:
              <br />
              • Si falta la <strong>cuenta</strong>: elegí una cuenta activa del selector desplegable.
              <br />
              • Si falta el <strong>page_id</strong>: pegá el ID numérico de tu FanPage de Facebook (15 a 16 dígitos).
              <br />
              • Si faltan <strong>imágenes</strong>: usá el botón de subida para cargar el archivo con su nombre asignado.
            </p>
          </div>

          <div className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-4">
            <h3 className="text-sm font-semibold text-zinc-200">3. Regla de oro: ¿Puedo tocar Meta directamente?</h3>
            <p className="mt-1 text-xs text-zinc-400 leading-relaxed">
              <strong>Evitá renombrar campañas, conjuntos o anuncios directo en el Administrador de Meta.</strong> El sistema cruza las ventas por el nombre exacto de cada anuncio. Si cambiás los nombres a mano en Meta, el motor no podrá atribuir las ventas y las métricas quedarán descalzadas.
            </p>
          </div>

          <div className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-4">
            <h3 className="text-sm font-semibold text-zinc-200">4. ¿Cómo volver a levantar la app si reinicio la computadora?</h3>
            <p className="mt-1 text-xs text-zinc-400 leading-relaxed">
              Simplemente hacé doble clic sobre el archivo <code>iniciar.bat</code> en la carpeta raíz. El asistente levantará los servidores automáticamente y abrirá la pantalla en tu navegador en <code>http://localhost:8000</code>.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
