import json
from simular_arbol import *
fallas=[]
def chequear(nombre,a):
    r=diagnosticar(a)
    act=[m['id'] for m in r['modulos'] if m['estado']=='activo']
    pos={i:n for n,i in enumerate([m['id'] for m in r['modulos']])}
    for m in r['modulos']:
        if m['estado']!='activo': continue
        for pr in CATD[m['id']]['prereq']:
            alts=[x for x in pr.split('|') if x in pos]
            if alts and not any(pos[x]<pos[m['id']] for x in alts): fallas.append((nombre,'orden',m['id'],pr))
            if not alts and not any(S_ok for S_ok in []): pass
    ids={m['id'] for m in r['modulos']}
    sx={m['id'] for m in r['no_recomendados']}
    if ids & sx: fallas.append((nombre,'activo y X',ids&sx))
    if not act: fallas.append((nombre,'sin módulos activos'))
    return r
for n,a in CASOS.items(): chequear(n,a)
base=dict(tamano='50-249',n_operadores=10,giro='manufactura',alcance='linea_area',secundarios=[],datos='excel',volumen='50-200',tipo_dato='variable',fase_actual='D',objetivos=[],equipo='2-4',semanas='4-12',puede_experimentar='si')
n=0
for s in T['sintomas']:
    for fase in T['fases']:
        for tam in ('lt10','250+'):
            a=dict(base,sintoma=s,fase_actual=fase,tamano=tam); chequear(f'{s}/{fase}/{tam}',a); n+=1
print(n,'combinaciones probadas; fallas:',len(fallas))
for f in fallas[:15]: print(f)
# aserciones de casos clave
r=diagnosticar(CASOS['JANA (validar el efecto del código LISP)'])
assert any('menos de 3 operadores' in w for w in r['advertencias'])
assert {'condicion','operador','tiempo','errores','tamano_unidad'}<={c['nombre'] for c in r['hoja_datos_sugerida']}
r=diagnosticar(CASOS['Optimizar con 5 factores sin poder experimentar'])
assert {'DOE-FRAC','RSM'}<={m['id'] for m in r['no_recomendados']}
r=diagnosticar(dict(base,sintoma='S13',f_s13_factores='5+',f_s13_optimizar='si',fase_actual='D'))
assert {'DOE-FRAC','RSM','MSA-VAR'}<={m['id'] for m in r['modulos'] if m['estado']=='activo'}
print('aserciones OK')
