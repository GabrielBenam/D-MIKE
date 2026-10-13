// D-MIKE v0.21 · interfaz acordada: cinta por pestañas (propuesta 3), riel DMAIC compacto (4/15), inicio (6), paleta de comandos (7),
// ventana de módulos por fase (12) y ruta DMAIC (8), pestañas tipo navegador con clic derecho, vista dividida (11), interruptor de tema,
// sesión plegable, descripción de cada comando al pasar el mouse y ayuda F1.
const U2 = { menus: [], cmds: [], desc: {}, cerradas: [], recientes: [], cintaActiva: null };
const norm = s => (s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/…|\.\.\./g, "").trim();

// ---------- descripciones (tooltips) ----------
function descripcion(texto, accion) {
  const d = U2.desc[norm(texto)] || U2.desc[norm(texto.replace(/\s*\(.*\)\s*$/, ""))];
  if (d) return `${texto}: ${d}`;
  if (accion && accion.startsWith("mod:")) {
    const m = Object.values(G.catalogo).flat().find(x => x.id === accion.slice(4));
    return `${texto}: abre el módulo${m && m.tipo ? " (" + (m.tipo === "formato" ? "formato" : "análisis") + ")" : ""}`;
  }
  return texto;
}
function ponerDescripciones() {
  document.querySelectorAll("#menus .desplegable button[role='menuitem']").forEach(b => { if (!b.disabled) b.title = descripcion(b.textContent, b.dataset.accion); });
}

// ---------- ejecutar una opción de menú ----------
async function ejecutarOpcion(o) {
  if (!o.accion) return;
  if (o.accion.startsWith("mod:")) return abrirModulo(o.accion.slice(4));
  if (ACCIONES_UI[o.accion]) return ACCIONES_UI[o.accion]();
  registrarSesion(await api().accion(o.accion));
}

// ---------- cinta por pestañas ----------
const ICONO_MENU = { Archivo: "abrir", Editar: "copiar", Datos: "filtro", Calc: "calc", Estadística: "grafica", Gráficas: "grafica", "Herramientas de calidad": "res", Lean: "tablero", Gestión: "ruta", Proyecto: "panel", Ver: "panel", Ayuda: "buscar" };
const SVG2 = { abrir: "M3 7h6l2 2h10v10H3zM3 11h18", copiar: "M8 8h11v13H8zM5 16V3h11", filtro: "M3 5h18l-7 8v6l-4-2v-4z", calc: "M5 3h14v18H5zM8 7h8M8 12h2M12 12h2M8 16h2M12 16h2",
  grafica: "M4 20V4M4 20h16M8 16l4-5 3 3 5-7", res: "M5 3h14v18H5zM8 8h8M8 12h8M8 16h5", tablero: "M3 3h8v8H3zM13 3h8v5h-8zM13 10h8v11h-8zM3 13h8v8H3z", ruta: "M4 12h16M14 6l6 6-6 6",
  panel: "M3 4h18v16H3zM9 4v16", buscar: "M11 4a7 7 0 110 14 7 7 0 010-14zM21 21l-5-5", fijar: "M9 4h6l-1 6 3 3H7l3-3zM12 13v7", cerrar: "M6 6l12 12M18 6L6 18",
  dividir: "M3 4h18v16H3zM12 4v16", modulos: "M4 5h4v14H4zM10 5h4v14h-4zM16 5h4v14h-4z" };
const svgI = (n, s = 20) => `<svg viewBox="0 0 24 24" width="${s}" height="${s}" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${SVG2[n]}"/></svg>`;
function pintarCinta(titulo) {
  const c = $("#cinta"), m = U2.menus.find(x => x.titulo === titulo) || U2.menus[0]; U2.cintaActiva = m.titulo;
  document.querySelectorAll("#menus .menu > button").forEach(b => b.classList.toggle("cinta-activa", b.textContent === m.titulo));
  c.innerHTML = ""; let fila = null;
  const grupo = nombre => { fila = el("div", { class: "cinta-botones" }); c.append(el("div", { class: "cinta-grupo", role: "group", "aria-label": nombre || m.titulo }, fila, el("div", { class: "cinta-et" }, nombre || ""))); };
  for (const o of m.opciones) {
    if (o.texto.startsWith("§")) { grupo(o.texto.slice(1)); continue; }
    if (o.texto === "-") { grupo(""); continue; }
    if (!fila) grupo("");
    const b = el("button", { class: "cinta-b", disabled: !o.accion, title: o.accion ? descripcion(o.texto, o.accion) : "En construcción", onclick: () => ejecutarOpcion(o) });
    b.innerHTML = window.iconoCinta ? iconoCinta(o.accion, 24) : svgI("res"); b.append(el("span", {}, o.texto.replace(/…$/, "").replace(/\s*\((Ctrl|F1)[^)]*\)$/, "")));
    fila.append(b);
  }
  const fijar = el("button", { class: "cinta-fijar", title: "Contraer la cinta (Ctrl+F1): se mostrará solo al hacer clic en una pestaña", "aria-label": "Contraer la cinta", onclick: () => alternarCinta(false) });
  fijar.innerHTML = svgI("cerrar", 14); c.append(fijar);
  if (!c.dataset.rueda) { c.dataset.rueda = "1"; c.addEventListener("wheel", ev => { if (c.scrollWidth > c.clientWidth && Math.abs(ev.deltaY) > Math.abs(ev.deltaX)) { c.scrollLeft += ev.deltaY; ev.preventDefault(); } }, { passive: false }); }
}
function alternarCinta(fija) {
  fija = fija === undefined ? !document.body.classList.contains("cinta-fija") : fija;
  document.body.classList.toggle("cinta-fija", fija); $("#cinta").hidden = !fija; guardarPref("cinta", fija ? "1" : "0");
  if (fija) pintarCinta(U2.cintaActiva || "Estadística"); else document.querySelectorAll("#menus .cinta-activa").forEach(b => b.classList.remove("cinta-activa"));
}

