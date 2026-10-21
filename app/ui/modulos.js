// Módulos del MVP en la interfaz: pestañas, diálogo sobre columnas, resultado y formatos (cabecera + tablas).
// Toda la lógica y los cálculos viven en Python; aquí solo se dibuja.

const P = { abiertas: [], activa: "hoja" };
const DIALOGO = ["ESTADISTICOS", "CORRIDA", "BOXPLOT", "PARETO", "ANOVA", "DISTRIB", "MSA-ATR", "SPC", "CAPACIDAD", "CORREL", "REGRESION", "DISENO-RSM", "FACTORIAL", "RSM", "OPTIMIZADOR", "ORDENAR", "REEMPLAZAR", "CALCULADORA", "PATRON", "ALEATORIOS", "RECODIFICAR", "APILAR", "DUPLICADOS", "PROBABILIDAD", "MSA-VAR", "HIPOTESIS", "ANOVA2", "TUKEY", "DIST-ID", "BOXCOX", "POTENCIA", "NOPARAM", "CHI2", "RENDIMIENTO"];
const FORMATO = ["HOJA-DATOS", "AMEF", "PLAN-CONTROL", "TABLERO", "OEE", "TAKT", "KANBAN", "CHARTER", "SIPOC", "ISHIKAWA", "CINCO-PQ", "SMED", "GANTT", "CUATRO-Q", "A3", "KAIZEN", "TARJETAS", "MUDAS", "KATA", "KANO", "QFD", "CTQ-TREE", "VSM", "TIEMPOS", "BALANCE", "TPM", "POKAYOKE", "CINCO-S", "GEMBA", "SCRUM", "LSW", "TRABAJO-EST", "DEF-PROBLEMA", "HOSHIN", "PMAPA", "TOC", "ESPAGUETI", "FINANZAS", "MUESTREO", "DESEMPENO", "CHECKLIST-FASE", "VISUAL", "FLUJO", "INTERESADOS", "RIESGOS", "BITACORA", "RACI", "LECCIONES", "VALOR-GANADO", "COSTO-CALIDAD", "JUSTIFICACION", "EDT", "CRONOGRAMA", "MONTECARLO", "ARBOL-DECISION", "FODA", "AFINIDAD", "ENFOQUE"];
const TITULOS = { "HOJA-DATOS": "Hoja de recolección", AMEF: "AMEF", "PLAN-CONTROL": "Plan de control", TABLERO: "Tablero semanal",
  OEE: "OEE", TAKT: "Takt time", KANBAN: "Kanban", CHARTER: "Acta del proyecto", SIPOC: "SIPOC", ISHIKAWA: "Ishikawa", "CINCO-PQ": "5 Porqués",
  SMED: "SMED", GANTT: "Gantt DMAIC", "CUATRO-Q": "4 Qs", A3: "Informe A3", KAIZEN: "Kaizen", TARJETAS: "Oportunidades", MUDAS: "Mudas", KATA: "Kata", KANO: "Kano", QFD: "QFD", "CTQ-TREE": "Árbol CTQ", VSM: "VSM", TIEMPOS: "Tiempos", "DEF-PROBLEMA": "Problema", HOSHIN: "Hoshin", PMAPA: "Mapa de proceso", TOC: "TOC", ESPAGUETI: "Espagueti", FINANZAS: "Finanzas", MUESTREO: "Muestreo", DESEMPENO: "DPMO y sigma", "CHECKLIST-FASE": "Checklist", VISUAL: "Andon", FLUJO: "Flujo continuo", INTERESADOS: "Interesados", RIESGOS: "Riesgos", BITACORA: "Bitácora", RACI: "RACI", LECCIONES: "Cierre", "VALOR-GANADO": "Valor ganado", "COSTO-CALIDAD": "Costo de calidad", JUSTIFICACION: "Justificación", EDT: "EDT", CRONOGRAMA: "Cronograma", MONTECARLO: "Monte Carlo", "ARBOL-DECISION": "Árbol de decisión", FODA: "FODA", AFINIDAD: "Afinidad", ENFOQUE: "Enfoque", BALANCE: "Balance",
  TPM: "TPM", POKAYOKE: "Poka Yoke", "CINCO-S": "5S", GEMBA: "Gemba", SCRUM: "Scrum", LSW: "LSW", "TRABAJO-EST": "Trabajo estándar" };
