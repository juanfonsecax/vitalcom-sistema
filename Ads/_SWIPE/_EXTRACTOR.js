// EXTRACTOR SWIPE FILE — pegar en mcp__Claude_Browser__javascript_tool
// REQUISITO: el tab debe estar en facebook.com (navegar primero a cualquier URL de Ad Library).
// Define window.__T (datos), window.__C (comprimir URL) y window.__M (salida masiva).
(async()=>{
window.__T=async function(pid,N){
 const u='https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=GT&media_type=image_and_meme&search_type=page&sort_data[mode]=total_impressions&sort_data[direction]=desc&view_all_page_id='+pid;
 let t; try{t=await (await fetch(u,{credentials:'include'})).text();}catch(e){return {pid:pid,err:'fetch'};}
 const doc=new DOMParser().parseFromString(t,'text/html');
 let conn=null;
 for(const s of doc.querySelectorAll('script')){
   const c=s.textContent; if(!c||c.indexOf('search_results_connection')<0) continue;
   let J; try{J=JSON.parse(c);}catch(e){continue;}
   const st=[J];
   while(st.length){const o=st.pop();
     if(o&&typeof o==='object'){ if(o.search_results_connection){conn=o.search_results_connection;break;}
       for(const k in o) if(o[k]&&typeof o[k]==='object') st.push(o[k]); }}
   if(conn)break;
 }
 if(!conn) return {pid:pid,err:'nodata'};
 const HOY=Date.now()/1000, R=[];
 (conn.edges||[]).forEach((ed,gi)=>{
   const cr=(ed.node||{}).collated_results||[]; const r=cr[0]; if(!r) return;
   const sn=r.snapshot||{};
   const im=(sn.images||[]).map(x=>x.resized_image_url||x.original_image_url).filter(Boolean);
   (sn.cards||[]).forEach(c=>{const v=c.resized_image_url||c.original_image_url; if(v)im.push(v);});
   if(!im[0]) return;
   R.push({id:r.ad_archive_id,grupo:gi+1,ngrp:cr.length,cc:r.collation_count||cr.length||1,
     d:r.start_date?Math.round((HOY-r.start_date)/86400):null,
     pag:sn.page_name||'',tit:sn.title||'',des:sn.link_description||'',cta:sn.cta_text||'',
     dst:(sn.link_url||'').replace(/^https?:\/\//,'').split('/')[0],
     body:((sn.body&&sn.body.text)||'').replace(/\s+/g,' ').trim(),img:im[0]});
 });
 return {pid:pid,tot:conn.count,grupos:conn.edges.length,ads:R.slice(0,N)};
};
window.__C=function(u){
 const m=u.match(/^https:\/\/([^\/]+)\/v\/([^\/]+)\/([^?]+)\?(.*)$/); if(!m) return null;
 const q={}; m[4].split('&').forEach(kv=>{const i=kv.indexOf('='); q[kv.slice(0,i)]=kv.slice(i+1);});
 return {host:m[1],seg:m[2],file:m[3],
   v:[q._nc_cat,q._nc_ohc,q._nc_oc,q.oh,q.oe].join('~'),
   c:[q.stp,q.ccb,q._nc_sid,q._nc_zt,q._nc_ht,q._nc_gid,q._nc_ss].join('~')};
};
window.__M=async function(pid,N){
 const o=await window.__T(pid,999);
 if(!o.ads||!o.ads.length) return '';
 const P=(s,n)=>(s||'').replace(/[^\x20-\x7E]/g,'').replace(/\s+/g,' ').replace(/\|/g,'/').replace(/~/g,'-').trim().slice(0,n);
 const T=o.ads.length, c0=window.__C(o.ads[0].img); if(!c0) return '';
 const k=c0.c.split('~');
 const L=['#P|'+pid+'|'+P(o.ads[0].pag,26)+'|'+c0.host+'|'+k[5]+'|'+k[0]+'|'+k[1]+'|'+k[2]+'|'+k[3]+'|'+k[4]+'|'+k[6]+'|'+c0.seg];
 o.ads.slice(0,N).forEach(a=>{
   const c=window.__C(a.img); if(!c) return;
   const arriba=a.grupo<=Math.max(T/2,3);
   if(!arriba && (a.d||0)>=21) return;   // unico descarte: viejo y abajo
   L.push(['A',a.id,a.cc,a.d,a.grupo,T,c.file+'~'+c.v,P(a.tit,44),P(a.des,34),P(a.cta,18),a.dst,P(a.body,70)].join('|'));
 });
 return L.join('\n');
};
// USO: procesar 2-3 paginas por llamada
const r=[];
for(const p of ['PAGE_ID_1','PAGE_ID_2']){ r.push(await window.__M(p,18)); await new Promise(x=>setTimeout(x,500)); }
return r.filter(Boolean).join('\n');
})()