// ---------- interruptor de tema y modo compacto (esquina superior derecha) ----------
function controlesVentana() {
  const nav = $("#menus"); if ($("#ctrl-ventana")) return;
  const sw = el("label", { class: "interruptor", title: "Modo oscuro (Ctrl+Mayús+D)" },
    el("input", { type: "checkbox", id: "interruptor-tema", "aria-label": "Modo oscuro", onchange: ev => alternarTema(ev.target.checked) }), el("span", { class: "pista" }), el("span", { class: "sw-txt" }, "Oscuro"));
  const fijar = el("button", { class: "boton-ctrl", title: "Fijar o contraer la cinta de comandos (Ctrl+F1)", onclick: () => alternarCinta() }, "Cinta");
  nav.parentElement.append(el("div", { id: "ctrl-ventana", class: "ctrl-ventana" }, fijar, sw));
  $("#interruptor-tema").checked = document.documentElement.dataset.tema === "oscuro";
}
function alternarCompacto(f) {
  f = f === undefined ? !document.body.classList.contains("compacto") : f;
  document.body.classList.toggle("compacto", f); guardarPref("compacto", f ? "1" : "0"); setTimeout(() => window.dibujarFilas && dibujarFilas(true), 60);
}

// ---------- sesión plegable ----------
function prepararSesion() {
  const t = document.querySelector(".sesion-titulo"); if (!t || t.dataset.u2) return; t.dataset.u2 = "1";
  t.setAttribute("role", "button"); t.tabIndex = 0; t.title = "Clic para desplegar o plegar el registro de la sesión";
  const f = () => { const a = !document.body.classList.contains("sesion-abierta"); document.body.classList.toggle("sesion-abierta", a); guardarPref("sesion_abierta", a ? "1" : "0"); setTimeout(() => window.dibujarFilas && dibujarFilas(true), 60); };
  t.addEventListener("click", f); t.addEventListener("keydown", ev => { if (ev.key === "Enter") f(); });
  if (leerPref("sesion_abierta") === "1") document.body.classList.add("sesion-abierta");
}

// ---------- riel DMAIC ----------
function alternarRiel(f) {
  f = f === undefined ? !document.body.classList.contains("riel") : f;
  document.body.classList.toggle("riel", f); guardarPref("riel", f ? "1" : "0");
  if (f) document.querySelectorAll("#fases .fase.abierta").forEach(x => x.classList.remove("abierta"));
}
document.addEventListener("click", ev => {          // en el riel solo una fase desplegada a la vez
  const cab = ev.target.closest("#fases .fase-cab");
  if (cab && document.body.classList.contains("riel")) document.querySelectorAll("#fases .fase.abierta").forEach(x => { if (x !== cab.closest(".fase")) x.classList.remove("abierta"); });
}, true);
document.addEventListener("click", ev => {
  if (!document.body.classList.contains("riel") || ev.target.closest("#fases") || ev.target.closest(".velo")) return;
  document.querySelectorAll("#fases .fase.abierta").forEach(x => x.classList.remove("abierta"));
});

// ---------- menú contextual genérico ----------
function cerrarCtx() { document.querySelectorAll(".ctx-menu").forEach(m => m.remove()); }
function menuCtx(x, y, titulo, items) {
  cerrarCtx();
  const m = el("div", { class: "ctx-menu", role: "menu" }, titulo ? el("div", { class: "ctx-titulo" }, titulo) : "");
  for (const it of items) {
    if (it === "-") { m.append(el("hr")); continue; }
    const [t, atajo, fn, des, ayuda] = it;
    m.append(el("button", { role: "menuitem", disabled: !!des, title: ayuda || "", onclick: () => { cerrarCtx(); fn && fn(); } }, el("span", {}, t), el("span", { class: "ctx-atajo" }, atajo || "")));
  }
  document.body.append(m);
  const r = m.getBoundingClientRect(); m.style.left = Math.min(x, innerWidth - r.width - 6) + "px"; m.style.top = Math.min(y, innerHeight - r.height - 6) + "px";
  m.querySelector("button:not([disabled])")?.focus();
}
document.addEventListener("click", ev => { if (!ev.target.closest(".ctx-menu")) cerrarCtx(); });
document.addEventListener("keydown", ev => { if (ev.key === "Escape") cerrarCtx(); });

