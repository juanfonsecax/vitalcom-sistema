import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { Guia } from "../pantallas/Guia";

test("la pantalla Guia se renderiza con sus tres secciones clave", () => {
  render(<Guia />);
  expect(screen.getByText("Guía de Uso del Sistema")).toBeInTheDocument();
  expect(screen.getByText("¿Qué hace cada pantalla y botón?")).toBeInTheDocument();
  expect(screen.getByText("¿Qué significa cada estado?")).toBeInTheDocument();
  expect(screen.getByText("¿Qué hacer si algo falla o se detiene?")).toBeInTheDocument();
});

test("la guía explica las pantallas y estados doctrinales", () => {
  render(<Guia />);
  expect(screen.getByText("Portafolio (Inicio)")).toBeInTheDocument();
  expect(screen.getByText("Órdenes de hoy")).toBeInTheDocument();
  expect(screen.getByText("Nuevo producto")).toBeInTheDocument();
  expect(screen.getByText("LISTO")).toBeInTheDocument();
  expect(screen.getByText("BLOQUEADO")).toBeInTheDocument();
  expect(screen.getByText("SEGUIR MIDIENDO")).toBeInTheDocument();
  expect(screen.getByText("ESCALAR (+20%)")).toBeInTheDocument();
});
