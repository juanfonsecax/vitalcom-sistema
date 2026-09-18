# -*- coding: utf-8 -*-
"""bandas_edad.py — LA TABLA DE DERIVACION DE BANDA DE EDAD, un solo lugar (G0.5 punto 4.2,
15-sep-2026).

POR QUE EXISTE
---------------
Vivia triplicada y desincronizada: `.claude/agents/ETAPA-6.md` (4 filas en prosa),
`gen_publicacion.py::BANDA_POR_AVATAR` (4 filas) y `gen_lanzador.py::BANDAS` (9 filas) —
confirmado en vivo que gen_lanzador.py era la mas completa: tenia '35-45'->'35-50' y
'30-45'->'30-45' que a las otras dos les faltaba. Mismo patron que ya resuelve
`Ads/_TOOLS/firma.py` para la firma de 5 ejes: "se importa, no se copia". gen_publicacion.py
y gen_lanzador.py importan ESTE modulo; ETAPA-6.md queda como puntero de prosa con la
evidencia doctrinal (APR-060) al lado, nunca como tabla independiente que alguien tiene
que acordarse de sincronizar.

DE DONDE SALE CADA FILA
------------------------
    45-65, 45-60, 35-55, 30-45, 40-55, 45-55, 25-45   identidad: el avatar YA es la banda
                                                        que se configura en Meta
    35-45 -> 35-50, 25-35 -> 25-40                     ensanche +5 arriba de rango, con
                                                        evidencia propia (APR-060, ver
                                                        ETAPA-6.md BANDA DE EDAD)
    25-40, 30-40                                       agregadas 15-sep-2026: dos valores
        del vocabulario que el operador senalo sin fila. PRODUCTOS/CLEARSTEM/_PLAN.json los
        declara como avatar_edad de ANTI_FALSIFICACION/MEDICOS_FALLARON (25-40) y
        TESTIMONIO_RADICAL (30-40) — pero PRODUCTOS/_DIM_CONJUNTOS.csv registra el avatar
        REAL medido en Meta para esos mismos angulos como 25-35, lo que sugiere que el plan
        guardo la banda YA DERIVADA en el campo avatar_edad en vez del bucket crudo. Este
        modulo no corrige _PLAN.json (no es su dueno — lo es ETAPA-2/ETAPA-6): registra
        identidad, SIN el ensanche +5 de 25-35/35-45 porque no hay evidencia APR-060 propia
        para estos dos, y deja la nota para que el operador lo confirme contra el avatar
        crudo antes de asumir que 25-40/30-40 son el bucket real.

USO
    from bandas_edad import banda_tupla, banda_str, BANDA_AMPLIA_TUPLA, BANDA_AMPLIA_STR
"""

# (avatar_edad declarado en el angulo, banda que se configura en Meta) — el ORDEN es el de
# alta: no reordenar, es el historial de cuando se agrego cada fila.
BANDAS = [
    ("45-65", "45-65"),
    ("45-60", "45-60"),
    ("35-55", "35-55"),
    ("35-45", "35-50"),
    ("25-35", "25-40"),
    ("30-45", "30-45"),
    ("40-55", "40-55"),
    ("45-55", "45-55"),
    ("25-45", "25-45"),
    ("25-40", "25-40"),   # sin ensanche propio — ver "DE DONDE SALE CADA FILA" arriba
    ("30-40", "30-40"),   # idem
]

BANDA_POR_AVATAR = dict(BANDAS)   # avatar_edad -> "NN-MM" (string, para nombres/reportes)

BANDA_AMPLIA_STR = "18-65+"
BANDA_AMPLIA_TUPLA = (18, 65)


def _a_tupla(s):
    ini, fin = s.replace("+", "").split("-")
    return int(ini), int(fin)


def banda_str(avatar_edad):
    """avatar_edad -> 'NN-MM' ya derivada. Cadena vacia -> BANDA_AMPLIA_STR (unica
    excepcion, ETAPA-6.md). Valor no reconocido -> None: el llamador decide si bloquea
    o cae a 'tal cual' segun su propio criterio (gen_publicacion bloquea, gen_lanzador
    avisa) — este modulo solo es dueno de la TABLA, no de que hacer si falta la fila."""
    ae = (avatar_edad or "").strip()
    if not ae:
        return BANDA_AMPLIA_STR
    return BANDA_POR_AVATAR.get(ae)


def banda_tupla(avatar_edad):
    """Igual que banda_str pero devuelve (age_min, age_max) para targeting.age_min/max."""
    ae = (avatar_edad or "").strip()
    if not ae:
        return BANDA_AMPLIA_TUPLA
    s = BANDA_POR_AVATAR.get(ae)
    return _a_tupla(s) if s else None