function ctxPestana(ev, b) {
  const id = b.dataset.p, a = P.abiertas.find(x => x.id === id), res = id.startsWith("res:"), fmt = id.startsWith("fmt:");
  const otras = P.abiertas.filter(x => x.id !== id), idx = P.abiertas.indexOf(a);
  menuCtx(ev.clientX, ev.clientY, id === "hoja" ? "Hoja de datos" : (a ? (a.titulo || (a.res && a.res.titulo) || id) : id), [
    ["Abrir a la derecha", "Ctrl+\\", () => abrirDerecha(id), !res, "Vista dividida: disponible para resultados"],
    ["Cerrar la vista derecha", "", cerrarDerecha, $("#derecha").hidden],
    "-",
    ["Repetir con los datos actuales", "F5", () => repetirRes(a.res), !res], ["Modificar parámetros…", "Ctrl+E", () => dialogoModulo(a.res.modulo, a.res.definicion), !(res && a.res.definicion)],
    ["Exportar…", "Ctrl+Mayús+E", () => res ? aplicarProyecto(api().exportar_resultado(a.res.uid)) : aplicarProyecto(api().exportar_formato(fmt ? id.slice(4) : "TABLERO")), !(res || fmt || id === "vis:TABLERO")],
    ["Vista dividida del formato", "", () => { F[id.slice(4)].dividida = !F[id.slice(4)].dividida; dibujarFormato(id.slice(4)); }, !fmt],
    "-",
    ["Cerrar", "Ctrl+W", () => cerrarPestana(id), id === "hoja"], ["Cerrar las demás", "", () => { otras.forEach(x => U2.cerradas.push(x)); P.abiertas = a ? [a] : []; activar(id); }, !otras.length],
    ["Cerrar las de la derecha", "", () => { const q = P.abiertas.slice(idx + 1); q.forEach(x => U2.cerradas.push(x)); P.abiertas = P.abiertas.slice(0, idx + 1); activar(P.abiertas.some(x => x.id === P.activa) || P.activa === "hoja" ? P.activa : id); }, id === "hoja" || idx === P.abiertas.length - 1],
    ["Reabrir la última cerrada", "Ctrl+Mayús+T", reabrir, !U2.cerradas.length]]);
}
function reabrir() { const c = U2.cerradas.pop(); if (c) abrirPestana(c.id, c.res, c.titulo); }
async function repetirRes(r) { const x = await aplicarProyecto(api().repetir_resultado(r.uid)); if (!x.error && x.resultado) abrirPestana(`res:${x.resultado.uid}`, x.resultado); }

