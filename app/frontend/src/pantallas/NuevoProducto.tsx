/**
 * Nuevo producto — el pedido 1 del operador: arrancar con tres cosas.
 *   1. Imagen del producto + nombre.
 *   2. Descripción lo más extensa posible.
 *   3. Costo en Q → la tabla de Guatemala al instante (la calcula costear.py, no la app).
 *   4. (Opcional) Videos de la competencia → se transcriben en esta máquina.
 *
 * Al confirmar, `alta_producto.py` escribe todo de una vez (o nada) y `flujo.py --todo`
 * sitúa al producto en el grafo.
 */
import { useEffect, useMemo, useState, type DragEvent } from "react";
import { useMutation, useQuery, useQueryClient, type UseMutationResult } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { api, type AccionEncolada, type ResultadoAlta, type ResultadoTranscripcion } from "../api/cliente";
import { TablaGuatemala } from "../componentes/TablaGuatemala";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Chip, Tarjeta, cn } from "../componentes/ui";
import { trabajoEnPalabras } from "../lenguaje";

const MINIMO_DESCRIPCION = 120; // el mismo mínimo que exige alta_producto.py

const PASOS = ["Imagen y nombre", "Descripción", "Costo y precios", "Videos (opcional)"] as const;

const SUGERENCIAS = [
  "ingredientes o componentes, con cantidades",
  "dosis o modo de uso",
  "qué problema resuelve y en cuánto tiempo",
  "registro sanitario (MSPAS, FDA) si lo tiene",
  "proveedor, tiempo de entrega y garantía",
  "a quién se lo venderías: edad, sexo, situación",
];

function usarDemora<T>(valor: T, ms: number) {
  const [demorado, setDemorado] = useState(valor);
  useEffect(() => {
    const t = setTimeout(() => setDemorado(valor), ms);
    return () => clearTimeout(t);
  }, [valor, ms]);
  return demorado;
}

function Pasos({ actual, ir }: { actual: number; ir: (n: number) => void }) {
  return (
    <ol className="flex flex-wrap gap-2">
      {PASOS.map((nombre, i) => (
        <li key={nombre}>
          <button
            type="button"
            onClick={() => i < actual && ir(i)}
            className={cn(
              "rounded-lg border px-3 py-1.5 text-sm",
              i === actual && "border-sky-700 bg-sky-950/40 text-sky-200",
              i < actual && "border-zinc-700 text-zinc-300 hover:border-zinc-500",
              i > actual && "border-zinc-800 text-zinc-400",
            )}
          >
            {i + 1}. {nombre}
          </button>
        </li>
      ))}
    </ol>
  );
}

