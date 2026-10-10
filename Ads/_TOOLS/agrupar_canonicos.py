# -*- coding: utf-8 -*-
"""
agrupar_canonicos.py — agrupa las 111 fichas en BLUEPRINTS CANONICOS.

Un canonico = una FAMILIA ESTRUCTURAL. No es un concepto_key: `C2_BENEFICIOS`
agrupa 41 piezas estructuralmente incomparables, y esa es justo la razon por la
que existe esta capa (ver _HANDOFF_FICHAS.md seccion 7).

Lo unico escrito a mano aca es MAPA (que ficha pertenece a que familia) y la
prosa de cada familia. TODO lo demas se DERIVA de los JSON de las fichas, para
que un canonico no pueda contradecir a sus miembros.

Uso:
    python Ads/_TOOLS/agrupar_canonicos.py            # escribe CANONICOS/ + canonico_id
    python Ads/_TOOLS/agrupar_canonicos.py --dry-run  # solo valida y reporta
"""
import json
import os
import re
import sys
import collections

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Ads/
BP = os.path.join(RAIZ, "_SWIPE", "_BLUEPRINTS")
FICHAS = os.path.join(BP, "FICHAS")
CANON = os.path.join(BP, "CANONICOS")

SCHEMA = "canonico-1.0"

# ─────────────────────────────────────────────────────────────────────────────
# EL MAPA — unica parte escrita a mano.
# `dispositivo` = la estructura que se replica. `dispositivo_neutro` = esa misma
# estructura sin ningun dato del anuncio de referencia (zona del cuerpo, dolencia,
# producto): es lo que el prompt de FASE 2 lee. `ejes` = que cambia entre
# miembros sin dejar de ser la misma familia.
# ─────────────────────────────────────────────────────────────────────────────
FAMILIAS = [
    {
        "id": "CN01_ANTES_DESPUES",
        "nombre": "Antes / Despues partido",
        "dispositivo": (
            "DOS ESTADOS DEL MISMO SUJETO EN UNA SOLA PIEZA. La imagen se parte "
            "en dos mitades — vertical, horizontal o por el eje del producto — y "
            "cada mitad muestra el mismo cuerpo, rostro u organo en un estado "
            "distinto. El producto vive en la costura: es la bisagra que explica "
            "el salto. La prueba no se argumenta, se ve."
        ),
        "dispositivo_neutro": (
            "EL ANTES/DESPUES PARTIDO POR EL PRODUCTO. Dos fotos de la MISMA "
            "zona afectada, una al lado de la otra y rotuladas ANTES y DESPUES, "
            "con el producto plantado en el centro tapando la costura. El "
            "producto es lo que separa los dos estados: la causalidad se lee "
            "sin texto."
        ),
        "cuando_elegirlo": (
            "El resultado es VISIBLE en el cuerpo (piel, varices, hinchazon, "
            "cabello, peso). Si el beneficio es una sensacion interna que no se "
            "fotografia — dormir mejor, menos zumbido, mas memoria — esta familia "
            "obliga a inventar la imagen y la pieza se cae."
        ),
        "ejes": [
            "eje del corte: vertical / horizontal / apilado / rostro partido al medio",
            "material: fotografia real, macro, render anatomico o selfie casero",
            "que hace de bisagra: el producto, una flecha, la linea del gotero o nada",
            "el 'despues' puede ser el producto YA PUESTO en el cuerpo (F050)",
            "registro: crudo sin marco (F097) o enmarcado con etiqueta neutra (F099)",
        ],
        "miembros": ["F004", "F006", "F023", "F024", "F031", "F035", "F050",
                     "F058", "F068", "F072", "F097", "F098", "F099", "F103"],
    },
    {
        "id": "CN02_TIMELINE_PROGRESION",
        "nombre": "Timeline de progresion",
        "dispositivo": (
            "TRES O MAS ESTADOS EN FILA, CADA UNO CON SU ETIQUETA DE PLAZO. A "
            "diferencia del antes/despues, aca el eje del tiempo esta DIBUJADO: "
            "dia 1, semana 2, mes 3. La pieza no promete un salto, promete un "
            "recorrido — y al hacerlo instala la idea de que el producto se toma "
            "durante un periodo, no una vez."
        ),
        "dispositivo_neutro": (
            "EL TIMELINE DE 3 ESTADOS EN EL TOPE. Tres imagenes del mismo "
            "sujeto o de la misma zona afectada, separadas por flechas, con una "
            "etiqueta de plazo debajo de cada una (SEMANA 0 / 4 / 8) y una "
            "linea de descripcion. No promete un resultado: promete un "
            "CRONOGRAMA."
        ),
        "cuando_elegirlo": (
            "El producto es un TRATAMIENTO con curva de resultado y el argumento "
            "de venta es la duracion (por eso empuja el pack de 3). Tambien "
            "cuando el resultado es invisible: el timeline lo puede narrar en "
            "ilustracion o render sin necesitar una foto real."
        ),
        "ejes": [
            "material del estado: render de organo, ilustracion de linea, foto cotidiana",
            "que dice la etiqueta: plazo real (semana 1) o momento de uso (al despertar)",
            "escala del eje: pareja o desigual/logaritmica, que comprime el final",
            "posicion: banda superior sobre el titular, o cuerpo central de la pieza",
            "un frasco por periodo debajo = el pack se justifica solo (F061-63)",
        ],
        "miembros": ["F029", "F036", "F039", "F040", "F041", "F042", "F053",
                     "F061", "F062", "F063", "F100", "F101"],
    },
    {
        "id": "CN03_OFERTA_MULTIPLICADOR",
        "nombre": "Multiplicador de cantidad",
        "dispositivo": (
            "UN NUMERAL DE CANTIDAD DOMINA LA PIEZA. El digito (2X1, 3X2, el "
            "numero de unidades) se lee ANTES que el producto y antes que el "
            "titular: ocupa un cuarto del alto, va dentro de un escudo, cartucho, "
            "llama o card de oro, y el resto de la pieza se ordena alrededor. El "
            "argumento no es el beneficio: es cuanto te llevas."
        ),
        "dispositivo_neutro": (
            "EL NUMERAL DE CANTIDAD GIGANTE. Un digito grande ocupa cerca de un "
            "tercio del alto del frame y se lee antes que el producto, el "
            "precio o el titular. No dice 'oferta': dice CUANTO te llevas. El "
            "precio unitario derivado hace la division por el lector."
        ),
        "cuando_elegirlo": (
            "Publico que ya conoce el producto o la categoria (NC3+), BOFU y "
            "retargeting. Exige una oferta de volumen real: sin 2x1 ni pack, el "
            "numeral no tiene que decir."
        ),
        "ejes": [
            "contenedor del numeral: escudo, cartucho ovalado, llama, card dorada, banda",
            "que acompana: dos retratos del avatar (F044), tres tubos en abanico (F065)",
            "la variante 'segunda unidad a precio reducido' en banda de ancho completo",
            "si lleva bloques de cierre apilados (garantia + envio + CTA) o solo el numeral",
        ],
        "miembros": ["F001", "F010", "F033", "F044", "F057", "F065", "F066", "F075"],
    },
    {
        "id": "CN04_ESCALERA_PRECIOS",
        "nombre": "Escalera de tiers",
        "dispositivo": (
            "TRES NIVELES DE COMPRA EN CARDS PARALELAS, cada uno con su cantidad "
            "y su precio, ordenados para que la aritmetica hable sola: el salto "
            "del tier 1 al 2 cuesta menos que una unidad suelta. El tier heroe se "
            "marca con medalla, borde o subtitulo de intencion. No se argumenta "
            "cual conviene — se deja ver."
        ),
        "dispositivo_neutro": (
            "LA ESCALERA DE 3 PRECIOS EN COLUMNA, CADA UNO EN SU PROPIA CARD. "
            "Los tres niveles de compra se apilan verticalmente en un flanco "
            "del frame, cada uno en card con borde de color e icono de "
            "destaque. La escalera ES el anuncio y el resto (titular, producto, "
            "CTA) la rodea."
        ),
        "cuando_elegirlo": (
            "Hay 3 tiers reales con precio unitario decreciente y el publico ya "
            "decidio comprar (BOFU/NC4). Con 1 o 2 tiers la escalera se ve "
            "incompleta y pierde todo su mecanismo."
        ),
        "ejes": [
            "orientacion: columna al flanco (F019) o tabla horizontal (F038)",
            "marcador del heroe: medalla, numeracion, subtitulo de intencion",
            "si muestra % de descuento, precio unitario, o el AHORRO calculado aparte (F108)",
            "la garantia puede entrar como CUARTA columna de la escalera (F086)",
        ],
        "miembros": ["F019", "F038", "F083", "F086", "F108"],
    },
    {
        "id": "CN05_LISTA_BENEFICIOS",
        "nombre": "Lista de beneficios con icono",
        "dispositivo": (
            "N BENEFICIOS ENUMERADOS, cada uno con su icono o foto circular, "
            "alineados en columna al flanco o en fila bajo el titular. Es la "
            "estructura mas neutra del banco: no dramatiza, ordena. El producto "
            "queda en podio o al centro y la lista lo rodea."
        ),
        "dispositivo_neutro": (
            "LA COLUMNA DE BENEFICIOS CON TITULO MAS SUBTITULO. Cada fila es un "
            "icono en contenedor redondeado mas TITULO EN MAYUSCULAS mas "
            "subtitulo gris, con el producto en podio o al centro. El par sirve "
            "al lector que escanea (solo titulos) y al que profundiza (con "
            "subtitulos). El ultimo item es el sello regulatorio disfrazado de "
            "beneficio."
        ),
        "cuando_elegirlo": (
            "El producto tiene 3-6 beneficios distintos y ninguno domina a los "
            "otros. Es la estructura de FASE 1 (C2 variante ligera) justamente "
            "porque es la mas neutra: mide el ANGULO sin que el creativo se lleve "
            "el credito."
        ),
        "ejes": [
            "orientacion: columna vertical al flanco o fila horizontal bajo el titular",
            "cantidad: 3 (fila) / 5-6 (columna) — cambia la densidad, no la estructura",
            "marcador del item: icono plano, cuadrado redondeado, foto circular real",
            "fondo: plano de marca o textura biologica (F064)",
        ],
        "miembros": ["F002", "F007", "F046", "F064"],
    },
    {
        "id": "CN06_CHECKLIST_SINTOMAS",
        "nombre": "Checklist de sintomas / diagnostico",
        "dispositivo": (
            "UNA LISTA DE PROBLEMAS, NO DE BENEFICIOS. Cada item es un sintoma "
            "que la persona reconoce en si misma, con su mini-foto o icono de "
            "evidencia y su check. La pieza funciona como test de "
            "auto-diagnostico: el lector se cuenta a si mismo cuantos tiene. El "
            "producto aparece recien despues de la lista, como la salida."
        ),
        "dispositivo_neutro": (
            "LA COLUMNA DE PROBLEMAS CON EVIDENCIA FOTOGRAFICA MAS CHECK. No "
            "dice que elimina el problema: MUESTRA la foto de cada sintoma y la "
            "tacha con un check. La prueba es visual, no verbal. La figura de "
            "autoridad va DETRAS del producto: respalda, no compite."
        ),
        "cuando_elegirlo": (
            "Publico FRIO (TOFU/NC2) que tiene el problema pero no lo nombra "
            "todavia. Es la unica familia que engancha a alguien que no esta "
            "buscando nada: le pone nombre a lo que siente."
        ),
        "ejes": [
            "orientacion: columna vertical, fila horizontal o collage de cuadrantes (F030)",
            "evidencia del item: fotografia real del sintoma o icono ilustrado",
            "header: pregunta de identificacion ('¿Te pasa esto?') o diagnostico en cadena (F026)",
            "el cierre puede ser check verde por item o un solo check global",
        ],
        "miembros": ["F003", "F008", "F009", "F026", "F030"],
    },
    {
        "id": "CN07_DOLOR_A_PLENO",
        "nombre": "Foto de dolor a pleno",
        "dispositivo": (
            "LA FOTOGRAFIA DEL SINTOMA OCUPA MEDIA PIEZA O MAS, a sangre, del "
            "tamano de una persona. No hay lista ni argumento: hay un rostro o un "
            "cuerpo en el gesto exacto del dolor — la mano en el oido, la pierna "
            "que arde, la cara de la noche sin dormir. El texto es una sola frase "
            "que nombra ese momento."
        ),
        "dispositivo_neutro": (
            "LA FOTO DEL SINTOMA A SANGRE, DEL TAMANO DE UNA PERSONA. Un cuerpo "
            "real con la zona afectada encendida en rojo ocupa media pieza o "
            "mas y sangra por el borde. El titular es una PREGUNTA DE UNA "
            "PALABRA sobre franja de color, y el producto cruza el frame en "
            "diagonal."
        ),
        "cuando_elegirlo": (
            "TOFU puro, para detener el scroll con reconocimiento emocional. "
            "Necesita un sintoma con GESTO fotografiable; si el problema no tiene "
            "una postura reconocible, no hay foto que tomar."
        ),
        "ejes": [
            "encuadre: mitad de la pieza (F012-13) o sangrado completo (F005)",
            "el hook puede apuntar al SINTOMA o saltar a la CAUSA (F013)",
            "el producto puede estar ya PUESTO sobre el avatar en la misma toma (F049)",
            "puede fotografiar la emocion en el momento exacto con el objeto que la produce (F055)",
        ],
        "miembros": ["F005", "F012", "F013", "F049", "F055"],
    },
    {
        "id": "CN08_UGC_CRUDO",
        "nombre": "UGC crudo sin una palabra",
        "dispositivo": (
            "UNA SOLA FOTOGRAFIA QUE NO PARECE UN ANUNCIO, sin texto "
            "sobreimpreso, sin logo y a veces sin producto. Presta un rostro real "
            "en su propia casa, una foto clinica sin retoque o el bodegon cenital "
            "de todo lo que la persona ya probo y le fallo. Lo que se replica no "
            "es un layout: son las condiciones de captura."
        ),
        "dispositivo_neutro": (
            "LA FOTO CRUDA, SIN UNA SOLA PALABRA. Una sola fotografia que no "
            "parece un anuncio: la zona afectada vista de cerca en encuadre "
            "clinico sin retoque, o un rostro real en su propia casa, o el "
            "bodegon cenital de todo lo que la persona ya probo y le fallo. No "
            "hay titular, ni precio, ni logo, y el producto puede no aparecer. "
            "La evidencia esta DENTRO de la foto y las condiciones de captura "
            "dan toda la autoridad."
        ),
        "cuando_elegirlo": (
            "El publico esta quemado de carteles y la categoria huele a estafa. "
            "Compra atencion por parecer contenido, no publicidad. El copy tiene "
            "que cargar TODO el argumento — si el texto del anuncio es debil, esta "
            "familia no vende."
        ),
        "ejes": [
            "sujeto: rostro del avatar, zona del sintoma, o el bodegon de lo que fallo",
            "entorno: clinico, laboral, domestico — cambia a quien le habla",
            "conservar la imperfeccion (pliegue, sombra dura, fondo desordenado) es la regla",
        ],
        "miembros": ["F021", "F022", "F091", "F092"],
    },
    {
        "id": "CN09_UGC_PRODUCTO_EN_MANO",
        "nombre": "UGC con el producto en la mano",
        "dispositivo": (
            "LA MANO REAL SOSTIENE EL PRODUCTO — la caja recien abierta con el "
            "pack adentro, el frasco a la altura del pecho en un selfie. Prueba "
            "dos cosas de una: que el producto EXISTE y que YA LLEGO. El texto "
            "entra como caja de subtitulo de video o nota manuscrita, nunca como "
            "titular de cartel."
        ),
        "dispositivo_neutro": (
            "LA MANO SOSTENIENDO LA CAJA ABIERTA CON EL PACK ADENTRO. Una mano "
            "real entra por el borde inferior sosteniendo la caja de envio "
            "abierta, con las unidades acomodadas sobre el relleno. Es la foto "
            "de la ENTREGA, no del producto: muestra lo que va a llegar a la "
            "puerta, en la mano de alguien, ya desempacado."
        ),
        "cuando_elegirlo": (
            "MOFU: la objecion viva es 'esto no llega' o 'no es real'. El "
            "unboxing responde la logistica sin nombrarla."
        ),
        "ejes": [
            "una mano / dos manos / selfie con rostro",
            "estado: caja cerrada, caja abierta con el pack visible, frasco suelto",
            "marcador de autenticidad: brochazo, nota manuscrita, caja de subtitulo",
        ],
        "miembros": ["F014", "F015", "F078"],
    },
    {
        "id": "CN10_PRUEBA_SOCIAL",
        "nombre": "Prueba social en tarjetas y rating",
        "dispositivo": (
            "EL TESTIMONIO DE OTROS SE VUELVE OBJETO GRAFICO: tarjetas de resena "
            "con foto de perfil, nombre, ciudad y estrellas; una fila de "
            "comentarios de red social; o un rating decimal del tamano de un "
            "titular. La cifra no acompana — es la pieza."
        ),
        "dispositivo_neutro": (
            "LAS TRES TARJETAS DE RESENA CON FOTO DE PERFIL, NOMBRE, CIUDAD Y "
            "ESTRELLAS. Cada testimonio va en card blanca con avatar circular a "
            "la izquierda, el nombre y la CIUDAD debajo, cinco estrellas "
            "doradas a la derecha y la cita entre comillas con las palabras "
            "clave resaltadas en color. El icono de WhatsApp sobre cada avatar "
            "sugiere que la resena llego por chat."
        ),
        "cuando_elegirlo": (
            "MOFU/BOFU donde la objecion es '¿a quien mas le funciono?'. Necesita "
            "volumen real o al menos un numero de clientes defendible; con 3 "
            "resenas inventadas la pieza se lee falsa."
        ),
        "ejes": [
            "formato de la prueba: cards de resena, comentarios de red, rating decimal",
            "posicion del rating: barra propia o apilado bajo el rostro, que hace que la nota se lea como la de ELLA (F111)",
            "densidad de la vitrina: 8 cards con subtitulo o 4 sin (F107 vs F109)",
        ],
        "miembros": ["F025", "F059", "F107", "F109", "F111"],
    },
    {
        "id": "CN11_PANTALLA_SIMULADA",
        "nombre": "Captura de pantalla simulada",
        "dispositivo": (
            "LA PIEZA IMITA UNA INTERFAZ QUE EL LECTOR YA USA: el resultado de un "
            "buscador con el producto insertado, el marco del telefono con barra "
            "de estado completa, dos globos de chat sobre una escena real. Toma "
            "prestada la credibilidad del medio, no la de la marca."
        ),
        "dispositivo_neutro": (
            "LA CAPTURA DE PANTALLA DE UN BUSCADOR, CON EL PRODUCTO INSERTADO "
            "EN EL RESULTADO. La pieza imita la interfaz de una pagina de "
            "resultados: barra de busqueda con la pregunta escrita, pestanas, "
            "un bloque de respuesta destacado con el producto recortado adentro "
            "y, debajo, el comienzo de un segundo resultado con su URL. No se "
            "ve como anuncio porque imita algo que no lo es."
        ),
        "cuando_elegirlo": (
            "Publico NC1-NC2 que todavia no busca el producto: la captura le "
            "muestra la busqueda que 'deberia' haber hecho. Tambien para llevar "
            "la conversacion a WhatsApp mostrando el chat como CTA."
        ),
        "ejes": [
            "interfaz imitada: buscador, chat, ficha de producto",
            "con marco de telefono completo o solo el recorte de la captura",
            "la palabra clave puede funcionar como CTA literal (F067)",
        ],
        "miembros": ["F027", "F067", "F090"],
    },
    {
        "id": "CN12_AVATAR_DESEO",
        "nombre": "Avatar del deseo con el producto",
        "dispositivo": (
            "EL CUERPO O LA VIDA QUE SE QUIERE, FOTOGRAFIADO COMPLETO, y el "
            "producto sostenido dentro de esa escena. No muestra el problema en "
            "ningun lado: muestra el estado de llegada. El aparato comercial "
            "(oferta, sellos, precio) se apila en el flanco opuesto o baja a una "
            "banda, sin invadir la figura."
        ),
        "dispositivo_neutro": (
            "EL AVATAR DESEADO SOSTENIENDO EL PRODUCTO, EN SU ACTIVIDAD. Una "
            "persona real en su entorno cotidiano mira el envase que tiene en "
            "la mano. No hay problema ni sintoma: se muestra el CUERPO Y LA "
            "VIDA que el producto acompana. El titular declara para quien es en "
            "la primera linea, antes de nombrar el producto; el aparato "
            "comercial va en el flanco opuesto sin invadir la figura."
        ),
        "cuando_elegirlo": (
            "Categorias donde el motor es aspiracional y no clinico — figura, "
            "piel, energia, vitalidad. Si el avatar de la foto no se parece a la "
            "compradora guatemalteca, la pieza expulsa en vez de atraer."
        ),
        "ejes": [
            "encuadre: de espaldas, de frente, silueta en contraluz, en su actividad",
            "el eje 1:1 -> 4:5 mueve la oferta de card lateral a banda central bajo el titular",
            "fenotipo de la modelo (F094 vs F095) e intensidad del verbo, moldea vs realza (F105 vs F106)",
            "puede llevar o retirar el panel de prueba sin cambiar la plantilla",
        ],
        "miembros": ["F016", "F020", "F034", "F094", "F095", "F105", "F106"],
    },
    {
        "id": "CN13_ANATOMIA_MECANISMO",
        "nombre": "Anatomia y mecanismo de accion",
        "dispositivo": (
            "EL INTERIOR DEL CUERPO SE DIBUJA Y SE ENCIENDE: el organo iluminado, "
            "la silueta digital con los puntos de accion prendidos, el sistema "
            "interno superpuesto sobre el torso del avatar, las flechas de "
            "mecanismo trazadas sobre la zona. Explica POR QUE funciona, no que "
            "resultado da."
        ),
        "dispositivo_neutro": (
            "EL RESULTADO YA LOGRADO AL FONDO Y EL MECANISMO COMO GRAFICO "
            "ANATOMICO JUNTO AL PRODUCTO. Personas felices en su vida cotidiana "
            "ocupan el fondo y, flotando junto al envase, un grafico anatomico "
            "de la zona afectada encendida, del tamano de un puno. No se "
            "muestra el dolor: se muestra la vida SIN el dolor y, en el "
            "grafico, POR QUE funciona."
        ),
        "cuando_elegirlo": (
            "El publico ya probo cosas que fallaron y la objecion es "
            "'¿por que esto si?'. Convierte un producto mas en un mecanismo. "
            "Exige un mecanismo real que se pueda localizar en el cuerpo."
        ),
        "ejes": [
            "material: render anatomico, ilustracion digital, silueta en movimiento",
            "el organo puede ir SOLO, sobre el avatar, o junto a la escena de vida (F017)",
            "flechas de recorrido dibujadas encima del cuerpo real (F047)",
            "el producto puede ir entre la anatomia y el avatar, como puente (F087)",
        ],
        "miembros": ["F017", "F047", "F070", "F087", "F088"],
    },
    {
        "id": "CN14_COMPARACION_DOS_COLUMNAS",
        "nombre": "Comparacion en dos columnas",
        "dispositivo": (
            "LA PIEZA SE PARTE EN DOS COLUMNAS ENFRENTADAS y cada una lista un "
            "estado: yo sin / yo con, problema / solucion, falso / real, el "
            "remedio de la cocina / el producto. El rival casi nunca es una marca "
            "competidora — es la persona contra si misma o contra lo que ya hace "
            "gratis."
        ),
        "dispositivo_neutro": (
            "EL COMPARADOR DE DOS OPCIONES, CON EL PRODUCTO FOTOGRAFIADO EN "
            "CADA UNA. Dos cards o columnas enfrentadas, una con un envase y "
            "otra con dos, cada una con su precio y su cantidad. La decision se "
            "toma mirando cuanto producto hay en cada foto, no leyendo cuanto "
            "cuesta."
        ),
        "cuando_elegirlo": (
            "Hay una alternativa concreta que el publico YA esta usando (remedio "
            "casero, generico, falsificacion) y el argumento es la friccion de esa "
            "alternativa, no su ineficacia. Discutir si el remedio sirve pierde; "
            "cobrarle el olor, la preparacion y el tiempo gana."
        ),
        "ejes": [
            "rival elegido: yo mismo, remedio casero, producto falso, no hacer nada",
            "material: tabla dibujada a mano, ilustraciones planas, dos fotos del producto",
            "posicion: pieza entera o comparador reducido al pie (F037)",
            "puede combinarse con el multiplicador al centro del eje (F052)",
        ],
        "miembros": ["F037", "F043", "F052", "F054", "F073", "F102", "F110"],
    },
    {
        "id": "CN15_INGREDIENTES_ACTIVO",
        "nombre": "Despiece de ingredientes",
        "dispositivo": (
            "LA FORMULA SE ABRE Y SE MUESTRA POR PARTES: el activo principal solo "
            "en un circulo grande con su dosis y su explicacion, el despiece de "
            "los componentes alrededor del frasco, la lista de CATEGORIAS de "
            "ingrediente (no de ingredientes sueltos), o el badge con la cifra "
            "gigante de cuantos tipos lleva."
        ),
        "dispositivo_neutro": (
            "EL BADGE DE FORMULA MULTIPLE CON LA CIFRA GIGANTE Y LOS TIPOS "
            "ENUMERADOS. Un bloque en una esquina declara cuantas cosas hace la "
            "formula (5 EN 1) con el numeral al mayor tamano y, debajo, enumera "
            "los tipos incluidos en numeracion romana. La columna de beneficios "
            "que sigue es la explicacion de ese numero."
        ),
        "cuando_elegirlo": (
            "Publico NC4 que compara formulas y lee etiquetas, o cuando el "
            "diferencial real del producto es la dosis. Requiere una formula que "
            "aguante el escrutinio: si el activo esta subdosificado, esta familia "
            "expone el problema en vez de venderlo."
        ),
        "ejes": [
            "granularidad: un solo activo protagonista o el despiece completo",
            "agrupar por CATEGORIA de ingrediente comprime una lista larga (F085)",
            "la cifra de cantidad de activos puede volverse el badge dominante (F077)",
            "la dosis en miligramos entra como pildora junto al circulo del activo",
        ],
        "miembros": ["F077", "F079", "F080", "F085"],
    },
    {
        "id": "CN16_EMISOR_COMERCIAL",
        "nombre": "Cartel de tienda / emisor comercial",
        "dispositivo": (
            "QUIEN VENDE PESA MAS QUE QUE SE VENDE. El logo de la farmacia o la "
            "tienda funciona como emisor, se repite arriba y abajo, y el TELEFONO "
            "puede ser el elemento mas grande de la pieza. Las garantias, los "
            "botones de contacto y el nombre del producto como titular completan "
            "un cartel de comercio, no de marca."
        ),
        "dispositivo_neutro": (
            "EL LOGO DEL PUNTO DE VENTA COMO EMISOR, CON EL BADGE DE DURACION "
            "DEL TRATAMIENTO. El anuncio no lo firma la marca del producto sino "
            "la farmacia o tienda, cuyo logotipo ocupa una esquina superior con "
            "su nombre y su sucursal. Enfrente, un badge circular declara para "
            "cuantos dias alcanza el frasco y lo traduce a meses; el telefono "
            "puede ser el elemento mas grande."
        ),
        "cuando_elegirlo": (
            "La pagina ya tiene reconocimiento local y la venta se cierra por "
            "mensaje. Convierte al que ya conoce el negocio. Con una fanpage nueva "
            "y sin prueba social, esta familia no tiene de donde sacar autoridad."
        ),
        "ejes": [
            "peso del telefono: barra de pie discreta o el mayor tamano de la pieza (F082)",
            "el titular puede ser el NOMBRE del producto flanqueado por el simbolo de marca (F071)",
            "badge de duracion del tratamiento como sello de seriedad (F060)",
            "dos botones apilados del mismo tamano al pie, sin jerarquia entre ellos (F076)",
        ],
        "miembros": ["F060", "F071", "F074", "F076", "F082"],
    },
    {
        "id": "CN17_TITULAR_DOMINANTE",
        "nombre": "Titular tipografico dominante",
        "dispositivo": (
            "EL TEXTO ES LA IMAGEN. Tres lineas apiladas con una sola palabra en "
            "color sobre un fondo casi vacio, un titular que NIEGA que el problema "
            "sea el problema, una pregunta contra el propio pasado, un hook de "
            "retargeting explicito. El producto aparece pequeno o al pie: lo que "
            "detiene el scroll es la frase."
        ),
        "dispositivo_neutro": (
            "EL REENCUADRE DEL PROBLEMA EN EL TITULAR. El texto es la imagen: "
            "dos oraciones cortas separadas por coma sobre un fondo casi vacio; "
            "la primera niega lo que la persona cree de si misma y la segunda "
            "ofrece una explicacion distinta, con la palabra clave subrayada. "
            "No promete nada todavia: le cambia el diagnostico. El producto "
            "aparece pequeno."
        ),
        "cuando_elegirlo": (
            "Hay UNA frase con giro real — reencuadre, negacion, pregunta "
            "incomoda. Sin ese giro queda un cartel vacio. Es tambien la unica "
            "familia con una pieza de NC5 (retargeting explicito, F056)."
        ),
        "ejes": [
            "mecanismo del giro: negacion, reencuadre, pregunta al propio pasado, retargeting",
            "una sola palabra en color de acento marca el pivote de la frase",
            "puede llevar una banda que RE-CATEGORIZA el problema bajo el titular (F104)",
            "espacio libre alto: el vacio es parte del dispositivo",
        ],
        "miembros": ["F032", "F048", "F051", "F056", "F104"],
    },
    {
        "id": "CN18_CALLOUTS_PRODUCTO",
        "nombre": "Callouts cableados al producto",
        "dispositivo": (
            "EL PRODUCTO AL CENTRO Y LAS ETIQUETAS FLOTANDO ALREDEDOR, cada una "
            "unida al frasco por una linea punteada. Convierte al envase en un "
            "diagrama tecnico. Algunos callouts pueden ir TACHADOS: lo que el "
            "producto NO tiene se vuelve argumento igual que lo que tiene."
        ),
        "dispositivo_neutro": (
            "LOS CALLOUTS FLOTANTES CON LINEA PUNTEADA AL PRODUCTO. Cuatro "
            "pildoras blancas con icono cuelgan alrededor del envase y cada una "
            "apunta al producto con una linea punteada curva. No hay columna ni "
            "fila: los beneficios ORBITAN el producto, cada uno ligado "
            "espacialmente a la pieza que lo cumple."
        ),
        "cuando_elegirlo": (
            "El diferencial esta en atributos del producto mismo (sin azucar, sin "
            "gluten, absorcion sublingual, dosis) y no en un resultado. Requiere "
            "una foto del envase limpia y con espacio a los lados."
        ),
        "ejes": [
            "cantidad de callouts: 3 (respira) o mas (se lee como ficha tecnica)",
            "callouts en positivo, o tachados para marcar lo que se evita (F093)",
            "formato vertical 9:16 da mas aire a las lineas punteadas (F011)",
        ],
        "miembros": ["F011", "F093"],
    },
    {
        "id": "CN19_INSTRUCTIVO_PASOS",
        "nombre": "Instructivo de pasos numerados",
        "dispositivo": (
            "COMO SE USA, EN PASOS NUMERADOS CON SU FOTO DE LA ACCION. Responde "
            "la pregunta que frena la compra en productos de aplicacion no obvia: "
            "'¿y esto como se hace?'. La seccion de modo de preparacion puede "
            "intercalarse entre los beneficios y el precio, con su propio header "
            "en pregunta."
        ),
        "dispositivo_neutro": (
            "EL INSTRUCTIVO DE 4 PASOS NUMERADOS, CADA UNO CON SU FOTO DE LA "
            "ACCION. Cuatro filas apiladas: foto cuadrada de la mano ejecutando "
            "el paso, numeral grande, titulo del verbo en dos colores y una "
            "explicacion de dos lineas. La pieza no vende el producto, ENSENA A "
            "USARLO, y al hacerlo demuestra que es facil."
        ),
        "cuando_elegirlo": (
            "El producto tiene un modo de uso que no se adivina (ovulo, gotero "
            "sublingual, parche, polvo que se prepara). Si se toma como cualquier "
            "capsula, el instructivo gasta espacio en algo que nadie pregunta."
        ),
        "ejes": [
            "3-4 pasos con foto real de la accion, o solo iconos",
            "pieza entera (F045) o seccion embebida en un cartel de beneficios (F084)",
            "header en pregunta ('¿Como se prepara?') que le da funcion de FAQ",
        ],
        "miembros": ["F045", "F084"],
    },
    {
        "id": "CN20_PRECIO_ANCLA",
        "nombre": "Precio unico con ancla",
        "dispositivo": (
            "UN SOLO PRECIO, PRESENTADO CONTRA SU ANCLA. El bloque va en card de "
            "ancho completo o en tres partes (precio tachado, precio actual, "
            "ahorro) bajo una columna corta de atributos. No hay escalera ni "
            "eleccion: hay una cifra y su referencia."
        ),
        "dispositivo_neutro": (
            "EL PRECIO CON ANCLAJE EN CARD DE ANCHO COMPLETO, BAJO UNA COLUMNA "
            "CORTA DE 3 ATRIBUTOS. La mitad izquierda es una escalera de "
            "lectura de cuatro pisos: pregunta, promesa, tres atributos, "
            "precio; cada piso mas chico que el anterior salvo el precio, que "
            "vuelve a crecer. Un solo precio presentado contra su ancla "
            "(tachado, actual, ahorro)."
        ),
        "cuando_elegirlo": (
            "La oferta tiene UNA sola presentacion, o se quiere empujar una sola "
            "unidad sin abrir la decision. Hermano de CN04_ESCALERA_PRECIOS: si "
            "hay 3 tiers reales, ese canonico rinde mas."
        ),
        "ejes": [
            "bloque de tres partes (tachado / actual / ahorro) o card simple con ancla",
            "cuantos atributos lo preceden: 3 es el maximo antes de tapar el precio",
            "el ancla puede ser precio anterior, precio de farmacia o precio por unidad",
        ],
        "miembros": ["F018", "F081"],
    },
    {
        "id": "CN21_AVATAR_CARD_BENEFICIOS",
        "nombre": "Avatar con card de beneficios flotante",
        "dispositivo": (
            "EL AVATAR SOSTIENE EL PRODUCTO A LA ALTURA DEL PECHO y una card "
            "semitransparente de beneficios flota a su lado, sin taparlo. La "
            "persona da la cara; la card da el argumento. Su pieza hermana retira "
            "al avatar y deja la MISMA card y la MISMA oferta — que el rostro sea "
            "opcional es el hallazgo de esta familia."
        ),
        "dispositivo_neutro": (
            "EL AVATAR SOSTIENE EL PRODUCTO A LA ALTURA DEL PECHO, CON LA CARD "
            "DE BENEFICIOS FLOTANDO A SU LADO. La persona ocupa la mitad del "
            "frame, sostiene el envase con las dos manos y lo presenta hacia "
            "camara; a su lado, una card semitransparente con cuatro beneficios "
            "en iconos. El producto queda en el centro por estar en sus manos. "
            "La persona da la cara; la card da el argumento."
        ),
        "cuando_elegirlo": (
            "MOFU donde conviene que alguien 'ponga la cara' pero el argumento "
            "sigue siendo la lista. Correr la pieza CON y SIN avatar es un test "
            "limpio: cambia una sola variable."
        ),
        "ejes": [
            "con avatar (F028) o sin nadie, misma card y misma oferta (F089)",
            "lado de la card respecto del avatar",
            "opacidad de la card: solida o velo sobre la foto",
        ],
        "miembros": ["F028", "F089"],
    },
    {
        "id": "CN22_ESCENA_DE_USO",
        "nombre": "Escena del momento de uso",
        "dispositivo": (
            "UNA FOTOGRAFIA DEL MOMENTO EN QUE EL PRODUCTO ENTRA EN LA VIDA: el "
            "frasco iluminado sobre la mesa de noche en escena nocturna, la cinta "
            "metrica como eje vertical del frame y el gesto de auto-medirse. No es "
            "el problema ni el resultado — es el ritual. Instala CUANDO se usa sin "
            "escribirlo."
        ),
        "dispositivo_neutro": (
            "LA ESCENA DEL MOMENTO EN QUE EL PRODUCTO ENTRA EN LA VIDA. El "
            "envase queda iluminado en su lugar de uso (por ejemplo sobre la "
            "mesa de noche, en una habitacion a oscuras, bajo la luz calida de "
            "una lampara). La pieza no muestra el problema ni el mecanismo: "
            "muestra el MOMENTO Y EL LUGAR donde el producto se usa, y ese "
            "contexto declara para que sirve."
        ),
        "cuando_elegirlo": (
            "El momento de uso es parte del beneficio (antes de dormir, en ayunas, "
            "despues del bano) o el gesto de medicion es en si el disparador "
            "emocional. Necesita una escena reconocible del hogar guatemalteco."
        ),
        "ejes": [
            "momento retratado: nocturno, matinal, de control/medicion",
            "el objeto del ritual puede volverse el eje grafico del frame (F096)",
            "iluminacion: calida y baja (noche) o neutra de dia",
        ],
        "miembros": ["F069", "F096"],
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# CONTRATO DE VARIABLES POR FAMILIA — escrito a mano, y hace falta que lo sea.
#
# Derivar el contrato contando variables entre miembros NO funciona: cada tanda
# nombro lo mismo distinto (RETRATO_ANTES / FOTO_ANTES / IMAGEN_ANTES), asi que
# en CN01 (14 miembros) ninguna variable alcanza el 60% y el nucleo sale vacio.
# El conteo queda igual publicado como `variables_observadas` (evidencia), pero
# lo que el motor de lotes le pide a un producto es ESTO.
#
# Vocabulario comun a todas las familias (no se repite en cada lista):
#   PRODUCTO_NOMBRE · PRODUCTO_FOTO · PALETA_ACENTO · PALETA_OSCURA · PALETA_CLARO
# ─────────────────────────────────────────────────────────────────────────────
BASE_COMUN = ["PRODUCTO_NOMBRE", "PRODUCTO_FOTO",
              "PALETA_ACENTO", "PALETA_OSCURA", "PALETA_CLARO"]

CONTRATOS = {
    "CN01_ANTES_DESPUES": [
        "TITULAR", "IMAGEN_ANTES", "IMAGEN_DESPUES",
        "ETIQUETA_ANTES", "ETIQUETA_DESPUES", "EJE_DEL_CORTE", "CTA",
    ],
    "CN02_TIMELINE_PROGRESION": [
        "TITULAR", "ESTADO_1", "ESTADO_2", "ESTADO_3",
        "LABEL_PLAZO_1", "LABEL_PLAZO_2", "LABEL_PLAZO_3",
        "MATERIAL_DEL_ESTADO", "CTA",
    ],
    "CN03_OFERTA_MULTIPLICADOR": [
        "MULTIPLICADOR", "CONTENEDOR_MULTIPLICADOR", "TITULAR",
        "PRECIO_OFERTA", "MONEDA", "GARANTIAS", "CTA",
    ],
    "CN04_ESCALERA_PRECIOS": [
        "CANT_1", "CANT_2", "CANT_3", "PRECIO_1", "PRECIO_2", "PRECIO_3",
        "MONEDA", "UNIDAD", "TIER_HEROE", "MARCADOR_HEROE", "GARANTIAS", "CTA",
    ],
    "CN05_LISTA_BENEFICIOS": [
        "TITULAR", "BENEFICIOS", "MARCADOR_ITEM", "ORIENTACION_LISTA", "CTA",
    ],
    "CN06_CHECKLIST_SINTOMAS": [
        "HEADER_IDENTIFICACION", "SINTOMAS", "EVIDENCIA_ITEM",
        "ORIENTACION_LISTA", "FRASE_SALIDA", "CTA",
    ],
    "CN07_DOLOR_A_PLENO": [
        "FOTO_DEL_GESTO", "GESTO_DESCRITO", "TITULAR", "ENCUADRE", "CTA",
    ],
    "CN08_UGC_CRUDO": [
        "SUJETO", "ENTORNO", "ANGULO", "LUZ", "IMPERFECCION_QUE_SE_CONSERVA",
    ],
    "CN09_UGC_PRODUCTO_EN_MANO": [
        "SUJETO", "ESTADO_DEL_PAQUETE", "ANGULO", "LUZ",
        "TEXTO_SOBREIMPRESO", "MARCADOR_AUTENTICIDAD",
    ],
    "CN10_PRUEBA_SOCIAL": [
        "TITULAR", "TESTIMONIOS", "NOMBRES", "CIUDADES",
        "CALIFICACION", "CANTIDAD_CLIENTES", "FORMATO_PRUEBA", "CTA",
    ],
    "CN11_PANTALLA_SIMULADA": [
        "INTERFAZ_IMITADA", "CONSULTA_O_MENSAJE", "RESPUESTA",
        "PALABRA_CLAVE_CTA",
    ],
    "CN12_AVATAR_DESEO": [
        "FOTO_AVATAR", "AVATAR_DESCRIPCION", "ENCUADRE", "TITULAR_DESEO",
        "BENEFICIOS", "PRECIO_OFERTA", "MONEDA", "POSICION_APARATO_COMERCIAL", "CTA",
    ],
    "CN13_ANATOMIA_MECANISMO": [
        "ORGANO_O_SISTEMA", "MATERIAL_ANATOMICO", "PUNTOS_DE_ACCION",
        "TITULAR_MECANISMO", "CTA",
    ],
    "CN14_COMPARACION_DOS_COLUMNAS": [
        "RIVAL", "HEADER_COLUMNA_A", "HEADER_COLUMNA_B",
        "ITEMS_COLUMNA_A", "ITEMS_COLUMNA_B", "MATERIAL_TABLA", "CTA",
    ],
    "CN15_INGREDIENTES_ACTIVO": [
        "ACTIVO_PRINCIPAL", "DOSIS", "EXPLICACION_ACTIVO",
        "ACTIVOS_SECUNDARIOS", "GRANULARIDAD", "CTA",
    ],
    "CN16_EMISOR_COMERCIAL": [
        "LOGO_TIENDA", "NOMBRE_TIENDA", "TELEFONO", "TITULAR",
        "GARANTIAS", "PESO_DEL_TELEFONO", "CTA",
    ],
    "CN17_TITULAR_DOMINANTE": [
        "TITULAR", "PALABRA_PIVOTE", "MECANISMO_DEL_GIRO", "CTA",
    ],
    "CN18_CALLOUTS_PRODUCTO": [
        "CALLOUTS", "CALLOUTS_TACHADOS", "TITULAR", "CTA",
    ],
    "CN19_INSTRUCTIVO_PASOS": [
        "HEADER_PREGUNTA", "PASOS", "FOTO_POR_PASO", "CTA",
    ],
    "CN20_PRECIO_ANCLA": [
        "PRECIO_ANCLA", "PRECIO_ACTUAL", "AHORRO", "MONEDA",
        "ATRIBUTOS", "CTA",
    ],
    "CN21_AVATAR_CARD_BENEFICIOS": [
        "FOTO_AVATAR", "BENEFICIOS", "LADO_DE_LA_CARD",
        "PRECIO_OFERTA", "MONEDA", "CON_O_SIN_AVATAR", "CTA",
    ],
    "CN22_ESCENA_DE_USO": [
        "MOMENTO", "ESCENA", "OBJETO_DEL_RITUAL", "ILUMINACION", "TITULAR", "CTA",
    ],
}


def cargar_fichas():
    fichas = {}
    for nombre in sorted(os.listdir(FICHAS)):
        if not re.fullmatch(r"F\d{3}\.json", nombre):
            continue
        ruta = os.path.join(FICHAS, nombre)
        with open(ruta, encoding="utf-8") as fh:
            fichas[nombre[:-5]] = json.load(fh)
    return fichas


def validar(fichas):
    """Cobertura exacta: cada ficha en un canonico y solo uno."""
    errores = []
    vistos = collections.Counter()
    for fam in FAMILIAS:
        for fid in fam["miembros"]:
            vistos[fid] += 1
            if fid not in fichas:
                errores.append("%s: miembro inexistente %s" % (fam["id"], fid))
    faltan_contrato = [fam["id"] for fam in FAMILIAS if fam["id"] not in CONTRATOS]
    if faltan_contrato:
        errores.append("canonicos sin contrato_variables: %s" % ", ".join(faltan_contrato))
    sobran = sorted(set(CONTRATOS) - {fam["id"] for fam in FAMILIAS})
    if sobran:
        errores.append("contratos sin canonico: %s" % ", ".join(sobran))
    dup = [f for f, n in vistos.items() if n > 1]
    if dup:
        errores.append("fichas en mas de un canonico: %s" % ", ".join(sorted(dup)))
    huerfanas = sorted(set(fichas) - set(vistos))
    if huerfanas:
        errores.append("fichas sin canonico: %s" % ", ".join(huerfanas))
    return errores


def cabeza(dispositivo):
    """La frase en MAYUSCULAS con la que abre `dispositivo_dominante`."""
    m = re.match(r"^([A-ZÁÉÍÓÚÑ0-9 ,\+\-–«»\"()%/]{6,140}?)[.:]", dispositivo)
    return m.group(1).strip() if m else dispositivo[:80].strip()


def perfilar(fam, fichas):
    ms = [fichas[f] for f in fam["miembros"]]
    n = len(ms)

    def conteo(camino):
        c = collections.Counter()
        for d in ms:
            v = d["clasificacion"].get(camino)
            c[v if v is not None else "sin_dato"] += 1
        return dict(c.most_common())

    ncs = [d["clasificacion"].get("nivel_conciencia") for d in ms]
    ncs = [x for x in ncs if isinstance(x, int)]

    # Variables en tres cubetas. La union cruda no sirve: en un canonico de 5 miembros
    # produce 60+ variables, la mayoria idiosincraticas de UNA pieza. Eso no es el
    # contrato de la familia, es ruido que el llenador tendria que inventar.
    #   nucleo      = en >=60% de los miembros -> sin esto la familia no se puede armar
    #   opcionales  = en >=2 miembros          -> recurren, pero no son obligatorias
    #   (en 1 solo miembro -> se quedan en SU ficha, no suben al canonico)
    vc = collections.Counter()
    for d in ms:
        for v in dict.fromkeys(d.get("variables_requeridas", [])):
            vc[v] += 1
    umbral = max(2, round(n * 0.6))
    nucleo = sorted([v for v, k in vc.items() if k >= umbral])
    opcionales = sorted([v for v, k in vc.items() if 2 <= k < umbral])

    # reglas duras compartidas por >=2 miembros (normalizando por si acaso)
    rc = collections.Counter()
    for d in ms:
        for r in dict.fromkeys(d.get("reglas_duras", [])):
            rc[r.strip()] += 1
    compartidas = [r for r, k in rc.most_common() if k >= 2]

    def union(clave, tope):
        out, visto = [], set()
        for d in sorted(ms, key=lambda x: -x["origen"].get("score", 0)):
            for item in d.get(clave, []):
                k = item.strip().lower()
                if k not in visto:
                    visto.add(k)
                    out.append(item.strip())
        return out[:tope]

    ref = max(ms, key=lambda d: d["origen"].get("score", 0))

    return {
        "n_miembros": n,
        "ficha_referencia": ref["ficha_id"],
        "score_referencia": ref["origen"].get("score"),
        "perfil": {
            "concepto_key": conteo("concepto_key"),
            "rol_embudo": conteo("rol_embudo"),
            "estetica": conteo("estetica"),
            "formato": conteo("formato"),
            "densidad": conteo("densidad"),
            "nivel_conciencia_rango": [min(ncs), max(ncs)] if ncs else None,
        },
        "contrato_variables": BASE_COMUN + CONTRATOS[fam["id"]],
        "variables_observadas": {"nucleo": nucleo, "recurrentes": opcionales},
        "reglas_duras_compartidas": compartidas,
        "reglas_duras_referencia": ref.get("reglas_duras", []),
        "cuando_usar": union("cuando_usar", 8),
        "cuando_no_usar": union("cuando_no_usar", 6),
        "blueprint_equivalente": sorted(
            {d.get("blueprint_equivalente") for d in ms if d.get("blueprint_equivalente")}
        ) or None,
        "miembros": [
            {
                "ficha_id": d["ficha_id"],
                "score": d["origen"].get("score"),
                "anunciante": d["origen"].get("anunciante"),
                "concepto_key": d["clasificacion"].get("concepto_key"),
                "formato": d["clasificacion"].get("formato"),
                "rol_embudo": d["clasificacion"].get("rol_embudo"),
                "estetica": d["clasificacion"].get("estetica"),
                "dispositivo": cabeza(d["dispositivo_dominante"]),
            }
            for d in sorted(ms, key=lambda x: -x["origen"].get("score", 0))
        ],
    }


def main():
    dry = "--dry-run" in sys.argv
    fichas = cargar_fichas()
    print("fichas cargadas: %d" % len(fichas))

    errores = validar(fichas)
    if errores:
        print("\nVALIDACION FALLIDA:")
        for e in errores:
            print("  -", e)
        return 1
    print("cobertura: %d fichas en %d canonicos, sin duplicados ni huerfanas"
          % (len(fichas), len(FAMILIAS)))

    if dry:
        for fam in FAMILIAS:
            print("  %-30s %2d" % (fam["id"], len(fam["miembros"])))
        return 0

    os.makedirs(CANON, exist_ok=True)
    indice = []
    for fam in FAMILIAS:
        derivado = perfilar(fam, fichas)
        doc = collections.OrderedDict()
        doc["canonico_id"] = fam["id"]
        doc["schema_version"] = SCHEMA
        doc["nombre"] = fam["nombre"]
        doc["dispositivo_canonico"] = fam["dispositivo"]
        doc["dispositivo"] = fam["dispositivo_neutro"]
        doc["cuando_elegirlo"] = fam["cuando_elegirlo"]
        doc["ejes_de_variacion"] = fam["ejes"]
        doc["n_miembros"] = derivado["n_miembros"]
        doc["ficha_referencia"] = derivado["ficha_referencia"]
        doc["score_referencia"] = derivado["score_referencia"]
        doc["perfil"] = derivado["perfil"]
        doc["contrato_variables"] = derivado["contrato_variables"]
        doc["variables_observadas"] = derivado["variables_observadas"]
        doc["reglas_duras_compartidas"] = derivado["reglas_duras_compartidas"]
        doc["reglas_duras_referencia"] = derivado["reglas_duras_referencia"]
        doc["cuando_usar"] = derivado["cuando_usar"]
        doc["cuando_no_usar"] = derivado["cuando_no_usar"]
        doc["blueprint_equivalente"] = derivado["blueprint_equivalente"]
        doc["miembros"] = derivado["miembros"]

        ruta = os.path.join(CANON, fam["id"] + ".json")
        with open(ruta, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        indice.append(doc)
        print("  escrito %s (%d miembros, ref %s)"
              % (fam["id"], doc["n_miembros"], doc["ficha_referencia"]))

    # inyectar canonico_id en las fichas — la ficha nunca se edita a mano
    pertenencia = {}
    for fam in FAMILIAS:
        for fid in fam["miembros"]:
            pertenencia[fid] = fam["id"]
    tocadas = 0
    for fid, d in fichas.items():
        nuevo = pertenencia[fid]
        if d.get("canonico_id") != nuevo:
            d["canonico_id"] = nuevo
            with open(os.path.join(FICHAS, fid + ".json"), "w", encoding="utf-8") as fh:
                json.dump(d, fh, ensure_ascii=False, indent=2)
                fh.write("\n")
            tocadas += 1
    print("canonico_id actualizado en %d fichas" % tocadas)

    # indice legible
    md = ["# CANONICOS — indice generado",
          "",
          "> Generado por `Ads/_TOOLS/agrupar_canonicos.py`. **No editar a mano.**",
          "> Para cambiar una agrupacion se edita `FAMILIAS` en el script y se vuelve a correr.",
          "",
          "| canonico | n | ref | conceptos | embudo | dispositivo |",
          "|---|---|---|---|---|---|"]
    for doc in indice:
        ck = " ".join("%s:%d" % (k.split("_")[0], v)
                      for k, v in doc["perfil"]["concepto_key"].items())
        re_ = " ".join("%s:%d" % (k, v) for k, v in doc["perfil"]["rol_embudo"].items())
        md.append("| `%s` %s | %d | %s | %s | %s | %s |"
                  % (doc["canonico_id"], doc["nombre"], doc["n_miembros"],
                     doc["ficha_referencia"], ck, re_,
                     cabeza(doc["dispositivo_canonico"])))
    md.append("")
    md.append("**Total: %d fichas en %d canonicos.** Cobertura exacta: cada ficha "
              "pertenece a uno y solo un canonico." % (len(fichas), len(FAMILIAS)))
    md.append("")
    with open(os.path.join(CANON, "_INDICE.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md))
    print("indice escrito en CANONICOS/_INDICE.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
