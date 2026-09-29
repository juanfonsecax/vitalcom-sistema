/**
 * ProductoDetalle — la ficha de UN producto: un header con lo esencial (nombre, fase, paso de
 * ahora, bloqueante) y pestañas (P4/T3) — Resumen (el recorrido F1→F2→F3→F4 completo, antes toda
 * la pantalla) y una por fase (Fase 1/2/3/4), que renderizan las pantallas viejas de cada fase
 * SIN reescribirlas: Fase1/2/3/4 absorben acá su navegación, no su contenido.
 *
 * Las pestañas son URL-driven: `/producto/$clave/faseN` sigue siendo una URL real (el operador
 * la puede compartir o recargar) que selecciona la pestaña N; `/producto/$clave` a secas
 * selecciona la fase VIGENTE del producto (`d.fase`), o Resumen si no tiene ninguna. Nunca hay
 * un estado de pestaña que no sea, al mismo tiempo, una URL.
 *
 * Todo lo que se ve sale de `flujo.py <pk> --json`: los pasos, su estado, lo que cada uno
 * produce y quién es el dueño de cada dato. La pantalla no reordena ni completa nada.
 */
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useLocation, useNavigate, useParams } from "@tanstack/react-router";
import { ChevronDown } from "lucide-react";
import { api, type DatosParaArrancar, type Flujo, type Nodo, type Requisito } from "../api/cliente";
import { FormularioPackshot, FotoDelProducto, ParaArrancar } from "../componentes/arranque";
import { AvisosDelRecorrido, BannerRezago, tituloDelPasoActual, type MotorInfo } from "../componentes/resumen";
import { Cargando, Chip, Info, Problema, Tarjeta } from "../componentes/ui";
import { Badge } from "@/components/ui/badge";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { ClaveGlosario } from "../glosario";
import { estadoEnPalabras, faseEnUnaFrase, pasoCorto, quienLoHace } from "../lenguaje";
import { Fase1 } from "./Fase1";
import { Fase2 } from "./Fase2";
import { Fase3 } from "./Fase3";
import { Fase4 } from "./Fase4";

type TabId = "resumen" | "fase1" | "fase2" | "fase3" | "fase4";

const CLAVE_GLOSARIO_DE_FASE: Record<string, ClaveGlosario | undefined> = {
  F1: "fase_1",
  F2: "fase_2",
  F3: "fase_3",
  F4: "fase_4",
};

/** La fase vigente (`d.fase`), como pestaña por defecto. Una fase fuera de F1/F2/F3/F4 (p. ej.
 * PAUSADO, como VARICOSE) cae en Resumen: no hay pestaña de fase que le corresponda. */
function tabDeFase(fase: string | null | undefined): TabId {
  if (fase === "F1") return "fase1";
  if (fase === "F2") return "fase2";
  if (fase === "F3") return "fase3";
  if (fase === "F4") return "fase4";
  return "resumen";
}

/** La pestaña que dice la URL, o `null` cuando la URL es la ficha a secas (`/producto/$clave`) —
 * ahí manda la fase vigente (`tabDeFase`), no un default fijo. */
function tabDeRuta(pathname: string): TabId | null {
  if (pathname.endsWith("/fase1")) return "fase1";
  if (pathname.endsWith("/fase2")) return "fase2";
  if (pathname.endsWith("/fase3")) return "fase3";
  if (pathname.endsWith("/fase4")) return "fase4";
  return null;
}

const RUTA_DE_TAB: Record<
  TabId,
  "/producto/$clave" | "/producto/$clave/fase1" | "/producto/$clave/fase2" | "/producto/$clave/fase3" | "/producto/$clave/fase4"
> = {
  resumen: "/producto/$clave",
  fase1: "/producto/$clave/fase1",
  fase2: "/producto/$clave/fase2",
  fase3: "/producto/$clave/fase3",
  fase4: "/producto/$clave/fase4",
};

