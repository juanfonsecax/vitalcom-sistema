/**
 * tema.ts — claro / oscuro / según el sistema.
 *
 * La preferencia se guarda en localStorage (conveniencia del navegador, nunca dato del
 * negocio) y se aplica como la clase `dark` en <html>, que es lo que leen los tokens de
 * estilos.css. Cualquier lectura/escritura de localStorage va en try/catch: una ventana
 * privada o el storage bloqueado no debe romper la pantalla.
 */
import { useCallback, useEffect, useState } from "react";

export type Tema = "light" | "dark" | "system";

const CLAVE_STORAGE = "vitalcom.tema";

function leerTemaGuardado(): Tema {
  try {
    const guardado = window.localStorage.getItem(CLAVE_STORAGE);
    if (guardado === "light" || guardado === "dark" || guardado === "system") return guardado;
  } catch {
    // Storage no disponible: seguimos con el default.
  }
  return "system";
}

function prefiereSistemaOscuro(): boolean {
  try {
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  } catch {
    return false;
  }
}

function aplicarTema(tema: Tema) {
  const oscuro = tema === "dark" || (tema === "system" && prefiereSistemaOscuro());
  document.documentElement.classList.toggle("dark", oscuro);
}

export function useTema() {
  const [tema, setTemaEstado] = useState<Tema>(() => leerTemaGuardado());

  useEffect(() => {
    aplicarTema(tema);
  }, [tema]);

  useEffect(() => {
    if (tema !== "system") return;
    let media: MediaQueryList;
    try {
      media = window.matchMedia("(prefers-color-scheme: dark)");
    } catch {
      return;
    }
    const escuchar = () => aplicarTema("system");
    media.addEventListener("change", escuchar);
    return () => media.removeEventListener("change", escuchar);
  }, [tema]);

  const setTema = useCallback((siguiente: Tema) => {
    setTemaEstado(siguiente);
    try {
      window.localStorage.setItem(CLAVE_STORAGE, siguiente);
    } catch {
      // Sin persistencia: el tema vale para esta sesión de pantalla.
    }
  }, []);

  return { tema, setTema };
}