window.MODULOS = {};
DIALOGO.forEach(id => MODULOS[id] = () => dialogoModulo(id));
FORMATO.forEach(id => MODULOS[id] = () => abrirPestana(`fmt:${id}`, null));

// ---------- pestañas ----------
function pintarPestanas() {
  const nav = $("#pestanas"); nav.innerHTML = "";
  nav.append(el("button", { class: "pestana" + (P.activa === "hoja" ? " activa" : ""), "data-p": "hoja",
    onclick: () => activar("hoja") }, "Hoja de datos"));
  for (const a of P.abiertas) {
    nav.append(el("span", { class: "pestana" + (P.activa === a.id ? " activa" : ""), "data-p": a.id },
      el("button", { class: "pestana-t", onclick: () => activar(a.id), title: a.titulo }, a.titulo),
      el("button", { class: "pestana-x", "aria-label": "Cerrar", title: "Cerrar", onclick: () => cerrarPestana(a.id) }, "×")));
  }
}

function activar(id) {
  P.activa = id; document.getElementById("inicio")?.remove();   // abrir cualquier cosa cierra la pantalla de inicio
  if (!id.startsWith("graf:") && window.gSalirCinta && document.body.classList.contains("cinta-grafico")) gSalirCinta();
  if (window.barraContexto) setTimeout(() => barraContexto(id), 0);
  const enHoja = id === "hoja";
  $("#marco-hoja").hidden = !enHoja; $("#vista").hidden = enHoja;
  pintarPestanas();
  if (enHoja) { $("#hoja").focus(); return; }
  const a = P.abiertas.find(x => x.id === id);
  if (id.startsWith("res:")) pintarResultado(a.res);
  else if (id.startsWith("graf:")) pintarGraficaEdicion(a.res);
  else if (id === "vis:TABLERO") pintarTableroVista(true);
  else if (id === "vis:AYUDA") pintarAyudaVista();
  else pintarFormato(id.slice(4));
}

function abrirPestana(id, res, titulo) {
  if (!P.abiertas.find(x => x.id === id)) {
    const t = titulo || (res ? res.titulo : TITULOS[id.slice(4)]);
    P.abiertas.push({ id, titulo: t, res });
  }
  activar(id);
}

function cerrarPestana(id) {
  const c = P.abiertas.find(x => x.id === id); if (c && window.U2) U2.cerradas.push(c);
  P.abiertas = P.abiertas.filter(x => x.id !== id);
  activar(P.activa === id ? (P.abiertas.length ? P.abiertas[P.abiertas.length - 1].id : "hoja") : P.activa);
}
window.cerrarTodas = () => { P.abiertas = []; activar("hoja"); };

