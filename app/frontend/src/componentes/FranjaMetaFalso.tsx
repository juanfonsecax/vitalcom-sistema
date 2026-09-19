import { useQuery } from "@tanstack/react-query";
import { api } from "../api/cliente";

export function FranjaMetaFalso() {
  const claude = useQuery({ queryKey: ["claude"], queryFn: api.claude, staleTime: 30_000 });
  if (!claude.data?.meta_falso) return null;
  return (
    <div
      role="alert"
      data-testid="franja-meta-falso"
      className="bg-rose-600 px-4 py-1.5 text-center text-xs font-bold uppercase tracking-wider text-white shadow-md"
    >
      META FALSO — nada llega a Meta
    </div>
  );
}
