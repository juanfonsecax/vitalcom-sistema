/**
 * copiar.tsx — copiar texto/imagen al portapapeles + el lightbox de imagen ampliada.
 *
 * Extraído de Fase2.tsx (galería de conceptos) para que Fase1.tsx (referencia fija +
 * prompts de ángulo) use el MISMO mecanismo en vez de duplicarlo — un dato, un dueño,
 * también vale para comportamiento de UI compartido.
 */
import { useState, type ReactNode } from "react";

/** Copia texto plano al portapapeles. Lanza si el navegador no lo soporta. */
export async function copiarTextoAlPortapapeles(texto: string): Promise<void> {
  await navigator.clipboard.writeText(texto);
}

/**
 * Copia una imagen al portapapeles como PNG (Clipboard API exige image/png; la referencia
 * del swipe suele venir en .jpg). Lanza si el navegador no soporta escribir imágenes al
 * portapapeles (ClipboardItem / canvas) — el llamador decide el fallback (descargar).
 */
export async function copiarImagenAlPortapapeles(url: string): Promise<void> {
  if (typeof ClipboardItem === "undefined" || !navigator.clipboard?.write) {
    throw new Error("Clipboard de imágenes no disponible en este navegador");
  }
  const respuesta = await fetch(url);
  const blob = await respuesta.blob();
  const bitmap = await createImageBitmap(blob);
  const canvas = document.createElement("canvas");
  canvas.width = bitmap.width;
  canvas.height = bitmap.height;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("No se pudo preparar el canvas");
  ctx.drawImage(bitmap, 0, 0);
  const pngBlob: Blob | null = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
  if (!pngBlob) throw new Error("No se pudo convertir la imagen a PNG");
  await navigator.clipboard.write([new ClipboardItem({ "image/png": pngBlob })]);
}

/** Descarga el archivo (fallback cuando el navegador no puede copiar la imagen). */
export function descargarArchivo(url: string, nombrePorDefecto: string) {
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = url.split("/").pop() || nombrePorDefecto;
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
}

/** Botón "Copiar" de texto plano, con su propio estado de "Copiado" (2.5s). */
export function BotonCopiarTexto({
  texto,
  className,
  children = "Copiar",
  etiquetaCopiado = "Copiado",
}: {
  texto: string;
  className?: string;
  children?: ReactNode;
  etiquetaCopiado?: string;
}) {
  const [copiado, setCopiado] = useState(false);
  return (
    <button
      type="button"
      onClick={() =>
        copiarTextoAlPortapapeles(texto).then(() => {
          setCopiado(true);
          setTimeout(() => setCopiado(false), 2500);
        })
      }
      className={
        className ||
        "shrink-0 rounded-lg border border-border bg-muted px-2 py-0.5 text-[11px] font-medium text-foreground transition-colors hover:bg-accent"
      }
    >
      {copiado ? etiquetaCopiado : children}
    </button>
  );
}

/** Botón "Copiar imagen" (PNG), con fallback a descarga si el navegador no soporta el portapapeles. */
export function BotonCopiarImagen({
  url,
  nombreArchivo = "referencia.jpg",
  className,
}: {
  url: string;
  nombreArchivo?: string;
  className?: string;
}) {
  const [copiada, setCopiada] = useState(false);
  return (
    <button
      type="button"
      onClick={async () => {
        try {
          await copiarImagenAlPortapapeles(url);
          setCopiada(true);
          setTimeout(() => setCopiada(false), 2500);
        } catch {
          descargarArchivo(url, nombreArchivo);
        }
      }}
      className={
        className ||
        "shrink-0 rounded border border-border bg-muted px-2 py-0.5 text-[11px] font-medium text-foreground transition-colors hover:bg-accent"
      }
    >
      {copiada ? "Copiada" : "Copiar imagen"}
    </button>
  );
}

/** El bloque imagen (click para ampliar) + etiqueta + botón "Copiar imagen", tal como lo usa
 * la galería de FASE 2. `onAmpliar` abre el lightbox de arriba. */
export function ImagenDeReferencia({
  url,
  alt,
  etiqueta,
  onAmpliar,
}: {
  url: string;
  alt: string;
  etiqueta: string;
  onAmpliar: (url: string) => void;
}) {
  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <button
        type="button"
        onClick={() => onAmpliar(url)}
        className="block w-full"
        title="Ver referencia en tamaño completo"
      >
        <img src={url} alt={alt} className="h-32 w-full object-cover object-top" />
      </button>
      <div className="flex items-center justify-between gap-2 bg-muted/40 px-2 py-1">
        <span className="text-[10px] uppercase tracking-wider text-muted-foreground">{etiqueta}</span>
        <BotonCopiarImagen url={url} nombreArchivo={url.split("/").pop() || "referencia.jpg"} />
      </div>
    </div>
  );
}

/** El lightbox de imagen ampliada (overlay que cierra con click), compartido entre F1 y F2. */
export function Lightbox({ url, alt, onCerrar }: { url: string; alt: string; onCerrar: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-6"
      onClick={onCerrar}
    >
      <img src={url} alt={alt} className="max-h-full max-w-full rounded-lg border border-zinc-700 object-contain" />
    </div>
  );
}
