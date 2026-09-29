/**
 * glosario.ts — las palabras del sistema, explicadas en una línea.
 *
 * Es el pedido 5 del operador: "que sea más claro que hoy; hay data técnica que no se
 * entiende". Las definiciones viven acá, en un solo archivo, tomadas de CLAUDE.md
 * (§DEFINICIONES CLAVE e invariantes) y de la doctrina que cada término tiene por dueño.
 * Cada término que aparece en pantalla lleva su (i) y lee de acá.
 */

export type Termino = {
  /** Cómo se escribe en pantalla. */
  rotulo: string;
  /** Una línea, en palabras de todos los días. */
  que_es: string;
  /** Quién manda sobre ese dato en el sistema. */
  dueno?: string;
};

export const GLOSARIO = {
  angulo: {
    rotulo: "ángulo",
    que_es:
      "Por qué le duele a la persona: la causa concreta que el producto resuelve. Es territorio del problema, no del formato del anuncio.",
    dueno: "CLAUDE.md · DEFINICIONES CLAVE",
  },
  concepto: {
    rotulo: "concepto",
    que_es: "Cómo se muestra el anuncio. Va aparte del ángulo: mismo dolor, mil maneras de contarlo.",
    dueno: "Ads/_SWIPE/_CATALOGO_CONCEPTOS.md",
  },
  cpa: {
    rotulo: "CPA",
    que_es: "Cuánto cuesta conseguir una venta. Se mide en la moneda del mercado, por venta, nunca con ROAS.",
    dueno: "decidir.py · _PARAMETROS_DECISION.csv",
  },
  break_even: {
    rotulo: "break-even",
    que_es:
      "El techo: lo máximo que podés pagar por una venta sin perder plata. Si el CPA lo pasa, cada venta cuesta más de lo que deja.",
    dueno: "costear.py · _DIM_COSTEO.csv",
  },
  ic: {
    rotulo: "intervalo de confianza",
    que_es:
      "El rango donde está el costo real por venta mientras hay pocas ventas. Si ese rango todavía cruza el break-even, no alcanza para decidir.",
    dueno: "decidir.py (IC 95 %)",
  },
  seguir_midiendo: {
    rotulo: "SEGUIR MIDIENDO",
    que_es:
      "No subir ni bajar el presupuesto todavía: faltan ventas para saber. Cuando el motor puede calcularlo, dice cuántas ventas faltan.",
    dueno: "decidir.py",
  },
  escalar: {
    rotulo: "ESCALAR",
    que_es: "Poner más plata: la evidencia alcanza y el costo por venta está por debajo del techo.",
    dueno: "decidir.py",
  },
  pausar: {
    rotulo: "PAUSAR",
    que_es: "Apagar: gastó de más sin vender lo suficiente y la evidencia ya alcanza para cortar.",
    dueno: "decidir.py",
  },
  renovar: {
    rotulo: "RENOVAR",
    que_es:
      "El ángulo vende, pero el anuncio se cansó. Se cambia el creativo, no se apaga el ángulo.",
    dueno: "decidir.py",
  },
  fase_1: {
    rotulo: "FASE 1",
    que_es:
      "Se prueban 6 ángulos distintos con un mismo concepto, un conjunto por ángulo. Mide qué dolor vende.",
    dueno: "CALENDARIO_ESCALADO.md §1.7",
  },
  fase_2: {
    rotulo: "FASE 2",
    que_es:
      "Con el ángulo ganador fijo, se prueban 10 conceptos para ver cuál lo vende más barato.",
    dueno: "fase-2-conceptos",
  },
  fase_3: {
    rotulo: "FASE 3",
    que_es:
      "El ángulo y el concepto ya están validados, mismo presupuesto: la variable es el flujo LucidBot. Se reescribe hacia el ganador (CAMBIO_BOT) y se mide el cierre, hasta que llegue al piso del 10 %.",
    dueno: "fase-3-flujo",
  },
  fase_4: {
    rotulo: "FASE 4",
    que_es:
      "Ya no se mide: se compra volumen del ángulo, el concepto y el flujo ya validados, con una campaña 1-1-7.",
    dueno: "fase-4-escalado",
  },
  cambio_bot: {
    rotulo: "CAMBIO_BOT",
    que_es:
      "El evento que marca que el flujo LucidBot ya se reescribió hacia el ángulo y concepto ganadores. Sin fecha posterior al concepto ganador, no cuenta para el gate de FASE 4.",
    dueno: "Ads/_TOOLS/registrar_evento.py · PLANTILLAS_FLUJO_BOT.md",
  },
  cierre_post_cambio_bot: {
    rotulo: "cierre post-CAMBIO_BOT",
    que_es:
      "Mensajes → ventas contados DESPUÉS del último CAMBIO_BOT. Gate duro: bajo 10 % no se escala (PROHIBIDO_ESCALAR_CIERRE_BAJO). El 15-20 % es solo un benchmark de referencia.",
    dueno: "Ads/_TOOLS/flujo.py · GUIA_MADRE_PARAMETRIZADA.md",
  },
  uno_uno_cinco: {
    rotulo: "1-1-5",
    que_es: "Una campaña, un conjunto, cinco anuncios. Se usa en FASE 2 y siempre con ABO.",
    dueno: "Calet 16-ago · CLAUDE.md",
  },
  abo_cbo: {
    rotulo: "ABO / CBO",
    que_es:
      "ABO: el presupuesto lo fijás vos en cada conjunto. CBO: lo reparte Meta. Se testea en ABO; se escala en CBO.",
    dueno: "CLAUDE.md · ÁNGULO vs CONCEPTO",
  },
  ganador_por_venta: {
    rotulo: "ganador por venta",
    que_es:
      "Un ángulo gana cuando VENDE, no cuando genera conversaciones. Las conversaciones sirven para cortar, nunca para coronar.",
    dueno: "invariante 1",
  },
  rezago: {
    rotulo: "rezago de la data",
    que_es:
      "Cuántos días hace que no llega data nueva de ventas. Una orden de hoy sobre data vieja decide a ciegas.",
    dueno: "decidir.py · recopilar-lucidsales",
  },
  nodo: {
    rotulo: "paso del flujo",
    que_es:
      "El punto exacto del recorrido donde está el producto. Sale del grafo declarado, no de la memoria de nadie.",
    dueno: "DOCTRINA/FLUJO.json · flujo.py",
  },
  bloqueante: {
    rotulo: "bloqueante",
    que_es: "Un dato que falta y frena el paso. Siempre viene con el nombre de quien lo produce.",
    dueno: "flujo.py",
  },
  banda_edad: {
    rotulo: "banda de edad",
    que_es:
      "El rango de edad configurado en Meta. Sale del avatar del ángulo, con Advantage+ apagado.",
    dueno: "ETAPA-6.md · _DIM_BANDAS.csv",
  },
  cohorte_preliminar: {
    rotulo: "cohorte preliminar",
    que_es:
      "Este es negocio CONTRA ENTREGA: las devoluciones tardan ~8 días en confirmarse. Un período de menos de 10 días todavía puede bajar cuando esas devoluciones lleguen — no declarar ganador ni apagar nada con un número preliminar.",
    dueno: "DOCTRINA/CONTABILIDAD.md · gen_pl.py (dias_cohorte_maduro)",
  },
  margen_logistico: {
    rotulo: "margen logístico",
    que_es:
      "Lo que el panel de Dropi llama «Ganancias»: venta menos producto menos flete. Todavía no descuenta devoluciones, personal ni pauta — no es tu ganancia.",
    dueno: "DOCTRINA/CONTABILIDAD.md §3",
  },
  margen_contribucion: {
    rotulo: "margen de contribución",
    que_es: "El margen logístico ya menos devoluciones, personal y otros gastos. Todavía no descuenta la pauta.",
    dueno: "DOCTRINA/CONTABILIDAD.md §3",
  },
  resultado_neto: {
    rotulo: "resultado neto",
    que_es: "Lo último de la cadena: ya descontó producto, flete, devoluciones, personal, pauta y gastos fijos.",
    dueno: "DOCTRINA/CONTABILIDAD.md §3",
  },
  vista_cohorte: {
    rotulo: "vista cohorte",
    que_es: "Agrupa por la fecha en que se HIZO la orden: «¿rindió la pauta de esta ventana?». No es lo mismo que la caja.",
    dueno: "DOCTRINA/CONTABILIDAD.md §2 · VISTA A",
  },
  vista_caja: {
    rotulo: "vista caja",
    que_es: "Agrupa por la fecha en que el dinero SE MOVIÓ de verdad (cartera de Dropi). Responde «¿cuánto entró?», no «¿rindió la pauta?».",
    dueno: "DOCTRINA/CONTABILIDAD.md §2 · VISTA B",
  },
} as const satisfies Record<string, Termino>;

export type ClaveGlosario = keyof typeof GLOSARIO;