function Dato({ requisito }: { requisito: Requisito }) {
  return (
    <li className="flex gap-2 text-sm">
      <span className={requisito.ok ? "text-emerald-400" : "text-rose-400"}>
        {requisito.ok ? "✓" : "✗"}
      </span>
      <span>
        <span className="text-foreground">{requisito.dato}</span>
        <span className="block text-xs text-muted-foreground">
          {requisito.observado}
          {requisito.dueno && <> · lo produce {requisito.dueno}</>}
        </span>
      </span>
    </li>
  );
}

function Paso({ nodo, esActual }: { nodo: Nodo; esActual: boolean }) {
  const estado = estadoEnPalabras(nodo.estado);
  return (
    <Tarjeta
      className={
        esActual
          ? "border-primary/40 bg-primary/10 ring-1 ring-primary/30"
          : nodo.estado === "NO_APLICA"
            ? "border-dashed"
            : undefined
      }
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-medium text-foreground">
          {esActual && <span className="mr-2 text-primary">▸ estás acá</span>}
          {nodo.titulo || pasoCorto(nodo.id)}
        </h3>
        <Chip tono={estado.tono}>{estado.texto}</Chip>
      </div>
      <p className="mt-1 font-mono text-[11px] text-muted-foreground">{nodo.id}</p>
      <p className="mt-2 text-sm text-muted-foreground">{nodo.como}</p>
      <p className="mt-2 text-xs text-muted-foreground">
        {quienLoHace(nodo.ejecutor_tipo)} · {nodo.ejecutor}
      </p>
      {nodo.produce.length > 0 && (
        <ul className="mt-3 space-y-2 border-t border-border pt-3">
          {nodo.produce.map((r) => (
            <Dato key={r.dato} requisito={r} />
          ))}
        </ul>
      )}
    </Tarjeta>
  );
}

/** El contenido de la pestaña Resumen — para el humano, no para el motor: qué falta para
 * avanzar, qué frena, dónde está parado el producto, y el recorrido técnico COMPLETO
 * plegado (accesible, pero sin apagar a nadie). Nada cambió de cálculo: es la misma data
 * de `flujo.py`, contada en el orden en que el operador la necesita. */
function Resumen({ d }: { d: Flujo }) {
  const actual = d.nodos.find((n) => n.id === d.nodo_actual) ?? null;
  const demas = d.nodos.filter((n) => n.id !== d.nodo_actual);

  return (
    <div className="space-y-6 pt-4">
      <AvisosDelRecorrido avisos={d.avisos} />

      {d.entradas.length > 0 && (
        <Tarjeta>
          <p className="text-sm font-semibold text-foreground">
            Qué falta para pasar a la siguiente fase
            <Info termino="ganador_por_venta" />
          </p>
          <ul className="mt-2 space-y-2">
            {(d.entradas as Requisito[]).map((e, i) => (
              <Dato key={i} requisito={e} />
            ))}
          </ul>
        </Tarjeta>
      )}

      {d.bloqueantes.length > 0 && (
        <Tarjeta className="border-rose-900 bg-rose-950/30">
          <p className="text-sm font-medium text-rose-200">Esto frena el paso de ahora</p>
          <ul className="mt-2 space-y-2">
            {d.bloqueantes.map((b) => (
              <Dato key={b.dato} requisito={b} />
            ))}
          </ul>
        </Tarjeta>
      )}

      {actual && (
        <div className="space-y-2">
          <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Estás acá</p>
          <Paso nodo={actual} esActual />
        </div>
      )}

      {demas.length > 0 && (
        <Collapsible>
          <CollapsibleTrigger className="flex w-full items-center justify-between rounded-lg border px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-muted/50">
            <span>Ver el recorrido técnico completo ({demas.length} pasos)</span>
            <ChevronDown className="size-4" />
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="mt-3 space-y-3">
              {demas.map((nodo) => (
                <Paso key={nodo.id} nodo={nodo} esActual={false} />
              ))}
            </div>
          </CollapsibleContent>
        </Collapsible>
      )}
    </div>
  );
}