// ---------- diálogo sobre columnas ----------
async function dialogoModulo(id, previo) {
  const r = await api().dialogo_modulo(id);
  if (r.error) return registrarSesion(r.sesion);
  const d = r.dialogo, cuerpo = el("div", { class: "formulario dialogo-mod" }), ctl = {};
  for (const c of d.campos) {
    let input;
    if (c.tipo === "col") {
      const cols = d.columnas.filter(x => !c.filtro || x.tipo === c.filtro);
      input = el("select", { name: c.campo }, el("option", { value: "" }, c.opcional ? "(ninguna)" : "Elige una columna"),
        cols.map(x => el("option", { value: x.j, selected: c.defecto === x.j }, `${x.etiqueta} ${x.nombre}`.trim())));
    } else if (c.tipo === "opcion") {
      input = el("select", { name: c.campo }, c.opciones.map(([v, t]) => el("option", { value: v, selected: String(c.defecto) === v }, t)));
    } else if (c.tipo === "multi" || c.tipo === "cols") {
      const ops = c.tipo === "multi" ? c.opciones.map(([v, t]) => [v, t])
        : d.columnas.filter(x => !c.filtro || x.tipo === c.filtro).map(x => [String(x.j), `${x.etiqueta} ${x.nombre}`.trim()]);
      const def = (c.defecto || []).map(String);
      const caja = el("div", { class: "multi", "data-campo": c.campo }, ops.map(([v, t]) =>
        el("label", { class: "casilla" }, el("input", { type: "checkbox", value: v, checked: def.includes(v) }), " " + t)));
      cuerpo.append(el("div", { class: "grupo-multi" }, el("span", {}, c.etiqueta), caja)); ctl[c.campo] = [c, caja]; continue;
    } else if (c.tipo === "bool") {
      input = el("input", { type: "checkbox", name: c.campo, checked: !!c.defecto });
      cuerpo.append(el("label", { class: "casilla" }, input, " " + c.etiqueta)); ctl[c.campo] = [c, input]; continue;
    } else {
      input = el("input", { name: c.campo, value: c.defecto ?? "", autocomplete: "off", class: c.tipo === "numero" ? "num" : "" });
    }
    ctl[c.campo] = [c, input];
    cuerpo.append(el("label", {}, el("span", {}, c.etiqueta), input));
  }
  if (previo && previo.parametros) {                 // «Modificar análisis»: precarga lo que se usó, ubicando las columnas por su nombre
    const porNombre = n => (d.columnas.find(x => x.nombre === n || `C${x.j + 1}` === n) || {}).j;
    for (const [k, [c, i]] of Object.entries(ctl)) {
      const v = previo.parametros[k], col = (previo.columnas || {})[k];
      if (c.tipo === "col") { const j = col != null ? porNombre(col) : null; i.value = j != null ? String(j) : ""; }
      else if (c.tipo === "cols") { const js = (col || []).map(porNombre).filter(x => x != null).map(String); i.querySelectorAll("input").forEach(x => { x.checked = js.includes(x.value); }); }
      else if (c.tipo === "multi") { const vs = (v || []).map(String); i.querySelectorAll("input").forEach(x => { x.checked = vs.includes(x.value); }); }
      else if (c.tipo === "bool") i.checked = !!v;
      else if (v != null) i.value = String(v);
    }
  }
  const error = el("p", { class: "error-dialogo", role: "alert" });
  cuerpo.append(error);
  dialogo(previo ? `${d.titulo} (modificar)` : d.titulo, cuerpo, async () => {
    const params = {};
    for (const [k, [c, i]] of Object.entries(ctl)) {
      const marcados = () => [...i.querySelectorAll("input:checked")].map(x => x.value);
      params[k] = c.tipo === "bool" ? i.checked : c.tipo === "col" ? (i.value === "" ? null : +i.value)
        : c.tipo === "multi" ? marcados() : c.tipo === "cols" ? marcados().map(Number) : i.value;
    }
    const res = await aplicarProyecto(api().ejecutar_modulo(id, params));
    if (res.error) { error.textContent = res.sesion[0].texto.replace(/^[^:]+: /, ""); return false; }
    if (res.resultado) abrirPestana(`res:${res.resultado.uid}`, res.resultado); else activar("hoja");
  });
  document.querySelector(".dialogo").classList.add("ancho");
}

