import json,sys
T=json.load(open('arbol_diagnostico.json',encoding='utf-8'))
CATD={c['id']:c for c in T['catalogo']}
ORDEN={c['id']:i for i,c in enumerate(T['catalogo'])}
FIDX={f:i for i,f in enumerate(T['fases'])}
RANK={'O':1,'R':2,'N':3,'P':3}
def match(c,a,act=None):
    for k,v in c.items():
        if k=='no':
            if match(v,a,act): return False
        elif k=='activo_alguno':
            if not act or not any(m in act for m in v): return False
        else:
            val=a.get(k)
            if isinstance(v,dict):
                for o,x in v.items():
                    if o=='in' and val not in x: return False
                    if o=='lt' and not(val is not None and val<x): return False
                    if o=='contiene' and not(isinstance(val,list) and x in val): return False
            elif val!=v: return False
    return True
def diagnosticar(a):
    S={}   # id -> dict(prio,motivos,lock)
    adv=[];notas=[];cols={};mins={}
    def activar(i,p,m):
        s=S.setdefault(i,dict(prio=None,motivos=[],lock=False))
        if s['prio']=='X' or s['lock']:
            s['silent']=False; return
        if s['prio'] is None or RANK[p]>RANK[s['prio']]: s['prio']=p
        if m and m not in s['motivos']: s['motivos'].append(m)
    def fijar(i,p,m):
        s=S.setdefault(i,dict(prio=None,motivos=[],lock=False))
        if s['prio'] is None: s['silent']=True
        s['prio']=p; s['lock']=True
        if m and m not in s['motivos']: s['motivos'].append(m)
    fi=FIDX.get(a.get('fase_actual','D'),0)
    def act_set(): return {i for i,s in S.items() if s['prio'] in ('N','R','P') and any(FIDX[f]>=fi for f in CATD[i]['fases'])}
    def aplicar(r,deg=False):
        for i,p,m in r.get('activar',[]):
            if deg: p='O'
            activar(i,p,('síntoma secundario: '+m) if deg else m)
        if deg: return
        for i,p,m in r.get('fijar',[]): fijar(i,p,m)
        adv.extend(x for x in r.get('advertir',[]) if x not in adv)
        if r.get('nota') and r['nota'] not in notas: notas.append(r['nota'])
        for c in r.get('columnas',[]): cols.setdefault(c['nombre'],c)
        mins.update(r.get('minimos',{}))
    sec=a.get('secundarios') or []
    for r in T['reglas']:
        if r['etapa']==1:
            s=r['sintoma_base']
            if a.get('sintoma')==s: aplicar(r)
            elif s in sec: aplicar(r,deg=True)
    for r in T['reglas']:
        if r['etapa']==2 and match(r['si'],a): aplicar(r)
    def prereqs():
        ch=True
        while ch:
            ch=False
            for i in sorted(act_set(),key=lambda x:ORDEN[x]):
                for pr in CATD[i]['prereq']:
                    alts=pr.split('|')
                    if a.get('tipo_dato')=='atributo' and any(x.startswith('MSA-') for x in alts): alts=alts[::-1]
                    ok=any(S.get(x,{}).get('prio') in ('N','R','P') or (S.get(x,{}).get('prio')=='O' and S[x]['lock']) for x in alts)
                    if not ok:
                        cand=[x for x in alts if S.get(x,{}).get('prio')!='X']
                        if cand:
                            S.setdefault(cand[0],dict(prio=None,motivos=[],lock=False))
                            S[cand[0]]['prio']='P'; S[cand[0]]['motivos'].append('prerrequisito de '+i); ch=True
    prereqs()
    for r in T['reglas']:
        if r['etapa']==3 and match(r['si'],a,act_set()): aplicar(r)
    prereqs()
    mods=[];sug=[];nor=[]
    for i,s in S.items():
        c=CATD[i]; p=s['prio']
        if s.get('silent') and p in ('O','X'): continue
        if p in ('O',): sug.append(dict(id=i,nombre=c['nombre'],motivos=s['motivos']));continue
        if p=='X': nor.append(dict(id=i,nombre=c['nombre'],motivos=s['motivos']));continue
        if c['min_tamano'] and False: pass
        fs=[FIDX[f] for f in c['fases']]
        fut=[f for f in fs if f>=fi]
        if fut: fa=min(fut);est='activo';ver=False
        else: fa=max(fs);ver=(p=='P' or c.get('verificable'));est='activo' if ver else 'disponible'
        m=dict(id=i,nombre=c['nombre'],fase_asignada=T['fases'][fa],estado=est,prioridad=p,motivos=s['motivos'],tipo=c['tipo'],plantilla=c['plantilla'],datos_minimos=mins.get(i,c['datos_minimos']))
        if ver: m['verificar_fase_anterior']=True
        if est=='activo' and c['requiere_datos']: m['estado_datos']='esperando_datos' if a.get('datos')=='ninguno' else 'por_cargar'
        mods.append(m)
    if not any(m['estado']=='activo' for m in mods):
        prom=[m for m in mods if m['prioridad']=='N'] or mods
        for m in prom:
            m['estado']='activo';m['verificar_fase_anterior']=True
            if CATD[m['id']]['requiere_datos']: m['estado_datos']='esperando_datos' if a.get('datos')=='ninguno' else 'por_cargar'
        adv.append('Tu fase actual es posterior a las herramientas propias de este síntoma; se dejan activas para confirmar que ya se hicieron.')
    # orden topológico dentro de fase
    ids={m['id'] for m in mods}
    orden=[];vis=set()
    def visita(i):
        if i in vis: return
        vis.add(i)
        for pr in CATD[i]['prereq']:
            for x in pr.split('|'):
                if x in ids: visita(x)
        if CATD[i]['requiere_datos']:
            for x in ('HOJA-DATOS','MUESTREO'):
                if x in ids and x!=i: visita(x)
        orden.append(i)
    base=sorted([m for m in mods],key=lambda m:(FIDX[m['fase_asignada']],ORDEN[m['id']]))
    for m in base: visita(m['id'])
    pos={i:n for n,i in enumerate(orden)}
    mods.sort(key=lambda m:pos[m['id']])
    vmax=T['volumen_max'].get(a.get('volumen'))
    pend=[]
    for m in mods:
        if m['estado']!='activo': continue
        c=CATD[m['id']]
        if c['requiere_datos']:
            pend.append(dict(modulo=m['id'],minimos=m['datos_minimos']))
            if c['min_n'] and vmax is not None and a.get('datos')!='ninguno' and vmax<c['min_n']:
                w=f"{m['id']} necesita al menos {c['min_n']} datos y hoy hay a lo sumo {vmax if vmax<10**8 else 'muchos'}."
                if w not in adv: adv.append(w)
    act=[m for m in mods if m['estado']=='activo']
    sig=None
    for m in act:
        if m['prioridad'] in('N','P') or m.get('verificar_fase_anterior'): sig=m['id'];break
    if a.get('datos')=='ninguno' and any(m['id']=='HOJA-DATOS' for m in act): sig='HOJA-DATOS'
    return dict(perfil_empresa={k:a.get(k) for k in T['esquema_salida']['perfil_empresa']},
        diagnostico={k:a.get(k) for k in T['esquema_salida']['diagnostico']},
        modulos=mods,sugeridos=sug,no_recomendados=nor,hoja_datos_sugerida=list(cols.values()),
        advertencias=adv,notas=notas,pendientes_datos=pend,ruta_sugerida=[m['id'] for m in act],siguiente_paso=sig,
        datos_fijos={k:None for k in T['cuestionario'][-1]['campos']},version_perfil=1)
