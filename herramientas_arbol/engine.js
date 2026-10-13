function crearMotor(T){
  const CATD={},ORDEN={},FIDX={};
  T.catalogo.forEach((c,i)=>{CATD[c.id]=c;ORDEN[c.id]=i;});
  T.fases.forEach((f,i)=>{FIDX[f]=i;});
  const RANK={O:1,R:2,N:3,P:3};
  const nz=v=>v===undefined?null:v;
  function match(c,a,act){
    for(const k of Object.keys(c)){
      const v=c[k];
      if(k==='no'){ if(match(v,a,act)) return false; }
      else if(k==='activo_alguno'){ if(!act||!v.some(m=>act.has(m))) return false; }
      else{
        const val=nz(a[k]);
        if(v!==null&&typeof v==='object'&&!Array.isArray(v)){
          for(const o of Object.keys(v)){
            const x=v[o];
            if(o==='in'&&!x.includes(val)) return false;
            if(o==='lt'&&!(val!==null&&val<x)) return false;
            if(o==='contiene'&&!(Array.isArray(val)&&val.includes(x))) return false;
          }
        } else if(val!==v) return false;
      }
    }
    return true;
  }
  function diagnosticar(a){
    const S=new Map(); const adv=[],notas=[]; const cols=new Map(); const mins={};
    const fi=(a.fase_actual in FIDX)?FIDX[a.fase_actual]:0;
    const getS=i=>{ if(!S.has(i)) S.set(i,{prio:null,motivos:[],lock:false}); return S.get(i); };
    function activar(i,p,m){
      const s=getS(i);
      if(s.prio==='X'||s.lock){ s.silent=false; return; }
      if(s.prio===null||RANK[p]>RANK[s.prio]) s.prio=p;
      if(m&&!s.motivos.includes(m)) s.motivos.push(m);
    }
    function fijar(i,p,m){
      const s=getS(i);
      if(s.prio===null) s.silent=true;
      s.prio=p; s.lock=true;
      if(m&&!s.motivos.includes(m)) s.motivos.push(m);
    }
    const actSet=()=>{ const r=new Set(); for(const [i,s] of S){ if(['N','R','P'].includes(s.prio)&&CATD[i].fases.some(f=>FIDX[f]>=fi)) r.add(i);} return r; };
    function aplicar(r,deg){
      for(const [i,p0,m] of (r.activar||[])) activar(i,deg?'O':p0,deg?('síntoma secundario: '+m):m);
      if(deg) return;
      for(const [i,p,m] of (r.fijar||[])) fijar(i,p,m);
      for(const x of (r.advertir||[])) if(!adv.includes(x)) adv.push(x);
      if(r.nota&&!notas.includes(r.nota)) notas.push(r.nota);
      for(const c of (r.columnas||[])) if(!cols.has(c.nombre)) cols.set(c.nombre,c);
      Object.assign(mins,r.minimos||{});
    }
    const sec=a.secundarios||[];
    for(const r of T.reglas){
      if(r.etapa===1){
        const s=r.sintoma_base;
        if(a.sintoma===s) aplicar(r,false); else if(sec.includes(s)) aplicar(r,true);
      }
    }
    for(const r of T.reglas){ if(r.etapa===2&&match(r.si,a)) aplicar(r,false); }
    function prereqs(){
      let ch=true;
      while(ch){
        ch=false;
        const lista=[...actSet()].sort((x,y)=>ORDEN[x]-ORDEN[y]);
        for(const i of lista){
          for(const pr of CATD[i].prereq){
            let alts=pr.split('|');
            if(a.tipo_dato==='atributo'&&alts.some(x=>x.startsWith('MSA-'))) alts=alts.slice().reverse();
            const ok=alts.some(x=>{ const s=S.get(x); return s&&(['N','R','P'].includes(s.prio)||(s.prio==='O'&&s.lock)); });
            if(!ok){
              const cand=alts.filter(x=>{ const s=S.get(x); return !(s&&s.prio==='X'); });
              if(cand.length){ const s=getS(cand[0]); s.prio='P'; s.motivos.push('prerrequisito de '+i); ch=true; }
            }
          }
        }
      }
    }
    prereqs();
    for(const r of T.reglas){ if(r.etapa===3&&match(r.si,a,actSet())) aplicar(r,false); }
    prereqs();
    let mods=[]; const sug=[],nor=[];
    for(const [i,s] of S){
      const c=CATD[i],p=s.prio;
      if(s.silent&&(p==='O'||p==='X')) continue;
      if(p==='O'){ sug.push({id:i,nombre:c.nombre,motivos:s.motivos}); continue; }
      if(p==='X'){ nor.push({id:i,nombre:c.nombre,motivos:s.motivos}); continue; }
      const fs=c.fases.map(f=>FIDX[f]); const fut=fs.filter(f=>f>=fi);
      let fa,est,ver=false;
      if(fut.length){ fa=Math.min(...fut); est='activo'; }
      else{ fa=Math.max(...fs); ver=(p==='P'||!!c.verificable); est=ver?'activo':'disponible'; }
      const m={id:i,nombre:c.nombre,fase_asignada:T.fases[fa],estado:est,prioridad:p,motivos:s.motivos,tipo:c.tipo,plantilla:c.plantilla,datos_minimos:(i in mins)?mins[i]:c.datos_minimos};
      if(ver) m.verificar_fase_anterior=true;
      if(est==='activo'&&c.requiere_datos) m.estado_datos=(a.datos==='ninguno')?'esperando_datos':'por_cargar';
      mods.push(m);
    }
    if(!mods.some(m=>m.estado==='activo')){
      let prom=mods.filter(m=>m.prioridad==='N'); if(!prom.length) prom=mods;
      for(const m of prom){ m.estado='activo'; m.verificar_fase_anterior=true; if(CATD[m.id].requiere_datos) m.estado_datos=(a.datos==='ninguno')?'esperando_datos':'por_cargar'; }
      adv.push('Tu fase actual es posterior a las herramientas propias de este síntoma; se dejan activas para confirmar que ya se hicieron.');
    }
    const ids=new Set(mods.map(m=>m.id)); const orden=[],vis=new Set();
    function visita(i){
      if(vis.has(i)) return; vis.add(i);
      for(const pr of CATD[i].prereq) for(const x of pr.split('|')) if(ids.has(x)) visita(x);
      if(CATD[i].requiere_datos) for(const x of ['HOJA-DATOS','MUESTREO']) if(ids.has(x)&&x!==i) visita(x);
      orden.push(i);
    }
    const base=mods.slice().sort((x,y)=>(FIDX[x.fase_asignada]-FIDX[y.fase_asignada])||(ORDEN[x.id]-ORDEN[y.id]));
    for(const m of base) visita(m.id);
    const pos={}; orden.forEach((i,n)=>{pos[i]=n;});
    mods.sort((x,y)=>pos[x.id]-pos[y.id]);
    const vmax=T.volumen_max[a.volumen];
    const pend=[];
    for(const m of mods){
      if(m.estado!=='activo') continue;
      const c=CATD[m.id];
      if(c.requiere_datos){
        pend.push({modulo:m.id,minimos:m.datos_minimos});
        if(c.min_n&&vmax!==undefined&&a.datos!=='ninguno'&&vmax<c.min_n){
          const w=`${m.id} necesita al menos ${c.min_n} datos y hoy hay a lo sumo ${vmax<1e8?vmax:'muchos'}.`;
          if(!adv.includes(w)) adv.push(w);
        }
      }
    }
    const act=mods.filter(m=>m.estado==='activo');
    let sig=null;
    for(const m of act){ if(m.prioridad==='N'||m.prioridad==='P'||m.verificar_fase_anterior){ sig=m.id; break; } }
    if(a.datos==='ninguno'&&act.some(m=>m.id==='HOJA-DATOS')) sig='HOJA-DATOS';
    const pe={},dg={},df={};
    T.esquema_salida.perfil_empresa.forEach(k=>{pe[k]=nz(a[k]);});
    T.esquema_salida.diagnostico.forEach(k=>{dg[k]=nz(a[k]);});
    T.cuestionario[T.cuestionario.length-1].campos.forEach(k=>{df[k]=null;});
    return {perfil_empresa:pe,diagnostico:dg,modulos:mods,sugeridos:sug,no_recomendados:nor,hoja_datos_sugerida:[...cols.values()],advertencias:adv,notas:notas,pendientes_datos:pend,ruta_sugerida:act.map(m=>m.id),siguiente_paso:sig,datos_fijos:df,version_perfil:1};
  }
  return {diagnosticar,CATD};
}
if(typeof module!=='undefined') module.exports={crearMotor};
