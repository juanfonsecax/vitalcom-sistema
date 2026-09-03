# -*- coding: utf-8 -*-
"""Integra _RAW/copies/*.txt -> _COPIES.csv (llave ad_archive_id)"""
import io,csv,glob,os
COLS=['ad_archive_id','pagina_real','replicas','dias','pos_grupo','titulo','descripcion','cta','destino','texto_principal']
rows={}
if os.path.exists('_COPIES.csv'):
    for r in csv.DictReader(io.open('_COPIES.csv',encoding='utf-8')): rows[r['ad_archive_id']]=[r[c] for c in COLS]
n=0
for f in sorted(glob.glob('_RAW/copies/*.txt')):
    for ln in io.open(f,encoding='utf-8'):
        p=ln.rstrip(chr(10)).split('|')
        if len(p)<10 or not p[0].isdigit(): continue
        rows[p[0]]=p[:10]; n+=1
with io.open('_COPIES.csv','w',encoding='utf-8',newline='') as f:
    w=csv.writer(f); w.writerow(COLS)
    for k in sorted(rows,key=lambda x:(rows[x][1],int(rows[x][4] or 99))): w.writerow(rows[k])
print('_COPIES.csv: %d filas (%d leidas)'%(len(rows),n))
