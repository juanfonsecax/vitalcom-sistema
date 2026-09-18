@echo off
setlocal
rem ===========================================================================
rem  iniciar.bat — un doble clic levanta la app y abre el navegador.
rem  El operador no escribe comandos (hoja de ruta, seccion 1).
rem
rem  La app corre SOBRE ESTA CARPETA: la raiz donde esta este archivo es la
rem  carpeta del sistema (DOCTRINA/, PRODUCTOS/, Ads/). Eso evita el error del
rem  worktree del 17-sep-2026, donde faltaban las Ads\MEDIA_* y el estado salia
rem  falso. Para apuntar a otra carpeta: set VITALCOM_BASE antes de correr esto.
rem ===========================================================================

if "%VITALCOM_BASE%"=="" set "VITALCOM_BASE=%~dp0"
set "RAIZ=%~dp0"

if not exist "%VITALCOM_BASE%\DOCTRINA\FLUJO.json" (
  echo [X] No encuentro DOCTRINA\FLUJO.json en "%VITALCOM_BASE%".
  echo     Esta carpeta tiene que ser la del sistema.
  pause
  exit /b 1
)

where uv >nul 2>nul || (
  echo [X] Falta uv. Instalalo con:  python -m pip install --user uv
  pause
  exit /b 1
)

echo [1/3] Preparando el backend...
pushd "%RAIZ%app\backend"
call uv sync --quiet || (echo [X] uv sync fallo & popd & pause & exit /b 1)
popd

if not exist "%RAIZ%app\frontend\dist\index.html" (
  echo [2/3] Compilando la pantalla ^(solo la primera vez^)...
  where pnpm >nul 2>nul || (
    echo [X] Falta pnpm. Instalalo con:  npm install -g pnpm
    pause
    exit /b 1
  )
  pushd "%RAIZ%app\frontend"
  call pnpm install --silent || (echo [X] pnpm install fallo & popd & pause & exit /b 1)
  call pnpm build || (echo [X] pnpm build fallo & popd & pause & exit /b 1)
  popd
) else (
  echo [2/3] La pantalla ya esta compilada.
)

echo [3/3] Levantando http://localhost:8000 ...
start "" http://localhost:8000
pushd "%RAIZ%app\backend"
call uv run uvicorn vitalcom_app.main:app --host 127.0.0.1 --port 8000
popd
endlocal
