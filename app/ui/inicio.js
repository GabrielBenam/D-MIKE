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
function preguntarReceta(rc) {
  const filas = rc.hojas.map(h => el("li", {}, `${h.hoja}: ${h.filas ? h.filas + " filas con datos" : "sin datos (quedará pendiente)"}`));
  const cuerpo = el("div", { class: "ficha" },
    el("p", {}, el("b", {}, rc.nombre), rc.folio ? el("span", { class: "vacio" }, `  · folio ${rc.folio}`) : ""), rc.origen ? el("p", { class: "vacio" }, rc.origen) : "",
    el("p", {}, `La receta trae ${rc.formatos} formatos, ${rc.disenos} diseños de experimentos y ${rc.analisis} análisis. Los análisis sin datos quedan como pendientes.`),
    el("ul", {}, filas),
    rc.actualizable ? el("p", {}, `Ya está abierto el proyecto «${rc.actualizable.nombre}» con este folio: puedes agregarle solo lo nuevo, sin sobrescribir lo que ya escribiste.`) : "",
    el("p", { class: "vacio" }, "«Solo abrir los datos» carga las hojas en la hoja de datos para que hagas todo a mano; la receta queda guardada en el proyecto."));
  const correr = async (modo) => {
    document.querySelectorAll(".velo").forEach(v => v.remove());
    const r = await aplicarProyecto(api().ejecutar_receta(rc.ruta, modo, rc.actualizable ? rc.actualizable.id : null));
    if (!r.error) { cerrarPestanas(); document.getElementById("inicio")?.remove(); if (modo !== "datos") document.body.classList.add("sesion-abierta"); window.pintarDocs && pintarDocs(); }
  };
  dialogo("¿Ejecutar la receta?", cuerpo, () => correr("nuevo"), "Ejecutar en un proyecto nuevo");
  const botones = document.querySelector(".dialogo[aria-label='¿Ejecutar la receta?'] .dialogo-botones");
  if (botones) {
    const prim = botones.querySelector(".primario");
    botones.insertBefore(el("button", { class: "boton", onclick: () => correr("datos") }, "Solo abrir los datos"), prim);
    if (rc.actualizable) botones.insertBefore(el("button", { class: "boton", onclick: () => correr("actualizar") }, `Actualizar «${rc.actualizable.nombre.slice(0, 28)}»`), prim);
  }
}
window.preguntarReceta = preguntarReceta;

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
