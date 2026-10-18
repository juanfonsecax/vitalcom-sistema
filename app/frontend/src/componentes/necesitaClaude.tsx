/**
 * necesitaClaude.tsx — la tarjeta «Necesita Claude».
 *
 * Toda escritura en Meta (renombrar, activar, pausar, escalar) se hace por el MCP desde una sesión de
 * Claude; la app solo lee y verifica. Cuando una verificación descubre algo que exige una escritura,
 * el backend devuelve items `requiere_claude` (forma de `Ads/_TOOLS/requiere_claude.py`) y acá se
 * muestran: el motivo y la frase exacta para pegarle a Claude, con su botón «Copiar».
 *
 * Sin items NO se pinta nada (ni un contenedor vacío): el aviso existe solo cuando hace falta.
 */
import type { AvisoClaude } from "../api/cliente";
import { BotonCopiarTexto } from "./copiar";

export function NecesitaClaude({ avisos }: { avisos: AvisoClaude[] | null | undefined }) {
  if (!avisos || avisos.length === 0) return null;
  return (
    <section
      role="alert"
      data-testid="necesita-claude"
      className="space-y-3 rounded-lg border border-amber-500/40 bg-amber-500/10 p-4"
    >
      <h3 className="text-sm font-semibold text-amber-200">Necesita Claude</h3>
      <p className="text-xs text-muted-foreground">
        La app solo lee Meta. Para esto hay que abrir una sesión de Claude y pegarle la frase.
      </p>
      <ul className="space-y-3">
        {avisos.map((aviso, i) => (
          <li key={`${aviso.codigo}-${i}`} data-testid={`aviso-${aviso.codigo}`} className="space-y-1.5">
            <p className="text-sm">{aviso.motivo}</p>
            <div className="flex items-start gap-2">
              <code className="flex-1 whitespace-pre-wrap rounded bg-muted px-2 py-1 text-xs">
                {aviso.pedirle_a_claude}
              </code>
              <BotonCopiarTexto texto={aviso.pedirle_a_claude}>Copiar</BotonCopiarTexto>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
