<#
.SYNOPSIS
    Registra (o quita) la tarea de Task Scheduler que dispara el ciclo diario determinístico
    (Ads/_TOOLS/ciclo_diario.py) para el usuario actual.

.DESCRIPTION
    P3 T6 (25-sep-2026). Compatible con PowerShell 5.1 (terminal real del operador — sin operadores
    de PS7). NO se corre sola: el operador decide cuándo registrar la tarea. El script NO instala
    nada más, no toca Postgres ni PRODUCTOS/: solo declara la tarea programada.

    Triggers: diaria a las 05:00 Y al iniciar sesión (por si la máquina estaba apagada a las 05:00).
    StartWhenAvailable hace que Task Scheduler la corra apenas la máquina esté disponible si se
    perdió el horario. La acción llama a ciclo_diario.py con --si-falta-hoy, así que un disparo
    doble (05:00 + logon en la misma mañana) no hace nada la segunda vez.

.PARAMETER Quitar
    Si se pasa, desregistra la tarea en vez de crearla.

.EXAMPLE
    powershell -File Ads\_TOOLS\registrar_ciclo_diario.ps1
    powershell -File Ads\_TOOLS\registrar_ciclo_diario.ps1 -Quitar
#>
param(
    [switch]$Quitar
)

$ErrorActionPreference = "Stop"

$NombreTarea = "VITALCOM ciclo diario"
$RaizRepo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$ScriptCiclo = Join-Path $RaizRepo "Ads\_TOOLS\ciclo_diario.py"

if ($Quitar) {
    $existente = Get-ScheduledTask -TaskName $NombreTarea -ErrorAction SilentlyContinue
    if ($null -eq $existente) {
        Write-Host "No hay ninguna tarea '$NombreTarea' registrada: nada que quitar."
        exit 0
    }
    Unregister-ScheduledTask -TaskName $NombreTarea -Confirm:$false
    Write-Host "Tarea '$NombreTarea' eliminada de Task Scheduler."
    exit 0
}

if (-not (Test-Path $ScriptCiclo)) {
    throw "No encuentro $ScriptCiclo -- revisa que este script siga en Ads/_TOOLS/ del repo real."
}

$PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PythonExe) {
    throw "No encuentro 'python' en el PATH de este usuario. Instalalo o corre esto desde una " +
          "terminal donde 'python --version' funcione, y volve a intentar."
}

$Accion = New-ScheduledTaskAction -Execute $PythonExe `
    -Argument ('"{0}" --si-falta-hoy' -f $ScriptCiclo) `
    -WorkingDirectory $RaizRepo

$TriggerDiario = New-ScheduledTaskTrigger -Daily -At "05:00"
$TriggerLogon = New-ScheduledTaskTrigger -AtLogOn

$Configuracion = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -DontStopOnIdleEnd

$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive

Register-ScheduledTask -TaskName $NombreTarea `
    -Action $Accion `
    -Trigger @($TriggerDiario, $TriggerLogon) `
    -Settings $Configuracion `
    -Principal $Principal `
    -Description "Corre Ads/_TOOLS/ciclo_diario.py --si-falta-hoy (P3 T6): bajar LucidSales/Meta, decidir, regenerar. Determinístico, sin LLM." `
    -Force | Out-Null

Write-Host "Tarea '$NombreTarea' registrada: diaria 05:00 + al iniciar sesión, con --si-falta-hoy."
Write-Host "Accion: `"$PythonExe`" `"$ScriptCiclo`" --si-falta-hoy"
Write-Host "Directorio de trabajo: $RaizRepo"