// ---------- resultado ----------
const CON_GRAFICA_EDITABLE = ["PARETO", "DISTRIB", "BOXPLOT", "CORRIDA", "SPC", "CAPACIDAD", "REGRESION", "RSM", "FACTORIAL"];
function pintarResultado(res) {
  const v = $("#vista"); v.innerHTML = "";
  const barra = el("div", { class: "vista-barra" }, el("span", { class: "vista-titulo" }, res.titulo),
    res.etiqueta ? el("span", { class: "etiqueta-sint", title: "Este resultado se calculó con datos sintéticos" }, res.etiqueta) : "",
    el("span", { class: "vista-fecha" }, res.fecha),
    res.definicion ? el("button", { class: "boton chico", title: "Vuelve a correr el análisis con los datos actuales de la hoja",
      onclick: async () => { const r = await aplicarProyecto(api().repetir_resultado(res.uid)); if (!r.error && r.resultado) abrirPestana(`res:${r.resultado.uid}`, r.resultado); } }, "Repetir con datos actuales") : "",
    res.definicion && res.definicion.congelado ? el("button", { class: "boton chico", title: "Vuelve a correr el análisis con la copia congelada de sus entradas (no con la hoja actual) y comprueba su huella SHA-256",
      onclick: async () => { const r = await aplicarProyecto(api().reproducir_resultado(res.uid)); if (!r.error && r.resultado) abrirPestana(`res:${r.resultado.uid}`, r.resultado); } }, "Reproducir versión guardada") : "",
    el("span", { class: "res-estado", id: "res-estado" }),
    el("button", { class: "boton chico", title: "Copia tablas y conclusiones para pegarlas en Excel o en un reporte",
      onclick: async () => copiarTexto(await api().texto_resultado(res.uid)) }, "Copiar"),
    ["ESTADISTICOS", "CORREL", "REGRESION", "CAPACIDAD", "DISTRIB"].includes(res.modulo) ? el("button", { class: "boton chico",
      title: "Excel con las fórmulas equivalentes y una columna para capturar lo que da Minitab", onclick: () => aplicarProyecto(api().exportar_verificacion(res.uid)) }, "Verificar en Excel…") : "",
    el("button", { class: "boton chico", onclick: () => aplicarProyecto(api().exportar_resultado(res.uid)) }, "Exportar…"),
    el("button", { class: "boton chico", onclick: async () => { await aplicarProyecto(api().borrar_resultado(res.uid)); cerrarPestana(`res:${res.uid}`); } }, "Eliminar"));
  const cuerpo = el("div", { class: "resultado" });
  for (const a of res.avisos) cuerpo.append(el("p", { class: "aviso-res" }, a));
  let kg = -1;
  for (const b of res.bloques) {
    if (b.tipo === "grafica") kg++;
    if (b.tipo === "grafica" && b.inter && window.Plotly && window.graficaInteractiva && leerPref("graficas_int") !== "0") { cuerpo.append(graficaInteractiva(res, kg, b)); continue; }
    if (b.tipo === "grafica") {
      const g = el("div", { class: "grafica" }); g.innerHTML = b.svg; cuerpo.append(g);
      if (!b.inter && CON_GRAFICA_EDITABLE.includes(res.modulo))          // resultado anterior a la gráfica editable (v0.25)
        cuerpo.append(el("p", { class: "texto-res nota" }, "Esta gráfica es una imagen fija de una versión anterior. Usa «Repetir con datos actuales» para obtener la versión editable (estilo, color y pestaña Gráfico)."));
    }
    else if (b.tipo === "texto") cuerpo.append(el("p", { class: "texto-res " + b.clase }, b.texto));
    else if (b.tipo === "tabla") {
      cuerpo.append(el("div", { class: "tabla-marco" }, el("div", { class: "tabla-titulo" }, b.titulo),
        el("table", { class: "tabla-res" }, el("thead", {}, el("tr", {}, b.cabeza.map((h, j) => el("th", { class: b.alinear[j] === "d" ? "d" : "" }, h)))),
          el("tbody", {}, b.filas.map(f => el("tr", {}, f.map((x, j) => el("td", { class: b.alinear[j] === "d" ? "d" : "" }, String(x)))))))));
    }
  }
  v.append(barra, cuerpo);
  api().estado_resultado(res.uid).then(e => { const b = document.getElementById("res-estado"); if (!b || !e || e.estado === "sin_copia") return;
    b.className = "res-estado " + e.estado; b.textContent = e.estado === "vigente" ? `Vigente · huella ${e.huella}` : `Desactualizado: ${e.motivo}`;
    b.title = e.estado === "vigente" ? `Los datos de la hoja coinciden con la copia congelada (motor v${e.version}).` : "El resultado sigue consultable; «Repetir con datos actuales» lo recalcula y «Reproducir versión guardada» rehace el original."; });
}