export function NuevoProducto() {
  const [paso, setPaso] = useState(0);
  const [nombre, setNombre] = useState("");
  const [imagen, setImagen] = useState<File | null>(null);
  const [descripcion, setDescripcion] = useState("");
  const [costo, setCosto] = useState("");
  const [mercado, setMercado] = useState(""); // lo elige el operador: no hay mercado por defecto
  const [arrastrando, setArrastrando] = useState(false);
  const cola = useQueryClient();

  const vistaPrevia = useMemo(() => (imagen ? URL.createObjectURL(imagen) : null), [imagen]);
  const costoValido = /^\d+(\.\d+)?$/.test(costo) && Number(costo) > 0;
  const costoDemorado = usarDemora(costo, 350);

  const mercados = useQuery({ queryKey: ["mercados"], queryFn: api.mercados });

  const costeo = useQuery({
    queryKey: ["costeo", costoDemorado],
    queryFn: () => api.costeo(costoDemorado),
    enabled: /^\d+(\.\d+)?$/.test(costoDemorado) && Number(costoDemorado) > 0,
  });

  const alta = useMutation({
    mutationFn: () => {
      const formulario = new FormData();
      formulario.set("nombre", nombre.trim());
      formulario.set("costo", costo);
      formulario.set("mercado", mercado);
      formulario.set("descripcion", descripcion);
      formulario.set("imagen", imagen!);
      return api.alta(formulario);
    },
    onSuccess: () => cola.invalidateQueries({ queryKey: ["productos"] }),
  });

  // Transcribir tarda minutos: es una acción del runner (202 + un trabajo que se sigue en Trabajos).
  const transcripcion = useMutation({
    mutationFn: (clave: string) => api.transcribir(clave),
  });

  const soltar = (evento: DragEvent) => {
    evento.preventDefault();
    setArrastrando(false);
    const archivo = evento.dataTransfer.files?.[0];
    if (archivo && archivo.type.startsWith("image/")) setImagen(archivo);
  };

  const puedeSeguir = [
    nombre.trim().length >= 3 && imagen !== null && mercado !== "",
    descripcion.trim().length >= MINIMO_DESCRIPCION,
    costoValido && costeo.isSuccess,
    true,
  ][paso];

  if (alta.isSuccess) {
    return <Listo resultado={alta.data} transcripcion={transcripcion} />;
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Nuevo producto</h1>
        <p className="text-sm text-zinc-400">
          Tres cosas y arranca: la foto, una descripción larga y el costo en quetzales.
        </p>
      </header>

      <Pasos actual={paso} ir={setPaso} />

      {paso === 0 && (
        <Tarjeta className="space-y-4">
          <label className="block">
            <span className="text-sm text-zinc-300">Nombre del producto</span>
            <Input
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              placeholder="Ej.: Serum Vitamina C"
              className="mt-1"
            />
          </label>
          <label className="block">
            <span className="text-sm text-zinc-300">Mercado de venta</span>
            <select
              value={mercado}
              onChange={(e) => setMercado(e.target.value)}
              className="mt-1 block w-full rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm"
            >
              <option value="">Elegí el mercado…</option>
              {mercados.data?.map((m) => (
                <option key={m.mercado} value={m.mercado}>
                  {m.pais} ({m.moneda})
                </option>
              ))}
            </select>
          </label>
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setArrastrando(true);
            }}
            onDragLeave={() => setArrastrando(false)}
            onDrop={soltar}
            className={cn(
              "flex min-h-48 flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-6 text-center",
              arrastrando ? "border-sky-500 bg-sky-950/30" : "border-zinc-700",
            )}
          >
            {vistaPrevia ? (
              <img src={vistaPrevia} alt="Foto del producto" className="max-h-56 rounded-lg" />
            ) : (
              <p className="text-sm text-zinc-400">Arrastrá acá la foto limpia del producto</p>
            )}
            <label className="cursor-pointer text-sm text-sky-300 hover:text-sky-200">
              {imagen ? "Cambiar foto" : "o elegila desde la computadora"}
              <input
                type="file"
                accept="image/png,image/jpeg,image/webp"
                className="hidden"
                aria-label="Foto del producto"
                onChange={(e) => setImagen(e.target.files?.[0] ?? null)}
              />
            </label>
            <p className="text-xs text-zinc-400">
              Esta foto queda declarada como el packshot: es la que usan los creativos. Que sea el
              envase real, sin anuncio encima.
            </p>
          </div>
        </Tarjeta>
      )}

      {paso === 1 && (
        <Tarjeta className="space-y-3">
          <label className="block">
            <span className="text-sm text-zinc-300">Descripción del producto</span>
            <textarea
              value={descripcion}
              onChange={(e) => setDescripcion(e.target.value)}
              rows={10}
              className="mt-1 flex min-h-16 w-full rounded-lg border border-input bg-input/30 px-3 py-2 text-sm shadow-xs transition-colors placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 outline-none"
              placeholder="Mientras más cuentes, mejores ángulos salen."
            />
          </label>
          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-400">Conviene incluir:</span>
            <Chip tono={descripcion.trim().length >= MINIMO_DESCRIPCION ? "bien" : "aviso"}>
              {descripcion.trim().length} / {MINIMO_DESCRIPCION} caracteres mínimos
            </Chip>
          </div>
          <ul className="grid gap-1 text-xs text-zinc-400 sm:grid-cols-2">
            {SUGERENCIAS.map((s) => (
              <li key={s}>· {s}</li>
            ))}
          </ul>
        </Tarjeta>
      )}

      {paso === 2 && (
        <div className="space-y-4">
          <Tarjeta>
            <label className="block max-w-xs">
              <span className="text-sm text-zinc-300">Costo del pedido completo, en quetzales</span>
              <div className="relative mt-1">
                <span className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground">
                  Q
                </span>
                <Input
                  value={costo}
                  inputMode="decimal"
                  onChange={(e) => setCosto(e.target.value.replace(",", "."))}
                  aria-label="Costo en quetzales"
                  className="pl-6"
                />
              </div>
            </label>
            <p className="mt-2 text-xs text-zinc-400">
              Si se vende en combo (2x1), va el costo de TODO el pedido: VARICOSE vende 2 frascos de
              Q45, así que va 90.
            </p>
          </Tarjeta>
          {costeo.isFetching && <p className="text-sm text-zinc-400">Consultando la tabla…</p>}
          {costeo.error && <p className="text-sm text-rose-300">{(costeo.error as Error).message}</p>}
          {costeo.data && costoDemorado === costo && <TablaGuatemala costeo={costeo.data} />}
        </div>
      )}

      {paso === 3 && (
        <Tarjeta className="space-y-3">
          <p className="text-sm text-zinc-300">
            Los videos de la competencia son opcionales, pero con ellos la FASE 1 arranca con
            ángulos probados en el mercado.
          </p>
          <ol className="list-decimal space-y-1 pl-5 text-sm text-zinc-400">
            <li>Terminá el alta con el botón de abajo.</li>
            <li>
              Copiá los videos a la carpeta que te va a mostrar la pantalla siguiente (
              <code className="text-zinc-300">Ads/1.1 Videos/[PRODUCTO]/</code>).
            </li>
            <li>Tocá «Transcribir videos»: se pasan a texto acá mismo, sin subirlos a ningún lado.</li>
          </ol>
          <p className="text-xs text-zinc-400">
            La transcripción toma lo que se ESCUCHA. Si un video no tiene voz y todo está en texto
            en pantalla, la app te lo avisa.
          </p>
        </Tarjeta>
      )}

      {alta.error && (
        <Tarjeta className="border-rose-900 bg-rose-950/40">
          <p className="text-sm text-rose-200">
            <strong>No se dio de alta.</strong> {(alta.error as Error).message}
          </p>
        </Tarjeta>
      )}

      <div className="flex justify-between">
        <button
          type="button"
          disabled={paso === 0}
          onClick={() => setPaso((p) => p - 1)}
          className="rounded-lg px-4 py-2 text-sm text-zinc-400 hover:text-zinc-100 disabled:opacity-0"
        >
          ← Atrás
        </button>
        {paso < PASOS.length - 1 ? (
          <Button
            type="button"
            disabled={!puedeSeguir}
            onClick={() => setPaso((p) => p + 1)}
          >
            Siguiente →
          </Button>
        ) : (
          <Button
            type="button"
            disabled={alta.isPending}
            onClick={() => alta.mutate()}
          >
            {alta.isPending ? "Dando de alta…" : "Dar de alta el producto"}
          </Button>
        )}
      </div>
    </div>
  );
}

