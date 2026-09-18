/**
 * TablaGuatemala — la tabla de precios de un costo, tal como la devuelve `costear.py`.
 *
 * Criterio del Hito 2: lo que se ve es la salida del script "byte a byte". Por eso los
 * números se muestran con `String(valor)`, sin `toFixed` ni separadores: 30.8 se ve 30.8,
 * igual que en la consola. Si hay que cambiar cómo se ve una cifra, se cambia el script.
 */
import type { Costeo } from "../api/cliente";
import { Chip, Info, Tarjeta } from "./ui";

const q = (valor: number | null | undefined) => (valor === null || valor === undefined ? "—" : `Q${String(valor)}`);

/**
 * Cómo elige fila `costear.py` (su `elegir_fila`): la exacta; si no hay, la MÁS CERCANA; en
 * empate, la superior; y si el costo pasa la última fila, avisa TECHO DE TABLA EXCEDIDO.
 * Acá no se deduce nada: se repite el criterio que el script informa.
 */
function explicarFila(costeo: Costeo): { texto: string; tono: "aviso" | "alto" } | null {
  const criterio = costeo.criterio_de_fila;
  const costo = `Q${String(costeo.costo_ingresado)}`;
  const fila = `Q${String(costeo.fila_usada)}`;
  if (criterio === "exacta") return null;
  if (criterio.includes("TECHO")) {
    return {
      texto: `El costo ${costo} pasa la última fila de la tabla. Se usa ${fila}, pero los precios de esa fila no alcanzan a cubrir este costo: hay que agregar la fila en _DIM_COSTEO.csv antes de lanzar.`,
      tono: "alto",
    };
  }
  return {
    texto: `El costo ${costo} no tiene fila propia en la tabla. costear.py usa la fila ${fila} (criterio: ${criterio}). Es la regla del script: la más cercana, y en empate la superior.`,
    tono: "aviso",
  };
}

export function TablaGuatemala({ costeo }: { costeo: Costeo }) {
  const aviso = explicarFila(costeo);
  const arranque = costeo.arranque as { decision?: string; nota?: string; p1u_minimo?: number };

  return (
    <Tarjeta className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-medium text-zinc-100">Tabla de precios · Guatemala</h3>
        <Chip tono={aviso?.tono ?? "dato"} titulo="Qué fila de _DIM_COSTEO.csv se usó">
          fila Q{String(costeo.fila_usada)} · {costeo.criterio_de_fila}
        </Chip>
      </div>

      {aviso && (
        <p
          className={aviso.tono === "alto" ? "text-xs text-rose-300" : "text-xs text-amber-300"}
          data-testid="aviso-fila"
        >
          {aviso.texto}
        </p>
      )}

      <table className="w-full text-sm" data-testid="escalera">
        <thead>
          <tr className="text-left text-xs uppercase tracking-wide text-zinc-500">
            <th className="pb-2 font-medium">Oferta</th>
            <th className="pb-2 font-medium">Precio</th>
            <th className="pb-2 font-medium">Costo del pedido</th>
          </tr>
        </thead>
        <tbody>
          {costeo.escalera.map((fila) => (
            <tr key={fila.unidades} className="border-t border-zinc-800">
              <td className="py-2 text-zinc-300">
                {fila.unidades} unidad{fila.unidades > 1 ? "es" : ""}
              </td>
              <td className="py-2 font-semibold text-zinc-100">{q(fila.precio)}</td>
              <td className="py-2 text-zinc-400">{q(fila.costo_pedido)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4" data-testid="umbrales">
        <div>
          <dt className="text-xs text-zinc-500">
            CPA objetivo
            <Info termino="cpa" />
          </dt>
          <dd className="text-zinc-100">{q(costeo.cpa_objetivo)}</dd>
        </div>
        <div>
          <dt className="text-xs text-zinc-500">
            Break-even
            <Info termino="break_even" />
          </dt>
          <dd className="font-semibold text-zinc-100">{q(costeo.cpa_break_even)}</dd>
        </div>
        <div>
          <dt className="text-xs text-zinc-500">Envío</dt>
          <dd className="text-zinc-100">{q(costeo.valor_envio)}</dd>
        </div>
        <div>
          <dt className="text-xs text-zinc-500">Ganancia por pedido de 1u</dt>
          <dd className="text-zinc-100">{q(costeo.utilidad_esperada)}</dd>
        </div>
      </dl>

      {arranque.nota && (
        <p className="text-xs text-zinc-400">
          <span className="font-medium text-zinc-300">Cómo arranca la oferta ({arranque.decision}):</span>{" "}
          {arranque.nota}
        </p>
      )}
      <p className="text-[11px] text-zinc-600">
        Fuente: {costeo.fuente} · escalera {costeo.origen_escalera}. Estas cifras se muestran para
        decidir; las guarda etapa-guardar-producto al cerrar el paquete de FASE 1.
      </p>
    </Tarjeta>
  );
}