async function listaResultados() {
  const lista = await api().resultados();
  const cuerpo = el("div", { class: "lista-res" }, lista.length ? lista.map(r => el("div", { class: "fila-res" },
    el("span", {}, r.titulo), el("span", { class: "vista-fecha" }, r.fecha),
    el("button", { class: "boton chico", onclick: async () => { cerrarVelo(); abrirPestana(`res:${r.uid}`, await api().resultado(r.uid)); } }, "Abrir")))
    : el("p", { class: "vacio" }, "Todavía no hay resultados en este proyecto."));
  dialogo("Resultados del proyecto", cuerpo, () => true, "Cerrar");
  document.querySelector(".dialogo").classList.add("ancho");
}
window.listaResultados = listaResultados;

// ---------- formatos ----------
const F = {};   // id -> {espec, datos, calc, fijos}

async function pintarFormato(id) {
  const r = await api().abrir_formato(id);
  F[id] = r; dibujarFormato(id);
}

function opcionesCol(espec, filtro, valor) {
  const cols = espec.columnas_hoja.filter(c => !filtro || c.tipo === filtro);
  return [el("option", { value: "" }, "(ninguna)"), ...cols.map(c => el("option", { value: c.nombre, selected: c.nombre === valor }, c.nombre))];
}

function control(espec, c, valor, alCambiar) {
  let i;
  if (c.tipo === "opcion") i = el("select", {}, c.opciones.map(([v, t]) => el("option", { value: v, selected: v === valor }, t)));
  else if (c.tipo === "col") i = el("select", {}, opcionesCol(espec, c.filtro, valor));
  else if (c.tipo === "largo") { i = el("textarea", { rows: 2, spellcheck: "true" }); i.value = valor ?? ""; }
  else i = el("input", { value: valor ?? "", autocomplete: "off", spellcheck: "false", class: ["numero", "entero"].includes(c.tipo) ? "num" : "" });
  if (c.campo) i.name = c.campo;
  if (c.lectura) { i.readOnly = true; i.tabIndex = -1; i.classList.add("fijo-in"); i.title = i.value; }
  i.addEventListener("change", alCambiar);
  return i;
}

