/**
 * arranque.tsx — «datos para arrancar» de un producto: la foto en el encabezado y la tarjeta
 * «Para arrancar te falta».
 *
 * Todo sale de `GET /api/productos/{pk}/datos` (`datos_producto.py`): esta pantalla no decide qué
 * falta ni cómo se resuelve, solo dibuja lo que el motor dice. Cada arreglo que tiene una acción
 * escritora del manifiesto se hace acá mismo (`api.cargarDato`); los que no la tienen se cuentan en
 * una frase, sin comandos.
 */
import { useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, type DatosParaArrancar, type ItemDeDatos } from "../api/cliente";
import { Lightbox } from "./copiar";
import { Chip, Tarjeta, cn } from "./ui";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

/** Ancla de la tarjeta: otras pantallas (FASE 2) llevan hasta acá en vez de mostrar un comando. */
export const ID_PARA_ARRANCAR = "para-arrancar";

const POR_QUE_LA_FOTO = "La IA la usa para que el producto salga igual en todos los anuncios.";

/** La foto al lado del nombre: miniatura que se amplía, o el botón para subirla si no hay. */
export function FotoDelProducto({
  datos,
  nombre,
  onSubir,
}: {
  datos: DatosParaArrancar | undefined;
  nombre: string;
  onSubir: () => void;
}) {
  const [ampliada, setAmpliada] = useState(false);
  if (!datos || !datos.ok) return null;
  const url = datos.packshot?.url;
  if (url) {
    return (
      <>
        <div className="flex shrink-0 flex-col items-center gap-1">
          <button
            type="button"
            onClick={() => setAmpliada(true)}
            title="Ver la foto del producto en grande"
            className="overflow-hidden rounded-lg border border-border"
          >
            <img src={url} alt={`Foto de ${nombre}`} className="size-16 object-cover" />
          </button>
          <button type="button" onClick={onSubir} className="text-[10px] text-muted-foreground hover:text-foreground">
            Cambiar foto
          </button>
        </div>
        {ampliada && <Lightbox url={url} alt={`Foto de ${nombre}`} onCerrar={() => setAmpliada(false)} />}
      </>
    );
  }
  return (
    <Button type="button" variant="outline" size="sm" onClick={onSubir} title={POR_QUE_LA_FOTO}>
      Subí la foto del producto
    </Button>
  );
}

/** El formulario chico de la foto: archivo + lo que se lee en el envase. */
export function FormularioPackshot({
  clave,
  datos,
  onListo,
  onCerrar,
}: {
  clave: string;
  datos: DatosParaArrancar | undefined;
  onListo: () => void;
  onCerrar: () => void;
}) {
  const previo = datos?.packshot ?? null;
  const [archivo, setArchivo] = useState<File | null>(null);
  const [marca, setMarca] = useState(previo?.marca_impresa ?? "");
  const [color, setColor] = useState(previo?.color_envase ?? "");
  const [formato, setFormato] = useState(previo?.formato_envase ?? "");
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const completo = !!archivo && !!marca.trim() && !!color.trim() && !!formato.trim();

  async function guardar() {
    if (!archivo) return;
    setGuardando(true);
    setError(null);
    try {
      await api.cargarDato(
        clave,
        "producto.cargar_packshot",
        {
          marca_impresa: marca.trim(),
          color_envase: color.trim(),
          formato_envase: formato.trim(),
          ...(previo ? { reemplazar: true } : {}),
        },
        archivo,
      );
      onListo();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setGuardando(false);
    }
  }

  return (
    <Tarjeta className="space-y-3">
      <div>
        <p className="text-sm font-semibold text-foreground">
          {previo ? "Cambiar la foto del producto" : "Subí la foto del producto"}
        </p>
        <p className="text-xs text-muted-foreground">{POR_QUE_LA_FOTO}</p>
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        <label className="space-y-1 text-xs text-muted-foreground sm:col-span-2">
          Foto del envase (PNG o JPG)
          <input
            type="file"
            accept=".png,.jpg,.jpeg"
            aria-label="Foto del producto"
            onChange={(e) => setArchivo(e.target.files?.[0] ?? null)}
            className="block text-xs text-muted-foreground file:mr-2 file:rounded file:border-0 file:bg-muted file:px-2 file:py-1 file:text-xs file:text-foreground"
          />
        </label>
        <label className="space-y-1 text-xs text-muted-foreground">
          Marca impresa en el envase
          <Input aria-label="Marca impresa" value={marca} onChange={(e) => setMarca(e.target.value)} />
        </label>
        <label className="space-y-1 text-xs text-muted-foreground">
          Color del envase
          <Input
            aria-label="Color del envase"
            placeholder="Ej: azul con blanco"
            value={color}
            onChange={(e) => setColor(e.target.value)}
          />
        </label>
        <label className="space-y-1 text-xs text-muted-foreground sm:col-span-2">
          Formato del envase
          <Input
            aria-label="Formato del envase"
            placeholder="Ej: frasco de 60 cápsulas con tapa blanca"
            value={formato}
            onChange={(e) => setFormato(e.target.value)}
          />
        </label>
      </div>
      {error && <p className="text-xs text-rose-300">{error}</p>}
      <div className="flex gap-2">
        <Button type="button" size="sm" onClick={guardar} disabled={!completo || guardando}>
          {guardando ? "Guardando…" : "Guardar foto"}
        </Button>
        <Button type="button" size="sm" variant="ghost" onClick={onCerrar}>
          Cancelar
        </Button>
      </div>
    </Tarjeta>
  );
}