/** El header (nombre, fase, paso de ahora, bloqueante) — depende de `flujo.py`, así que solo
 * se puede pintar cuando esa consulta ya resolvió. Separado del resto para que NO bloquee a
 * Fase1/2/3: cuando la URL ya trae el sufijo de fase (`tabDeUrl`), esas pantallas arrancan sus
 * propias consultas de una vez, en paralelo con esta — nunca esperan a que el header cargue. */
function Header({
  d,
  datos,
  onSubirFoto,
}: {
  d: Flujo;
  datos: DatosParaArrancar | undefined;
  onSubirFoto: () => void;
}) {
  const motor = (d.motor ?? null) as MotorInfo | null;
  const tituloDelPaso = tituloDelPasoActual(d.nodos, d.nodo_actual, d.como);
  const quien = quienLoHace(d.ejecutor);
  const estado = estadoEnPalabras(d.estado);
  const primerBloqueante = d.bloqueantes[0];
  const claveGlosarioFase = d.fase ? CLAVE_GLOSARIO_DE_FASE[d.fase] : undefined;

  return (
    <>
      <BannerRezago motor={motor} />
      <div className="space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <FotoDelProducto datos={datos} nombre={d.nombre || d.producto_key} onSubir={onSubirFoto} />
            <div>
              <h1 className="text-2xl font-semibold">{d.nombre || d.producto_key}</h1>
              <p className="text-sm text-muted-foreground">{d.producto_key}</p>
            </div>
          </div>
          <Badge variant="outline" title={faseEnUnaFrase(d.fase)}>
            {d.fase ?? "sin fase"}
            {claveGlosarioFase && <Info termino={claveGlosarioFase} />}
          </Badge>
        </div>
        <div>
          {d.fase_titulo && <p className="text-sm font-medium">{d.fase_titulo}</p>}
          <p className="text-sm text-muted-foreground">{faseEnUnaFrase(d.fase)}</p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <p className="text-xs uppercase tracking-wide text-muted-foreground">
              El paso de ahora — y qué sigue
              <Info termino="nodo" />
            </p>
            <p className="mt-1 text-sm">
              {tituloDelPaso} <Chip tono={estado.tono}>{estado.texto}</Chip>
            </p>
            <p className="mt-1 text-xs text-muted-foreground">{quien}</p>
            {d.ejecutor && <p className="text-xs text-muted-foreground">{d.ejecutor}</p>}
            {d.nodo_actual && (
              <p className="mt-1 font-mono text-[11px] text-muted-foreground" title="Id interno del paso en el grafo">
                {d.nodo_actual}
              </p>
            )}
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-muted-foreground">
              Esto te bloquea
              <Info termino="bloqueante" />
            </p>
            {primerBloqueante ? (
              <p className="mt-1 text-sm">
                {primerBloqueante.dato}
                <span className="block text-xs text-muted-foreground">
                  lo produce {primerBloqueante.dueno}
                  {d.bloqueantes.length > 1 ? ` (+${d.bloqueantes.length - 1} más)` : ""}
                </span>
              </p>
            ) : (
              <p className="mt-1 text-sm text-estado-escalar">Nada lo frena.</p>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

export function ProductoDetalle() {
  const { clave } = useParams({ strict: false }) as { clave: string };
  const location = useLocation();
  const navigate = useNavigate();
  const flujo = useQuery({ queryKey: ["flujo", clave], queryFn: () => api.producto(clave) });
  // Los datos para arrancar (foto, precio, página, cuenta, costo…). Si el motor no responde, la ficha se
  // ve igual: solo falta la foto del encabezado y la tarjeta «Para arrancar te falta».
  const datos = useQuery({ queryKey: ["datos", clave], queryFn: () => api.datosParaArrancar(clave) });
  const cliente = useQueryClient();
  const [formularioFoto, setFormularioFoto] = useState(false);
  const recargarDatos = () => {
    setFormularioFoto(false);
    void cliente.invalidateQueries({ queryKey: ["datos", clave] });
    void cliente.invalidateQueries({ queryKey: ["flujo", clave] });
    void cliente.invalidateQueries({ queryKey: ["checklist", clave] });
  };
  // "Resumen" no tiene una URL propia distinta de la ficha a secas (`/producto/$clave` es,
  // a la vez, la URL de Resumen Y la de "sin sufijo de fase" — de ahí el default a la fase
  // vigente). Por eso, cuando el operador la elige a mano estando ya en esa URL, hace falta
  // este estado local para que la pestaña cambie sin depender de una URL que no puede cambiar.
  // La URL manda apenas trae un sufijo de fase — `tabDeUrl` siempre le gana a este estado.
  const [tabManual, setTabManual] = useState<TabId | null>(null);

  const d = flujo.data;
  // Sin sufijo de fase en la URL, la pestaña por defecto es la fase VIGENTE (`d.fase`) — pero
  // esa fase todavía no se conoce mientras `flujo` carga, así que el default cae en Resumen
  // hasta que llegue (nunca se bloquea la pantalla entera por esto).
  const tabDeUrl = tabDeRuta(location.pathname);
  const tabActiva: TabId = tabDeUrl ?? tabManual ?? tabDeFase(d?.fase);

  function cambiarTab(siguiente: string) {
    if (siguiente === tabActiva) return;
    const destino = siguiente as TabId;
    if (destino === "resumen") {
      setTabManual("resumen");
      if (tabDeUrl) navigate({ to: "/producto/$clave", params: { clave } });
      return;
    }
    setTabManual(null);
    navigate({ to: RUTA_DE_TAB[destino], params: { clave } });
  }

  return (
    <div className="space-y-6">
      <Link to="/productos" className="text-xs text-muted-foreground hover:text-foreground">
        ← productos
      </Link>

      {/* Header (P4/T3): nombre, fase, paso de ahora y bloqueante — siempre visible, sin
          importar qué pestaña esté abierta. Depende de `flujo.py`: mientras esa consulta está en
          vuelo, NO retiene a Fase1/2/3 (ver el comentario de `Header` más arriba). */}
      {flujo.isLoading ? (
        <Cargando que={`el recorrido de ${clave}`} />
      ) : flujo.error ? (
        <Problema error={flujo.error} />
      ) : (
        <Header d={d!} datos={datos.data} onSubirFoto={() => setFormularioFoto(true)} />
      )}

      {formularioFoto && (
        <FormularioPackshot
          clave={clave}
          datos={datos.data}
          onListo={recargarDatos}
          onCerrar={() => setFormularioFoto(false)}
        />
      )}
      <ParaArrancar
        clave={clave}
        datos={datos.data}
        onSubirFoto={() => setFormularioFoto(true)}
        onCargado={recargarDatos}
      />

      <Tabs value={tabActiva} onValueChange={cambiarTab}>
        <TabsList>
          <TabsTrigger value="resumen">Resumen</TabsTrigger>
          <TabsTrigger value="fase1">Fase 1</TabsTrigger>
          <TabsTrigger value="fase2">Fase 2</TabsTrigger>
          <TabsTrigger value="fase3">Fase 3</TabsTrigger>
          <TabsTrigger value="fase4">Fase 4</TabsTrigger>
        </TabsList>
        {/* Un solo panel, cuyo contenido cambia con la pestaña — así solo la fase abierta hace
            sus fetches (Fase1/2/3/4 son pantallas pesadas, no conviene montarlas las cinco). */}
        <TabsContent value={tabActiva}>
          {tabActiva === "resumen" &&
            (flujo.isLoading ? (
              <Cargando que="el recorrido" />
            ) : flujo.error ? (
              <Problema error={flujo.error} />
            ) : (
              <Resumen d={d!} />
            ))}
          {tabActiva === "fase1" && (
            <div className="pt-4">
              <Fase1 />
            </div>
          )}
          {tabActiva === "fase2" && (
            <div className="pt-4">
              <Fase2 clave={clave} />
            </div>
          )}
          {tabActiva === "fase3" && (
            <div className="pt-4">
              <Fase3 clave={clave} />
            </div>
          )}
          {tabActiva === "fase4" && (
            <div className="pt-4">
              <Fase4 clave={clave} />
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
