# -*- coding: utf-8 -*-
"""Descarga masiva desde _RAW/masivo/*.txt (URLs comprimidas).
Formato:  #P|pid|pagina|host|gid|stp|ccb|sid|zt|ht|ss|seg
          A|ad_id|cc|dias|pos|total_pos|file~cat~ohc~oc~oh~oe|titulo|desc|cta|destino|texto
Filtro de cuadrante: descarta pos en mitad inferior CON dias>=21 (perdedor no pausado).
"""
import io,os,csv,glob,re,hashlib,datetime,urllib.request,collections
HOY=datetime.date.today().isoformat()
COLS=['ad_archive_id','page_id','anunciante','pos','total_pos','cuadrante','dias_corriendo',
      'replicas','archivo','titulo','descripcion','cta','destino','texto_principal','fecha_cosecha']
def cuad(pos,tot,d):
    arriba = pos <= max(tot/2.0,3)
    if arriba and d>=21: return 'GANADOR_ESTABLECIDO'
    if arriba: return 'WINNER_CALIENTE'
    if d>=21: return 'DESCARTE_VIEJO_ABAJO'
    return 'EN_PRUEBA'
prev=set()
if os.path.exists('_PROCESADOS.txt'):
    prev={l.strip() for l in io.open('_PROCESADOS.txt',encoding='utf-8') if l.strip()}
hashes={}
for root,_,fs in os.walk('_IMG'):
    for fn in fs:
        p=os.path.join(root,fn)
        hashes[hashlib.md5(open(p,'rb').read()).hexdigest()]=p
rows=[];ok=0;err=0;dup=0;desc=0
for f in sorted(glob.glob('_RAW/masivo/*.txt')):
    C=None
    for ln in io.open(f,encoding='utf-8'):
        p=ln.rstrip('\n').split('|')
        if p[0]=='#P': C=p; continue
        if p[0]!='A' or not C: continue
        aid,cc,d,pos,tot=p[1],int(p[2]),int(p[3]),int(p[4]),int(p[5])
        q=cuad(pos,tot,d)
        if q=='DESCARTE_VIEJO_ABAJO': desc+=1; continue
        if aid in prev: continue
        fp=p[6].split('~')
        if len(fp)<6: continue
        url=('https://%s/v/%s/%s?stp=%s&_nc_cat=%s&ccb=%s&_nc_sid=%s&_nc_ohc=%s&_nc_oc=%s'
             '&_nc_zt=%s&_nc_ht=%s&_nc_gid=%s&_nc_ss=%s&oh=%s&oe=%s')%(
             C[3],C[11],fp[0],C[5],fp[1],C[6],C[7],fp[2],fp[3],C[8],C[9],C[4],C[10],fp[4],fp[5])
        sub=os.path.join('_IMG',re.sub('[^0-9A-Za-z_-]','_',C[2])[:38].strip('_'))
        if not os.path.isdir(sub): os.makedirs(sub)
        dest=os.path.join(sub,'%02d_%s.jpg'%(pos,aid))
        if not os.path.exists(dest):
            try:
                rq=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
                data=urllib.request.urlopen(rq,timeout=30).read()
            except Exception as e:
                print('  ERR %s %s'%(aid,str(e)[:40])); err+=1; continue
            h=hashlib.md5(data).hexdigest()
            if h in hashes: dup+=1; prev.add(aid); continue
            open(dest,'wb').write(data); hashes[h]=dest; ok+=1
        prev.add(aid)
        rows.append([aid,C[1],C[2],pos,tot,q,d,cc,dest.replace(os.sep,'/'),
                     p[7],p[8],p[9],p[10],p[11] if len(p)>11 else '',HOY])
io.open('_PROCESADOS.txt','w',encoding='utf-8').write('\n'.join(sorted(prev)))
nuevo=not os.path.exists('_BANCO.csv')
with io.open('_BANCO.csv','a',encoding='utf-8',newline='') as f:
    w=csv.writer(f)
    if nuevo: w.writerow(COLS)
    w.writerows(rows)
print('bajadas=%d  dup=%d  descartadas_por_cuadrante=%d  err=%d  filas=%d'%(ok,dup,desc,err,len(rows)))
