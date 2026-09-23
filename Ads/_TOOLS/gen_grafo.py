#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_grafo.py — el GATE DE RECONCILIACION, pero del SISTEMA.

Por que existe
--------------
`verificar_producto.py` comprueba que un PRODUCTO sea coherente consigo mismo.
Nada comprobaba que el SISTEMA lo fuera. Y el sistema ya fallo tres veces por lo
mismo — una copia que nadie sabia que existia:

  · AGENTS.md, copia linea por linea de CLAUDE.md (538 vs 538).
  · .codex/agents/, tercera copia ya divergida: 13 de 17 etapas.
  · .agents/skills/, dos skills polizonas fuera de skills-lock.json, una de
    ellas apuntando a `.Codex/agents/` — un directorio ya retirado.

Las tres eran invisibles hasta que un humano las miro. Este script las vuelve un
numero. Es lo que un mapeador de codigo generico NO puede hacer, porque no sabe
que en este repo `.claude/` corre y lo jubilado no existe: se probo Graphify
el 2026-09-03 y el 26 % de su grafo salia de zonas muertas, rankeando el
COPYWRITING_ADS.md retirado igual que el vivo.

Que mide
--------
  1. COSTO      arranque en frio y techo de instrucciones por fase, en tokens.
  2. DIOS       que documento hereda mas tokens (peso x cantidad de lectores).
  3. HUERFANOS  .md y .csv que el sistema mantiene y nadie consume.
  4. MUERTAS    referencias a archivos que ya no existen. Se separan de los
                INSUMOS que el documento le pide al operador y que todavia
                no entrego: eso es estado normal, no defecto.
  5. MODELO     agentes sin `model: inherit`.

Como se usa
-----------
    python Ads/_TOOLS/gen_grafo.py                  # informe, SOLO LECTURA
    python Ads/_TOOLS/gen_grafo.py --comparar       # informe + delta vs la base guardada
    python Ads/_TOOLS/gen_grafo.py --estricto       # exit 1 si hay hallazgos
    python Ads/_TOOLS/gen_grafo.py --escribir       # ademas, guarda/actualiza la linea base

Contrato de CLI (T6, parejo con flujo.py y decidir.py): un "mirar" nunca
escribe. Por defecto este comando SOLO LEE — ni siquiera reescribe la linea
base. `--escribir` es el unico flag que toca disco (`_LINEA_BASE_SISTEMA.json`).
`--comparar` y `--estricto` se combinan libremente con o sin `--escribir`.
La regla es medir antes y despues: corre `--comparar` antes del cambio, corre
`--escribir` despues del cambio para fijar la nueva base, y el delta sale solo
la proxima vez que se compare.

