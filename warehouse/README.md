# warehouse — la capa analítica del sistema

## Qué es y qué NO es

**No reemplaza a los CSV.** `PRODUCTOS/*.csv` sigue siendo la fuente de verdad y todos los
generadores siguen leyéndolos igual que antes. Esto se monta encima y sólo lee.

Lo que agrega es lo que los CSV solos no pueden dar:

| | |
|---|---|
| **Tests que corren solos** | 29 tests de integridad en cada build: llaves únicas, no nulos, relaciones entre tablas, valores permitidos. El primer build encontró finales de línea mezclados en `_FACT_ENTREGA.csv` (405 CRLF + 233 LF) que Python toleraba y llevaban meses ahí. |
| **Un conjunto = un objeto** | `stg_alias` canoniza el nombre antes de cualquier join, así que renombrar en Meta no parte la serie histórica. |
| **Una métrica, una definición** | El CPA y el cierre se calculan en un solo lugar. No se pueden recalcular distinto en dos scripts. |
| **Linaje explícito** | `dbt docs generate` muestra qué depende de qué. |

## Correrlo

```bash
cd warehouse && DBT_PROFILES_DIR=. python -m dbt.cli.main build
```

`gen_decisiones.py` ya lo corre solo antes de cada lectura, y `gen_app.py --todo` corre a
`gen_decisiones.py`. En la práctica no hace falta invocarlo a mano.

## Estructura

```
staging/   los CSV tipados y canonizados. Materializados como TABLA, no vista:
           una vista guardaría el read_csv() con ruta relativa y sólo funcionaría
           corriendo desde warehouse/.
marts/     dim_conjunto      un renglón por conjunto real, con su ángulo derivado del NOMBRE
           fct_conjunto_dia  el hecho diario: gasto, mensajes y ventas juntos
           fct_anuncio_dia   el grano del CONCEPTO, con los 5 ejes de la firma
```

## Por qué el ángulo sale del nombre y no de una tabla

El `ad_id` de Meta llegó corrupto en 2 006 de 2 475 filas de `_FACT_VENTAS.csv` (notación
científica: los últimos dígitos se perdieron y no vuelven). El JOIN por id es irrecuperable. El
**nombre** llega intacto en cualquier export, para siempre. Por eso la parametrización viaja en el
nombre y por eso `dim_conjunto` lo parsea con regex en vez de mantener una tabla paralela.
