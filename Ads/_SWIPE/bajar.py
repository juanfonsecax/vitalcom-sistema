# -*- coding: utf-8 -*-
"""Lee _RAW/*.tsv (meta+urls o full) -> descarga imagenes a _IMG/ -> anexa a _ADS.csv"""
import io,os,csv,glob,re,collections,datetime,urllib.request
HOY=datetime.date.today().isoformat()
COLS=['ad_archive_id','page_id','anunciante','rank_impresiones','dias_corriendo','collation_count',
      'velocidad','ads_activos_pagina','ad_mas_viejo_pagina','archivo','copy','fecha_cosecha',
      'replicas_misma_imagen']
TAB=chr(9); NL=chr(10)
meta={};urls={}
for f in sorted(glob.glob('_RAW/meta_*.tsv')):
    for ln in io.open(f,encoding='utf-8'):
        p=ln.rstrip(NL).split(TAB)
        if len(p)>=11 and p[5]:
            meta[p[5]]=dict(pid=p[0],pn=p[1],tot=p[2],n=p[3],maxd=p[4],cc=p[6],d=p[7],r=p[8],v=p[9],b=p[10])
for f in sorted(glob.glob('_RAW/urls_*.tsv')):
    for ln in io.open(f,encoding='utf-8'):
        p=ln.rstrip(NL).split(TAB)
        if len(p)==2 and p[1].startswith('http'): urls[p[0]]=p[1]
for f in sorted(glob.glob('_RAW/full_*.tsv')):
    for ln in io.open(f,encoding='utf-8'):
        p=ln.rstrip(NL).split(TAB)
        if len(p)>=12 and p[5] and p[11].startswith('http'):
            meta[p[5]]=dict(pid=p[0],pn=p[1],tot=p[2],n=p[3],maxd=p[4],cc=p[6],d=p[7],r=p[8],v=p[9],b=p[10])
            urls[p[5]]=p[11]
prev=set()
if os.path.exists('_PROCESADOS.txt'):
    prev={l.strip() for l in io.open('_PROCESADOS.txt',encoding='utf-8') if l.strip()}
base={a:u.split('/')[-1].split('?')[0] for a,u in urls.items()}
repl=collections.Counter(base.values())
vistas=set()
if os.path.exists('_VISTAS.txt'):
    vistas={l.strip() for l in io.open('_VISTAS.txt',encoding='utf-8') if l.strip()}
rows=[];ok=0;err=0;dup=0;sinmeta=0
for aid,u in urls.items():
    m=meta.get(aid)
    if not m: sinmeta+=1; continue
    if aid in prev: continue
    b=base[aid]
    if b in vistas: dup+=1; continue
    vistas.add(b)
    sub=os.path.join('_IMG',re.sub('[^0-9A-Za-z_-]','_',m['pn'] or m['pid'])[:38].strip('_'))
    if not os.path.isdir(sub): os.makedirs(sub)
    dest=os.path.join(sub,'%02d_%s.jpg'%(int(m['r'] or 99),aid))
    if not os.path.exists(dest):
        try:
            rq=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(rq,timeout=30) as r,open(dest,'wb') as o: o.write(r.read())
            ok+=1
        except Exception as e:
            print('  ERR %s %s'%(aid,str(e)[:50])); err+=1; continue
    rows.append([aid,m['pid'],m['pn'],m['r'],m['d'],m['cc'],m['v'],m['tot'],m['maxd'],
                 dest.replace(os.sep,'/'),m['b'],HOY,repl[b]])
prev.update(a for a in urls if a in meta)
io.open('_PROCESADOS.txt','w',encoding='utf-8').write(chr(10).join(sorted(prev)))
nuevo=not os.path.exists('_ADS.csv')
with io.open('_ADS.csv','a',encoding='utf-8',newline='') as f:
    w=csv.writer(f)
    if nuevo: w.writerow(COLS)
    w.writerows(rows)
io.open('_VISTAS.txt','w',encoding='utf-8').write(chr(10).join(sorted(vistas)))
print('descargadas=%d errores=%d dup_omitidas=%d sin_meta=%d filas=%d'%(ok,err,dup,sinmeta,len(rows)))