El modelo de costo es tokens ~= bytes / 3.6, calibrado contra la auditoria del
2026-09-02 (CLAUDE.md: 12.903 B -> 3.580 tok). Es un TECHO: cuenta como cargado
todo .md que un agente menciona. No es comparable con otra metrica, solo consigo
mismo — que es justo para lo que sirve.
"""

import argparse
import collections
import io
import json
import os
import re
import sys
import unicodedata

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(BASE)

BYTES_POR_TOKEN = 3.6
LINEA_BASE = os.path.join("PRODUCTOS", "_AUDITORIAS", "_LINEA_BASE_SISTEMA.json")

# Zonas que CLAUDE.md declara referencia humana: el sistema NO las ejecuta.
# Sin esto, un mapeador cuenta lo jubilado igual que lo vivo. `_ARCHIVO` salio
# de esta lista el 22-sep-2026 (T9): el directorio ya no existe en el repo, y
# `_RESPALDOS/` (su reemplazo para backups en vivo, gitignored) no necesita
# entrar aca — no tiene .md ni lo alcanza `construir()` (solo lista archivos
# EN los directorios declarados, no recursivo).
ZONAS_MUERTAS = ("_ROADMAP", "_OPERADOR", "_CONOCIMIENTO",
                 "_SKILLS_FUENTE", "INFPRODUCTOS", "graphify-out", ".git")
# .md de raiz que son para el humano, no para el flujo. No son huerfanos.
DOCS_HUMANOS = ("README.md", "AGENTS.md")

MAY = "A-Z0-9_ÁÉÍÓÚÑ"
RE_MD = re.compile(r"\b([" + MAY + r"][" + MAY + r"-]{2,}\.md)\b")
RE_CSV = re.compile(r"\b(_[A-Z_]+\.csv)\b")
RE_ETAPA = re.compile(r"\b(etapa-[a-z0-9-]+)\b")
# Rutas citadas entre comillas o backticks: es lo que atrapa a un `.Codex/...`
RE_RUTA = re.compile(r"[`\"'(]((?:\.[a-zA-Z]+|Ads|PRODUCTOS|DOCTRINA)/[\w./À-ÿ -]+?"
                     r"\.(?:md|py|csv|json|sh|txt))[`\"')]")
# La linea manda CREAR el archivo o lo marca opcional: es insumo, no ruta rota.
# Se compara SIN TILDES (ver sin_tildes): el mismo caracter acentuado llega en
# dos formas Unicode distintas segun quien escribio el archivo, y una regex con
# la tilde adentro falla EN SILENCIO contra la otra forma. Sin tildes no puede.
RE_INSUMO = re.compile(r"\b(opcional|copiar?|copia|pegar?|pega|guardar?|guarda|"
                       r"crear|crea|poner?|pone|adjuntar?|adjunta|"
                       r"entregar?|entrega|aporta|genera)\w*", re.I)


def sin_tildes(texto):
    """Normaliza para comparar: la tilde no debe decidir si un match ocurre."""
    return "".join(c for c in unicodedata.normalize("NFD", texto)
                   if not unicodedata.combining(c))


def tokens(ruta):
    try:
        return int(os.path.getsize(ruta) / BYTES_POR_TOKEN)
    except OSError:
        return 0


def leer(ruta):
    try:
        return io.open(ruta, encoding="utf-8", errors="ignore").read()
    except OSError:
        return ""


def zona_viva(ruta):
    return not ruta.replace("\\", "/").lstrip("./").startswith(ZONAS_MUERTAS)


def frontmatter(texto):
    if not texto.startswith("---"):
        return {}
    fin = texto.find("\n---", 3)
    datos, clave = {}, None
    for linea in texto[3:fin].splitlines():
        m = re.match(r"^([a-z_]+):\s*(.*)$", linea)
        if m:
            clave = m.group(1)
            datos[clave] = m.group(2)
        elif clave:
            datos[clave] += " " + linea.strip()
    return datos


def construir():
    """Devuelve el indice de .md y el grafo de agentes y skills con lo que consumen."""
    indice = {}
    for carpeta in (".", "DOCTRINA", "Ads/_TOOLS", "Ads/_SWIPE", "PRODUCTOS"):
        if os.path.isdir(carpeta):
            for f in os.listdir(carpeta):
                if f.endswith(".md"):
                    indice.setdefault(f, os.path.join(carpeta, f).replace("\\", "/"))

    def refs(texto):
        return ({m for m in RE_MD.findall(texto) if m in indice},
                set(RE_CSV.findall(texto)))

    agentes = {}
    for f in sorted(os.listdir(".claude/agents")):
        if not f.endswith(".md"):
            continue
        ruta = ".claude/agents/" + f
        texto = leer(ruta)
        fm = frontmatter(texto)
        md, csv = refs(texto)
        agentes[fm.get("name", f)] = {
            "archivo": ruta,
            "tokens": tokens(ruta),
            "model": fm.get("model", "(sin declarar)"),
            "desc_tok": int(len(fm.get("description", "").encode("utf-8")) / BYTES_POR_TOKEN),
            "lee_md": sorted(md),
            "lee_csv": sorted(csv)}

    skills = {}
    for d in sorted(os.listdir(".claude/skills")):
        ruta = ".claude/skills/%s/SKILL.md" % d
        if not os.path.isfile(ruta):
            continue
        texto = leer(ruta)
        fm = frontmatter(texto)
        md, csv = refs(texto)
        skills[fm.get("name", d)] = {
            "archivo": ruta,
            "tokens": tokens(ruta),
            "desc_tok": int(len(fm.get("description", "").encode("utf-8")) / BYTES_POR_TOKEN),
            "invoca": sorted(set(RE_ETAPA.findall(texto))),
            "lee_md": sorted(md),
            "lee_csv": sorted(csv)}

    return indice, agentes, skills


def analizar():
    indice, agentes, skills = construir()
    claude = tokens("CLAUDE.md")

    frio = (claude
            + sum(a["desc_tok"] for a in agentes.values())
            + sum(s["desc_tok"] for s in skills.values()))

    def costo_fase(nombre):
        """Se SUMA por subagente: cada uno hereda CLAUDE.md entero, no lo comparte."""
        s = skills.get(nombre)
        if not s:
            return 0
        total = s["tokens"] + sum(tokens(indice[m]) for m in s["lee_md"])
        for etapa in s["invoca"]:
            a = agentes.get(etapa)
            if a:
                total += claude + a["tokens"] + sum(tokens(indice[m]) for m in a["lee_md"])
        return total

    fases = {n: costo_fase(n) for n in
             ("fase-1-angulos", "fase-2-conceptos", "fase-3-escalado", "ciclo-diario")}

    lectores = collections.Counter()
    for a in agentes.values():
        for m in a["lee_md"]:
            lectores[m] += 1
    dios = sorted(((m, c, tokens(indice[m]), c * tokens(indice[m]))
                   for m, c in lectores.items()), key=lambda x: -x[3])

    # Fuentes vivas: todo lo que el sistema SI ejecuta. Nada de zonas muertas.
    fuentes = [a["archivo"] for a in agentes.values()]
    fuentes += [s["archivo"] for s in skills.values()]
    # README.md y AGENTS.md son para el humano: que ELLOS nombren un doc no lo
    # vuelve consumido por el flujo. Si son fuente, tapan al huerfano real.
    fuentes += [p for p in indice.values()
                if zona_viva(p) and os.path.basename(p) not in DOCS_HUMANOS]
    fuentes += ["Ads/_TOOLS/" + f for f in os.listdir("Ads/_TOOLS")
                if f.endswith((".py", ".sh"))]
    fuentes += ["CLAUDE.md", ".claude/settings.json"]

    nombrados_md, nombrados_csv = set(), set()
    for ruta in fuentes:
        texto = leer(ruta)
        propio = os.path.basename(ruta)
        nombrados_md |= {m for m in RE_MD.findall(texto) if m != propio}
        nombrados_csv |= set(RE_CSV.findall(texto))

    docs_raiz = sorted(f for f in os.listdir(".") if f.endswith(".md"))
    huerfanos_md = [d for d in docs_raiz
                    if d not in nombrados_md
                    and d not in DOCS_HUMANOS
                    and d != "CLAUDE.md"]
    csv_disco = sorted(f for f in os.listdir("PRODUCTOS") if f.endswith(".csv"))
    huerfanos_csv = [c for c in csv_disco if c not in nombrados_csv]

    # Una ruta que no existe puede ser dos cosas MUY distintas, y confundirlas
    # arruina el gate: si reporta como defecto algo que esta bien, se ignora.
    #   · RUTA MUERTA  — el documento apunta a un archivo que deberia estar y no
    #     esta. Siempre es un defecto (asi murio `.Codex/agents/`).
    #   · INSUMO       — el documento le PIDE al operador que cree el archivo.
    #     Que no exista es el estado normal antes de que lo entregue.
    # Se separan por la linea que los nombra: si manda crear o dice opcional,
    # es insumo. Heuristica, no verdad: por eso van en listas distintas y solo
    # las muertas cuentan para --estricto.
    muertas, insumos = [], []
    vistas = set()
    for ruta in fuentes:
        lineas = leer(ruta).splitlines()
        for i, linea in enumerate(lineas):
            for cand in RE_RUTA.findall(linea):
                if os.path.exists(cand) or (ruta, cand) in vistas:
                    continue
                vistas.add((ruta, cand))
                # La prosa se corta y el verbo suele caer en la linea de
                # arriba, separado de la ruta. Por eso la ventana incluye la
                # linea previa. (Es el caso de ETAPA-RECOLECCION.)
                contexto = (lineas[i - 1] if i else "") + " " + linea
                destino = insumos if RE_INSUMO.search(sin_tildes(contexto)) else muertas
                destino.append([ruta, cand])

    sin_inherit = sorted(n for n, a in agentes.items() if a["model"] != "inherit")

    return {"arranque_frio": frio,
            "claude_md": claude,
            "fases": fases,
            "nodos_dios": dios,
            "huerfanos_md": huerfanos_md,
            "huerfanos_csv": huerfanos_csv,
            "rutas_muertas": muertas,
            "insumos_faltantes": insumos,
            "sin_inherit": sin_inherit,
            "inventario": {"agentes": len(agentes), "skills": len(skills),
                           "docs_raiz": len(docs_raiz), "csv": len(csv_disco)}}


def informe(r, previo=None):
    L = ["=" * 74,
         "GRAFO DEL SISTEMA  ·  gen_grafo.py  ·  tokens = bytes / %.1f" % BYTES_POR_TOKEN,
         "=" * 74, ""]

    def delta(actual, antes):
        if previo is None or antes is None:
            return ""
        if antes == actual:
            return "        ="
        return "   %+7d" % (actual - antes)

    L += ["1. COSTO",
          "   arranque en frio ......... %8d tok%s"
          % (r["arranque_frio"], delta(r["arranque_frio"], (previo or {}).get("arranque_frio")))]
    for f, v in r["fases"].items():
        L.append("   %-24s %8d tok%s"
                 % (f, v, delta(v, (previo or {}).get("fases", {}).get(f))))

    L += ["", "2. NODOS DIOS  (lo que mas se hereda: peso x lectores)"]
    for m, c, t, heredado in r["nodos_dios"][:8]:
        L.append("   %8d tok heredados  %-34s %6d tok x %d agentes" % (heredado, m, t, c))

    L += ["", "3. HALLAZGOS",
          "   .md sin consumidor ....... %s" % (", ".join(r["huerfanos_md"]) or "ninguno"),
          "   .csv sin consumidor ...... %s" % (", ".join(r["huerfanos_csv"]) or "ninguno"),
          "   agentes sin model:inherit  %s" % (", ".join(r["sin_inherit"]) or "ninguno")]
    if r["rutas_muertas"]:
        L.append("   RUTAS MUERTAS:")
        for origen, destino in r["rutas_muertas"]:
            L.append("      %s  ->  %s  (NO EXISTE)" % (origen, destino))
    else:
        L.append("   rutas muertas ............ ninguna")
    if r.get("insumos_faltantes"):
        L.append("   insumos que el operador aun no entrego (normal, no es defecto):")
        for origen, destino in r["insumos_faltantes"]:
            L.append("      %s  espera  %s" % (origen, destino))

    inv = r["inventario"]
    L += ["", "4. INVENTARIO",
          "   agentes %d · skills %d · docs raiz %d · CSV %d"
          % (inv["agentes"], inv["skills"], inv["docs_raiz"], inv["csv"]),
          "=" * 74]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="Mapa y gate de coherencia del SISTEMA.")
    ap.add_argument("--comparar", action="store_true",
                    help="mostrar el delta contra la linea base guardada")
    ap.add_argument("--estricto", action="store_true", help="exit 1 si hay hallazgos")
    ap.add_argument("--escribir", action="store_true",
                    help="guarda/actualiza la linea base (por defecto solo lee)")
    args = ap.parse_args()

    r = analizar()
    previo = None
    if args.comparar and os.path.isfile(LINEA_BASE):
        previo = json.load(io.open(LINEA_BASE, encoding="utf-8"))
    print(informe(r, previo))

    if args.escribir:
        os.makedirs(os.path.dirname(LINEA_BASE), exist_ok=True)
        json.dump(r, io.open(LINEA_BASE, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print("linea base guardada en %s" % LINEA_BASE)

    # Los insumos faltantes NO cuentan: no son defectos del sistema.
    hallazgos = (len(r["huerfanos_md"]) + len(r["huerfanos_csv"])
                 + len(r["rutas_muertas"]) + len(r["sin_inherit"]))
    if args.estricto and hallazgos:
        print("\n%d hallazgos. --estricto -> exit 1" % hallazgos)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
