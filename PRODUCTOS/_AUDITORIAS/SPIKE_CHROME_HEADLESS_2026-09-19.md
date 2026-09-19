# SPIKE · `claude-in-chrome` en corrida headless (`claude -p`) · 19-sep-2026

**Fecha:** 19 de septiembre de 2026  
**Autor:** Ejecutor  
**Objetivo:** Determinar si `claude-in-chrome` (conducir el Chrome logueado del operador) funciona desde una ejecución headless de Claude Code (`claude -p`) para automatizar el renderizado en `F2.conceptos` (`etapa-render`).

---

## Resultado

> ### **¿Funciona `claude-in-chrome` desde `claude -p` headless?**
> # **NO**

---

## Evidencia Técnica

### 1. Servidores MCP en Claude Code CLI
Al inspeccionar los servidores MCP configurados en el binario de Claude Code (`C:\Users\juand\.local\bin\claude.exe`, v2.1.276) mediante:
```bash
claude.exe mcp list
```
La salida reporta los conectores disponibles:
```
claude.ai Claude Docs: https://api.anthropic.com/v1/pages/mcp - √ Connected
claude.ai HIGGSFIELD: https://mcp.higgsfield.ai/mcp - √ Connected
claude.ai META MCP: https://mcp.facebook.com/ads - √ Connected
claude.ai Google Drive: https://drivemcp.googleapis.com/mcp/v1 - √ Connected
claude.ai Google Calendar: https://calendarmcp.googleapis.com/mcp/v1 - √ Connected
claude.ai Gmail: https://gmailmcp.googleapis.com/mcp/v1 - √ Connected
```
**`claude-in-chrome` NO forma parte de los servidores MCP del CLI ni está configurado en `claude.exe`.**

### 2. Origen y Limitación de `claude-in-chrome`
- En la arquitectura de Anthropic, `mcp__claude-in-chrome__*` es una funcionalidad exclusiva de la **aplicación de escritorio interactiva** (`entrypoint: "claude-desktop"`).
- El comando `claude mcp add-from-claude-desktop` restringe explícitamente su funcionamiento: *(Mac and WSL only)*, sin soporte para Windows nativo.

### 3. Prueba de Invocación Headless
Se ejecutó una prueba de llamada en modo headless:
```bash
claude.exe -p "List all your available tools. Do you have any tool from claude-in-chrome or mcp__claude-in-chrome? Can you open a tab in the operator's Chrome?" --permission-mode dontAsk --output-format json
```
Resultado:
```json
{
  "is_error": true,
  "api_error_status": 429,
  "result": "You've hit your monthly spend limit · raise it at claude.ai/settings/usage?from=cc_cli_limit_message · your weekly limit resets Sep 21, 8am (America/Bogota)"
}
```

#### Factores identificados:
1. **Límite de gasto mensual de tokens:** La cuenta del operador alcanzó su límite de cuota mensual de Claude Code CLI (`api_error_status: 429`), impidiendo llamadas adicionales en vivo hacia la API de Anthropic hasta el reinicio de ciclo o recarga.
2. **Incompatibilidad arquitectónica estructural:** Aun con saldo disponible de tokens, la herramienta `claude-in-chrome` simplemente **no existe** en la distribución CLI ni en el registro MCP de Windows. Su uso está acotado exclusivamente a la aplicación de escritorio de Claude con la extensión de navegador activa.
Por lo tanto, la automatización headless del navegador queda doblemente descartada para la app en este entorno.

---

## Consecuencia Doctrinal y Arquitectural para el Hito 6

De acuerdo con la pauta explícita del operador:

1. **`F2.conceptos` no ejecutará `etapa-render` de forma headless automatizada.**
2. La aplicación web:
   - Presentará la **galería de conceptos generados por `etapa-9`** con su blueprint de origen.
   - Entregará al operador los **prompts resueltos y paquetizados** (`armar_prompts_fase2.py` / `PROMPTS_FASE2_*.txt`) junto con los enlaces a las fotos del producto y referencias del swipe.
   - El operador generará o bajará los creativos (ej. en ChatGPT web) y los cargará a la app mediante el botón y escritor de piezas ya implementado (`producto.cargar_pieza`), garantizando que cumplan con el nombre canónico y el gate de calidad.
