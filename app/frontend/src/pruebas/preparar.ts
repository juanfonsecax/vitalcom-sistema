import "@testing-library/jest-dom/vitest";

// jsdom no implementa matchMedia. Lo usan el hook use-mobile.ts de shadcn/ui (para el
// Sidebar) y el alternador de tema (componentes/tema.ts) — sin este polyfill, cualquier
// prueba que monte la barra lateral revienta con "window.matchMedia is not a function".
if (typeof window !== "undefined" && !window.matchMedia) {
  window.matchMedia = (query: string) =>
    ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }) as MediaQueryList;
}
