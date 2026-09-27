@echo off
setlocal enabledelayedexpansion
rem ===========================================================================
rem  iniciar.bat — un doble clic levanta la app y abre el navegador.
rem  El operador no escribe comandos (hoja de ruta, seccion 1).
rem
rem  La app corre SOBRE ESTA CARPETA: la raiz donde esta este archivo es la
rem  carpeta del sistema (DOCTRINA/, PRODUCTOS/, Ads/). Eso evita el error del
rem  worktree del 17-sep-2026, donde faltaban las Ads\MEDIA_* y el estado salia
rem  falso. Para apuntar a otra carpeta: set VITALCOM_BASE antes de correr esto.
rem
rem  BASE AMBIGUA (T8, 23-sep-2026): la carpeta que contiene este .bat puede
rem  ser un WORKTREE vinculado (ej. SISTEMA-app, donde se desarrolla) en vez
rem  de la carpeta PRINCIPAL (SISTEMA, la dueña de los datos: PRODUCTOS/,
rem  Ads/MEDIA_*, los CSV). Un worktree vinculado nunca se actualiza con los
rem  datos reales, asi que la app leeria CSV viejos sin avisar. Si %~dp0 es un
rem  worktree vinculado, este script SE NIEGA a arrancar en vez de adivinar.
rem ===========================================================================

set "RAIZ=%~dp0"

if "%VITALCOM_BASE%"=="" (
  set "GITDIR="
  set "GITCOMUN="
  for /f "usebackq delims=" %%G in (`git -C "%RAIZ%" rev-parse --path-format=absolute --git-dir 2^>nul`) do set "GITDIR=%%G"
  for /f "usebackq delims=" %%G in (`git -C "%RAIZ%" rev-parse --path-format=absolute --git-common-dir 2^>nul`) do set "GITCOMUN=%%G"
  if not "!GITDIR!"=="" if not "!GITDIR!"=="!GITCOMUN!" (
    set "PRINCIPAL="
    for /f "usebackq tokens=1,* delims= " %%A in (`git -C "%RAIZ%" worktree list --porcelain 2^>nul ^| findstr /b "worktree "`) do (
      if "!PRINCIPAL!"=="" set "PRINCIPAL=%%B"
    )
    echo [X] Esta carpeta es un WORKTREE VINCULADO de git, no la carpeta del sistema.
    echo     Un worktree vinculado nunca se actualiza con los datos reales
    echo     ^(PRODUCTOS\, Ads\MEDIA_*^): la app leeria CSV viejos sin avisarlo.
    if not "!PRINCIPAL!"=="" (
      echo     Corre iniciar.bat desde la carpeta del sistema:
      echo         !PRINCIPAL!
    ) else (
      echo     Corre iniciar.bat desde la carpeta PRINCIPAL del repositorio ^(SISTEMA^).
    )
    echo     Para forzar otra carpeta a proposito: set VITALCOM_BASE antes de correr esto.
    pause
    exit /b 1
  )
  set "VITALCOM_BASE=%RAIZ%"
)

if not exist "%VITALCOM_BASE%\DOCTRINA\FLUJO.json" (
  echo [X] No encuentro DOCTRINA\FLUJO.json en "%VITALCOM_BASE%".
  echo     Esta carpeta tiene que ser la del sistema.
  pause
  exit /b 1
)

if not exist "%VITALCOM_BASE%\PRODUCTOS\_DIM_PRODUCTOS.csv" (
  echo [X] No encuentro PRODUCTOS\_DIM_PRODUCTOS.csv en "%VITALCOM_BASE%".
  echo     Esta carpeta tiene que ser la del sistema, con sus datos reales.
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

rem La pantalla se recompila si no existe o si algun archivo del codigo es mas
rem nuevo que la version compilada (si no, un cambio de codigo nunca se ve).
set "COMPILAR="
if not exist "%RAIZ%app\frontend\dist\index.html" set "COMPILAR=1"
if not defined COMPILAR (
  powershell -NoProfile -Command "$d=(Get-Item -LiteralPath '%RAIZ%app\frontend\dist\index.html').LastWriteTime; $n=Get-ChildItem -LiteralPath '%RAIZ%app\frontend\src','%RAIZ%app\frontend\index.html','%RAIZ%app\frontend\package.json' -Recurse -File | Where-Object { $_.LastWriteTime -gt $d } | Select-Object -First 1; if ($n) { exit 1 } else { exit 0 }"
  if errorlevel 1 set "COMPILAR=1"
)

if defined COMPILAR (
  echo [2/3] Compilando la pantalla ^(el codigo cambio desde la ultima vez^)...
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
  echo [2/3] La pantalla compilada esta al dia.
)

echo [3/3] Levantando http://localhost:8000 ...
start "" http://localhost:8000
pushd "%RAIZ%app\backend"
call uv run uvicorn vitalcom_app.main:app --host 127.0.0.1 --port 8000
popd
endlocal
