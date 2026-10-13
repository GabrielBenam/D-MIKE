// Interfaz de D-MIKE. Toda la lógica vive en Python; aquí solo se dibuja y se llama al puente.
const $ = s => document.querySelector(s);
const api = () => window.pywebview.api;

function el(tag, attrs = {}, ...hijos) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") e.className = v; else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else if (v !== false && v !== null) e.setAttribute(k, v === true ? "" : v);
  }
  hijos.flat().forEach(h => e.append(h));
  return e;
}

function registrarSesion(e) {
  if (!e) return;
  if (Array.isArray(e)) return e.forEach(registrarSesion);
  const li = el("li", { class: e.tipo }, el("span", { class: "hora" }, e.hora), e.texto);
  $("#sesion").append(li); li.scrollIntoView({ block: "end" });
}

function dibujarMenus(menus) {
  const nav = $("#menus");
  const cerrar = () => nav.querySelectorAll(".menu.abierto").forEach(m => m.classList.remove("abierto"));
  for (const m of menus) {
    const caja = el("div", { class: "desplegable", role: "menu" });
    for (const o of m.opciones) {
      if (o.texto === "-") { caja.append(el("hr")); continue; }
      if (o.texto.startsWith("§")) { caja.append(el("div", { class: "menu-grupo", role: "presentation" }, o.texto.slice(1))); continue; }
      const b = el("button", { role: "menuitem", disabled: !o.accion, "data-accion": o.accion || "",
        title: o.accion ? false : "En construcción",
        onclick: async () => { cerrar(); if (o.accion.startsWith("mod:")) return abrirModulo(o.accion.slice(4));
          if (ACCIONES_UI[o.accion]) return ACCIONES_UI[o.accion]();
          registrarSesion(await api().accion(o.accion)); } });
      if (window.iconoCinta && o.accion) { const ic = document.createElement("span"); ic.className = "menu-icono"; ic.innerHTML = iconoCinta(o.accion, 16); b.append(ic); }
      b.append(o.texto); caja.append(b);
    }
    const menu = el("div", { class: "menu" });
    menu.append(el("button", { "aria-haspopup": "true", onclick: ev => {
      const abierto = menu.classList.contains("abierto"); cerrar();
      if (!abierto) menu.classList.add("abierto"); ev.stopPropagation(); } }, m.titulo), caja);
    menu.addEventListener("mouseenter", () => { if (nav.querySelector(".menu.abierto") && !menu.classList.contains("abierto")) { cerrar(); menu.classList.add("abierto"); } });
    nav.append(menu);
  }
  document.addEventListener("click", cerrar);
  document.addEventListener("keydown", ev => { if (ev.key === "Escape") cerrar(); });
}

const G = { fases: [], catalogo: {}, proyecto: null };
const AVANCE = { pendiente: "Pendiente", en_curso: "En curso", hecho: "Hecho" };