/** El arreglo en línea de UN faltante que tiene acción escritora. */
function ArregloEnLinea({
  clave,
  item,
  onSubirFoto,
  onCargado,
}: {
  clave: string;
  item: ItemDeDatos;
  onSubirFoto: () => void;
  onCargado: () => void;
}) {
  const [valor, setValor] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const cuentas = useQuery({
    queryKey: ["cuentas"],
    queryFn: () => api.cuentas(),
    enabled: item.accion === "producto.cargar_cuenta",
  });
  const activas = (cuentas.data ?? []).filter((c) => c.estado_cuenta === "ACTIVE");

  async function guardar(accion: string, datos: Record<string, unknown>) {
    setGuardando(true);
    setError(null);
    try {
      await api.cargarDato(clave, accion, datos);
      onCargado();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setGuardando(false);
    }
  }

  let control: ReactNode = null;
  if (item.accion === "producto.cargar_packshot") {
    control = (
      <Button type="button" size="sm" onClick={onSubirFoto}>
        Subir la foto
      </Button>
    );
  } else if (item.accion === "producto.cargar_page_id") {
    control = (
      <>
        <Input
          aria-label="Número de la página de Facebook"
          placeholder="Ej: 1279576438561754"
          value={valor}
          onChange={(e) => setValor(e.target.value)}
          className="max-w-56"
        />
        <Button
          type="button"
          size="sm"
          disabled={!valor.trim() || guardando}
          onClick={() => guardar("producto.cargar_page_id", { page_id: valor.trim() })}
        >
          {guardando ? "Guardando…" : "Guardar página"}
        </Button>
      </>
    );
  } else if (item.accion === "producto.cargar_cuenta") {
    control = (
      <>
        <select
          aria-label="Cuenta publicitaria"
          value={valor}
          onChange={(e) => setValor(e.target.value)}
          className="flex h-8 rounded-lg border border-input bg-input/30 px-2 text-sm"
        >
          <option value="">Elegí una cuenta…</option>
          {activas.map((c) => (
            <option key={c.cuenta_alias} value={c.cuenta_alias}>
              {c.cuenta_alias}
            </option>
          ))}
        </select>
        <Button
          type="button"
          size="sm"
          disabled={!valor || guardando}
          onClick={() => guardar("producto.cargar_cuenta", { cuenta: valor })}
        >
          {guardando ? "Guardando…" : "Asignar cuenta"}
        </Button>
      </>
    );
  } else if (item.accion === "producto.cambiar_costo") {
    control = (
      <>
        <Input
          aria-label="Costo en quetzales"
          inputMode="decimal"
          placeholder="Costo en Q"
          value={valor}
          onChange={(e) => setValor(e.target.value)}
          className="w-32"
        />
        <Button
          type="button"
          size="sm"
          disabled={!valor.trim() || guardando}
          onClick={() => guardar("producto.cambiar_costo", { costo: valor.trim() })}
        >
          {guardando ? "Guardando…" : "Guardar costo"}
        </Button>
      </>
    );
  }

  return (
    <li className="space-y-2 rounded-lg border border-border bg-muted/20 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-sm font-medium text-foreground">{item.rotulo}</span>
        <Chip tono="alto">Falta</Chip>
      </div>
      <p className="text-xs text-muted-foreground">{item.como_resolver || item.detalle}</p>
      {control && <div className={cn("flex flex-wrap items-center gap-2")}>{control}</div>}
      {error && <p className="text-xs text-rose-300">{error}</p>}
    </li>
  );
}

/** «Para arrancar te falta»: solo lo que falta, cada cosa con su arreglo. Sin faltantes, no se dibuja. */
export function ParaArrancar({
  clave,
  datos,
  onSubirFoto,
  onCargado,
}: {
  clave: string;
  datos: DatosParaArrancar | undefined;
  onSubirFoto: () => void;
  onCargado: () => void;
}) {
  if (!datos || !datos.ok) return null;
  const faltan = datos.items.filter((i) => i.estado === "falta");
  if (faltan.length === 0) return null;
  return (
    <Tarjeta id={ID_PARA_ARRANCAR} className="space-y-3 border-amber-800/60 bg-amber-950/20">
      <p className="text-sm font-semibold text-amber-200">Para arrancar te falta</p>
      <ul className="space-y-2">
        {faltan.map((item) => (
          <ArregloEnLinea key={item.clave} clave={clave} item={item} onSubirFoto={onSubirFoto} onCargado={onCargado} />
        ))}
      </ul>
    </Tarjeta>
  );
}