function ctxModulo(ev, li) {
  const id = li.dataset.id, fase = li.closest(".fase")?.dataset.fase, activo = li.classList.contains("activo");
  const nombre = li.querySelector(".mod-nombre")?.textContent || id, m = (G.proyecto?.activos[fase] || []).find(x => x.id === id);
  const construido = !li.classList.contains("pendiente");
  menuCtx(ev.clientX, ev.clientY, nombre, [["Abrir", "Enter", () => abrirModulo(id), !construido], "-",
    ...(activo ? [["Marcar como hecho", "", () => aplicarProyecto(api().marcar_avance(id, "hecho")), m && m.avance === "hecho"],
                  ["Marcar en curso", "", () => aplicarProyecto(api().marcar_avance(id, "en_curso")), m && m.avance === "en_curso"],
                  ["Marcar como pendiente", "", () => aplicarProyecto(api().marcar_avance(id, "pendiente")), m && m.avance === "pendiente"], "-",
                  ["Pasar a inactivos", "", () => aplicarProyecto(api().desactivar_modulo(id))]]
                : [["Activar en esta fase", "", () => aplicarProyecto(api().activar_modulo(id, fase)), !construido]]),
    "-", ["Ver en el tablero de módulos", "", () => ventanaModulos("fase")], ["Ayuda de este módulo", "Mayús+F1", () => abrirAyuda("?" + nombre)]]);
}
function ctxGrafica(ev, g) {
  const svg = g.querySelector("svg"); if (!svg) return;
  menuCtx(ev.clientX, ev.clientY, "Gráfica", [["Copiar como imagen", "", () => copiarImagen(svg)], ["Agrandar", "F11", () => agrandar(svg)],
    ["Exportar el resultado…", "", () => { const a = P.abiertas.find(x => x.id === P.activa); if (a && a.res) aplicarProyecto(api().exportar_resultado(a.res.uid)); }, !P.activa.startsWith("res:")]]);
}
async function copiarImagen(svg) {
  try {
    const r = svg.getBoundingClientRect(), s = new XMLSerializer().serializeToString(svg), img = new Image(), c = document.createElement("canvas");
    c.width = r.width * 2; c.height = r.height * 2;
    await new Promise((ok, mal) => { img.onload = ok; img.onerror = mal; img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(s); });
    const x = c.getContext("2d"); x.fillStyle = "#fff"; x.fillRect(0, 0, c.width, c.height); x.drawImage(img, 0, 0, c.width, c.height);
    const blob = await new Promise(ok => c.toBlob(ok, "image/png"));
    await navigator.clipboard.write([new ClipboardItem({ "image/png": blob })]);
    registrarSesion({ hora: new Date().toTimeString().slice(0, 8), texto: "Gráfica copiada como imagen: pégala en Word, PowerPoint o Excel." });
  } catch (e) { registrarSesion({ hora: new Date().toTimeString().slice(0, 8), texto: "No se pudo copiar la imagen; usa Exportar para guardarla en PNG.", tipo: "aviso" }); }
}
function agrandar(svg) {
  const v = el("div", { class: "velo velo-grande", onclick: ev => { if (ev.target === v) v.remove(); } }), c = el("div", { class: "grande" });
  c.innerHTML = svg.outerHTML; c.append(el("button", { class: "boton", onclick: () => v.remove() }, "Cerrar (Esc)")); v.append(c); document.body.append(v);
  const esc = ev => { if (ev.key === "Escape") { v.remove(); document.removeEventListener("keydown", esc); } }; document.addEventListener("keydown", esc);
}
document.addEventListener("contextmenu", ev => {
  const t = ev.target;
  const tab = t.closest("#pestanas .pestana"); if (tab) { ev.preventDefault(); return ctxPestana(ev, tab); }
  const li = t.closest("#fases li[data-id]"); if (li) { ev.preventDefault(); return ctxModulo(ev, li); }
  const fc = t.closest("#fases .fase-cab"); if (fc) { ev.preventDefault(); const f = fc.closest(".fase").dataset.fase;
    return menuCtx(ev.clientX, ev.clientY, "Fase " + f, [["Mostrar sus módulos", "", () => fc.click()], ["Tablero de módulos", "Ctrl+Mayús+F", () => ventanaModulos("fase")], ["Ruta DMAIC", "Ctrl+Mayús+R", () => ventanaModulos("ruta")], ["Checklist de la fase", "", () => abrirModulo("CHECKLIST-FASE")]]); }
  const g = t.closest(".vista .grafica, #derecha .grafica"); if (g) { ev.preventDefault(); return ctxGrafica(ev, g); }
  const rc = t.closest(".inicio-reciente"); if (rc) { ev.preventDefault();
    return menuCtx(ev.clientX, ev.clientY, rc.dataset.nombre, [["Abrir", "Enter", () => abrirReciente(rc.dataset.ruta)], ["Quitar de la lista", "", async () => { const r = await api().quitar_reciente(rc.dataset.ruta); U2.recientes = r.recientes; pantallaInicio(); }]]); }
});

// ---------- vista dividida (resultados a la derecha) ----------
function abrirDerecha(id) {
  const a = P.abiertas.find(x => x.id === id); if (!a || !a.res) return;
  const d = $("#derecha"), v = $("#vista");
  v.id = "vista-tmp"; d.id = "vista";                              // pintarResultado escribe en #vista
  try { pintarResultado(a.res); } finally { d.id = "derecha"; v.id = "vista"; }
  d.prepend(el("div", { class: "derecha-cab" }, el("span", {}, "Vista derecha"), el("button", { class: "boton chico", onclick: cerrarDerecha, title: "Cerrar la vista derecha" }, "Cerrar")));
  d.hidden = false; document.body.classList.add("dividida");
  if (P.activa === id) activar("hoja"); else activar(P.activa);
  setTimeout(() => window.dibujarFilas && dibujarFilas(true), 60);
}
function cerrarDerecha() { const d = $("#derecha"); d.hidden = true; d.innerHTML = ""; document.body.classList.remove("dividida"); setTimeout(() => window.dibujarFilas && dibujarFilas(true), 60); }