// Panel DMAIC: raíz «DMAIC» desplegable → fases → módulos activos, y dentro de cada fase el desplegable «Inactivos».
const PANEL = { inactivos: new Set() };
function pintarFases(proyecto) {
  const panel = $("#fases");
  const abiertas = new Set([...panel.querySelectorAll(".fase.abierta")].map(x => x.dataset.fase));
  if (proyecto && proyecto.fase_actual && (!G.proyecto || G.proyecto.fase_actual !== proyecto.fase_actual) && !document.body.classList.contains("riel")) abiertas.add(proyecto.fase_actual);
  G.proyecto = proyecto;
  panel.innerHTML = "";
  let cerrado = false; try { cerrado = localStorage.getItem("dmike_dmaic_cerrado") === "1"; } catch (e) { /* sin almacenamiento */ }
  const raiz = el("button", { class: "dmaic-raiz", "aria-expanded": String(!cerrado), title: "Mostrar u ocultar las fases",
    onclick: () => { const c = panel.classList.toggle("dmaic-cerrado"); raiz.setAttribute("aria-expanded", String(!c)); try { localStorage.setItem("dmike_dmaic_cerrado", c ? "1" : "0"); } catch (e) { /* nada */ } } },
    el("span", { class: "chev" }), el("span", {}, "DMAIC"), el("span", { class: "fase-cuenta" }, proyecto && proyecto.fase_actual ? `fase actual: ${proyecto.fase_actual}` : ""));
  panel.classList.toggle("dmaic-cerrado", cerrado);
  panel.append(raiz);
  const cont = el("div", { class: "dmaic-fases" }); panel.append(cont);
  const sug = new Set(proyecto ? proyecto.sugeridos : []), nor = new Set(proyecto ? proyecto.no_recomendados : []);
  for (const f of G.fases) {
    const disp = G.catalogo[f.id], act = proyecto ? proyecto.activos[f.id] || [] : [];
    const idsAct = new Set(act.map(m => m.id)), info = id => disp.find(d => d.id === id) || {};
    const inactivos = disp.filter(m => !idsAct.has(m.id));
    const abrir = (id, construido) => construido ? abrirModulo(id) : registrarSesion({ hora: new Date().toTimeString().slice(0, 8), texto: "Ese módulo todavía está en construcción.", tipo: "aviso" });
    const listaAct = act.length ? el("ul", { class: "activos" }, act.map(m => {
      const construido = info(m.id).construido;
      return el("li", { class: `activo ${m.avance}${construido ? "" : " pendiente"}`, "data-id": m.id, tabindex: "0",
        title: [m.prioridad_texto, (m.motivos || []).join("; ")].filter(Boolean).join(": ") + (construido ? " · clic para abrir" : ""),
        onclick: () => abrir(m.id, construido), onkeydown: ev => { if (ev.key === "Enter") abrir(m.id, construido); } },
        el("span", { class: "punto", "aria-label": AVANCE[m.avance] }), el("span", { class: "mod-nombre" }, m.nombre),
        m.prioridad ? el("span", { class: "prio", title: m.prioridad_texto }, m.prioridad) : "",
        proyecto && proyecto.siguiente_paso === m.id ? el("span", { class: "sig" }, "siguiente") : "",
        el("button", { class: "mod-mas", title: "Avance y opciones", "aria-label": `Opciones de ${m.nombre}`,
          onclick: ev => { ev.stopPropagation(); fichaModulo(m, construido, f.id); } }, "⋯"));
    })) : el("p", { class: "vacio" }, proyecto && proyecto.version ? "Sin módulos activos en esta fase." : "Sin módulos activos. Abre un perfil (Proyecto) o activa módulos desde «Inactivos».");
    const abiertoIn = PANEL.inactivos.has(f.id);
    const listaIn = el("ul", { class: "inactivos-lista", hidden: !abiertoIn }, inactivos.map(m => el("li", {
        class: (m.construido ? "" : "pendiente") + (nor.has(m.id) ? " norec" : ""), "data-id": m.id, tabindex: "0",
        title: m.construido ? (nor.has(m.id) ? "No recomendado por el diagnóstico · clic para abrir" : "Clic para abrir") : "En construcción",
        onclick: () => abrir(m.id, m.construido), onkeydown: ev => { if (ev.key === "Enter") abrir(m.id, m.construido); } },
      el("span", { class: "mod-nombre" }, m.nombre), sug.has(m.id) ? el("span", { class: "marca-sug" }, "sugerido") : "",
      m.construido ? el("button", { class: "mod-activar", title: `Activar en ${f.nombre}`, "aria-label": `Activar ${m.nombre}`,
        onclick: async ev => { ev.stopPropagation(); await aplicarProyecto(api().activar_modulo(m.id, f.id)); } }, "+") : "")));
    const botonIn = el("button", { class: "grupo-in", "aria-expanded": String(abiertoIn), onclick: () => {
      const a = listaIn.hidden; listaIn.hidden = !a; botonIn.setAttribute("aria-expanded", String(a)); a ? PANEL.inactivos.add(f.id) : PANEL.inactivos.delete(f.id); } },
      el("span", { class: "chev" }), `Inactivos (${inactivos.length})`);
    const pop = el("div", { class: "pop-cab" }, el("b", {}, f.nombre), el("span", { class: "pop-cuenta" }, `${act.length} activos`),
      el("div", { class: "pop-botones" }, el("button", { class: "boton chico", title: "Ruta DMAIC y módulos de cada fase en una sola ventana (Ctrl+Mayús+F)", onclick: () => window.ventanaModulos && ventanaModulos(f.id) }, "Módulos del proyecto")));
    const cuerpo = el("div", { class: "fase-cuerpo" }, pop, listaAct, botonIn, listaIn);
    const caja = el("section", { class: "fase" + (abiertas.has(f.id) ? " abierta" : "") + (proyecto && proyecto.fase_actual === f.id ? " actual" : ""), "data-fase": f.id });
    caja.append(el("button", { class: "fase-cab", "aria-expanded": String(abiertas.has(f.id)), onclick: ev => {
      const a = caja.classList.toggle("abierta"); ev.currentTarget.setAttribute("aria-expanded", a); } },
      el("span", { class: "letra", title: `${f.nombre}: clic para ver sus módulos` }, f.id), el("span", { class: "fase-nombre" }, f.nombre),
      el("span", { class: "fase-cuenta", title: "Activos de disponibles" }, `${act.length} de ${disp.length}`)), cuerpo);
    cont.append(caja);
  }
  pintarFranja(proyecto);
}

function pintarFranja(p) {
  const fr = $("#franja");
  if (!p) { fr.hidden = true; fr.innerHTML = ""; return; }
  fr.hidden = false; fr.innerHTML = "";
  const campo = (et, v, extra = {}) => el("div", { class: "fijo", ...extra }, el("span", { class: "fijo-et" }, et),
    el("span", { class: "fijo-v" + (v ? "" : " falta") }, v || "sin capturar"));
  const f = Object.fromEntries(p.fijos.map(x => [x.campo, x]));
  const logo = f.logo && f.logo.valor ? el("img", { class: "logo", src: f.logo.valor, alt: "Logo" }) : "";
  fr.append(logo, campo("Proyecto", f.nombre_proyecto.valor, { "data-campo": "nombre_proyecto" }),
    campo("Cliente o área", f.cliente_area.valor, { "data-campo": "cliente_area" }),
    campo("Responsable", f.responsable.valor, { "data-campo": "responsable" }),
    campo("Tamaño (personal)", p.empresa.tamano), campo("Giro", (p.empresa.giro || "").replace(/_/g, " ")),
    campo("Perfil", p.version ? "v" + p.version : "sin perfil"),
    el("button", { class: "boton chico", onclick: dialogoFijos }, "Editar datos fijos"));
}

