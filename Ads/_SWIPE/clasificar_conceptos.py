# -*- coding: utf-8 -*-
"""Pre-clasificacion de creativos por CONCEPTO usando senales de TEXTO.

LIMITE HONESTO: el texto es un PROXY. Solo 5 de los 10 conceptos tienen firma
textual confiable (TESTIMONIO, EDUCATIVO_MECANISMO, AUTORIDAD, PRUEBA_SOCIAL_NUM,
OFERTA_PRECIO). Los otros 5 (DEMO_USO, COMPARACION, AMENAZA_CHOQUE, PRODUCTO_HERO,
CONVERSACION_CHAT) son VISUALES: el texto casi nunca los delata. Esos salen como
REVISAR_VISUAL y son precisamente los que necesitan el ojo del operador.
"""
import csv,io,os,re,unicodedata,collections

def norm(s):
    s=(s or '').lower()
    s=unicodedata.normalize('NFD',s)
    return ''.join(c for c in s if unicodedata.category(c)!='Mn')

# (concepto, peso, patron)  — peso alto = senal mas especifica
REGLAS=[
 ('AUTORIDAD',        3, r'\b(dr\.|dra\.|doctor|doctora|traumatolog|dermatolog|medico|naturista|especialista)'),
 ('PRUEBA_SOCIAL_NUM',3, r'(\+ ?[\d.,]{3,}\s*(clientes|personas|vendidos|satisfech)|[\d.,]+\s*/\s*5|\bcalificacion\b|\b\d\.\d/5\b|mas de [\d.,]{3,}|\+[\d.,]{3,}\b)'),
 ('PRUEBA_SOCIAL_NUM',2, r'(mejor calificaci|clientes satisfech|personas felices|\bvendidos\b|unete a)'),
 ('TESTIMONIO',       3, r'\b(me (curo|ayudo|cambio|paso|funciono)|yo (pensaba|probe|tenia|sentia)|llevaba \d|ojala hubiera|te lo recomiendo|antes terminaba|hoy me siento|conoce la experiencia|dicen quienes|as[ií] fue como conoc)'),
 ('TESTIMONIO',       2, r'\b(pense que era|hasta que decid|solo aniad|solo empec|no cambi[eé] mi|un dia me di cuenta|me da rabia)'),
 ('EDUCATIVO_MECANISMO',3, r'(sabias que|cientificos descubrieron|se llama\b|lo que (tu|su) \w+ no (aprendio|sabe)|que hace especial|es un ant|combina \w+ ,? ?\w* y \w+|formulado con|\bmecanismo\b)'),
 ('EDUCATIVO_MECANISMO',2, r'(no siempre parece|no siempre significa|muchas veces,|lo que hay dentro|por que\b.*\?|interruptor del metabolismo)'),
 ('OFERTA_PRECIO',    3, r'(\b2\s?x\s?1\b|\b3\s?x\s?2\b|lleva 3 y paga 2|\bq ?\d{2,}|\b\d{1,3}% de descuento|paga 2 y lleva 3|combo a q|los 3 frascos)'),
 ('OFERTA_PRECIO',    2, r'(oferta limitada|super oferta|mega oferta|super promo|precio especial|ultimas unidades|solo hoy|promocion)'),
 ('COMPARACION',      3, r'(no todos los \w+ son iguales|a diferencia de|\bvs\.?\b|en vez de|mejor que)'),
 ('AMENAZA_CHOQUE',   3, r'(ahuyenta|plaga|cucaracha|rata|raton|invaden|asqueros)'),
 ('DEMO_USO',         2, r'(modo de uso|unas gotas|aplicar|aplicá|se aplica|en un solo paso|listo para usar|instalacion)'),
 ('CONVERSACION_CHAT',2, r'(captura de|pantallazo)'),
]
CONCEPTOS_TEXTO_FIABLE={'TESTIMONIO','EDUCATIVO_MECANISMO','AUTORIDAD','PRUEBA_SOCIAL_NUM','OFERTA_PRECIO'}

def es_catalogo(blob):
    return '{{product.' in blob

def clasificar(blob):
    n=norm(blob)
    sc=collections.Counter()
    for con,peso,pat in REGLAS:
        if re.search(pat,n): sc[con]+=peso
    if not sc: return ('REVISAR_VISUAL',0,'')
    top,val=sc.most_common(1)[0]
    # empate -> ambiguo
    empatados=[c for c,v in sc.items() if v==val]
    if len(empatados)>1:
        return ('AMBIGUO',val,'+'.join(sorted(empatados)))
    conf='ALTA' if (val>=3 and top in CONCEPTOS_TEXTO_FIABLE) else 'BAJA'
    return (top,val,conf)

filas=[]
# _ADS.csv (indice viejo): campo 'copy'
if os.path.exists('_ADS.csv'):
    for r in csv.DictReader(io.open('_ADS.csv',encoding='utf-8')):
        blob=r.get('copy','') or ''
        filas.append({'ad_archive_id':r['ad_archive_id'],'anunciante':r.get('anunciante',''),
            'archivo':r.get('archivo',''),'dias':r.get('dias_corriendo',''),
            'cc':r.get('collation_count','1'),'blob':blob,'fuente':'_ADS'})
# _BANCO.csv (indice nuevo): titulo+descripcion+texto_principal
if os.path.exists('_BANCO.csv'):
    for r in csv.DictReader(io.open('_BANCO.csv',encoding='utf-8')):
        blob=' '.join([r.get('titulo','') or '',r.get('descripcion','') or '',r.get('texto_principal','') or ''])
        filas.append({'ad_archive_id':r['ad_archive_id'],'anunciante':r.get('anunciante',''),
            'archivo':r.get('archivo',''),'dias':r.get('dias_corriendo',''),
            'cc':r.get('replicas','1'),'blob':blob,'fuente':'_BANCO'})

vistos=set(); out=[]
for f in filas:
    if f['ad_archive_id'] in vistos: continue
    vistos.add(f['ad_archive_id'])
    cat=es_catalogo(f['blob'])
    if cat:
        con,val,conf=('CATALOGO_DINAMICO',9,'N/A')
    else:
        con,val,conf=clasificar(f['blob'])
    out.append([f['ad_archive_id'],f['anunciante'],f['archivo'],f['dias'],f['cc'],
                'SI' if cat else 'NO',con,conf,f['blob'][:110]])

COLS=['ad_archive_id','anunciante','archivo','dias_corriendo','replicas',
      'es_catalogo','concepto_auto','confianza','texto_muestra']
with io.open('_PRECLASIFICACION.csv','w',encoding='utf-8',newline='') as fh:
    w=csv.writer(fh); w.writerow(COLS); w.writerows(out)

d=collections.Counter(r[6] for r in out)
tot=len(out)
print('total creativos: %d'%tot)
print()
for k,v in d.most_common():
    print('%-22s %4d  %5.1f%%'%(k,v,100*v/tot))
print()
conf=collections.Counter(r[7] for r in out if r[6] not in ('CATALOGO_DINAMICO','REVISAR_VISUAL','AMBIGUO'))
print('confianza en los clasificados:',dict(conf))
