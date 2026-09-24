/**
 * Resultados.tsx — el dinero, en construcción.
 *
 * T4 la llena con el estado de resultados real: DOCTRINA/CONTABILIDAD.md manda sobre
 * cualquier otro cálculo (negocio CONTRA ENTREGA; un cohorte de menos de 10 días es
 * PRELIMINAR). Esta pantalla no calcula nada todavía — es el marcador de lugar del gate P4.
 */
import { LineChart } from "lucide-react";

export function Resultados() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-border px-6 py-16 text-center">
      <LineChart className="size-8 text-muted-foreground" />
      <h1 className="text-lg font-semibold tracking-tight">Resultados — en construcción</h1>
      <p className="max-w-md text-sm text-muted-foreground">
        Acá va a vivir el estado de resultados real (ganancia, caja, break-even por producto),
        leyendo la capa de contabilidad del sistema. Todavía no está construido.
      </p>
    </div>
  );
}