// ---------- ventana de módulos: por fase (propuesta 12) o ruta DMAIC (propuesta 8) ----------
function ventanaModulos(modo) {
  document.querySelectorAll(".velo-modulos").forEach(x => x.remove());
  const v = el("div", { class: "velo velo-modulos", onclick: ev => { if (ev.target === v) v.remove(); } }), caja = el("div", { class: "ventana-mod", role: "dialog", "aria-label": "Módulos del proyecto" });
  const cuerpo = el("div", { class: "vm-cuerpo" }), inact = el("input", { type: "checkbox", id: "vm-in" });
  const seg = m => el("button", { class: "vm-seg" + (m === modo ? " activo" : ""), onclick: () => { modo = m; pintar(); caja.querySelectorAll(".vm-seg").forEach(b => b.classList.toggle("activo", b.dataset.m === m)); }, "data-m": m }, m === "fase" ? "Por fase" : "Ruta DMAIC");
  caja.append(el("div", { class: "vm-cab" }, el("b", {}, "Módulos del proyecto"), el("div", { class: "vm-segs" }, seg("fase"), seg("ruta")), el("span", { style: "flex:1" }),
    el("label", { class: "vm-check" }, inact, " Mostrar inactivos"), el("button", { class: "boton chico", onclick: () => v.remove() }, "Cerrar")), cuerpo);
  inact.addEventListener("change", () => pintar());
  const AV = { hecho: "hecho", en_curso: "en curso", pendiente: "pendiente" };
  function tarjeta(m, fase, activo) {
    const b = el("button", { class: "vm-tarjeta" + (activo ? "" : " inactiva"), title: activo ? "Clic para abrir · clic derecho para opciones" : "Inactivo · clic para abrir", "data-id": m.id,
      onclick: () => { v.remove(); abrirModulo(m.id); } }, el("b", {}, m.nombre), el("span", {}, activo ? (AV[m.avance] || "") : "inactivo"));
    b.addEventListener("contextmenu", ev => { ev.preventDefault(); ev.stopPropagation(); menuCtx(ev.clientX, ev.clientY, m.nombre, [["Abrir", "", () => { v.remove(); abrirModulo(m.id); }],
      ...(activo ? [["Marcar como hecho", "", async () => { await aplicarProyecto(api().marcar_avance(m.id, "hecho")); pintar(); }], ["Pasar a inactivos", "", async () => { await aplicarProyecto(api().desactivar_modulo(m.id)); pintar(); }]]
                 : [["Activar en " + fase, "", async () => { await aplicarProyecto(api().activar_modulo(m.id, fase)); pintar(); }]])]); });
    return b;
  }
  function pintar() {
    cuerpo.innerHTML = ""; const p = G.proyecto;
    const act = f => p ? (p.activos[f] || []) : [], ina = f => (G.catalogo[f] || []).filter(m => m.construido && !act(f).some(a => a.id === m.id));
    if (modo === "fase") {
      const g = el("div", { class: "vm-columnas" });
      for (const f of G.fases) {
        const col = el("div", { class: "vm-col", "data-fase": f.id }, el("div", { class: "vm-col-cab" }, el("span", { class: "vm-letra f-" + f.id }, f.id), f.nombre, el("span", { class: "vm-n" }, String(act(f.id).length))));
        act(f.id).forEach(m => col.append(tarjeta(m, f.id, true)));
        if (!act(f.id).length) col.append(el("p", { class: "vacio" }, "Sin módulos activos."));
        if (inact.checked) ina(f.id).forEach(m => col.append(tarjeta(m, f.id, false)));
        g.append(col);
      }
      cuerpo.append(g);
    } else {
      const pasos = el("div", { class: "vm-pasos" }), fa = p ? p.fase_actual : null, orden = "DMAIC";
      let sel = fa || "D";
      const chips = el("div", { class: "vm-chips" });
      const pintarChips = () => { chips.innerHTML = ""; act(sel).forEach(m => { const c = tarjeta(m, sel, true); c.classList.add("chip"); chips.append(c); });
        if (inact.checked) ina(sel).forEach(m => { const c = tarjeta(m, sel, false); c.classList.add("chip"); chips.append(c); });
        if (!chips.children.length) chips.append(el("p", { class: "vacio" }, "Sin módulos activos en esta fase.")); pasos.querySelectorAll(".vm-paso").forEach(x => x.classList.toggle("sel", x.dataset.f === sel)); };
      for (const f of G.fases) {
        const a = act(f.id), h = a.filter(m => m.avance === "hecho").length;
        const estado = fa && orden.indexOf(f.id) < orden.indexOf(fa) ? "cerrada" : f.id === fa ? "actual" : "por iniciar";
        pasos.append(el("button", { class: "vm-paso f-" + f.id + (f.id === fa ? " actual" : ""), "data-f": f.id, onclick: () => { sel = f.id; pintarChips(); } },
          el("b", {}, `${f.id} · ${f.nombre}`), el("span", {}, `${a.length} activos · ${h} hechos · ${estado}`)));
      }
      cuerpo.append(pasos, chips); pintarChips();
    }
  }
  pintar(); v.append(caja); document.body.append(v);
  const esc = ev => { if (ev.key === "Escape") { v.remove(); document.removeEventListener("keydown", esc); } }; document.addEventListener("keydown", esc);
}