async function aplicarProyecto(promesa) {
  const r = await promesa;
  registrarSesion(r.sesion);
  if (r.proyecto !== undefined) pintarFases(r.proyecto);
  if (r.hoja) pintarHoja(r.hoja);
  pintarArchivo(r.archivo);
  return r;
}

function pintarArchivo(a) {
  if (!a) return;
  G.archivo = a;
  $("#archivo").textContent = (a.nombre || "Sin guardar") + (a.modificado ? " •" : "");
  $("#archivo").title = a.modificado ? "Hay cambios sin guardar" : "";
  document.title = "D-MIKE" + (a.nombre ? " - " + a.nombre : "");
}

function confirmarDescartar(accion) {
  if (!G.archivo || !G.archivo.modificado) return accion();
  dialogo("Cambios sin guardar", el("p", {}, "El proyecto tiene cambios sin guardar. ¿Descartarlos y continuar?"), accion, "Descartar");
}

function dialogoFijos() {
  const p = G.proyecto;
  const val = k => p ? (p.fijos.find(x => x.campo === k) || {}).valor || "" : "";
  const campos = [["nombre_proyecto", "Proyecto"], ["cliente_area", "Cliente o área"], ["responsable", "Responsable"], ["notas", "Notas"]];
  const cuerpo = el("div", { class: "formulario" }, campos.map(([k, t]) =>
    el("label", {}, el("span", {}, t), el("input", { name: k, value: val(k), autocomplete: "off" }))));
  dialogo("Datos fijos del proyecto", cuerpo, () => aplicarProyecto(api().fijar_datos(
    Object.fromEntries([...cuerpo.querySelectorAll("input")].map(i => [i.name, i.value])))));
}

function fichaModulo(m, construido, fase) {
  const cuerpo = el("div", { class: "ficha" },
    m.prioridad_texto ? el("p", {}, el("b", {}, "Prioridad: "), m.prioridad_texto) : "",
    (m.motivos || []).length ? el("p", {}, el("b", {}, "Por qué: "), m.motivos.join("; ")) : "",
    m.datos_minimos ? el("p", {}, el("b", {}, "Datos mínimos: "), m.datos_minimos) : "",
    m.verificar ? el("p", { class: "nota-aviso" }, "Verifica primero lo de la fase anterior.") : "",
    m.conservado ? el("p", { class: "nota-aviso" }, "Conservado de una versión anterior del perfil.") : "",
    el("div", { class: "opciones" }, el("p", {}, "Avance"), Object.entries(AVANCE).map(([v, t]) =>
      el("label", {}, el("input", { type: "radio", name: "avance", value: v, checked: v === m.avance }), " " + t))),
    el("div", { class: "ficha-botones" },
      construido ? el("button", { class: "boton", onclick: () => { cerrarVelo(); abrirModulo(m.id); } }, "Abrir módulo") : el("p", { class: "vacio" }, "Este módulo está en construcción."),
      el("button", { class: "boton", title: "Lo quita de los activos; sus capturas y resultados se conservan", onclick: async () => { cerrarVelo(); await aplicarProyecto(api().desactivar_modulo(m.id)); } }, "Pasar a inactivos")));
  dialogo(m.nombre, cuerpo, () => aplicarProyecto(api().marcar_avance(m.id, cuerpo.querySelector("input:checked").value)), "Guardar avance");
}

function cerrarVelo() { document.querySelectorAll(".velo").forEach(v => v.remove()); }
function abrirModulo(id) { if (window.MODULOS && MODULOS[id]) MODULOS[id](); }
function cerrarPestanas() { if (window.cerrarTodas) cerrarTodas(); }

function dialogo(titulo, cuerpo, alAceptar, textoAceptar = "Aceptar") {
  const fondo = el("div", { class: "velo" });
  const cerrar = () => { fondo.remove(); $("#hoja").focus(); };
  const caja = el("div", { class: "dialogo", role: "dialog", "aria-label": titulo },
    el("div", { class: "dialogo-titulo" }, titulo), cuerpo,
    el("div", { class: "dialogo-botones" },
      el("button", { class: "boton", onclick: cerrar }, "Cancelar"),
      el("button", { class: "boton primario", onclick: async () => { const r = await alAceptar(); if (r !== false) cerrar(); } }, textoAceptar)));
  fondo.append(caja); document.body.append(fondo);
  fondo.addEventListener("keydown", ev => { if (ev.key === "Escape") cerrar(); });
  caja.querySelector("input, button").focus();
}