function dibujarFormato(id) {
  const { espec, datos, calc, fijos } = F[id];
  if (id === "QFD" && F[id].dividida === undefined) F[id].dividida = true;          // la casa de la calidad se ve completa desde el inicio
  const v = $("#vista"); v.innerHTML = "";
  const guardar = () => guardarFormato(id);
  v.append(el("div", { class: "vista-barra" }, el("span", { class: "vista-titulo" }, espec.titulo),
    el("button", { class: "boton chico", title: "Muestra las gráficas a la derecha mientras capturas a la izquierda (Ctrl+\\)", onclick: () => { F[id].dividida = !F[id].dividida; cuerpo.classList.toggle("dividida", F[id].dividida); } },
      id === "QFD" ? "Casa completa a la derecha" : "Vista dividida"),
    el("button", { class: "boton chico", title: "Libro de Excel con el formato y sus cálculos", onclick: () => aplicarProyecto(api().exportar_formato(id)) }, "Exportar a Excel…")));
  const cuerpo = el("div", { class: "formato" + (F[id].dividida ? " dividida" : ""), "data-formato": id });
  const cab = el("div", { class: "cabecera-fmt" });
  for (const c of espec.cabecera) {
    let i;
    if (c.fijo) i = el("input", { value: fijos[c.fijo] || "", readonly: true, class: "fijo-in", title: "Dato fijo del proyecto (Proyecto > Datos fijos)" });
    else if (c.calc) i = el("output", { class: "calc-in", "data-cab": c.campo }, calc.cab[c.campo] || "—");
    else i = control(espec, c, datos.cabecera[c.campo], async () => { datos.cabecera[c.campo] = i.value; await guardar(); if (id === "TABLERO") dibujarFormato(id); });
    cab.append(el("label", { class: (c.calc ? "calc" : "") + (c.tipo === "largo" ? " largo" : ""), title: c.ayuda || "" }, el("span", {}, c.etiqueta), i));
  }
  cuerpo.append(el("div", { class: "tarjetas", id: `tarjetas-${id}` }), cab, el("div", { class: "avisos-fmt", id: `avisos-${id}` }),
    el("div", { class: "bloques-fmt", id: `bloques-${id}` }));
  const ns = calc.semanas;
  for (const t of espec.tablas) {
    const cols = t.columnas.filter(c => !c.oculto && (!c.semana || !ns || c.semana <= ns));
    const tabla = el("table", { class: "tabla-fmt", "data-tabla": t.id });
    tabla.append(el("thead", {}, el("tr", {}, el("th", { class: "n" }, "#"),
      cols.map(c => el("th", { style: `min-width:${c.ancho || 110}px`, title: c.ayuda || "", class: c.ayuda ? "con-ayuda" : "", "data-campo": c.campo }, c.etiqueta)), el("th", {}))));
    const tb = el("tbody");
    datos.tablas[t.id].forEach((f, i) => {
      const tr = el("tr", { "data-i": i }, el("td", { class: "n" }, i + 1));
      for (const c of cols) {
        const td = el("td", { "data-c": c.campo });
        if (c.calc) td.classList.add("calc");
        else td.append(control(espec, c, f[c.campo], () => { f[c.campo] = td.firstChild.value; guardar(); }));
        tr.append(td);
      }
      tr.append(el("td", {}, t.fijas ? "" : el("button", { class: "quitar", title: "Quitar fila", onclick: () => { datos.tablas[t.id].splice(i, 1); guardar().then(() => dibujarFormato(id)); } }, "×")));
      tb.append(tr);
    });
    tabla.append(tb);
    cuerpo.append(el("div", { class: "tabla-titulo" }, t.titulo), el("div", { class: "tabla-scroll" }, tabla),
      t.fijas ? "" : el("div", { class: "acciones-tabla" },
        el("button", { class: "boton chico agregar", onclick: () => { datos.tablas[t.id].push({}); guardar().then(() => dibujarFormato(id)); } }, "Agregar fila"),
        t.catalogo ? el("button", { class: "boton chico agregar", onclick: () => elegirKpis(id, t.id) }, "Agregar del catálogo…") : ""));
  }
  if (espec.nota) cuerpo.append(el("p", { class: "texto-res nota" }, espec.nota));
  v.append(cuerpo);
  aplicarCalculo(id);
}

