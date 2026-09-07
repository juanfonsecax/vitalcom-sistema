# -*- coding: utf-8 -*-
"""app_html.py — Renderizador de la SPA moderna y ultra-rápida de VitalCom.

Organizada en los 4 módulos nativos de alto impacto:
  1. DECISIONES & FATIGA: Motor determinista + detector temprano de fatiga.
  2. LANZADOR 1-CLIC: Portafolio + consola de 7 pasos (Fase 1 y Fase 2 Lean).
  3. FÁBRICA CREATIVA: 22 Blueprints canónicos del mercado GT (0 iframes pesados).
  4. SALUD & SISTEMA: Auditoría de frescura y comandos CLI directos.
"""

import json

def _incrustar(obj):
    """JSON seguro para incrustar dentro de un tag <script>."""
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def HTML(estado, lanzador, decisiones=None, blueprints=None):
    decisiones = decisiones or {"resumen_acciones": {}, "productos": []}
    blueprints = blueprints or []
    app = estado.get("app", {})
    titulo = app.get("titulo", "VitalCom Guatemala")
    subtitulo = app.get("subtitulo", "Sistema Operativo de E-commerce COD")
    generado = estado.get("generado", "")

    return f"""<!doctype html>
<html lang="es" data-theme="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{titulo} · Sistema</title>
  <style>
    :root {{
      --ground: #0b0f19;
      --surface: #131927;
      --surface-2: #1c2438;
      --line: #263048;
      --line-soft: #1d2538;
      --ink: #f1f5f9;
      --ink-2: #94a3b8;
      --ink-3: #64748b;
      --accent: #3b82f6;
      --accent-soft: #1e293b;
      --accent-hover: #60a5fa;
      --good: #4ade80;
      --good-bg: #143823;
      --warn: #fbbf24;
      --warn-bg: #382d13;
      --crit: #f87171;
      --crit-bg: #3b1a1a;
      --fatiga: #38bdf8;
      --fatiga-bg: #0c2b42;
      --radius: 10px;
      --font-sans: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      --font-mono: ui-monospace, 'Cascadia Code', 'SF Mono', 'Roboto Mono', monospace;
      --shadow: 0 4px 20px -2px rgba(0,0,0,0.4);
    }}
    :root[data-theme="light"] {{
      --ground: #f8fafc;
      --surface: #ffffff;
      --surface-2: #f1f5f9;
      --line: #e2e8f0;
      --line-soft: #edf2f7;
      --ink: #0f172a;
      --ink-2: #475569;
      --ink-3: #94a3b8;
      --accent: #2563eb;
      --accent-soft: #eff6ff;
      --accent-hover: #1d4ed8;
      --good: #16a34a;
      --good-bg: #dcfce7;
      --warn: #d97706;
      --warn-bg: #fef3c7;
      --crit: #dc2626;
      --crit-bg: #fee2e2;
      --fatiga: #0284c7;
      --fatiga-bg: #e0f2fe;
      --shadow: 0 4px 15px -2px rgba(0,0,0,0.06);
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--ground);
      color: var(--ink);
      font-family: var(--font-sans);
      font-size: 14px;
      line-height: 1.55;
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }}

    /* HEADER SUPERIOR */
    header.topbar {{
      background: var(--surface);
      border-bottom: 1px solid var(--line);
      padding: 0 24px;
      height: 60px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex: none;
      z-index: 10;
    }}
    .brand-box {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .brand-logo {{
      width: 32px;
      height: 32px;
      background: linear-gradient(135deg, var(--accent), #8b5cf6);
      border-radius: 8px;
      display: grid;
      place-items: center;
      color: #fff;
      font-weight: 800;
      font-size: 17px;
      box-shadow: 0 2px 8px rgba(59,130,246,0.35);
    }}
    .brand-title {{
      font-weight: 700;
      font-size: 16px;
      letter-spacing: -0.01em;
      color: var(--ink);
    }}
    .brand-tag {{
      background: var(--accent-soft);
      color: var(--accent);
      font-size: 10.5px;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .topbar-actions {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .status-pill {{
      display: flex;
      align-items: center;
      gap: 7px;
      background: var(--surface-2);
      border: 1px solid var(--line);
      padding: 5px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-family: var(--font-mono);
      color: var(--ink-2);
    }}
    .status-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--good);
      box-shadow: 0 0 8px var(--good);
    }}
    .btn-quick {{
      background: var(--accent-soft);
      color: var(--accent);
      border: 1px solid var(--line);
      padding: 6px 13px;
      border-radius: 7px;
      font-size: 12.5px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s;
    }}
    .btn-quick:hover {{
      background: var(--accent);
      color: #fff;
    }}
    .btn-theme {{
      background: var(--surface-2);
      border: 1px solid var(--line);
      color: var(--ink);
      width: 34px;
      height: 34px;
      border-radius: 8px;
      display: grid;
      place-items: center;
      cursor: pointer;
      font-size: 15px;
    }}

    /* NAVEGACIÓN DE MÓDULOS */
    nav.mod-nav {{
      background: var(--surface);
      border-bottom: 1px solid var(--line);
      padding: 0 24px;
      display: flex;
      gap: 6px;
      flex: none;
    }}
    .nav-tab {{
      background: none;
      border: none;
      border-bottom: 2px solid transparent;
      padding: 12px 18px;
      color: var(--ink-2);
      font-size: 13.5px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 9px;
      transition: all 0.15s;
    }}
    .nav-tab:hover {{
      color: var(--ink);
      background: var(--surface-2);
    }}
    .nav-tab.active {{
      color: var(--accent);
      border-bottom-color: var(--accent);
      background: var(--accent-soft);
    }}
    .tab-badge {{
      background: var(--surface-2);
      border: 1px solid var(--line);
      padding: 1px 7px;
      border-radius: 12px;
      font-size: 11px;
      font-family: var(--font-mono);
      font-weight: 700;
      color: var(--ink-2);
    }}
    .nav-tab.active .tab-badge {{
      background: var(--accent);
      color: #fff;
      border-color: transparent;
    }}

    /* CONTENEDOR PRINCIPAL */
    main.viewport {{
      flex: 1;
      overflow-y: auto;
      padding: 24px;
      max-width: 1380px;
      width: 100%;
      margin: 0 auto;
    }}

    /* SECCIONES Y CARDS */
    .module-view {{
      display: none;
    }}
    .module-view.active {{
      display: block;
      animation: fadeIn 0.15s ease-out;
    }}
    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(4px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    .card {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      margin-bottom: 20px;
      overflow: hidden;
      box-shadow: var(--shadow);
    }}
    .card-header {{
      padding: 14px 20px;
      border-bottom: 1px solid var(--line-soft);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--surface);
    }}
    .card-header h3 {{
      font-size: 15px;
      font-weight: 700;
      color: var(--ink);
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .card-body {{
      padding: 20px;
    }}

    /* STATS SUMMARY GRID */
    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px;
      margin-bottom: 22px;
    }}
    .stat-card {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 16px 18px;
      box-shadow: var(--shadow);
      display: flex;
      align-items: center;
      gap: 16px;
      cursor: pointer;
      transition: transform 0.1s, border-color 0.15s;
    }}
    .stat-card:hover {{
      transform: translateY(-2px);
      border-color: var(--accent);
    }}
    .stat-icon {{
      width: 44px;
      height: 44px;
      border-radius: 10px;
      display: grid;
      place-items: center;
      font-size: 20px;
      flex: none;
    }}
    .stat-val {{
      font-size: 24px;
      font-weight: 800;
      font-family: var(--font-mono);
      line-height: 1.1;
      color: var(--ink);
    }}
    .stat-label {{
      font-size: 12px;
      font-weight: 600;
      color: var(--ink-2);
      margin-top: 3px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    /* BADGES */
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 3px 9px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 700;
      font-family: var(--font-mono);
      letter-spacing: 0.03em;
      text-transform: uppercase;
      white-space: nowrap;
    }}
    .b-escalar {{ background: var(--good-bg); color: var(--good); border: 1px solid var(--good); }}
    .b-pausar {{ background: var(--crit-bg); color: var(--crit); border: 1px solid var(--crit); }}
    .b-renovar {{ background: var(--fatiga-bg); color: var(--fatiga); border: 1px solid var(--fatiga); }}
    .b-testeo {{ background: var(--warn-bg); color: var(--warn); border: 1px solid var(--warn); }}
    .b-neutro {{ background: var(--surface-2); color: var(--ink-2); border: 1px solid var(--line); }}

    /* TABLAS */
    table.data-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    table.data-table th {{
      background: var(--surface-2);
      color: var(--ink-3);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 10px 14px;
      font-weight: 700;
      border-bottom: 1px solid var(--line);
      text-align: left;
    }}
    table.data-table td {{
      padding: 12px 14px;
      border-bottom: 1px solid var(--line-soft);
      vertical-align: middle;
    }}
    table.data-table tr:hover td {{
      background: var(--surface-2);
    }}
    .num {{
      text-align: right;
      font-family: var(--font-mono);
      font-variant-numeric: tabular-nums;
      font-size: 12.5px;
    }}

    /* TOOLBARS & FILTROS */
    .filter-bar {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px;
      margin-bottom: 18px;
    }}
    .filter-btn {{
      background: var(--surface);
      border: 1px solid var(--line);
      color: var(--ink-2);
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 12.5px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s;
    }}
    .filter-btn:hover {{
      color: var(--ink);
      border-color: var(--accent);
    }}
    .filter-btn.active {{
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
    }}
    .search-input {{
      background: var(--surface);
      border: 1px solid var(--line);
      color: var(--ink);
      padding: 8px 14px;
      border-radius: 8px;
      font-size: 13px;
      outline: none;
      min-width: 260px;
      font-family: inherit;
    }}
    .search-input:focus {{
      border-color: var(--accent);
    }}

    /* BOTONES DE COPIADO */
    .btn-copy {{
      background: var(--surface-2);
      border: 1px solid var(--line);
      color: var(--ink-2);
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 11.5px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      transition: all 0.15s;
    }}
    .btn-copy:hover {{
      background: var(--accent-soft);
      color: var(--accent);
      border-color: var(--accent);
    }}
    .btn-copy.done {{
      background: var(--good-bg);
      color: var(--good);
      border-color: var(--good);
    }}

    /* BLUEPRINTS GRID */
    .bp-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 18px;
    }}
    .bp-card {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 18px;
      box-shadow: var(--shadow);
      display: flex;
      flex-direction: column;
      gap: 12px;
      transition: transform 0.15s, border-color 0.15s;
    }}
    .bp-card:hover {{
      border-color: var(--accent);
      transform: translateY(-2px);
    }}
    .bp-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 10px;
    }}
    .bp-code {{
      font-family: var(--font-mono);
      font-weight: 800;
      font-size: 13px;
      color: var(--accent);
    }}
    .bp-name {{
      font-size: 15px;
      font-weight: 700;
      color: var(--ink);
      line-height: 1.25;
    }}
    .bp-device {{
      background: var(--surface-2);
      border-left: 3px solid var(--accent);
      padding: 10px 12px;
      border-radius: 0 6px 6px 0;
      font-size: 12.5px;
      color: var(--ink-2);
      line-height: 1.5;
    }}
    .bp-rules {{
      font-size: 12px;
      color: var(--ink-2);
      display: flex;
      flex-direction: column;
      gap: 5px;
    }}
    .bp-rule-item {{
      display: flex;
      gap: 7px;
      align-items: flex-start;
    }}
    .bp-rule-dot {{
      color: var(--accent);
      font-weight: bold;
    }}
    .bp-vars {{
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      margin-top: 4px;
    }}
    .bp-var-chip {{
      background: var(--surface-2);
      border: 1px solid var(--line-soft);
      color: var(--ink-3);
      font-family: var(--font-mono);
      font-size: 10px;
      padding: 2px 6px;
      border-radius: 4px;
    }}

    /* LANZADOR CONSOLE */
    .stepper-nav {{
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      margin-bottom: 22px;
    }}
    .step-btn {{
      background: var(--surface);
      border: 1px solid var(--line);
      color: var(--ink-2);
      padding: 8px 16px;
      border-radius: 20px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.15s;
    }}
    .step-btn:hover {{
      color: var(--ink);
      border-color: var(--accent);
    }}
    .step-btn.active {{
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
    }}
    .step-btn.done {{
      border-color: var(--good);
      color: var(--good);
    }}
    .step-btn.done.active {{
      background: var(--good);
      color: #fff;
    }}

    .field-row {{
      display: flex;
      border: 1px solid var(--line);
      border-radius: 8px;
      margin-bottom: 10px;
      overflow: hidden;
      background: var(--surface);
    }}
    .field-label {{
      background: var(--surface-2);
      color: var(--ink-3);
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 10px 14px;
      width: 140px;
      flex: none;
      border-right: 1px solid var(--line);
      display: flex;
      align-items: center;
    }}
    .field-val {{
      padding: 10px 14px;
      font-family: var(--font-mono);
      font-size: 12.5px;
      flex: 1;
      word-break: break-all;
      display: flex;
      align-items: center;
      color: var(--ink);
    }}
    .field-val.textarea {{
      white-space: pre-wrap;
      max-height: 180px;
      overflow-y: auto;
      font-family: var(--font-sans);
      font-size: 13px;
      line-height: 1.6;
    }}

    /* CHECKLIST */
    .chk-list {{
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .chk-item {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px 16px;
      display: flex;
      gap: 12px;
      align-items: flex-start;
      cursor: pointer;
      transition: background 0.15s;
    }}
    .chk-item:hover {{
      background: var(--surface-2);
    }}
    .chk-item input[type="checkbox"] {{
      margin-top: 3px;
      width: 18px;
      height: 18px;
      accent-color: var(--accent);
      cursor: pointer;
    }}
    .chk-item.checked label b {{
      text-decoration: line-through;
      color: var(--ink-3);
    }}
    .chk-item label {{
      cursor: pointer;
      font-size: 13.5px;
      line-height: 1.45;
    }}
    .chk-why {{
      font-size: 12px;
      color: var(--ink-3);
      margin-top: 4px;
      display: block;
    }}

    /* AVISOS */
    .alert-box {{
      padding: 14px 18px;
      border-radius: 8px;
      margin-bottom: 18px;
      font-size: 13.5px;
      line-height: 1.5;
    }}
    .alert-warn {{ background: var(--warn-bg); color: var(--warn); border-left: 4px solid var(--warn); }}
    .alert-good {{ background: var(--good-bg); color: var(--good); border-left: 4px solid var(--good); }}
    .alert-crit {{ background: var(--crit-bg); color: var(--crit); border-left: 4px solid var(--crit); }}
    .alert-info {{ background: var(--accent-soft); color: var(--accent); border-left: 4px solid var(--accent); }}

    /* TOAST */
    .toast {{
      position: fixed;
      bottom: 24px;
      left: 50%;
      transform: translateX(-50%) translateY(100px);
      background: var(--ink);
      color: var(--ground);
      padding: 10px 22px;
      border-radius: 30px;
      font-size: 13.5px;
      font-weight: 700;
      box-shadow: 0 8px 25px rgba(0,0,0,0.5);
      opacity: 0;
      pointer-events: none;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      z-index: 1000;
    }}
    .toast.show {{
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }}

    /* RESPONSIVE */
    @media (max-width: 860px) {{
      header.topbar {{ padding: 0 16px; height: auto; padding: 12px 16px; flex-wrap: wrap; gap: 10px; }}
      nav.mod-nav {{ overflow-x: auto; padding: 0 12px; }}
      main.viewport {{ padding: 16px; }}
      .field-row {{ flex-direction: column; }}
      .field-label {{ width: 100%; border-right: none; border-bottom: 1px solid var(--line); }}
    }}
  </style>
</head>
<body>

  <!-- TOPBAR -->
  <header class="topbar">
    <div class="brand-box">
      <div class="brand-logo">V</div>
      <div>
        <div style="display:flex;align-items:center;gap:8px;">
          <span class="brand-title">{titulo}</span>
          <span class="brand-tag">Guatemala</span>
        </div>
        <div style="font-size:11.5px;color:var(--ink-3);font-family:var(--font-mono);">{subtitulo} · {generado}</div>
      </div>
    </div>
    <div class="topbar-actions">
      <div class="status-pill">
        <span class="status-dot"></span>
        <span id="pill-text">Motor Operativo Activo</span>
      </div>
      <button class="btn-quick" onclick="copiarComandoDiario()">
        📋 Copiar ciclo_hoy.py
      </button>
      <button class="btn-theme" onclick="toggleTheme()" title="Cambiar tema">🌓</button>
    </div>
  </header>

  <!-- NAVEGACIÓN PRINCIPAL ENTRE LOS 4 MÓDULOS -->
  <nav class="mod-nav">
    <button class="nav-tab active" data-mod="decisiones">
      ⚡ Decisiones & Fatiga
      <span class="tab-badge" id="badge-decisiones">{sum(decisiones.get('resumen_acciones', {}).values())}</span>
    </button>
    <button class="nav-tab" data-mod="lanzador">
      🚀 Lanzador 1-Clic
      <span class="tab-badge" id="badge-lanzador">{len([p for p in lanzador.get('productos', []) if p.get('tiene_plan')])}</span>
    </button>
    <button class="nav-tab" data-mod="blueprints">
      🎨 Fábrica Creativa
      <span class="tab-badge" id="badge-blueprints">{len(blueprints)}</span>
    </button>
    <button class="nav-tab" data-mod="salud">
      🩺 Salud & Consola
      <span class="tab-badge">OK</span>
    </button>
  </nav>

  <!-- VISTA PRINCIPAL (SPA) -->
  <main class="viewport">

    <!-- MÓDULO 1: DECISIONES & FATIGA -->
    <section id="mod-decisiones" class="module-view active">
      <div id="aviso-rezago"></div>
      <div class="stats-grid" id="stats-decisiones"></div>

      <div class="filter-bar">
        <input type="text" id="filtro-dec-text" class="search-input" placeholder="🔍 Filtrar por ángulo o producto..." oninput="filtrarDecisiones()">
        <button class="filter-btn active" data-fdec="TODOS" onclick="setFiltroDec('TODOS', this)">Todas las decisiones</button>
        <button class="filter-btn" data-fdec="ESCALAR" onclick="setFiltroDec('ESCALAR', this)">🟢 Escalar</button>
        <button class="filter-btn" data-fdec="PAUSAR" onclick="setFiltroDec('PAUSAR', this)">🔴 Pausar</button>
        <button class="filter-btn" data-fdec="RENOVAR" onclick="setFiltroDec('RENOVAR', this)">🔵 Renovar (Fatiga)</button>
        <button class="filter-btn" data-fdec="SEGUIR_MIDIENDO" onclick="setFiltroDec('SEGUIR_MIDIENDO', this)">🟡 Seguir midiendo</button>
      </div>

      <div id="contenedor-decisiones"></div>
    </section>

    <!-- MÓDULO 2: LANZADOR 1-CLIC -->
    <section id="mod-lanzador" class="module-view">
      <div id="lanzador-portafolio"></div>
      <div id="lanzador-consola" style="display:none;"></div>
    </section>

    <!-- MÓDULO 3: FÁBRICA CREATIVA -->
    <section id="mod-blueprints" class="module-view">
      <div class="alert-box alert-info">
        <b>Banco Canónico Validado del Mercado GT (111 piezas, 22 familias):</b> Estructuras comprobadas extraídas de 597 anuncios de 89 fanpages competidoras en Guatemala. 100% nativo y ultra-rápido, sin iframes pesados.
      </div>
      <div class="filter-bar">
        <input type="text" id="filtro-bp-text" class="search-input" placeholder="🔍 Buscar por nombre, dispositivo, problema..." oninput="filtrarBlueprints()">
        <button class="filter-btn active" data-femb="TODOS" onclick="setFiltroEmbudo('TODOS', this)">Todos (22)</button>
        <button class="filter-btn" data-femb="TOFU" onclick="setFiltroEmbudo('TOFU', this)">TOFU (Conciencia/Dolor)</button>
        <button class="filter-btn" data-femb="MOFU" onclick="setFiltroEmbudo('MOFU', this)">MOFU (Solución/Prueba)</button>
        <button class="filter-btn" data-femb="BOFU" onclick="setFiltroEmbudo('BOFU', this)">BOFU (Oferta/Conversión)</button>
      </div>
      <div class="bp-grid" id="contenedor-blueprints"></div>
    </section>

    <!-- MÓDULO 4: SALUD & CONSOLA -->
    <section id="mod-salud" class="module-view">
      <div id="contenedor-salud"></div>
    </section>

  </main>

  <!-- TOAST NOTIFICATION -->
  <div id="toast" class="toast">Texto copiado</div>

  <!-- DATA EMBEDDED -->
  <script type="application/json" id="datos-estado">{_incrustar(estado)}</script>
  <script type="application/json" id="datos-lanzador">{_incrustar(lanzador)}</script>
  <script type="application/json" id="datos-decisiones">{_incrustar(decisiones)}</script>
  <script type="application/json" id="datos-blueprints">{_incrustar(blueprints)}</script>

  <!-- LOGICA CLIENTE DE LA SPA -->
  <script>
    const D_ESTADO = JSON.parse(document.getElementById('datos-estado').textContent);
    const D_LANZADOR = JSON.parse(document.getElementById('datos-lanzador').textContent);
    const D_DECISIONES = JSON.parse(document.getElementById('datos-decisiones').textContent);
    const D_BLUEPRINTS = JSON.parse(document.getElementById('datos-blueprints').textContent);

    const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c =>
      ({{ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }}[c]));
    const q = n => (n == null ? '—' : n);

    // Toast
    let toastTimer;
    function toast(txt) {{
      const el = document.getElementById('toast');
      el.textContent = txt;
      el.classList.add('show');
      clearTimeout(toastTimer);
      toastTimer = setTimeout(() => el.classList.remove('show'), 1600);
    }}

    // Clipboard
    function copiar(txt, btn) {{
      navigator.clipboard.writeText(txt).then(() => {{
        toast('Copiado al portapapeles');
        if (btn) {{
          btn.classList.add('done');
          const prev = btn.textContent;
          btn.textContent = '✓ Copiado';
          setTimeout(() => {{
            btn.classList.remove('done');
            btn.textContent = prev;
          }}, 1600);
        }}
      }}).catch(() => toast('Error al copiar'));
    }}

    function copiarComandoDiario() {{
      copiar('python Ads/_TOOLS/ciclo_hoy.py');
    }}

    // Theme Switcher
    function toggleTheme() {{
      const html = document.documentElement;
      const cur = html.getAttribute('data-theme') || 'dark';
      const sig = cur === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', sig);
      try {{ localStorage.setItem('app/theme', sig); }} catch(e){{}}
    }}
    (function(){{
      try {{
        const guardado = localStorage.getItem('app/theme');
        if (guardado) document.documentElement.setAttribute('data-theme', guardado);
      }} catch(e){{}}
    }})();

    // Navegación de pestañas principales
    let moduloActivo = 'decisiones';
    document.querySelectorAll('.nav-tab').forEach(t => {{
      t.addEventListener('click', () => {{
        document.querySelectorAll('.nav-tab').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.module-view').forEach(v => v.classList.remove('active'));
        t.classList.add('active');
        const mod = t.dataset.mod;
        moduloActivo = mod;
        document.getElementById('mod-' + mod).classList.add('active');
        try {{ localStorage.setItem('app/modulo', mod); }} catch(e){{}}
      }});
    }});

    // =========================================================================
    // MÓDULO 1: DECISIONES OPERATIVAS & FATIGA
    // =========================================================================
    let filtroDecTipo = 'TODOS';

    function setFiltroDec(tipo, btn) {{
      filtroDecTipo = tipo;
      document.querySelectorAll('[data-fdec]').forEach(b => b.classList.remove('active'));
      if (btn) btn.classList.add('active');
      pintarDecisiones();
    }}

    function pintarDecisiones() {{
      const res = D_DECISIONES.resumen_acciones || {{}};

      // La ventana se cuenta desde el ultimo dia CON DATA. Si hay rezago, decirlo arriba de todo:
      // una orden fechada hoy sobre data de hace dias es el error que produjo la pausa del 06-sep.
      const rez = D_DECISIONES.rezago_dias;
      const hasta = D_DECISIONES.datos_hasta || '';
      const av = document.getElementById('aviso-rezago');
      if (av) {{
        if (rez !== null && rez !== undefined && rez > 2) {{
          av.innerHTML = `<div style="margin:0 0 14px;padding:11px 14px;border-radius:8px;
            background:var(--crit-bg);color:var(--crit);font-size:13px;font-weight:600;">
            ⚠️ La data llega hasta ${{hasta}} — ${{rez}} días de rezago.
            Estas órdenes no describen lo que pasó después de esa fecha: cargá el export antes de ejecutarlas.
            </div>`;
        }} else if (hasta) {{
          av.innerHTML = `<div style="margin:0 0 14px;font-size:12px;color:var(--ink-3);
            font-family:var(--font-mono);">data hasta ${{hasta}} · al día</div>`;
        }}
      }}
      const pEscalar = res['ESCALAR'] || 0;
      const pPausar = res['PAUSAR'] || 0;
      const pRenovar = res['RENOVAR'] || 0;
      const pTesteo = res['SEGUIR_MIDIENDO'] || 0;

      // Stats
      document.getElementById('stats-decisiones').innerHTML = `
        <div class="stat-card" onclick="setFiltroDec('ESCALAR')">
          <div class="stat-icon" style="background:var(--good-bg);color:var(--good);">🟢</div>
          <div>
            <div class="stat-val">${{pEscalar}}</div>
            <div class="stat-label">Escalar (+20% / +10%)</div>
          </div>
        </div>
        <div class="stat-card" onclick="setFiltroDec('RENOVAR')">
          <div class="stat-icon" style="background:var(--fatiga-bg);color:var(--fatiga);">🔵</div>
          <div>
            <div class="stat-val">${{pRenovar}}</div>
            <div class="stat-label">Renovar (Fatiga)</div>
          </div>
        </div>
        <div class="stat-card" onclick="setFiltroDec('PAUSAR')">
          <div class="stat-icon" style="background:var(--crit-bg);color:var(--crit);">🔴</div>
          <div>
            <div class="stat-val">${{pPausar}}</div>
            <div class="stat-label">Pausar (Tolerancia)</div>
          </div>
        </div>
        <div class="stat-card" onclick="setFiltroDec('SEGUIR_MIDIENDO')">
          <div class="stat-icon" style="background:var(--warn-bg);color:var(--warn);">🟡</div>
          <div>
            <div class="stat-val">${{pTesteo}}</div>
            <div class="stat-label">Seguir midiendo</div>
          </div>
        </div>
      `;

      // Tabla por producto
      const busq = (document.getElementById('filtro-dec-text').value || '').toLowerCase().trim();
      let h = '';

      (D_DECISIONES.productos || []).forEach(prod => {{
        let celdas = prod.celdas || [];
        if (filtroDecTipo !== 'TODOS') {{
          celdas = celdas.filter(c => c.estado === filtroDecTipo);
        }}
        if (busq) {{
          celdas = celdas.filter(c =>
            c.celda.toLowerCase().includes(busq) ||
            prod.nombre.toLowerCase().includes(busq) ||
            prod.producto_key.toLowerCase().includes(busq)
          );
        }}
        if (!celdas.length) return;

        let filas = '';
        celdas.forEach(c => {{
          let bCls = 'b-neutro';
          if (c.estado === 'ESCALAR') bCls = 'b-escalar';
          else if (c.estado === 'PAUSAR') bCls = 'b-pausar';
          else if (c.estado === 'RENOVAR') bCls = 'b-renovar';
          else if (c.estado === 'SEGUIR_MIDIENDO') bCls = 'b-testeo';

          const cpaStr = c.cpa_real_q ? 'Q' + c.cpa_real_q.toFixed(1) : '—';
          let cpaColor = 'var(--ink)';
          if (c.cpa_real_q) {{
            if (c.cpa_real_q <= prod.cpa_objetivo_q) cpaColor = 'var(--good)';
            else if (c.cpa_real_q <= prod.break_even_q) cpaColor = 'var(--warn)';
            else cpaColor = 'var(--crit)';
          }}

          filas += `
            <tr>
              <td><span class="badge ${{bCls}}">${{esc(c.estado)}}</span></td>
              <td>
                <b>${{esc(c.celda)}}</b>
                ${{!c.banda_ok ? '<br><span style="font-size:11px;color:var(--warn);">⚠️ Banda fuera de avatar</span>' : ''}}
              </td>
              <td class="num">${{c.ventas || 0}}</td>
              <td class="num">${{c.mensajes || 0}}</td>
              <td class="num">Q${{c.spend_q != null ? c.spend_q.toFixed(1) : '0.0'}}</td>
              <td class="num" style="font-weight:700;color:${{cpaColor}};">${{cpaStr}}</td>
              <td class="num">${{c.pct_pd != null ? c.pct_pd.toFixed(0) + '%' : '—'}}</td>
              <td>
                <div style="font-size:12.5px;color:var(--ink);">${{esc(c.accion_sugerida || '')}}</div>
                ${{c.fatiga_detectada ? '<div style="font-size:11.5px;color:var(--fatiga);margin-top:2px;">🔔 Alerta temprana: Ganador histórico perdiendo tracción en los últimos 3 días.</div>' : ''}}
              </td>
              <td style="text-align:right;">
                <button class="btn-copy" onclick="copiar('Meta Ads [${{prod.producto_key}}] ${{esc(c.celda)}}: ${{esc(c.accion_sugerida)}}', this)">Copiar orden</button>
              </td>
            </tr>
          `;
        }});

        h += `
          <div class="card">
            <div class="card-header">
              <h3>
                <span>${{esc(prod.nombre)}} (${{esc(prod.producto_key)}})</span>
                <span class="badge b-neutro">${{esc(prod.estado_producto || 'VIVO')}}</span>
              </h3>
              <div style="font-size:12px;font-family:var(--font-mono);color:var(--ink-2);display:flex;gap:14px;">
                <span>Break-Even: <b>Q${{prod.break_even_q ? prod.break_even_q.toFixed(2) : '—'}}</b></span>
                <span>Objetivo: <b>Q${{prod.cpa_objetivo_q ? prod.cpa_objetivo_q.toFixed(2) : '—'}}</b></span>
              </div>
            </div>
            <div style="overflow-x:auto;">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Estado</th>
                    <th>Celda / Ángulo</th>
                    <th class="num">Ventas</th>
                    <th class="num">Chats</th>
                    <th class="num">Gasto</th>
                    <th class="num">CPA Real</th>
                    <th class="num">% PD</th>
                    <th>Instrucción Operativa</th>
                    <th style="text-align:right;">Acción</th>
                  </tr>
                </thead>
                <tbody>${{filas}}</tbody>
              </table>
            </div>
          </div>
        `;
      }});

      if (!h) {{
        h = '<div class="alert-box alert-info">No se encontraron celdas con el filtro actual.</div>';
      }}
      document.getElementById('contenedor-decisiones').innerHTML = h;
    }}

    function filtrarDecisiones() {{
      pintarDecisiones();
    }}

    // =========================================================================
    // MÓDULO 2: LANZADOR 1-CLIC (PORTAFOLIO + 7 PASOS)
    // =========================================================================
    let pkActivo = null;
    let pasoActivo = 0;
    let memoriaChecks = {{}};
    try {{ memoriaChecks = JSON.parse(localStorage.getItem('lanzador/v1') || '{{}}'); }} catch(e){{}}

    function checkGuardado(id) {{ return !!memoriaChecks[id]; }}
    function toggleCheck(id, v) {{
      if (v) memoriaChecks[id] = 1; else delete memoriaChecks[id];
      try {{ localStorage.setItem('lanzador/v1', JSON.stringify(memoriaChecks)); }} catch(e){{}}
      pintarConsolaLanzador();
    }}

    function pintarLanzador() {{
      if (pkActivo) {{
        document.getElementById('lanzador-portafolio').style.display = 'none';
        document.getElementById('lanzador-consola').style.display = 'block';
        pintarConsolaLanzador();
      }} else {{
        document.getElementById('lanzador-portafolio').style.display = 'block';
        document.getElementById('lanzador-consola').style.display = 'none';
        pintarPortafolioLanzador();
      }}
    }}

    function verProducto(pk) {{
      pkActivo = pk;
      pasoActivo = 0;
      pintarLanzador();
    }}

    function volverPortafolio() {{
      pkActivo = null;
      pintarLanzador();
    }}

    function pintarPortafolioLanzador() {{
      const prods = D_LANZADOR.productos || [];
      const vivos = prods.filter(p => p.estado === 'VIVO').length;
      const listos = prods.filter(p => p.tiene_plan && !p.plan.bloqueantes.length).length;
      const bloq = prods.filter(p => p.tiene_plan && p.plan.bloqueantes.length).length;
      const sinPlan = prods.filter(p => !p.tiene_plan).length;

      let filas = '';
      prods.forEach(p => {{
        let chip = 'b-neutro', est = 'Sin plan';
        if (p.tiene_plan) {{
          if (p.plan.bloqueantes.length) {{
            chip = 'b-pausar'; est = p.plan.bloqueantes.length + ' bloqueante(s)';
          }} else {{
            chip = 'b-escalar'; est = 'Listo para lanzar';
          }}
        }}

        const beStr = p.cpa_be_q ? 'Q' + p.cpa_be_q.toFixed(2) : '—';
        const cpaStr = p.cpa_acumulado_q ? 'Q' + p.cpa_acumulado_q.toFixed(2) : '—';
        const ventas = p.historial ? p.historial.ventas : '—';

        filas += `
          <tr style="cursor:pointer;" onclick="verProducto('${{p.producto_key}}')">
            <td>
              <b>${{esc(p.nombre)}}</b><br>
              <span style="font-family:var(--font-mono);font-size:11px;color:var(--ink-3);">${{esc(p.producto_key)}}</span>
            </td>
            <td><span class="badge b-neutro">${{esc(p.estado || '—')}}</span></td>
            <td class="num">${{beStr}}</td>
            <td class="num">${{cpaStr}}</td>
            <td class="num">${{ventas}}</td>
            <td><span class="badge ${{chip}}">${{est}}</span></td>
            <td style="text-align:right;">
              <button class="btn-quick" onclick="event.stopPropagation();verProducto('${{p.producto_key}}')">Abrir Lanzador →</button>
            </td>
          </tr>
        `;
      }});

      document.getElementById('lanzador-portafolio').innerHTML = `
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon" style="background:var(--accent-soft);color:var(--accent);">📦</div>
            <div><div class="stat-val">${{vivos}}</div><div class="stat-label">Productos Vivos</div></div>
          </div>
          <div class="stat-card">
            <div class="stat-icon" style="background:var(--good-bg);color:var(--good);">🚀</div>
            <div><div class="stat-val">${{listos}}</div><div class="stat-label">Listos para Lanzar</div></div>
          </div>
          <div class="stat-card">
            <div class="stat-icon" style="background:var(--crit-bg);color:var(--crit);">⛔</div>
            <div><div class="stat-val">${{bloq}}</div><div class="stat-label">Bloqueados por Datos</div></div>
          </div>
          <div class="stat-card">
            <div class="stat-icon" style="background:var(--surface-2);color:var(--ink-3);">📄</div>
            <div><div class="stat-val">${{sinPlan}}</div><div class="stat-label">Sin Plan (_PLAN.json)</div></div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h3>Portafolio de Lanzamiento y Fases</h3>
            <span style="font-size:12px;color:var(--ink-3);">Click en una fila para entrar a la consola de lanzamiento</span>
          </div>
          <div style="overflow-x:auto;">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>Estado</th>
                  <th class="num">Break-Even</th>
                  <th class="num">CPA Histórico</th>
                  <th class="num">Ventas</th>
                  <th>Estado de Plan</th>
                  <th style="text-align:right;">Consola</th>
                </tr>
              </thead>
              <tbody>${{filas}}</tbody>
            </table>
          </div>
        </div>
      `;
    }}

    function pintarConsolaLanzador() {{
      const p = (D_LANZADOR.productos || []).find(x => x.producto_key === pkActivo);
      if (!p) return volverPortafolio();

      if (!p.tiene_plan) {{
        document.getElementById('lanzador-consola').innerHTML = `
          <button class="btn-quick" style="margin-bottom:18px;" onclick="volverPortafolio()">← Volver al Portafolio</button>
          <div class="card">
            <div class="card-header"><h3>${{esc(p.nombre)}} (${{esc(p.producto_key)}})</h3></div>
            <div class="card-body">
              <div class="alert-box alert-warn">
                <b>Este producto no tiene _PLAN.json configurado.</b> Para habilitar la consola de 7 pasos, etapa-6 debe sincronizar su plan de lanzamiento.
              </div>
              <h4>Datos Históricos Observados:</h4>
              <p>Gasto: $${{p.historial ? p.historial.spend_usd.toFixed(2) : '0'}} | Ventas: ${{p.historial ? p.historial.ventas : 0}}</p>
            </div>
          </div>
        `;
        return;
      }}

      const L = p.plan;
      const pasosNombres = ['1. Gate & Finanzas', '2. Creativos', '3. Campaña', '4. Conjuntos', '5. Copies', '6. Publicar', '7. Decisiones Post'];

      let stepper = '<div class="stepper-nav">';
      pasosNombres.forEach((nom, i) => {{
        stepper += `<button class="step-btn ${{pasoActivo === i ? 'active' : ''}}" onclick="pasoActivo=${{i}};pintarConsolaLanzador();">${{nom}}</button>`;
      }});
      stepper += '</div>';

      let contenidoPaso = '';
      if (pasoActivo === 0) {{
        // GATE
        const bloq = L.bloqueantes || [];
        contenidoPaso = `
          <div class="card">
            <div class="card-header"><h3>Validación Previa (Gate) y Economía</h3></div>
            <div class="card-body">
              ${{bloq.length ?
                `<div class="alert-box alert-crit"><b>⛔ Hay ${{bloq.length}} bloqueante(s) activos:</b><br>${{bloq.map(b => '· ' + esc(b.que) + ' (responsable: ' + esc(b.quien) + ')').join('<br>')}}</div>` :
                `<div class="alert-box alert-good"><b>✅ GATE SUPERADO:</b> Cuenta, página y Break-Even configurados. El producto está listo para lanzamiento.</div>`
              }}
              <div class="stats-grid">
                <div class="stat-card"><div class="stat-val">Q${{L.economia.cpa_be_q ? L.economia.cpa_be_q.toFixed(2) : '—'}}</div><div class="stat-label">CPA Break-Even</div></div>
                <div class="stat-card"><div class="stat-val">Q${{L.economia.cpa_base_q ? L.economia.cpa_base_q.toFixed(2) : '—'}}</div><div class="stat-label">CPA Objetivo</div></div>
                <div class="stat-card"><div class="stat-val">$${{L.presupuesto.por_conjunto_usd.toFixed(2)}}</div><div class="stat-label">Presupuesto/Conjunto/Día</div></div>
                <div class="stat-card"><div class="stat-val">${{L.presupuesto.dias_a_pd}} días</div><div class="stat-label">Margen a Decisión (PD)</div></div>
              </div>
              <p style="color:var(--ink-2);font-size:13px;line-height:1.6;"><b>Regla de Oro de CALENDARIO_ESCALADO §1.5:</b> Presupuesto derivado de 7 × Costo por Conversación observado. Durante los primeros ${{L.presupuesto.dias_a_pd}} días un conjunto con 0 ventas NO se pausa: aún está dentro de su margen de prueba.</p>
            </div>
          </div>
        `;
      }} else if (pasoActivo === 1) {{
        // CREATIVOS
        let tarjetas = '';
        (L.conjuntos || []).forEach(c => {{
          tarjetas += `
            <div class="card" style="margin-bottom:14px;">
              <div class="card-header">
                <b>Conjunto #${{c.n}}: ${{esc(c.angulo_titulo || c.angulo_key)}}</b>
                <span class="badge ${{c.lleva_precio ? 'b-testeo' : 'b-neutro'}}">${{c.lleva_precio ? 'Con Precio' : 'Sin Precio'}}</span>
              </div>
              <div class="card-body">
                <div class="field-row">
                  <div class="field-label">Archivo Media</div>
                  <div class="field-val">${{esc(c.archivo_creativo)}}</div>
                  <button class="btn-copy" onclick="copiar('${{esc(c.archivo_creativo)}}', this)">Copiar</button>
                </div>
                <div class="field-row">
                  <div class="field-label">Carpeta Destino</div>
                  <div class="field-val">Ads/MEDIA_${{esc(L.producto_key)}}/</div>
                  <button class="btn-copy" onclick="copiar('Ads/MEDIA_${{esc(L.producto_key)}}/', this)">Copiar</button>
                </div>
                ${{c.prompt_imagen ? `
                  <div class="field-row">
                    <div class="field-label">Prompt Generación</div>
                    <div class="field-val textarea">${{esc(c.prompt_imagen)}}</div>
                    <button class="btn-copy" onclick="copiar('${{esc(c.prompt_imagen)}}', this)">Copiar Prompt</button>
                  </div>
                ` : ''}}
              </div>
            </div>
          `;
        }});
        contenidoPaso = tarjetas;
      }} else if (pasoActivo === 2) {{
        // CAMPAÑA
        let camps = '';
        (L.campanas || []).forEach((c, idx) => {{
          camps += `
            <div class="card">
              <div class="card-header"><h3>Campaña #${{idx+1}}: ${{esc(c.rol)}}</h3></div>
              <div class="card-body">
                <div class="field-row">
                  <div class="field-label">Nombre Exacto</div>
                  <div class="field-val">${{esc(c.nombre)}}</div>
                  <button class="btn-copy" onclick="copiar('${{esc(c.nombre)}}', this)">Copiar</button>
                </div>
                <div class="field-row">
                  <div class="field-label">Objetivo</div>
                  <div class="field-val">${{esc(c.objetivo)}}</div>
                </div>
                <div class="field-row">
                  <div class="field-label">Presupuesto</div>
                  <div class="field-val">${{esc(c.presupuesto)}}</div>
                </div>
                <div class="field-row">
                  <div class="field-label">Programación</div>
                  <div class="field-val">${{esc(L.lanzamiento.legible)}} a las ${{esc(L.lanzamiento.hora)}}</div>
                  <button class="btn-copy" onclick="copiar('${{esc(L.lanzamiento.legible)}} ${{esc(L.lanzamiento.hora)}}', this)">Copiar</button>
                </div>
              </div>
            </div>
          `;
        }});
        contenidoPaso = camps;
      }} else if (pasoActivo === 3) {{
        // CONJUNTOS
        let conjs = '';
        (L.conjuntos || []).forEach(c => {{
          conjs += `
            <div class="card">
              <div class="card-header">
                <h3>Conjunto ${{c.n}}: ${{esc(c.angulo_titulo || c.angulo_key)}}</h3>
                <span class="badge b-neutro">$${{c.presupuesto_usd.toFixed(2)}} / día</span>
              </div>
              <div class="card-body">
                <div class="field-row">
                  <div class="field-label">Nombre Conjunto</div>
                  <div class="field-val">${{esc(c.nombre)}}</div>
                  <button class="btn-copy" onclick="copiar('${{esc(c.nombre)}}', this)">Copiar</button>
                </div>
                <div class="field-row">
                  <div class="field-label">Banda Edad</div>
                  <div class="field-val">${{esc(c.banda_edad)}} (Advantage+ Audience OFF · Sin Intereses)</div>
                  <button class="btn-copy" onclick="copiar('${{esc(c.banda_edad)}}', this)">Copiar</button>
                </div>
                ${{(c.anuncios || []).map(a => `
                  <div class="field-row">
                    <div class="field-label">Anuncio ${{a.letra}}</div>
                    <div class="field-val">${{esc(a.nombre)}}</div>
                    <button class="btn-copy" onclick="copiar('${{esc(a.nombre)}}', this)">Copiar</button>
                  </div>
                `).join('')}}
              </div>
            </div>
          `;
        }});
        contenidoPaso = conjs;
      }} else if (pasoActivo === 4) {{
        // COPIES
        let cps = '';
        (L.conjuntos || []).forEach(c => {{
          const cp = c.copy || {{}};
          cps += `
            <div class="card">
              <div class="card-header"><h3>Copies Conjunto ${{c.n}}: ${{esc(c.angulo_titulo || c.angulo_key)}}</h3></div>
              <div class="card-body">
                ${{(cp.textos || []).map((t, idx) => `
                  <div class="field-row">
                    <div class="field-label">Opción Texto ${{idx+1}}</div>
                    <div class="field-val textarea">${{esc(t)}}</div>
                    <button class="btn-copy" onclick="copiar('${{esc(t)}}', this)">Copiar</button>
                  </div>
                `).join('')}}
                ${{cp.titulos ? `
                  <div class="field-row">
                    <div class="field-label">Títulos</div>
                    <div class="field-val">${{esc(cp.titulos.join('  |  '))}}</div>
                    <button class="btn-copy" onclick="copiar('${{esc(cp.titulos.join('  |  '))}}', this)">Copiar</button>
                  </div>
                ` : ''}}
                ${{cp.descripcion ? `
                  <div class="field-row">
                    <div class="field-label">Descripción</div>
                    <div class="field-val">${{esc(cp.descripcion)}}</div>
                    <button class="btn-copy" onclick="copiar('${{esc(cp.descripcion)}}', this)">Copiar</button>
                  </div>
                ` : ''}}
              </div>
            </div>
          `;
        }});
        contenidoPaso = cps;
      }} else if (pasoActivo === 5) {{
        // CHECKLIST PUBLICAR
        const checks = [
          ['Objetivo = Tráfico WhatsApp', 'Meta por defecto intenta Interacción o Clics. Debe ser Tráfico dirigido al WhatsApp.'],
          ['"Maximizar conversaciones" verificado', 'Meta lo revierte a maximizar clics con cada duplicado. Es el error más costoso.'],
          ['Presupuesto a nivel CONJUNTO (ABO)', 'Desmarcar compartir presupuesto para evitar que un conjunto malo se coma la inversión.'],
          ['Advantage+ Audience DESACTIVADO (OFF)', 'Sin esto Meta ignora la edad objetivo y diluye el impacto en menores.'],
          ['Ningún anuncio ni conjunto con sufijo "- Copia"', 'El sufijo "- Copia" corrompe el tracking y hace la pieza anónima.'],
          ['Programado para las 4:00 AM de mañana', 'Nunca lanzar el mismo día: Meta consume el presupuesto diario en pocas horas nocturnas.']
        ];
        let items = '';
        checks.forEach((chk, i) => {{
          const chkId = 'chk/' + pkActivo + '/' + i;
          const done = checkGuardado(chkId);
          items += `
            <li class="chk-item ${{done ? 'checked' : ''}}" onclick="toggleCheck('${{chkId}}', ${{!done}})">
              <input type="checkbox" ${{done ? 'checked' : ''}} onclick="event.stopPropagation();toggleCheck('${{chkId}}', this.checked)">
              <label>
                <b>${{esc(chk[0])}}</b>
                <span class="chk-why">${{esc(chk[1])}}</span>
              </label>
            </li>
          `;
        }});
        contenidoPaso = `
          <div class="card">
            <div class="card-header"><h3>Checklist Anti-Pérdidas de Publicación</h3></div>
            <div class="card-body">
              <ul class="chk-list">${{items}}</ul>
            </div>
          </div>
        `;
      }} else if (pasoActivo === 6) {{
        // CALENDARIO DESPUÉS
        let cal = '';
        (L.calendario || []).forEach(d => {{
          cal += `
            <tr>
              <td><b>${{esc(d.dia)}}</b></td>
              <td style="font-family:var(--font-mono);">${{esc(d.fecha)}}</td>
              <td><b>${{esc(d.que)}}</b><br><span style="color:var(--ink-2);font-size:12px;">${{esc(d.hace)}}</span></td>
              <td style="font-size:12px;color:var(--accent);">${{esc(d.manda || '—')}}</td>
            </tr>
          `;
        }});
        contenidoPaso = `
          <div class="card">
            <div class="card-header"><h3>Calendario de Decisión Operativa</h3></div>
            <div style="overflow-x:auto;">
              <table class="data-table">
                <thead><tr><th>Cuándo</th><th>Fecha</th><th>Protocolo</th><th>Datos Requeridos</th></tr></thead>
                <tbody>${{cal}}</tbody>
              </table>
            </div>
          </div>
        `;
      }}

      document.getElementById('lanzador-consola').innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;">
          <button class="btn-quick" onclick="volverPortafolio()">← Volver al Portafolio</button>
          <div style="display:flex;gap:10px;">
            <button class="btn-quick" onclick="copiar('python Ads/_TOOLS/gen_fase2_lean.py ${{pkActivo}}')">⚡ Generar Fase 2 Lean (5 Blueprints)</button>
          </div>
        </div>
        <div class="card">
          <div class="card-header">
            <h3>${{esc(p.nombre)}} (${{esc(p.producto_key)}}) · ${{esc(L.fase_nombre)}}</h3>
            <span class="badge b-escalar">${{esc(L.fase_notacion)}}</span>
          </div>
        </div>
        ${{stepper}}
        ${{contenidoPaso}}
      `;
    }}

    // =========================================================================
    // MÓDULO 3: FÁBRICA CREATIVA (22 BLUEPRINTS CANÓNICOS)
    // =========================================================================
    let filtroEmbudo = 'TODOS';

    function setFiltroEmbudo(emb, btn) {{
      filtroEmbudo = emb;
      document.querySelectorAll('[data-femb]').forEach(b => b.classList.remove('active'));
      if (btn) btn.classList.add('active');
      pintarBlueprints();
    }}

    function pintarBlueprints() {{
      const busq = (document.getElementById('filtro-bp-text').value || '').toLowerCase().trim();
      let bps = D_BLUEPRINTS || [];

      if (filtroEmbudo !== 'TODOS') {{
        bps = bps.filter(b => b.embudo === filtroEmbudo);
      }}
      if (busq) {{
        bps = bps.filter(b =>
          b.codigo.toLowerCase().includes(busq) ||
          b.nombre.toLowerCase().includes(busq) ||
          b.dispositivo.toLowerCase().includes(busq)
        );
      }}

      let h = '';
      bps.forEach(b => {{
        let embBadge = 'b-neutro';
        if (b.embudo === 'TOFU') embBadge = 'b-pausar';
        else if (b.embudo === 'MOFU') embBadge = 'b-testeo';
        else if (b.embudo === 'BOFU') embBadge = 'b-escalar';

        const varsChips = (b.variables || []).slice(0, 6).map(v =>
          `<span class="bp-var-chip">${{esc(v)}}</span>`
        ).join('');

        const reglasList = (b.reglas || []).slice(0, 3).map(r =>
          `<div class="bp-rule-item"><span class="bp-rule-dot">·</span><span>${{esc(r)}}</span></div>`
        ).join('');

        h += `
          <div class="bp-card">
            <div class="bp-header">
              <div>
                <span class="bp-code">${{esc(b.codigo)}}</span>
                <div class="bp-name">${{esc(b.nombre)}}</div>
              </div>
              <span class="badge ${{embBadge}}">${{esc(b.embudo)}}</span>
            </div>

            <div class="bp-device">${{esc(b.dispositivo)}}</div>

            <div style="font-size:12px;color:var(--ink);font-weight:600;">
              Cuándo elegirlo: <span style="font-weight:400;color:var(--ink-2);">${{esc(b.cuando_elegirlo || 'Validado en GT.')}}</span>
            </div>

            ${{reglasList ? `
              <div class="bp-rules">
                <b style="font-size:11.5px;color:var(--ink);">Reglas duras de diseño:</b>
                ${{reglasList}}
              </div>
            ` : ''}}

            <div class="bp-vars">
              ${{varsChips}}
              ${{(b.variables || []).length > 6 ? `<span class="bp-var-chip">+${{b.variables.length - 6}} más</span>` : ''}}
            </div>

            <div style="display:flex;justify-content:space-between;align-items:center;margin-top:auto;padding-top:10px;border-top:1px solid var(--line-soft);">
              <span style="font-size:11px;font-family:var(--font-mono);color:var(--ink-3);">
                ${{b.n_miembros}} anuncios GT · Score: ${{b.score_ref || '—'}}
              </span>
              <div style="display:flex;gap:6px;">
                <button class="btn-copy" onclick="copiar('${{esc(b.codigo)}}: ${{esc(b.nombre)}} | Dispositivo: ${{esc(b.dispositivo)}}', this)">Copiar Blueprint</button>
                <a class="btn-copy" style="text-decoration:none;" href="../Ads/_SWIPE/_GALERIA.html" target="_blank" title="Abrir galería visual pesada en otra pestaña">Galería ↗</a>
              </div>
            </div>
          </div>
        `;
      }});

      if (!h) {{
        h = '<div class="alert-box alert-info" style="grid-column:1/-1;">No se encontraron blueprints con ese término de búsqueda.</div>';
      }}
      document.getElementById('contenedor-blueprints').innerHTML = h;
    }}

    function filtrarBlueprints() {{
      pintarBlueprints();
    }}

    // =========================================================================
    // MÓDULO 4: SALUD & CONSOLA DEL SISTEMA
    // =========================================================================
    function pintarSalud() {{
      const S = D_ESTADO.salud || {{}};
      const vistas = D_ESTADO.vistas || [];

      let filas = '';
      vistas.forEach(v => {{
        const est = v.estado || {{}};
        filas += `
          <tr>
            <td><b>${{esc(v.rotulo)}}</b><br><span style="font-size:11.5px;color:var(--ink-3);">${{esc(v.sub || '')}}</span></td>
            <td><span class="badge b-neutro">${{esc(v.tipo)}}</span></td>
            <td style="font-family:var(--font-mono);font-size:11.5px;">${{esc(v.fuente || 'En memoria SPA')}}</td>
            <td><span class="badge ${{est.clase === 'ok' ? 'b-escalar' : (est.clase === 'tibia' ? 'b-testeo' : 'b-neutro')}}">${{esc(est.detalle || 'Al día')}}</span></td>
            <td><button class="btn-copy" onclick="copiar('${{esc(v.genera || '')}}', this)">Copiar comando</button></td>
          </tr>
        `;
      }});

      document.getElementById('contenedor-salud').innerHTML = `
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon" style="background:var(--good-bg);color:var(--good);">✓</div>
            <div><div class="stat-val">${{S.al_dia || vistas.length}}</div><div class="stat-label">Vistas al Día</div></div>
          </div>
          <div class="stat-card">
            <div class="stat-icon" style="background:var(--warn-bg);color:var(--warn);">⏳</div>
            <div><div class="stat-val">${{S.envejecidas || 0}}</div><div class="stat-label">Envejecidas</div></div>
          </div>
          <div class="stat-card">
            <div class="stat-icon" style="background:var(--crit-bg);color:var(--crit);">✕</div>
            <div><div class="stat-val">${{S.faltantes || 0}}</div><div class="stat-label">Fuentes Faltantes</div></div>
          </div>
          <div class="stat-card">
            <div class="stat-icon" style="background:var(--accent-soft);color:var(--accent);">⚙️</div>
            <div><div class="stat-val">${{(S.pendientes || []).length}}</div><div class="stat-label">Pendientes Portafolio</div></div>
          </div>
        </div>

        <div class="card">
          <div class="card-header"><h3>Comandos Rápidos de Terminal (1 Clic)</h3></div>
          <div class="card-body" style="display:flex;flex-direction:column;gap:10px;">
            <div class="field-row">
              <div class="field-label">Ciclo Diario</div>
              <div class="field-val">python Ads/_TOOLS/ciclo_hoy.py</div>
              <button class="btn-copy" onclick="copiar('python Ads/_TOOLS/ciclo_hoy.py', this)">Copiar</button>
            </div>
            <div class="field-row">
              <div class="field-label">Motor Decisiones</div>
              <div class="field-val">python Ads/_TOOLS/decidir.py</div>
              <button class="btn-copy" onclick="copiar('python Ads/_TOOLS/decidir.py', this)">Copiar</button>
            </div>
            <div class="field-row">
              <div class="field-label">Actualizar Lanzador</div>
              <div class="field-val">python Ads/_TOOLS/gen_lanzador.py</div>
              <button class="btn-copy" onclick="copiar('python Ads/_TOOLS/gen_lanzador.py', this)">Copiar</button>
            </div>
            <div class="field-row">
              <div class="field-label">Fase 2 Lean (TINNIDROP)</div>
              <div class="field-val">python Ads/_TOOLS/gen_fase2_lean.py TINNIDROP</div>
              <button class="btn-copy" onclick="copiar('python Ads/_TOOLS/gen_fase2_lean.py TINNIDROP', this)">Copiar</button>
            </div>
            <div class="field-row">
              <div class="field-label">Ingesta Automática</div>
              <div class="field-val">python Ads/_TOOLS/ingestar_unificado.py</div>
              <button class="btn-copy" onclick="copiar('python Ads/_TOOLS/ingestar_unificado.py', this)">Copiar</button>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header"><h3>Registro de Vistas y Componentes</h3></div>
          <div style="overflow-x:auto;">
            <table class="data-table">
              <thead><tr><th>Vista</th><th>Tipo</th><th>Fuente</th><th>Estado</th><th>Acción</th></tr></thead>
              <tbody>${{filas}}</tbody>
            </table>
          </div>
        </div>
      `;
    }}

    // =========================================================================
    // INICIALIZACIÓN
    // =========================================================================
    pintarDecisiones();
    pintarLanzador();
    pintarBlueprints();
    pintarSalud();

    // Recordar pestaña anterior si existe
    try {{
      const modPrev = localStorage.getItem('app/modulo');
      if (modPrev && document.getElementById('mod-' + modPrev)) {{
        const btn = document.querySelector(`[data-mod="${{modPrev}}"]`);
        if (btn) btn.click();
      }}
    }} catch(e){{}}
  </script>
</body>
</html>
"""


def ALIAS(estado):
    """PANEL.html redirige a la SPA principal APP.html."""
    app = estado.get("app", {})
    destino = app.get("salida", "APP.html").rsplit("/", 1)[-1]
    titulo = app.get("titulo", "VitalCom Guatemala")
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>{titulo} · Redirección</title>
  <meta http-equiv="refresh" content="0;url={destino}">
  <style>
    body {{
      background: #0b0f19;
      color: #94a3b8;
      font-family: system-ui, sans-serif;
      display: grid;
      place-items: center;
      height: 100vh;
      margin: 0;
    }}
    a {{
      color: #3b82f6;
      text-decoration: none;
      font-weight: 600;
    }}
  </style>
</head>
<body>
  <div style="text-align:center;">
    Redirigiendo a la aplicación unificada VitalCom...<br><br>
    <a href="{destino}">Abrir {destino}</a>
  </div>
</body>
</html>
"""