CASOS={
'JANA (validar el efecto del código LISP)':dict(tamano='10-49',n_operadores=2,giro='ingenieria_documentacion',alcance='puntual',sintoma='S14',secundarios=['S07'],datos='manual',volumen='50-200',tipo_dato='mixto',fase_actual='M',objetivos=['tiempo','errores'],equipo='1',semanas='4-12',puede_experimentar='si',f_s14_diseno='cruzado'),
'Línea parada':dict(tamano='50-249',n_operadores=12,giro='manufactura',alcance='linea_area',sintoma='S04',secundarios=['S02'],datos='excel',volumen='50-200',tipo_dato='variable',fase_actual='M',objetivos=['entrega'],equipo='2-4',semanas='4-12',f_s04_registro='parcial',f_s04_cuello='si',f_s04_cliente='si',f_s02_vsm='no',f_s02_demanda='si'),
'Defectos con medición continua (fase Analizar)':dict(tamano='250+',n_operadores=30,giro='manufactura',alcance='linea_area',sintoma='S07',secundarios=[],datos='sistema',volumen='gt200',tipo_dato='variable',fase_actual='A',objetivos=['errores','costo'],equipo='5+',semanas='gt12',f_s07_definido='si'),
'Proyecto sin definir en empresa pequeña':dict(tamano='lt10',n_operadores=4,giro='servicios',alcance='puntual',sintoma='S01',secundarios=[],datos='ninguno',fase_actual='D',objetivos=['satisfaccion'],equipo='1',semanas='lt4',f_s01_req='parcial'),
'Optimizar con 5 factores sin poder experimentar':dict(tamano='50-249',n_operadores=8,giro='manufactura',alcance='linea_area',sintoma='S13',secundarios=[],datos='excel',volumen='15-50',tipo_dato='variable',fase_actual='A',objetivos=['costo'],equipo='2-4',semanas='4-12',puede_experimentar='no',f_s13_factores='5+',f_s13_optimizar='si'),
}
if __name__=='__main__':
    res={}
    for n,a in CASOS.items():
        r=diagnosticar(a); res[n]=r
        print('\n=====',n,'=====')
        for m in r['modulos']: print(f"  {m['fase_asignada']} {m['prioridad']} {m['id']:<14} {m['estado']}{' (verificar)' if m.get('verificar_fase_anterior') else ''}{' ['+m['estado_datos']+']' if m.get('estado_datos') else ''} | {'; '.join(m['motivos'][:2])}")
        print('  sugeridos:',[s['id'] for s in r['sugeridos']]);print('  no recomendados:',[s['id'] for s in r['no_recomendados']])
        print('  columnas:',[c['nombre'] for c in r['hoja_datos_sugerida']]);print('  siguiente:',r['siguiente_paso'])
        for w in r['advertencias']: print('  AVISO:',w)
        for w in r['notas']: print('  NOTA:',w)
    json.dump(res,open('casos_prueba_resultado.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
