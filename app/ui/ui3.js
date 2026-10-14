// D-MIKE 0.23 · varios proyectos abiertos (pestañas de documento e Inicio), botones de vista arriba del riel, una sola ventana
// de módulos (ruta DMAIC + fases), tarjeta de ayuda al pasar el cursor por la cinta, «Acerca de», nota de cada módulo con enlace
// a la ayuda, y cinta fija que absorbe la barra de herramientas.
const U3 = { tabs: {}, info: {}, tipT: null, tipCmd: null };
const ic3 = (n, s = 18) => window.iconoCinta ? iconoCinta(n, s) : "";

// ---------- varios proyectos: pestañas de documento ----------
async function pintarDocs() {
  const c = $("#docs"); if (!c) return;
  const r = await api().proyectos(); const lista = r.proyectos || [];
  const act = lista.find(p => p.activo); if (act) U3.activo = act.id;
  c.innerHTML = "";
  const ini = el("button", { class: "doc-tab doc-inicio" + (document.getElementById("inicio") ? " activo" : ""), title: "Inicio: gestionar proyectos", onclick: () => pantallaInicio(true) });
  ini.innerHTML = ic3("pantalla_inicio", 15); ini.append(el("span", {}, "Inicio")); c.append(ini);
  for (const p of lista) {
    const t = el("button", { class: "doc-tab" + (p.activo && !document.getElementById("inicio") ? " activo" : ""), title: p.ruta || p.nombre, "data-doc": String(p.id), onclick: () => cambiarDoc(p.id) },
      el("span", { class: "doc-nom" }, p.nombre + (p.modificado ? " *" : "")),
      p.etiqueta ? el("span", { class: "etiqueta-sint etiqueta-mini", title: p.etiqueta, "aria-label": p.etiqueta }, "SINTÉTICO") : "");
    const x = el("span", { class: "doc-x", role: "button", "aria-label": "Cerrar " + p.nombre, title: "Cerrar", onclick: ev => { ev.stopPropagation(); cerrarDoc(p.id); } }, "×");
    t.append(x); t.addEventListener("auxclick", ev => { if (ev.button === 1) cerrarDoc(p.id); }); c.append(t);
  }
  const mas = el("button", { class: "doc-mas", title: "Nuevo proyecto (Ctrl+N)", "aria-label": "Nuevo proyecto", onclick: () => ACCIONES_UI.nuevo_proyecto() }, "+");
  c.append(mas);
}
function guardarTabs() { const a = U3.activo; if (a) U3.tabs[a] = { abiertas: P.abiertas.slice(), activa: P.activa }; }
async function cambiarDoc(id) {
  document.getElementById("inicio")?.remove();
  const r0 = await api().proyectos(); const act = (r0.proyectos || []).find(p => p.activo);
  if (act && act.id === id) { pintarDocs(); return; }
  if (act) { U3.activo = act.id; guardarTabs(); }
  const r = await aplicarProyecto(api().cambiar_proyecto(id));
  if (r.error) return;
  const t = U3.tabs[id]; cerrarPestanas();
  if (t) { P.abiertas = t.abiertas.slice(); activar(P.abiertas.some(x => x.id === t.activa) ? t.activa : "hoja"); }
  U3.activo = id;
}
async function cerrarDoc(id) {
  const r = await api().cerrar_proyecto(id, false);
  if (r.confirmar) {
    dialogo("Cambios sin guardar", el("p", {}, `«${r.confirmar}» tiene cambios sin guardar. ¿Cerrarlo sin guardar?`), async () => {
      await aplicarProyecto(api().cerrar_proyecto(id, true)); delete U3.tabs[id]; cerrarPestanas();
    }, "Cerrar sin guardar");
    return;
  }
  await aplicarProyecto(Promise.resolve(r)); delete U3.tabs[id]; cerrarPestanas();
}

