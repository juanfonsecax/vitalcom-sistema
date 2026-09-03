# -*- coding: utf-8 -*-
"""Borra imagenes identicas (mismo hash) y limpia filas huerfanas del CSV. Correr tras bajar.py"""
import io,csv,os,hashlib,collections
h=collections.defaultdict(list)
for root,_,fs in os.walk('_IMG'):
    for fn in fs:
        p=os.path.join(root,fn)
        h[hashlib.md5(open(p,'rb').read()).hexdigest()].append(p)
rep={}
bor=0
for g in h.values():
    if len(g)<2: continue
    g.sort(); rep[g[0].replace(os.sep,'/')]=len(g)
    for x in g[1:]: os.remove(x); bor+=1
rows=list(csv.DictReader(io.open('_ADS.csv',encoding='utf-8')))
cols=list(rows[0].keys())
viv=[]
for r in rows:
    if not os.path.exists(r['archivo']): continue
    n=rep.get(r['archivo'])
    if n:
        try: r['replicas_misma_imagen']=max(int(r.get('replicas_misma_imagen') or 1),n)
        except: r['replicas_misma_imagen']=n
    viv.append(r)
with io.open('_ADS.csv','w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerows(viv)
print('dedup: %d borradas | %d creativos unicos'%(bor,len(viv)))