// ---------- paleta de comandos (Ctrl+K) ----------
function itemsPaleta() {
  const out = [];
  for (const m of U2.menus) for (const o of m.opciones) if (o.accion && o.texto !== "-") out.push({ t: o.texto.replace(/…$/, ""), g: m.titulo, d: descripcion(o.texto, o.accion), fn: () => ejecutarOpcion(o), mod: o.accion.startsWith("mod:") });
  for (const f of G.fases) out.push({ t: `Ir a la fase ${f.nombre}`, g: "DMAIC", d: "Despliega la fase en el riel", fn: () => { const c = document.querySelector(`#fases .fase[data-fase='${f.id}'] .fase-cab`); if (c) c.click(); } });
  out.push({ t: "Tablero de módulos por fase", g: "Ver", d: "Ventana con las cinco fases", fn: () => ventanaModulos("fase"), a: "Ctrl+Mayús+F" },
    { t: "Ruta DMAIC", g: "Ver", d: "Fases como pasos y módulos como etiquetas", fn: () => ventanaModulos("ruta"), a: "Ctrl+Mayús+R" },
    { t: "Pantalla de inicio", g: "Ver", d: "Proyectos recientes y accesos", fn: () => pantallaInicio(true), a: "Ctrl+Mayús+H" },
    { t: "Manual de uso", g: "Ayuda", d: "Ayuda con navegador y todos los comandos", fn: () => abrirAyuda(), a: "F1" },
    { t: "Reabrir la última pestaña cerrada", g: "Ventana", d: "Recupera la pestaña cerrada", fn: reabrir, a: "Ctrl+Mayús+T" },
    { t: "Fijar o contraer la cinta", g: "Ver", d: "Cinta de comandos siempre visible", fn: () => alternarCinta(), a: "Ctrl+F1" },
    { t: "Riel DMAIC compacto o panel ancho", g: "Ver", d: "Cambia la forma del panel de fases", fn: () => alternarRiel() },
    { t: "Gestionar proyectos", g: "Archivo", d: "Inicio: proyectos abiertos y recientes", fn: () => pantallaInicio(true) });
  const ya = new Set(out.map(x => norm(x.t)));
  for (const c of U2.cmds) if (!ya.has(norm(c.n))) out.push({ t: c.n, g: c.cat, d: c.d + (c.e === "P" ? " (propuesto: próxima versión)" : ""), a: c.a !== "—" ? c.a : "", prop: c.e === "P",
    fn: () => abrirAyuda("?" + c.n) });
  for (const x of out) if (!x.a) { const c = U2.cmds.find(k => norm(k.n) === norm(x.t)); if (c && c.a !== "—") x.a = c.a; }
  return out;
}
function paleta(inicial) {
  document.querySelectorAll(".velo-paleta").forEach(x => x.remove());
  const todos = itemsPaleta(); let sel = 0, vis = [];
  const v = el("div", { class: "velo velo-paleta", onclick: ev => { if (ev.target === v) v.remove(); } });
  const inp = el("input", { class: "pal-in", placeholder: "Busca un comando, módulo o fase · @ módulos · > comandos · ? ayuda", "aria-label": "Buscar comando", value: inicial || "" });
  const lista = el("div", { class: "pal-lista", role: "listbox" });
  const caja = el("div", { class: "paleta", role: "dialog", "aria-label": "Paleta de comandos" }, inp, lista);
  const pintar = () => {
    let q = inp.value.trim(), filtro = null;
    if (q.startsWith("?")) { lista.innerHTML = ""; lista.append(el("button", { class: "pal-item sel", onclick: () => { v.remove(); abrirAyuda(q); } }, el("span", {}, `Buscar «${q.slice(1).trim()}» en el manual`))); vis = [{ fn: () => abrirAyuda(q) }]; return; }
    if (q.startsWith("@")) { filtro = "mod"; q = q.slice(1); } else if (q.startsWith(">")) { filtro = "cmd"; q = q.slice(1); }
    const n = norm(q);
    vis = todos.filter(x => (!filtro || (filtro === "mod" ? x.mod : !x.mod)) && (!n || norm(x.t + " " + x.g).includes(n)))
      .sort((a, b) => (norm(a.t).startsWith(n) ? 0 : 1) - (norm(b.t).startsWith(n) ? 0 : 1) || (a.prop ? 1 : 0) - (b.prop ? 1 : 0)).slice(0, 60);
    sel = Math.min(sel, Math.max(vis.length - 1, 0)); lista.innerHTML = "";
    vis.forEach((x, i) => lista.append(el("button", { class: "pal-item" + (i === sel ? " sel" : "") + (x.prop ? " prop" : ""), title: x.d, onclick: () => { v.remove(); x.fn(); } },
      el("span", { class: "pal-t" }, x.t), el("span", { class: "pal-g" }, x.g), el("span", { class: "pal-a" }, x.a || ""))));
    if (!vis.length) lista.append(el("p", { class: "vacio" }, "Sin coincidencias. Escribe ? para buscar en el manual."));
  };
  inp.addEventListener("input", () => { sel = 0; pintar(); });
  inp.addEventListener("keydown", ev => {
    if (ev.key === "ArrowDown") { sel = Math.min(sel + 1, vis.length - 1); pintar(); ev.preventDefault(); lista.querySelector(".sel")?.scrollIntoView({ block: "nearest" }); }
    else if (ev.key === "ArrowUp") { sel = Math.max(sel - 1, 0); pintar(); ev.preventDefault(); lista.querySelector(".sel")?.scrollIntoView({ block: "nearest" }); }
    else if (ev.key === "Enter") { ev.preventDefault(); const x = vis[sel]; if (x) { v.remove(); x.fn(); } }
    else if (ev.key === "Escape") v.remove();
  });
  v.append(caja); document.body.append(v); pintar(); inp.focus();
}

