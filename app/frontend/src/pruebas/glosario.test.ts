/**
 * El glosario es el compromiso con el operador: ningún término técnico sin su explicación.
 * Si una pantalla usa un `<Info termino="x">`, `x` tiene que existir acá con su definición.
 */
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { expect, test } from "vitest";
import { GLOSARIO } from "../glosario";

const SRC = join(import.meta.dirname, "..");

function archivosFuente(carpeta: string): string[] {
  return readdirSync(carpeta, { withFileTypes: true }).flatMap((entrada) => {
    const ruta = join(carpeta, entrada.name);
    if (entrada.isDirectory()) return entrada.name === "pruebas" ? [] : archivosFuente(ruta);
    return /\.tsx?$/.test(entrada.name) ? [ruta] : [];
  });
}

test("cada término usado en pantalla está definido en el glosario", () => {
  const usados = new Set<string>();
  for (const archivo of archivosFuente(SRC)) {
    const codigo = readFileSync(archivo, "utf8");
    for (const coincidencia of codigo.matchAll(/termino="([a-z0-9_]+)"/g)) usados.add(coincidencia[1]);
  }
  expect(usados.size).toBeGreaterThan(0);
  const sinDefinir = [...usados].filter((t) => !(t in GLOSARIO));
  expect(sinDefinir).toEqual([]);
});

test("ninguna definición está vacía y cada una dice quién produce el dato", () => {
  for (const [clave, termino] of Object.entries(GLOSARIO)) {
    expect(termino.rotulo, clave).not.toBe("");
    expect(termino.que_es.length, clave).toBeGreaterThan(30);
    expect(termino.dueno, clave).toBeTruthy();
  }
});