function aplicarCalculo(id) {
  const { espec, calc } = F[id];
  for (const [k, val] of Object.entries(calc.cab)) { const o = document.querySelector(`[data-cab="${k}"]`); if (o) o.textContent = val || "—"; }
  if (calc.encabezados) for (const [k, v] of Object.entries(calc.encabezados)) document.querySelectorAll(`#vista th[data-campo="${k}"]`).forEach(th => { th.textContent = v; });
  const av = $(`#avisos-${id}`); if (av) { av.innerHTML = ""; calc.avisos.forEach(a => av.append(el("p", { class: "aviso-res" }, a))); }
  for (const t of espec.tablas) {
    const filas = document.querySelectorAll(`.tabla-fmt[data-tabla="${t.id}"] tbody tr`);
    filas.forEach((tr, i) => {
      const c = (calc.calc[t.id] || [])[i] || {}, k = (calc.clases[t.id] || [])[i] || {};
      tr.querySelectorAll("td[data-c]").forEach(td => {
        const campo = td.dataset.c;
        td.classList.remove("ok", "no", "alerta", "mal", "falta", "desde-hoja", "pendiente");
        if (k[campo]) td.classList.add(k[campo]);
        if (td.firstChild && td.firstChild.tagName === "INPUT") td.firstChild.placeholder = k[campo] === "pendiente" ? "pendiente" : "";
        if (td.classList.contains("calc")) {
          const col = t.columnas.find(x => x.campo === campo);
          if (col.tipo === "svg") td.innerHTML = c[campo] || ""; else td.textContent = c[campo] ?? "";
        } else if (campo in c) {
          const inp = td.firstChild; inp.value = c[campo]; inp.readOnly = true; td.classList.add("desde-hoja");
          inp.title = "Calculado desde la hoja de datos";
        } else if (td.firstChild && td.firstChild.readOnly && !td.firstChild.classList.contains("fijo-in")) { td.firstChild.readOnly = false; td.firstChild.title = ""; }
      });
    });
  }
  const tj = $(`#tarjetas-${id}`);
  if (tj) { tj.innerHTML = ""; (calc.tarjetas || []).forEach(t => { const ch = el("div", { class: "chispa" }); ch.innerHTML = t.chispa;
    tj.append(el("div", { class: "tarjeta " + t.estado }, el("div", { class: "t-nombre" }, t.indicador),
      el("div", { class: "t-valor" }, t.valor, el("span", { class: "t-unidad" }, " " + t.unidad)),
      el("div", { class: "t-meta" }, `Meta ${t.meta}` + (t.semana ? ` · S${t.semana}` : "") + (t.cambio ? ` · ${t.cambio}` : "")), ch)); }); }
  const bl = $(`#bloques-${id}`);
  if (bl) { bl.innerHTML = ""; (calc.bloques || []).forEach(b => { if (b.tipo === "grafica") { const g = el("div", { class: "grafica" + (b.clase ? " " + b.clase : "") }); g.innerHTML = b.svg; bl.append(g); }
    else bl.append(el("p", { class: "texto-res " + b.clase }, b.texto)); }); }
  const occ = document.querySelector(`.tabla-fmt th[title*="ppm"], .tabla-fmt th[title*="año"]`);
  if (occ && calc.ayuda && calc.ayuda.occ) occ.title = calc.ayuda.occ;
  if (id === "QFD" && bl) qfdInteractivo(bl);
}

// Comparación independiente del orden de las claves y de los campos vacíos (para decidir si el servidor cambió la estructura)
function canonico(o) {
  if (Array.isArray(o)) return "[" + o.map(canonico).join(",") + "]";
  if (o && typeof o === "object") return "{" + Object.keys(o).filter(k => o[k] !== "" && o[k] != null).sort().map(k => JSON.stringify(k) + ":" + canonico(o[k])).join(",") + "}";
  return JSON.stringify(String(o ?? ""));
}