/** Sigue el trabajo de transcripción hasta que termina y dice qué pasó, con el mismo lenguaje que Trabajos. */
function ProgresoDeTranscripcion({ trabajo }: { trabajo: string }) {
  const detalle = useQuery({
    queryKey: ["trabajo", trabajo],
    queryFn: () => api.trabajo(trabajo),
    refetchInterval: (consulta) => (trabajoEnPalabras(consulta.state.data?.estado).enCurso ? 2000 : false),
  });
  const estado = detalle.data?.estado ?? "ENCOLADO";
  const { texto, tono, enCurso } = trabajoEnPalabras(estado);
  const unidad = (detalle.data?.unidades?.[0] ?? {}) as { json?: ResultadoTranscripcion };
  const resultado = unidad.json;
  return (
    <div className="space-y-2 text-sm text-zinc-300" aria-live="polite">
      <p className="flex items-center gap-2">
        <Chip tono={tono} titulo={estado}>{texto}</Chip>
        <Link to="/trabajos/$id" params={{ id: trabajo }} className="text-sky-300 hover:text-sky-200">
          Ver el progreso en vivo →
        </Link>
      </p>
      {!enCurso && estado !== "EXITO" && detalle.data?.resultado && (
        <p className="text-rose-300">{(detalle.data.resultado as { detalle?: string }).detalle}</p>
      )}
      {resultado && (
        <div>
          <p>
            {resultado.archivos.filter((a) => a.estado === "TRANSCRITO").length} video(s) transcrito(s) con el modelo{" "}
            {resultado.modelo}.
          </p>
          {resultado.sin_voz.length > 0 && (
            <p className="mt-1 text-amber-300">
              Casi sin voz: {resultado.sin_voz.join(", ")}. Lo que vende puede estar en el texto en pantalla.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function Listo({
  resultado,
  transcripcion,
}: {
  resultado: ResultadoAlta;
  transcripcion: UseMutationResult<AccionEncolada, Error, string>;
}) {
  const carpetaVideos = `Ads/1.1 Videos/${resultado.producto_key}/`;
  return (
    <div className="space-y-6">
      <Tarjeta className="border-emerald-900 bg-emerald-950/30">
        <h1 className="text-xl font-semibold text-emerald-200">
          {resultado.nombre_display} quedó dado de alta
        </h1>
        <ul className="mt-3 space-y-1 text-sm text-zinc-300">
          <li>· fila en _DIM_PRODUCTOS.csv con estado NUEVO y costo Q{resultado.costo_q}</li>
          <li>· packshot declarado: <code className="text-zinc-400">{resultado.packshot}</code></li>
          <li>· descripción guardada en <code className="text-zinc-400">{resultado.archivo_datos}</code></li>
        </ul>
        <Button
          className="mt-4"
          render={
            <Link
              to="/producto/$clave"
              params={{ clave: resultado.producto_key }}
            />
          }
        >
          Ver dónde quedó en el flujo →
        </Button>
      </Tarjeta>

      <Tarjeta className="space-y-3">
        <h2 className="font-medium text-zinc-100">Videos de la competencia (opcional)</h2>
        <p className="text-sm text-zinc-400">
          Copiá los videos a <code className="text-zinc-200">{carpetaVideos}</code> y tocá el botón.
          Las transcripciones quedan en{" "}
          <code className="text-zinc-200">{resultado.carpeta_transcripciones}</code>.
        </p>
        <Button
          type="button"
          variant="outline"
          disabled={transcripcion.isPending}
          onClick={() => transcripcion.mutate(resultado.producto_key)}
        >
          {transcripcion.isPending ? "Pidiéndolo…" : "Transcribir videos"}
        </Button>
        {transcripcion.error && (
          <p className="text-sm text-rose-300">{transcripcion.error.message}</p>
        )}
        {transcripcion.data && <ProgresoDeTranscripcion trabajo={transcripcion.data.job_id} />}
      </Tarjeta>
    </div>
  );
}