// ---------- una sola ventana de módulos: ruta DMAIC arriba, módulos de cada fase abajo ----------
function ventanaModulosUnica(faseInicial) {
  document.querySelectorAll(".velo-modulos").forEach(x => x.remove());
  const v = el("div", { class: "velo velo-modulos", onclick: ev => { if (ev.target === v) v.remove(); } });
  const caja = el("div", { class: "ventana-mod", role: "dialog", "aria-label": "Módulos del proyecto" });
  const cuerpo = el("div", { class: "vm-cuerpo" }), inact = el("input", { type: "checkbox", id: "vm-in" });
  caja.append(el("div", { class: "vm-cab" }, el("b", {}, "Módulos del proyecto"), el("span", { class: "vm-sub" }, "Ruta DMAIC y módulos de cada fase"), el("span", { style: "flex:1" }),
    el("label", { class: "vm-check" }, inact, " Mostrar inactivos"), el("button", { class: "boton chico", onclick: () => v.remove() }, "Cerrar")), cuerpo);
  inact.addEventListener("change", () => pintar());
  const AV = { hecho: "hecho", en_curso: "en curso", pendiente: "pendiente" };
  let sel = typeof faseInicial === "string" && "DMAIC".includes(faseInicial) && faseInicial.length === 1 ? faseInicial : null;
  function tarjeta(m, fase, activo) {
    const b = el("button", { class: "vm-tarjeta" + (activo ? "" : " inactiva"), "data-id": m.id, title: (U3.info[m.id] || {}).desc || "", onclick: () => { v.remove(); abrirModulo(m.id); } },
      el("b", {}, m.nombre), el("span", {}, activo ? (AV[m.avance] || "") : "inactivo"));
    b.addEventListener("contextmenu", ev => { ev.preventDefault(); ev.stopPropagation(); menuCtx(ev.clientX, ev.clientY, m.nombre, [["Abrir", "", () => { v.remove(); abrirModulo(m.id); }],
      ...(activo ? [["Marcar como hecho", "", async () => { await aplicarProyecto(api().marcar_avance(m.id, "hecho")); pintar(); }], ["Marcar en curso", "", async () => { await aplicarProyecto(api().marcar_avance(m.id, "en_curso")); pintar(); }],
                    ["Pasar a inactivos", "", async () => { await aplicarProyecto(api().desactivar_modulo(m.id)); pintar(); }]]
                 : [["Activar en " + fase, "", async () => { await aplicarProyecto(api().activar_modulo(m.id, fase)); pintar(); }]]),
      "-", ["Ayuda de este módulo", "F1", () => { v.remove(); abrirAyuda("mod:" + m.id); }]]); });
    return b;
  }
  function pintar() {
    cuerpo.innerHTML = ""; const p = G.proyecto, fa = p ? p.fase_actual : null, orden = "DMAIC";
    const act = f => p ? (p.activos[f] || []) : [], ina = f => (G.catalogo[f] || []).filter(m => m.construido && !act(f).some(a => a.id === m.id));
    const pasos = el("div", { class: "vm-pasos" });
    for (const f of G.fases) {
      const a = act(f.id), h = a.filter(m => m.avance === "hecho").length;
      const estado = fa && orden.indexOf(f.id) < orden.indexOf(fa) ? "cerrada" : f.id === fa ? "actual" : "por iniciar";
      pasos.append(el("button", { class: "vm-paso f-" + f.id + (f.id === fa ? " actual" : "") + (f.id === sel ? " sel" : ""), "data-f": f.id, onclick: () => { sel = sel === f.id ? null : f.id; pintar(); } },
        el("b", {}, `${f.id} · ${f.nombre}`), el("span", {}, `${a.length} activos · ${h} hechos · ${estado}`)));
    }
    cuerpo.append(pasos);
    const g = el("div", { class: "vm-columnas" + (sel ? " una" : "") });
    for (const f of G.fases) {
      if (sel && f.id !== sel) continue;
      const col = el("div", { class: "vm-col", "data-fase": f.id }, el("div", { class: "vm-col-cab" }, el("span", { class: "vm-letra f-" + f.id }, f.id), f.nombre, el("span", { class: "vm-n" }, String(act(f.id).length))));
      act(f.id).forEach(m => col.append(tarjeta(m, f.id, true)));
      if (!act(f.id).length) col.append(el("p", { class: "vacio" }, "Sin módulos activos."));
      if (inact.checked) ina(f.id).forEach(m => col.append(tarjeta(m, f.id, false)));
      g.append(col);
    }
    cuerpo.append(g, el("p", { class: "vacio vm-ayuda" }, "Clic en una fase de la ruta para ver solo sus módulos; otro clic vuelve a mostrar todas. Clic derecho en un módulo para su avance."));
  }
  pintar(); v.append(caja); document.body.append(v);
  const esc = ev => { if (ev.key === "Escape") { v.remove(); document.removeEventListener("keydown", esc); } }; document.addEventListener("keydown", esc);
}

