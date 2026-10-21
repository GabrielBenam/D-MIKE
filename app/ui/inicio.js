// Arranque: barra de herramientas, atajos globales, panel DMAIC plegable y acciones de menú.
const ICONOS = {
  nuevo: "M6 3h8l4 4v14H6zM14 3v4h4", abrir: "M3 7h6l2 2h10v10H3zM3 11h18", guardar: "M5 3h12l3 3v15H5zM8 3v6h8V3M8 21v-6h8v6",
  deshacer: "M9 7L4 12l5 5M4 12h10a6 6 0 010 8h-3", rehacer: "M15 7l5 5-5 5M20 12H10a6 6 0 000 8h3",
  cortar: "M6 5a2.5 2.5 0 110 5 2.5 2.5 0 010-5zM6 14a2.5 2.5 0 110 5 2.5 2.5 0 010-5zM8 9l12 9M8 15L20 6", copiar: "M8 8h11v13H8zM5 16V3h11",
  pegar: "M9 4h6v3H9zM7 5H5v16h14V5h-2M9 12h6M9 16h6", importar: "M12 3v12M7 10l5 5 5-5M4 20h16", filtro: "M3 5h18l-7 8v6l-4-2v-4z",
  az: "M5 4v16M2 17l3 3 3-3M12 8h8l-8 8h8", za: "M5 4v16M2 17l3 3 3-3M12 16h8l-8-8h8", calc: "M5 3h14v18H5zM8 7h8M8 12h2M12 12h2M16 12h0M8 16h2M12 16h2M16 16h0",
  panel: "M3 4h18v16H3zM9 4v16", luna: "M20 14.5A8 8 0 019.5 4a8 8 0 1010.5 10.5z", sesion: "M3 4h18v16H3zM3 14h18", atajos: "M4 7h16v10H4zM7 11h1M11 11h1M15 11h1M8 14h8",
};
const icono = n => `<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="${ICONOS[n]}"/></svg>`;
const guardarPref = (k, v) => { try { localStorage.setItem("dmike_" + k, v); } catch (e) { /* sin almacenamiento: se ignora */ } };
const leerPref = k => { try { return localStorage.getItem("dmike_" + k); } catch (e) { return null; } };

function alternarPanel(forzar) {
  const oculto = forzar === undefined ? !document.body.classList.contains("sin-panel") : forzar;
  document.body.classList.toggle("sin-panel", oculto); guardarPref("sin_panel", oculto ? "1" : "0");
  const b = $("#b-panel"); if (b) { b.classList.toggle("on", !oculto); b.title = (oculto ? "Mostrar" : "Ocultar") + " el panel DMAIC (Ctrl+B)"; }
  setTimeout(() => dibujarFilas(true), 220);
}
// Tema oscuro: tokens en estilos.css; las gráficas SVG cambian sus colores fijos por variables --g-* al insertarse.
const COLORES_TEMA = { "#ffffff": "--g-fondo", "#2b2620": "--g-tinta", "#6f675b": "--g-suave", "#a79f92": "--g-tenue", "#e9e4da": "--g-rejilla",
  "#e2dcd0": "--g-linea", "#faf8f4": "--g-papel", "#fbe8dd": "--g-claro", "#f3efe7": "--g-panel", "#fdecea": "--no-fondo", "#e3f1e0": "--ok-fondo", "#fff4d6": "--adv-fondo" };
