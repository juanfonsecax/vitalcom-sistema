# PROPUESTA: Habilitar «Publicar FASE 1 en Meta» (`nodo.F1.publicar`)

**Fecha:** 18 de septiembre de 2026  
**Destinatario:** Operador del Sistema VitalCom  
**Emisor:** Ejecutor (con diseño validado en Hito 4)  
**Estado:** PENDIENTE DE APROBACIÓN EXPLÍCITA DEL OPERADOR  

---

## 1. ¿Qué cambia en el sistema?

Se cambia una sola línea en el manifiesto (`VISTAS/_MANIFIESTO.json`):
```json
"id": "nodo.F1.publicar",
"habilitada": true
```
**Nada más.** Ningún otro botón, script ni comportamiento se altera.

---

## 2. ¿Qué hace la aplicación al pulsar «Publicar FASE 1»?

El proceso de publicación sigue un flujo estricto paso a paso, diseñado para darte control total:

1. **Lee Meta en vivo (solo lectura):** Consulta las cuentas (`ads_get_ad_accounts`), las campañas existentes (`ads_get_ad_entities`), las páginas (`ads_get_user_pages`) y las imágenes (`ads_get_ad_images`). No crea ni modifica nada en esta fase.
2. **Arma el paquete técnico:** Corre `gen_publicacion.py` para estructurar la campaña, los 6 conjuntos y los anuncios según el plan del producto.
3. **Pide subir las imágenes a mano:** Te indica qué imágenes subir a la biblioteca de anuncios de la cuenta en el Administrador de Meta (o mediante la carpeta compartida). Esto evita fallas de subida de archivos pesados vía API.
4. **Presenta la orden completa en pantalla:** Muestra en detalle la campaña, presupuesto, segmentación, copies y creativos exactamente como se enviarán a Meta.
5. **Espera tu aprobación:** **SOLO** si tú pulsas el botón **«Aprobar»**, la aplicación procede a crear la campaña, conjuntos, creativos y anuncios en Meta. **TODO se crea en estado PAUSADO (`PAUSED`)**.
6. **Verifica contra Meta:** Relee Meta para confirmar que todo se creó correctamente y anota los identificadores (`ad_id`) correspondientes.
7. **Registra el evento:** Deja constancia formal en `PRODUCTOS/_EVENTOS.csv` y en la bitácora de la corrida.

---

## 3. ¿Qué NO hace?

- **NO activa anuncios:** No enciende ninguna campaña ni conjunto. El paso de encender los anuncios a las 4:00 AM corresponde al nodo `F1.activar`, el cual **sigue deshabilitado** (`habilitada: false`).
- **NO gasta presupuesto ni dinero:** Al quedar todo en pausa (`PAUSED`), Meta no consume ni un solo centavo de presupuesto.

---

## 4. Riesgos y cuidados a tener en cuenta

- **Conexión MCP de la cuenta:** La cuenta publicitaria asignada debe tener habilitado el acceso por MCP en `PRODUCTOS/_DIM_CUENTAS.csv` (por ejemplo `GTR 7`).
- **Página con WhatsApp:** La FanPage asignada al producto debe tener un número de WhatsApp Business válidamente conectado en la cuenta publicitaria.
- **Caducidad de la orden:** Por seguridad, las órdenes de publicación generadas tienen un tiempo de validez. Si no se aprueban dentro de la ventana de tiempo, caducan para evitar publicar información desactualizada.
- **Regla de oro:** Revisar siempre la pantalla de la orden antes de pulsar «Aprobar». Si algo no coincide con lo esperado, se cancela la orden sin consecuencias.

---

## 5. ¿Cómo se prueba la primera vez?

La primera prueba se realizará con **un producto real que tú elijas**, siguiendo estos pasos:
1. Asegurar que el producto tenga su paquete de FASE 1 armado (ángulos, copies, plan y piezas cargadas).
2. Hacer clic en «Publicar FASE 1».
3. Revisar la orden detallada generada en pantalla.
4. Si todo está correcto y das tu conformidad, pulsar «Aprobar».
5. Constatar directamente en el Administrador de Anuncios de Meta que la campaña y los 6 conjuntos se crearon en **PAUSA**.

---

### Decisión requerida del operador

> ⚠️ **Por Regla Dura 1:** NADA se ejecuta ni se habilita en Meta sin tu confirmación explícita.
> 
> **¿Habilito `F1.publicar` en el sistema?**  
> *(Respondé «sí» para habilitarlo en `VISTAS/_MANIFIESTO.json` o «no» para mantenerlo deshabilitado).*