// ---------- tarjeta de ayuda al pasar el cursor por la cinta (como AutoCAD) ----------
function cerrarTip() { clearTimeout(U3.tipT); document.querySelectorAll(".tip-cmd").forEach(t => t.remove()); U3.tipCmd = null; }
function mostrarTip(b) {
  cerrarTip();
  const acc = b.dataset.accion || "", nombre = b.dataset.nombre || b.textContent;
  const c = (U2.cmds || []).find(x => norm(x.n) === norm(nombre)) || null, mod = acc.startsWith("mod:") ? U3.info[acc.slice(4)] : null;
  const CTX = { G: "todo el programa", H: "la hoja", F: "los formatos", R: "los resultados", T: "el tablero", P: "el riel DMAIC" };
  const desc = (c && c.d) || (mod && mod.desc) || "";
  const lineas = [];
  if (mod) lineas.push(`Abre el módulo «${mod.titulo}»${mod.fases && mod.fases.length ? " (fase " + mod.fases.join(", ") + ")" : ""}.`);
  if (c && c.c) lineas.push("Funciona en " + c.c.map(x => CTX[x] || x).join(", ") + ".");
  if (c && c.a && c.a !== "—") lineas.push("Atajo: " + c.a + ".");
  const t = el("div", { class: "tip-cmd", role: "tooltip" });
  const cab = el("div", { class: "tip-cab" }); cab.innerHTML = ic3(acc, 30); cab.append(el("b", {}, nombre.replace(/…$/, "")));
  t.append(cab, el("p", { class: "tip-desc" }, desc || "Comando de D-MIKE."));
  if (lineas.length) t.append(el("p", { class: "tip-mas" }, lineas.join(" ")));
  t.append(el("div", { class: "tip-pie" }, el("span", {}, acc.startsWith("mod:") ? acc.slice(4) : (acc || "").toUpperCase()), el("span", {}, "Presiona F1 para más ayuda")));
  document.body.append(t);
  const r = b.getBoundingClientRect(), w = t.getBoundingClientRect();
  t.style.left = Math.max(6, Math.min(r.left, innerWidth - w.width - 8)) + "px"; t.style.top = (r.bottom + 6) + "px";
  U3.tipCmd = { acc, nombre };
}
document.addEventListener("mouseover", ev => {
  const b = ev.target.closest && ev.target.closest(".cinta-b");
  if (!b) { if (!(ev.target.closest && ev.target.closest(".tip-cmd"))) cerrarTip(); return; }
  if (U3.tipCmd && U3.tipCmd.nombre === b.dataset.nombre) return;
  clearTimeout(U3.tipT); U3.tipT = setTimeout(() => mostrarTip(b), 450);
});
document.addEventListener("mousedown", cerrarTip, true);
document.addEventListener("keydown", ev => {
  if (ev.key === "F1" && U3.tipCmd) { ev.preventDefault(); ev.stopImmediatePropagation(); const t = U3.tipCmd; cerrarTip();
    abrirAyuda(t.acc.startsWith("mod:") ? "mod:" + t.acc.slice(4) : "?" + t.nombre.replace(/…$/, "")); }
}, true);