// ---------- ayuda F1 ----------
async function abrirAyuda(consulta) {
  U2.ayudaConsulta = consulta || null;
  if (P.abiertas.some(x => x.id === "vis:AYUDA")) { if (P.activa === "vis:AYUDA") pintarAyudaVista(); else activar("vis:AYUDA"); } else abrirPestana("vis:AYUDA", null, "Ayuda");
}
async function pintarAyudaVista() {
  const v = $("#vista"); v.innerHTML = ""; const c = el("div", { class: "ayuda" }); v.append(c);
  if (!U2.ayudaDatos) U2.ayudaDatos = await api().ayuda_datos();
  const h = pintarAyuda(c, U2.ayudaDatos);
  if (U2.ayudaConsulta) { const q = U2.ayudaConsulta; U2.ayudaConsulta = null; if (q.startsWith("mod:")) h.mostrar(q); else h.buscar(q.replace(/^\?/, "").trim()); }
}
window.pintarAyudaVista = pintarAyudaVista;

// ---------- pantalla de inicio (propuesta 6) ----------
async function abrirReciente(ruta) {
  if (window.guardarTabs) guardarTabs();
  const r = await aplicarProyecto(api().abrir_proyecto(ruta));
  if (r.receta) return preguntarReceta(r.receta);
  if (!r.error) { cerrarPestanas(); $("#inicio")?.remove(); window.pintarDocs && pintarDocs(); }
}
async function pantallaInicio(forzar) {
  $("#inicio")?.remove();
  if (!forzar && !U2.recientes) return;
  const cerrar = () => $("#inicio")?.remove();
  const acc = (t, fn, prim, tit) => el("button", { class: "ini-acc" + (prim ? " prim" : ""), title: tit || t, onclick: async () => { await fn(); } }, t);
  const lado = el("div", { class: "ini-lado" }, el("img", { src: "logo10.svg", alt: "D-MIKE", class: "ini-logo" }),
    el("p", { class: "ini-lema" }, "Del dato a la decisión, fase por fase."),
    acc("Nuevo proyecto", () => ACCIONES_UI.nuevo_proyecto(), true, "Abre un proyecto vacío en una pestaña nueva (Ctrl+N)"),
    acc("Abrir proyecto…", () => ACCIONES_UI.abrir_proyecto(), false, "Abre un archivo .dmike o una receta en una pestaña nueva (Ctrl+O)"),
    acc("Abrir perfil del diagnóstico…", async () => { cerrar(); ACCIONES_UI.abrir_perfil ? ACCIONES_UI.abrir_perfil() : null; }),
    acc("Importar datos (CSV, Excel)…", async () => { cerrar(); ejecutarOpcion({ accion: "importar" }); }),
    acc("Ir a la hoja de datos", async () => cerrar()),
    el("span", { style: "flex:1" }), el("small", {}, `Versión ${U2.version || ""} · Ayuda F1 · Comandos Ctrl+K`));
  const rec = el("div", { class: "ini-rec" });
  (U2.recientes || []).forEach(r => {
    const fi = "DMAIC".indexOf(r.fase || "D");
    rec.append(el("button", { class: "inicio-reciente", "data-ruta": r.ruta, "data-nombre": r.nombre, title: r.ruta + " · clic derecho para más opciones", onclick: () => abrirReciente(r.ruta) },
      el("b", {}, r.nombre), el("div", { class: "ini-barras" }, [..."DMAIC"].map((f, i) => el("span", { class: i <= fi && r.fase ? "f-" + f : "" }))),
      el("small", {}, `${r.fase ? "Fase " + r.fase + " · " : ""}${r.avance || 0} módulos con avance · ${r.fecha || ""}`)));
  });
  if (!rec.children.length) rec.append(el("p", { class: "vacio" }, "Aún no hay proyectos recientes. Los que abras o guardes aparecerán aquí."));
  const abiertos = el("div", { class: "ini-rec ini-abiertos" });
  for (const p of ((await api().proyectos()).proyectos || [])) {
    const tarjeta = el("div", { class: "inicio-abierto" + (p.activo ? " activo" : "") }, el("b", {}, p.nombre + (p.modificado ? " *" : "")),
      el("small", {}, p.ruta || "Sin guardar"),
      el("div", { class: "ini-btns" }, el("button", { class: "boton chico", onclick: () => window.cambiarDoc ? cambiarDoc(p.id) : null }, p.activo ? "Ir al proyecto" : "Cambiar a este"),
        el("button", { class: "boton chico", onclick: async () => { await (window.cerrarDocUI ? cerrarDocUI(p.id) : null); pantallaInicio(true); } }, "Cerrar")));
    abiertos.append(tarjeta);
  }
  const der = el("div", { class: "ini-der" }, el("h2", {}, "Proyectos abiertos"), el("p", { class: "ini-sub" }, "Cada proyecto abierto es una pestaña arriba de la hoja, como los dibujos en AutoCAD."), abiertos,
    el("h2", { style: "margin-top:26px" }, "Proyectos recientes"), el("p", { class: "ini-sub" }, "Clic para abrir · clic derecho para quitar de la lista."), rec,
    el("label", { class: "ini-check" }, el("input", { type: "checkbox", checked: leerPref("inicio") !== "0", onchange: ev => guardarPref("inicio", ev.target.checked ? "1" : "0") }), " Mostrar esta pantalla al iniciar"));
  const p = el("section", { id: "inicio", class: "inicio", "aria-label": "Pantalla de inicio" }, lado, der);
  document.querySelector("main.cuerpo").append(p);
  window.pintarDocs && pintarDocs();
}