// QFD: clic en una celda de la matriz (9 → 3 → 1 → vacío) o del techo (++ → + → - → -- → vacío)
function qfdInteractivo(bl) {
  const d = F.QFD.datos;
  bl.querySelectorAll("[data-rel]").forEach(g => g.addEventListener("click", async () => {
    const [i, k] = g.dataset.rel.split(":").map(Number), f = d.tablas.requisitos_cliente[i], ciclo = ["", "9", "3", "1"];
    f[`rel_${k}`] = ciclo[(ciclo.indexOf(f[`rel_${k}`] || "") + 1) % 4]; await guardarFormato("QFD"); dibujarFormato("QFD");
  }));
  bl.querySelectorAll("[data-cor]").forEach(g => g.addEventListener("click", async () => {
    const [a, b] = g.dataset.cor.split(":"), ciclo = ["", "++", "+", "-", "--"], t = {};
    (d.cabecera.techo || "").replace(/,/g, ";").split(";").forEach(p => { const m = p.trim().split(/\s+/); if (m.length === 2) t[m[0]] = m[1]; });
    const clave = `${a}-${b}`; t[clave] = ciclo[(ciclo.indexOf(t[clave] || "") + 1) % ciclo.length];
    d.cabecera.techo = Object.entries(t).filter(([, v]) => v).map(([k2, v]) => `${k2} ${v}`).join("; ");
    await guardarFormato("QFD"); dibujarFormato("QFD");
  }));
}

async function guardarFormato(id) {
  const r = await aplicarProyecto(api().guardar_formato(id, F[id].datos));
  F[id].calc = r.calc;   // los datos se editan en sitio; no se reemplazan para no romper las referencias
  if (F[id].espec.redibujar && canonico(r.datos) !== canonico(F[id].datos)) { F[id].datos = r.datos; dibujarFormato(id); return r; }
  aplicarCalculo(id);
  return r;
}

// ---------- catálogo de indicadores ----------
async function elegirKpis(id, tid) {
  const cat = await api().catalogo_kpis();
  const cats = [...new Set(cat.map(k => k.categoria))];
  const buscar = el("input", { placeholder: "Buscar indicador", autocomplete: "off" });
  const filtro = el("select", {}, el("option", { value: "" }, "Todas las categorías"), cats.map(c => el("option", { value: c }, c)));
  const lista = el("div", { class: "lista-kpi" });
  const pintar = () => {
    const q = buscar.value.toLowerCase(); lista.innerHTML = "";
    cat.filter(k => (!filtro.value || k.categoria === filtro.value) && (!q || k.nombre.toLowerCase().includes(q))).forEach(k =>
      lista.append(el("label", { class: "kpi-op", title: `${k.formula}. Fuente: ${k.fuente}` },
        el("input", { type: "checkbox", value: k.id }), el("span", { class: "kpi-n" }, k.nombre),
        el("span", { class: "kpi-c" }, `${k.categoria} · ${k.unidad}` + (k.fuente.startsWith("BASE") ? " · base LSS" : "")))));
  };
  buscar.addEventListener("input", pintar); filtro.addEventListener("change", pintar); pintar();
  const cuerpo = el("div", { class: "formulario" }, el("div", { class: "kpi-filtros" }, buscar, filtro), lista);
  dialogo("Agregar indicadores del catálogo", cuerpo, async () => {
    const ids = [...lista.querySelectorAll("input:checked")].map(i => i.value);
    const filas = F[id].datos.tablas[tid];
    for (const kid of ids) {
      const k = cat.find(x => x.id === kid);
      const fila = { kpi_id: k.id, categoria: k.categoria, indicador: k.nombre, unidad: k.unidad, sentido: k.sentido, tarjeta: "Sí" };
      const vacia = filas.findIndex(f => !Object.values(f).some(v => v));
      if (vacia >= 0) filas[vacia] = fila; else filas.push(fila);
    }
    await guardarFormato(id); dibujarFormato(id);
  }, "Agregar");
  document.querySelector(".dialogo").classList.add("ancho");
}

function copiarTexto(t) {
  const a = el("textarea", { style: "position:fixed;opacity:0" }); a.value = t; document.body.append(a); a.select();
  try { document.execCommand("copy"); registrarSesion({ hora: new Date().toTimeString().slice(0, 8), texto: "Resultado copiado al portapapeles.", tipo: "info" }); }
  finally { a.remove(); }
}
