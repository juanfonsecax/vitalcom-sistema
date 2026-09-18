/**
 * progreso.ts — el progreso en vivo de un trabajo (SSE, `GET /api/trabajos/{id}/eventos`).
 *
 * Un `EventSource` por trabajo abierto. El navegador reconecta solo con `Last-Event-ID`, así que
 * un corte de red no repite ni pierde líneas; al llegar `fin` el servidor cierra y acá también.
 */
import { useEffect, useState } from "react";
import type { LineaEnVivo } from "./cliente";

const MAXIMO_DE_LINEAS = 1000;

export function usarProgreso(id: string | null, alTerminar?: () => void) {
  const [lineas, setLineas] = useState<LineaEnVivo[]>([]);
  const [conectado, setConectado] = useState(false);

  useEffect(() => {
    setLineas([]);
    setConectado(false);
    if (!id) return;
    const fuente = new EventSource(`/api/trabajos/${encodeURIComponent(id)}/eventos`);
    fuente.onopen = () => setConectado(true);
    fuente.addEventListener("linea", (evento) => {
      const linea = JSON.parse((evento as MessageEvent).data) as LineaEnVivo;
      setLineas((previas) => [...previas, linea].slice(-MAXIMO_DE_LINEAS));
    });
    fuente.addEventListener("estado", () => alTerminar?.());
    fuente.addEventListener("pendiente", () => alTerminar?.());
    fuente.addEventListener("fin", () => {
      fuente.close();
      setConectado(false);
      alTerminar?.();
    });
    return () => fuente.close();
    // `alTerminar` cambia en cada render: el efecto depende solo del trabajo que se sigue.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  return { lineas, conectado };
}