function aHex(c) {
  if (!c) return ""; c = c.trim().toLowerCase(); if (c === "white") return "#ffffff"; if (/^#[0-9a-f]{3}$/.test(c)) return "#" + [...c.slice(1)].map(x => x + x).join("");
  const m = c.match(/^rgba?\((\d+),\s*(\d+),\s*(\d+)/); return m ? "#" + [m[1], m[2], m[3]].map(v => (+v).toString(16).padStart(2, "0")).join("") : c;
}
function tematizar(raiz) {
  const svgs = raiz.tagName === "svg" ? [raiz] : raiz.querySelectorAll ? raiz.querySelectorAll("svg") : [];
  for (const svg of svgs) {
    if (svg.dataset.tema) continue; svg.dataset.tema = "1";
    for (const e of [svg, ...svg.querySelectorAll("*")]) {
      for (const a of ["fill", "stroke", "stop-color"]) {
        const v = aHex(e.style.getPropertyValue(a) || e.getAttribute(a)), k = COLORES_TEMA[v];
        if (k) e.style.setProperty(a, `var(${k}, ${v})`);
      }
    }
  }
}
new MutationObserver(ms => { for (const m of ms) for (const n of m.addedNodes) if (n.nodeType === 1 && !n.closest(".logo-img")) tematizar(n); })
  .observe(document.documentElement, { childList: true, subtree: true });
function alternarTema(forzar) {
  const oscuro = forzar === undefined ? document.documentElement.dataset.tema !== "oscuro" : forzar;
  if (oscuro) document.documentElement.dataset.tema = "oscuro"; else delete document.documentElement.dataset.tema;
  guardarPref("tema", oscuro ? "oscuro" : "claro"); const b = $("#b-tema"); if (b) b.classList.toggle("on", oscuro);
}

function alternarSesion(forzar) {
  const oculto = forzar === undefined ? !document.body.classList.contains("sin-sesion") : forzar;
  document.body.classList.toggle("sin-sesion", oculto); guardarPref("sin_sesion", oculto ? "1" : "0");
  const b = $("#b-sesion"); if (b) b.classList.toggle("on", !oculto);
  setTimeout(() => dibujarFilas(true), 50);
}

const ATAJOS = [["Archivo", [["Ctrl+N", "Nuevo proyecto"], ["Ctrl+O", "Abrir proyecto"], ["Ctrl+S", "Guardar"], ["Ctrl+Mayús+S", "Guardar como"]]],
  ["Edición", [["Ctrl+Z / Ctrl+Y", "Deshacer / Rehacer"], ["Ctrl+C / X / V", "Copiar / Cortar / Pegar"], ["Supr", "Borrar el contenido"], ["Ctrl+D / Ctrl+R", "Rellenar hacia abajo / la derecha"],
    ["Ctrl+F", "Buscar y reemplazar"], ["Ctrl+A", "Seleccionar los datos (otra vez: toda la hoja)"]]],
  ["Moverse", [["Flechas", "Mover la celda activa"], ["Mayús+flechas", "Extender la selección"], ["Ctrl+flechas", "Saltar al borde de los datos"], ["Inicio / Fin", "Primera / última columna"],
    ["Ctrl+Inicio / Fin", "Primera celda / última celda con datos"], ["Re Pág / Av Pág", "Subir / bajar una pantalla"], ["Enter, Tab", "Abajo, derecha (con Mayús, al revés)"], ["F2", "Editar la celda"]]],
  ["Filas y columnas", [["Ctrl++ / Ctrl+-", "Insertar / eliminar filas o columnas seleccionadas"], ["Ctrl+Mayús+L", "Filtrar filas"], ["Clic en C1, C2…", "Seleccionar toda la columna"], ["Clic en el número de fila", "Seleccionar la fila"],
    ["Clic derecho", "Menú con ordenar, filtrar, insertar y más"]]],
  ["Pantalla", [["Ctrl+B", "Mostrar u ocultar el panel DMAIC"], ["Ctrl+Mayús+D", "Tema oscuro o claro"]]]];
function dialogoAtajos() {
  const cuerpo = el("div", { class: "atajos" }, ATAJOS.map(([t, l]) => el("div", {}, el("h4", {}, t), l.map(([k, d]) => el("p", {}, el("kbd", {}, k), " " + d)))));
  dialogo("Atajos de teclado", cuerpo, () => true, "Cerrar"); document.querySelector(".dialogo").classList.add("ancho");
}

const ACCIONES_UI = {
  insertar_columna: () => aplicar(api().insertar_columna(Math.max(H.sel.c, 0))), eliminar_columna: () => aplicar(api().eliminar_columnas(rect().c0, rect().c1)),
  insertar_fila: () => aplicar(api().insertar_filas(Math.max(filaDe(rect().r0), 0), 1)), eliminar_fila: () => eliminarEnSeleccion(),
  tipo_columna: dialogoTipo, filtrar: dialogoFiltro, quitar_filtro: () => aplicar(api().filtrar([])),
  cortar: () => copiarSeleccion(true), copiar: () => copiarSeleccion(false), pegar: pegarDelPortapapeles, borrar: borrarSeleccion,
  seleccionar_todo: seleccionarTodo, rellenar_abajo: () => rellenar("abajo"), rellenar_derecha: () => rellenar("derecha"),
  ordenar_az: () => ordenarColumna(false), ordenar_za: () => ordenarColumna(true), buscar: () => abrirModulo("REEMPLAZAR"),
  tablero_vista: () => abrirPestana("vis:TABLERO", null, "Tablero de indicadores"),
  panel: () => alternarPanel(), sesion_ver: () => alternarSesion(), atajos: dialogoAtajos, tema: () => alternarTema(),
  abrir_perfil: () => aplicarProyecto(api().abrir_perfil()), datos_fijos: dialogoFijos, resultados: () => window.listaResultados && listaResultados(),
  nuevo_proyecto: async () => { if (window.guardarTabs) guardarTabs(); const r = await aplicarProyecto(api().nuevo_proyecto()); if (!r.error) { cerrarPestanas(); document.getElementById("inicio")?.remove(); window.pintarDocs && pintarDocs(); } },
  abrir_proyecto: async () => { if (window.guardarTabs) guardarTabs(); const r = await aplicarProyecto(api().abrir_proyecto()); if (r.receta) return preguntarReceta(r.receta); if (!r.error && r.sesion && !/cancelada/.test(r.sesion[0].texto)) { cerrarPestanas(); document.getElementById("inicio")?.remove(); window.pintarDocs && pintarDocs(); } },
  guardar: () => aplicarProyecto(api().guardar(false)), guardar_como: () => aplicarProyecto(api().guardar(true)),
  exportar: () => aplicarProyecto(api().exportar()), exportar_powerbi: () => aplicarProyecto(api().exportar_powerbi()),
  exportar_avance: () => aplicarProyecto(api().exportar_avance()), seguimiento: () => dialogoSeguimiento(),
  disenos_dialogo: () => dialogoDisenos(), importar_respuestas: () => aplicar(api().importar_respuestas()),
  exportar_corridas: async () => { const ds = await api().disenos(); if (ds.length > 1) return dialogoDisenos(); aplicar(api().exportar_corridas()); },
  importar_receta: async () => { if (window.guardarTabs) guardarTabs(); const r = await aplicarProyecto(api().abrir_receta()); if (r.receta) preguntarReceta(r.receta); },
  deshacer: () => aplicar(api().deshacer()), rehacer: () => aplicar(api().rehacer()), importar: () => aplicar(api().importar()),
};

const HERRAMIENTAS = [["nuevo", "Nuevo proyecto (Ctrl+N)", "nuevo_proyecto"], ["abrir", "Abrir proyecto (Ctrl+O)", "abrir_proyecto"], ["guardar", "Guardar (Ctrl+S)", "guardar"], "|",
  ["deshacer", "Deshacer (Ctrl+Z)", "deshacer"], ["rehacer", "Rehacer (Ctrl+Y)", "rehacer"], "|",
  ["cortar", "Cortar (Ctrl+X)", "cortar"], ["copiar", "Copiar (Ctrl+C)", "copiar"], ["pegar", "Pegar (Ctrl+V)", "pegar"], "|",
  ["importar", "Importar CSV, TXT o Excel", "importar"], ["az", "Ordenar de menor a mayor por la columna activa", "ordenar_az"], ["za", "Ordenar de mayor a menor", "ordenar_za"],
  ["filtro", "Filtrar filas (Ctrl+Mayús+L)", "filtrar"], ["calc", "Calculadora de columnas", "calculadora"], "|"];
function dibujarHerramientas() {
  const barra = $("#herramientas");
  for (const h of HERRAMIENTAS) {
    if (h === "|") { barra.append(el("span", { class: "sep" })); continue; }
    const b = el("button", { class: "ico", title: h[1], "aria-label": h[1], onclick: () => (h[2] === "calculadora" ? abrirModulo("CALCULADORA") : ACCIONES_UI[h[2]]()) });
    b.innerHTML = icono(h[0]); barra.append(b);
  }
  barra.append(el("span", { id: "herr-contexto", class: "herr-contexto", role: "group", "aria-label": "Herramientas del módulo abierto" }));
  barra.append(el("span", { class: "relleno-barra" }));
  for (const [id, ic, tit, fn] of [["b-panel", "panel", "Ocultar el riel DMAIC (Ctrl+B)", () => alternarPanel()], ["b-sesion", "sesion", "Mostrar u ocultar la sesión", () => alternarSesion()]]) {
    const b = el("button", { class: "ico on", id, title: tit, "aria-label": tit, onclick: fn }); b.innerHTML = icono(ic); barra.append(b);
  }
}

// ---------- barra de herramientas contextual: cambia según la pestaña activa (hoja, resultado, formato o tablero) ----------
const SIGUIENTE = {   // atajos útiles desde un módulo hacia el siguiente paso lógico
  RSM: [["OPTIMIZADOR", "Optimizar respuestas"]], "DISENO-RSM": [["FACTORIAL", "Analizar factorial"], ["RSM", "Analizar superficie"]],
  FACTORIAL: [["DISENO-RSM", "Diseño siguiente"], ["RSM", "Superficie de respuesta"]], SPC: [["CAPACIDAD", "Capacidad"]],
  CAPACIDAD: [["SPC", "Cartas de control"]], ANOVA: [["TUKEY", "Comparar con Tukey"]], ANOVA2: [["TUKEY", "Comparar con Tukey"]],
  CORREL: [["REGRESION", "Regresión"]], DISTRIB: [["DIST-ID", "Identificar distribución"], ["BOXCOX", "Box-Cox"]],
  "DIST-ID": [["BOXCOX", "Box-Cox"]], "MSA-VAR": [["SPC", "Cartas de control"]], PARETO: [["ISHIKAWA", "Ishikawa"]],
  TABLERO: [["vis:TABLERO", "Ver el tablero"]], CHARTER: [["INTERESADOS", "Interesados"], ["EDT", "EDT"]], EDT: [["CRONOGRAMA", "Cronograma"]],
  CRONOGRAMA: [["MONTECARLO", "Monte Carlo"], ["VALOR-GANADO", "Valor ganado"]], AMEF: [["PLAN-CONTROL", "Plan de control"]],
  "PLAN-CONTROL": [["SPC", "Cartas de control"]], ISHIKAWA: [["CINCO-PQ", "5 Porqués"]], VSM: [["TIEMPOS", "Tiempos"], ["BALANCE", "Balance"]],
  RIESGOS: [["BITACORA", "Bitácora"]], FODA: [["RIESGOS", "Registro de riesgos"]], INTERESADOS: [["RACI", "Matriz RACI"]],
  LECCIONES: [["CHECKLIST-FASE", "Checklist de fase"]], OEE: [["TPM", "TPM"], ["SMED", "SMED"]], SMED: [["OEE", "OEE"]],
};
function barraContexto(id) {
  const z = $("#herr-contexto"); if (!z) return; z.innerHTML = "";
  const b = (texto, titulo, fn, ic) => { const x = el("button", { class: "ctx", title: titulo, onclick: fn }); if (ic) x.innerHTML = icono(ic); x.append(texto); return x; };
  const ir = (dest) => dest.startsWith("vis:") ? ACCIONES_UI.tablero_vista() : abrirModulo(dest);
  const etiqueta = t => z.append(el("span", { class: "ctx-et" }, t));
  if (id === "hoja") {
    etiqueta("Hoja");
    z.append(b("Fila", "Insertar filas en la selección (Ctrl++)", () => insertarEnSeleccion()), b("Columna", "Insertar columna a la izquierda", () => ACCIONES_UI.insertar_columna()),
             b("Tipo…", "Tipo de la columna activa", () => dialogoTipo()), b("Estadísticos", "Estadísticos de columna", () => abrirModulo("ESTADISTICOS")),
             b("Gráfica", "Distribución y normalidad de una columna", () => abrirModulo("DISTRIB")));
    return;
  }
  const a = P.abiertas.find(x => x.id === id); if (!a) return;
  if (id.startsWith("res:")) {
    const r = a.res; etiqueta("Resultado");
    if (r.definicion) z.append(b("Modificar…", "Vuelve a abrir el diálogo con los mismos datos y opciones", () => dialogoModulo(r.modulo, r.definicion)),
                               b("Repetir", "Corre de nuevo con los datos actuales", async () => { const x = await aplicarProyecto(api().repetir_resultado(r.uid)); if (!x.error && x.resultado) abrirPestana(`res:${x.resultado.uid}`, x.resultado); }));
    z.append(b("Copiar", "Copia tablas y conclusiones", async () => copiarTexto(await api().texto_resultado(r.uid))),
             b("Exportar…", "Excel con reporte y datos, o la gráfica en PNG", () => aplicarProyecto(api().exportar_resultado(r.uid))));
    if (["ESTADISTICOS", "CORREL", "REGRESION", "CAPACIDAD", "DISTRIB"].includes(r.modulo)) z.append(b("Verificar en Excel…", "Fórmulas de Excel y columna para Minitab", () => aplicarProyecto(api().exportar_verificacion(r.uid))));
    (SIGUIENTE[r.modulo] || []).forEach(([dest, t]) => z.append(b(t, "Siguiente paso sugerido", () => ir(dest))));
    return;
  }
  if (id === "vis:TABLERO") {
    etiqueta("Tablero");
    z.append(b("Capturar datos…", "Formato Tablero semanal", () => abrirModulo("TABLERO")), b("Agregar indicadores", "Catálogo de 109 indicadores", () => { TB.nivel = "Exploración"; pintarTableroVista(false); }),
             b("Exportar…", "Excel del tablero", () => aplicarProyecto(api().exportar_formato("TABLERO"))));
    return;
  }
  if (id.startsWith("fmt:")) {
    const fid = id.slice(4); etiqueta("Formato");
    z.append(b("Exportar a Excel…", "Libro con el formato y sus cálculos", () => aplicarProyecto(api().exportar_formato(fid))),
             b("Nota de la base", "Ir a la nota con las fuentes del formato", () => { const n = document.querySelector("#vista .nota-fmt, #vista .nota"); if (n) n.scrollIntoView({ behavior: "smooth" }); }));
    (SIGUIENTE[fid] || []).forEach(([dest, t]) => z.append(b(t, "Siguiente paso sugerido", () => ir(dest))));
  }
}
window.barraContexto = barraContexto;

// Cualquier error inesperado del puente se informa en la sesión (antes se perdía en silencio)
window.addEventListener("unhandledrejection", ev => {
  const m = (ev.reason && (ev.reason.message || ev.reason)) || "error desconocido";
  registrarSesion({ hora: new Date().toTimeString().slice(0, 8), texto: `No se pudo completar la acción: ${String(m).slice(0, 200)}`, tipo: "aviso" });
});

// Receta del diagnóstico en línea: se muestra qué trae y se pide confirmación antes de armar el proyecto
const NOMBRE_MODO = { real: "Real", demostracion: "Demostración" };
function preguntarReceta(rc) {
  const filas = rc.hojas.map(h => el("li", {}, `${h.hoja}: ${h.filas ? h.filas + " filas con datos" : "sin datos (quedará pendiente)"}`));
  const elegir = el("select", { id: "receta-modo", "aria-label": "Modo del proyecto" },
    el("option", { value: rc.modo }, `${NOMBRE_MODO[rc.modo]} (detectado)`),
    el("option", { value: rc.modo === "real" ? "demostracion" : "real" }, NOMBRE_MODO[rc.modo === "real" ? "demostracion" : "real"]));
  const abiertos = rc.abiertos || [];
  const destino = el("select", { id: "receta-destino", "aria-label": "Proyecto abierto a actualizar" },
    abiertos.map(d => el("option", { value: String(d.id), selected: rc.actualizable ? rc.actualizable.id === d.id : false }, d.nombre)));
  const hayConflicto = !!(rc.actualizable || rc.conflicto_id);
  const cuerpo = el("div", { class: "ficha" },
    el("p", {}, el("b", {}, rc.nombre)), rc.origen ? el("p", { class: "vacio" }, rc.origen) : "",
    el("p", {}, el("b", {}, "Modo del proyecto: "), `${NOMBRE_MODO[rc.modo]} · ${rc.deteccion === "declarado" ? "declarado por la receta (no se puede cambiar)" : "inferido del origen de la receta"}.`),
    rc.puede_cambiar_modo ? el("p", {}, "Si no es correcto, cámbialo ahora; solo se permite UNA vez y antes de cargar datos: ", elegir) : "",
    rc.modo === "demostracion" || rc.puede_cambiar_modo ? el("p", { class: "vacio" }, `En demostración todo resultado y exportación lleva la etiqueta «${rc.etiqueta}». En modo real se rechazan los datos sintéticos.`) : "",
    rc.trae_folio ? el("p", { class: "aviso-ficha" }, "Esta receta trae un folio. Es la llave de una sesión web: D-MIKE lo ignora, no lo compara ni lo guarda. No lo compartas.") : "",
    el("p", {}, `La receta trae ${rc.formatos} formatos, ${rc.disenos} diseños de experimentos y ${rc.analisis} análisis. Los análisis sin datos quedan como pendientes.`),
    el("ul", {}, filas),
    rc.actualizable && rc.estado_revision && rc.estado_revision.accion !== "aplicar" ? el("p", { class: "aviso-ficha", id: "receta-revision" }, rc.estado_revision.motivo) : "",
    rc.actualizable ? el("p", {}, `El proyecto abierto «${rc.actualizable.nombre}» tiene el mismo id_proyecto: se propone actualizarlo, sin sobrescribir lo que ya escribiste.`)
      : rc.conflicto_id ? el("p", {}, `El id_proyecto de esta receta ya pertenece al proyecto reciente «${rc.conflicto_id.nombre}». Ábrelo para actualizarlo, o crea uno nuevo sin id_proyecto.`)
      : (abiertos.length ? el("p", {}, "Para actualizar, confirma a mano cuál de los proyectos abiertos es (esta receta no identifica uno por sí sola): ", destino) : ""),
    el("p", { class: "vacio" }, "«Solo abrir los datos» carga las hojas en la hoja de datos para que hagas todo a mano; la receta queda guardada en el proyecto."));
  const correr = async (modo, sinId) => {
    const modoElegido = rc.puede_cambiar_modo ? elegir.value : null;
    const idDoc = modo === "actualizar" ? parseInt(destino.value, 10) : null;
    document.querySelectorAll(".velo").forEach(v => v.remove());
    if (modo === "actualizar") return actualizarReceta(rc, idDoc, modoElegido, null, false);
    const r = await aplicarProyecto(api().ejecutar_receta(rc.ruta, modo, idDoc, modoElegido, !!sinId));
    if (!r.error) trasReceta(modo);
  };
  dialogo("¿Ejecutar la receta?", cuerpo, () => correr("nuevo", hayConflicto), hayConflicto ? "Crear nuevo sin id_proyecto" : "Ejecutar en un proyecto nuevo");
  const botones = document.querySelector(".dialogo[aria-label='¿Ejecutar la receta?'] .dialogo-botones");
  if (botones) {
    const prim = botones.querySelector(".primario");
    botones.insertBefore(el("button", { class: "boton", onclick: () => correr("datos", hayConflicto) }, "Solo abrir los datos"), prim);
    if (abiertos.length) botones.insertBefore(el("button", { class: "boton", id: "receta-actualizar", onclick: () => correr("actualizar") }, "Actualizar el proyecto elegido"), prim);
  }
}
window.preguntarReceta = preguntarReceta;

function trasReceta(modo) { cerrarPestanas(); document.getElementById("inicio")?.remove(); if (modo !== "datos") document.body.classList.add("sesion-abierta"); window.pintarDocs && pintarDocs(); }

// Control de revisión al actualizar (ESPEC_receta_v2 12.5): ya aplicada y más antigua avisan en la sesión; el conflicto se resuelve aquí, sin fusión automática
async function actualizarReceta(rc, idDoc, modoElegido, resolucion, forzar) {
  const r = await aplicarProyecto(api().ejecutar_receta(rc.ruta, "actualizar", idDoc, modoElegido, false, resolucion || null, !!forzar));
  if (r.error === "conflicto_revision") dialogoConflictoRevision(rc, r.revision, idDoc, modoElegido);
  else if (r.error === "revision_antigua") dialogoRevisionAntigua(rc, r.revision, idDoc, modoElegido);
  else if (!r.error) trasReceta("actualizar");
  return r;
}
function dialogoConflictoRevision(rc, dec, idDoc, modoElegido) {
  const cuerpo = el("div", { class: "ficha", id: "conflicto-revision" },
    el("p", { class: "aviso-ficha" }, dec.motivo),
    (dec.variables || []).length ? el("ul", {}, dec.variables.map(v => el("li", {}, `${v.nombre}: ${v.actual} no baja a ${v.recibido} en silencio (se conserva ${v.actual}).`))) : "",
    el("p", {}, "No hay fusión automática de campos. «Cancelar» no cambia nada. «Aplicar solo lo nuevo» agrega lo que falta sin sobrescribir lo que el proyecto ya tiene; la receta anterior pasa al historial de revisiones."));
  dialogo("Conflicto de revisión", cuerpo, async () => { await actualizarReceta(rc, idDoc, modoElegido, "solo_nuevo", false); return true; }, "Aplicar solo lo nuevo");
}
function dialogoRevisionAntigua(rc, dec, idDoc, modoElegido) {
  const cuerpo = el("div", { class: "ficha", id: "revision-antigua" }, el("p", { class: "aviso-ficha" }, dec.motivo),
    el("p", {}, "Por omisión no se aplica. Si de verdad quieres volver a esa revisión, fuérzala: la que está aplicada pasa al historial de revisiones."));
  dialogo("Receta más antigua", cuerpo, async () => { await actualizarReceta(rc, idDoc, modoElegido, null, true); return true; }, "Forzar y aplicar");
}

// Seguimiento del proyecto: solo lectura (variables, pendientes abiertos y estado de cada análisis)
async function dialogoSeguimiento() {
  const s = await api().seguimiento();
  const tabla = (cab, filas, vacio) => filas.length
    ? el("table", { class: "tabla-seg" }, el("thead", {}, el("tr", {}, cab.map(c => el("th", {}, c)))),
        el("tbody", {}, filas.map(f => el("tr", {}, f.map(c => el("td", {}, c === null || c === undefined ? "" : String(c)))))))
    : el("p", { class: "vacio" }, vacio);
  const cuerpo = el("div", { class: "ficha", id: "seguimiento" },
    el("p", {}, `Revisión aplicada: ${s.revision ?? "ninguna"} · revisiones anteriores guardadas: ${s.revisiones_guardadas} · tareas cerradas: ${s.tareas_cerradas}`),
    el("h4", {}, "Variables"), tabla(["Variable", "Hoja", "Unidad", "Estado de la evidencia", "Ensayo destructivo"],
      s.variables.map(v => [v.nombre, v.hoja, v.unidad, v.estado_evidencia, v.ensayo_destructivo ? "sí" : "no"]), "Este proyecto no tiene variables registradas."),
    el("h4", {}, "Pendientes abiertos"), tabla(["Pendiente", "Responsable", "Acción sugerida", "Origen"],
      s.tareas_abiertas.map(t => [t.descripcion, t.responsable, t.accion, t.origen]), "No hay pendientes abiertos."),
    el("h4", {}, "Análisis"), tabla(["Análisis", "Módulo", "Estado", "Motivo"],
      s.analisis.map(a => [a.id, a.modulo, a.estado, a.motivo]), "Este proyecto no tiene análisis registrados por una receta."));
  dialogo("Seguimiento del proyecto", cuerpo, () => true, "Cerrar"); document.querySelector(".dialogo").classList.add("ancho");
}
window.dialogoSeguimiento = dialogoSeguimiento;

// Diseños del proyecto (E3-2 y E3-3): identidad, versión, estado de la definición y de las respuestas
const ESTADO_DEF = { vigente: "vigente", cambiada: "cambió: registra una versión nueva", sin_linea_base: "sin línea base (diseño anterior a 0.29)", no_verificable: "faltan columnas del diseño en la hoja" };
function pedirMotivo(titulo, ayuda, accion) {
  const motivo = el("input", { placeholder: "Motivo (queda registrado)", style: "width:100%", autocomplete: "off" });
  dialogo(titulo, el("div", { class: "formulario" }, el("p", { class: "tb-sub" }, ayuda), el("label", {}, motivo)), async () => { await accion(motivo.value); return true; }, "Guardar");
}
async function dialogoDisenos() {
  const ds = await api().disenos();
  const recargar = async r => { if (r && r.sesion) registrarSesion(r.sesion); document.querySelector(".velo")?.remove(); await dialogoDisenos(); };
  const cuerpo = el("div", { class: "ficha", id: "disenos" }, ds.length ? ds.map(d => {
    const mezcla = d.respuestas.version != null && d.respuestas.version !== d.version_diseno;
    return el("div", { class: "tb-def" },
      el("h4", {}, `${d.design_id} · versión ${d.version_diseno} · ${d.corridas ?? "?"} corridas`),
      el("p", {}, `Respuesta: ${d.respuesta}. Factores: ${d.factores.join(", ")}. RunId: ${d.col_runid ? "columna " + d.col_runid + " (solo lectura)" : "derivado de OrdenEst, sin columna"}.`),
      el("p", {}, `Definición: ${ESTADO_DEF[d.estado_definicion] || d.estado_definicion}. Respuestas en la hoja: ${d.respuestas.n}${d.respuestas.n ? ` (versión ${d.respuestas.version ?? "sin etiqueta"})` : ""}${mezcla ? " · no coinciden con la versión vigente: no se analizan" : ""}.`),
      d.historial_versiones.length ? el("p", { class: "tb-sub" }, "Versiones anteriores: " + d.historial_versiones.map(h => `v${h.version}${h.motivo ? " (" + h.motivo + ")" : ""}`).join("; ")) : "",
      el("div", {}, 
        (d.estado_definicion === "cambiada" || d.estado_definicion === "sin_linea_base") ? el("button", { class: "boton chico", onclick: () => pedirMotivo("Registrar versión nueva", d.estado_definicion === "cambiada" ? "La definición cambió: se registrará la versión " + (d.version_diseno + 1) + ". Las respuestas actuales dejarán de coincidir con la versión vigente." : "Este diseño no tenía línea base: se tomará su estado actual como versión 1.", async m => recargar(await api().registrar_version_diseno(d.design_id, m))) }, d.estado_definicion === "cambiada" ? "Registrar versión nueva…" : "Tomar línea base…") : "",
        mezcla ? el("button", { class: "boton chico", onclick: () => pedirMotivo("Confirmar respuestas", `Declaras que las respuestas de la hoja corresponden a la versión ${d.version_diseno}. Escribe por qué.`, async m => recargar(await api().confirmar_respuestas_diseno(d.design_id, m))) }, "Confirmar que son de la versión vigente…") : "",
        el("button", { class: "boton chico", title: "Corridas en el orden en que se corren, con RunId y la respuesta en blanco", onclick: async () => { document.querySelector(".velo")?.remove(); await aplicar(api().exportar_corridas(d.design_id)); } }, "Exportar corridas…"),
        el("button", { class: "boton chico", onclick: async () => { document.querySelector(".velo")?.remove(); await aplicar(api().importar_respuestas(null, d.design_id)); } }, "Importar respuestas…")));
  }) : el("p", { class: "vacio" }, "Este proyecto no tiene diseños de experimentos. Crea uno en Estadística > Diseño de experimentos."));
  dialogo("Diseños del proyecto", cuerpo, () => true, "Cerrar"); document.querySelector(".dialogo").classList.add("ancho");
}
window.dialogoDisenos = dialogoDisenos;

async function iniciar() {
  const e = await api().estado_inicial();
  dibujarMenus(e.menus); dibujarHerramientas();
  G.fases = e.fases; G.catalogo = e.catalogo; pintarFases(e.proyecto);
  prepararHoja(); pintarHoja(e.hoja); pintarArchivo(e.archivo); barraContexto("hoja");
  if (leerPref("sin_panel") === "1") alternarPanel(true);
  if (leerPref("sin_sesion") === "1") alternarSesion(true);
  alternarTema(leerPref("tema") === "oscuro"); tematizar(document.body);
  document.addEventListener("keydown", ev => {
    if (!(ev.ctrlKey || ev.metaKey)) return;
    const k = ev.key.toLowerCase(), escribiendo = ev.target.closest("input, textarea, select"), hayVelo = document.querySelector(".velo");
    if (k === "s") { ev.preventDefault(); (ev.shiftKey ? ACCIONES_UI.guardar_como : ACCIONES_UI.guardar)(); }
    else if (k === "b") { ev.preventDefault(); alternarPanel(); }
    else if (k === "d" && ev.shiftKey) { ev.preventDefault(); alternarTema(); }
    else if ((k === "o" || k === "n") && !hayVelo) { ev.preventDefault(); (k === "o" ? ACCIONES_UI.abrir_proyecto : ACCIONES_UI.nuevo_proyecto)(); }
    else if ((k === "z" || k === "y") && !escribiendo && !hayVelo) { ev.preventDefault(); (k === "y" || ev.shiftKey ? ACCIONES_UI.rehacer : ACCIONES_UI.deshacer)(); }
  });
  e.sesion.forEach(registrarSesion);
  if (window.ui2Iniciar) ui2Iniciar(e);
  G.version = e.version; if (window.ui3Iniciar) ui3Iniciar(e);
  if (window.gIniciar) gIniciar();
  document.body.dataset.listo = "1";
}

if (window.pywebview && window.pywebview.api) iniciar();
else window.addEventListener("pywebviewready", iniciar);