// ---------- arranque ----------
function ui2Iniciar(e) {
  U2.menus = e.menus; U2.cmds = e.comandos || []; U2.version = e.version; U2.recientes = e.recientes || [];
  U2.cmds.forEach(c => { U2.desc[norm(c.n)] = c.d; });
  document.querySelectorAll("#menus .desplegable button[role='menuitem']").forEach((b, i) => {
    const t = b.textContent; for (const m of e.menus) { const o = m.opciones.find(x => x.texto === t); if (o) { b.dataset.accion = o.accion || ""; break; } }
  });
  ponerDescripciones(); controlesVentana(); prepararSesion();
  // cinta: con la cinta fija, el clic en un título de menú cambia la pestaña de la cinta en lugar de desplegar
  document.querySelector("#menus").addEventListener("click", ev => {
    const b = ev.target.closest(".menu > button"); if (!b || !document.body.classList.contains("cinta-fija")) return;
    ev.stopPropagation(); ev.preventDefault(); document.querySelectorAll("#menus .menu.abierto").forEach(m => m.classList.remove("abierto")); pintarCinta(b.textContent);
  }, true);
  if (leerPref("cinta") !== "0") alternarCinta(true);
  if (leerPref("riel") !== "0") alternarRiel(true);
  // la pestaña también se abre a la derecha con el botón del medio del mouse? no: se reserva para cerrar, como en los navegadores
  $("#pestanas").addEventListener("auxclick", ev => { const b = ev.target.closest(".pestana"); if (ev.button === 1 && b && b.dataset.p !== "hoja") cerrarPestana(b.dataset.p); });
  document.addEventListener("keydown", ev => {
    const k = ev.key.toLowerCase(), ctrl = ev.ctrlKey || ev.metaKey;
    if (ev.key === "F1") { ev.preventDefault(); return ev.shiftKey && P.activa !== "hoja" ? abrirAyuda("?" + (document.querySelector(".pestana.activa")?.textContent || "")) : abrirAyuda(); }
    if (!ctrl) return;
    if (k === "k") { ev.preventDefault(); paleta(); }
    else if (k === "f1") { ev.preventDefault(); alternarCinta(); }
    else if (k === "w" && P.activa !== "hoja") { ev.preventDefault(); cerrarPestana(P.activa); }
    else if (k === "t" && ev.shiftKey) { ev.preventDefault(); reabrir(); }
    else if (k === "\\") { ev.preventDefault(); if (P.activa.startsWith("res:")) abrirDerecha(P.activa); else if (P.activa.startsWith("fmt:")) { const f = P.activa.slice(4); F[f].dividida = !F[f].dividida; dibujarFormato(f); } }
    else if (k === "f" && ev.shiftKey) { ev.preventDefault(); ventanaModulos("fase"); }
    else if (k === "r" && ev.shiftKey) { ev.preventDefault(); ventanaModulos(); }
    else if (k === "h" && ev.shiftKey) { ev.preventDefault(); pantallaInicio(true); }
    else if (k === "e" && !ev.shiftKey && P.activa.startsWith("res:")) { ev.preventDefault(); const a = P.abiertas.find(x => x.id === P.activa); if (a.res.definicion) dialogoModulo(a.res.modulo, a.res.definicion); }
  });
  const sincronizar = () => { const s = $("#interruptor-tema"); if (s) s.checked = document.documentElement.dataset.tema === "oscuro"; };
  new MutationObserver(sincronizar).observe(document.documentElement, { attributes: true, attributeFilter: ["data-tema"] });
  const vacio = !e.archivo.nombre && (!e.hoja || !e.hoja.filas);
  if (vacio && leerPref("inicio") !== "0") pantallaInicio(true);
}
window.ui2Iniciar = ui2Iniciar;
Object.assign(ACCIONES_UI, { paleta: () => paleta(), ayuda: () => abrirAyuda(), pantalla_inicio: () => pantallaInicio(true), ventana_modulos: () => ventanaModulos("fase"),
  ruta_dmaic: () => ventanaModulos(), alternar_cinta: () => alternarCinta(), alternar_riel: () => alternarRiel() });
window.ventanaModulos = ventanaModulos; window.paleta = paleta; window.abrirAyuda = abrirAyuda;