// ---------- Acerca de D-MIKE ----------
function acercaDe() {
  const v = G.version || "";
  const cuerpo = el("div", { class: "acerca" },
    el("img", { src: document.documentElement.dataset.tema === "oscuro" ? "logo10_oscuro.svg" : "logo10.svg", alt: "D-MIKE", class: "acerca-logo" }),
    el("p", { class: "acerca-ver" }, `Versión ${v}`),
    el("p", {}, "Suite de calidad Lean Six Sigma para Windows: hoja de datos, análisis estadísticos al estilo Minitab, formatos Lean y de gestión, y modo proyecto por fases DMAIC en un solo archivo."),
    el("p", { class: "acerca-lema" }, "Del dato a la decisión, fase por fase."),
    el("h4", {}, "Créditos"), el("p", {}, "Diseño y dirección: Gabriel Benam, Ingeniero en Manufactura Aeronáutica y Black Belt Lean Six Sigma."),
    el("h4", {}, "Componentes de terceros"),
    el("ul", {}, ...["Montserrat (SIL Open Font License 1.1)", "Python, NumPy, SciPy y Matplotlib (licencias BSD y PSF)", "openpyxl (licencia MIT)", "pywebview (licencia BSD) y Microsoft Edge WebView2"].map(t => el("li", {}, t))),
    el("p", { class: "vacio" }, "Los proyectos de ejemplo usan datos sintéticos."));
  dialogo("Acerca de D-MIKE", cuerpo, () => {}, "Cerrar");
  document.querySelectorAll(".dialogo[aria-label='Acerca de D-MIKE'] .dialogo-botones button:not(.primario)").forEach(b => b.remove());
}

// ---------- nota de cada módulo: párrafo breve + enlace a la ayuda; las fuentes quedan plegadas ----------
function notaModulo(contenedor, mid) {
  if (!contenedor || contenedor.querySelector(".acerca-mod")) return;
  const i = U3.info[mid] || {}, notas = [...contenedor.querySelectorAll(":scope > .texto-res.nota, :scope > .bloques-fmt > .texto-res.nota")];
  const caja = el("div", { class: "acerca-mod" });
  const p = el("p", {}, el("b", {}, (i.titulo || mid) + ". "), (i.desc ? i.desc.replace(/\.?$/, ". ") : "") +
    (i.fases && i.fases.length ? `Se usa en la fase ${i.fases.join(", ")}. ` : "") + "Qué mide, cuándo usarlo y de dónde salen sus fórmulas: ");
  p.append(el("button", { class: "enlace", onclick: () => abrirAyuda("mod:" + mid) }, "ver en la ayuda"), ".");
  caja.append(p);
  if (notas.length) { const d = el("details", {}, el("summary", {}, "Fuentes y criterios")); notas.forEach(n => d.append(n)); caja.append(d); }
  contenedor.append(caja);
}
// se aplica cada vez que se pinta un formato o un resultado
new MutationObserver(() => {
  const v = $("#vista"); if (!v || v.hidden) return;
  const f = v.querySelector(".formato[data-formato]"); if (f) return notaModulo(f, f.dataset.formato);
  const a = P.abiertas.find(x => x.id === P.activa); if (a && a.res && a.res.definicion) notaModulo(v.querySelector(".resultado") || v, a.res.definicion.analisis);
}).observe(document.getElementById("vista"), { childList: true });

// ---------- arranque ----------
window.ui3Iniciar = function (e) {
  U3.info = e.modulos_info || {};
  pintarDocs();
  // los botones de la cinta guardan su comando para la tarjeta de ayuda (sin el globo nativo del navegador)
  new MutationObserver(() => document.querySelectorAll("#cinta .cinta-b[title]").forEach(b => {
    b.dataset.nombre = b.querySelector("span")?.textContent || ""; const m = (U2.menus || []).flatMap(x => x.opciones).find(o => o.texto.replace(/…$/, "").replace(/\s*\((Ctrl|F1)[^)]*\)$/, "") === b.dataset.nombre);
    if (m) b.dataset.accion = m.accion || ""; b.setAttribute("aria-label", b.title); b.removeAttribute("title");
  })).observe($("#cinta"), { childList: true, subtree: true });
  // cada respuesta del puente puede cambiar nombres o el indicador de cambios: se repintan las pestañas de documento
  const ap = window.aplicarProyecto; window.aplicarProyecto = async function (pr) { const r = await ap(pr); pintarDocs(); if (r && r.proyecto && window.gIniciar) gIniciar(); return r; };
  window.ventanaModulos = ventanaModulosUnica;
  Object.assign(ACCIONES_UI, { gestionar_proyectos: () => pantallaInicio(true), acerca_de: acercaDe, ventana_modulos: () => ventanaModulosUnica(), ruta_dmaic: () => ventanaModulosUnica() });
};
window.guardarTabs = guardarTabs; window.cerrarDocUI = cerrarDoc; window.pintarDocs = pintarDocs; window.cambiarDoc = cambiarDoc; window.acercaDe = acercaDe;
