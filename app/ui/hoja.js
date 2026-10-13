// Hoja de datos: selección de rangos, portapapeles, rellenar, atajos y menú contextual, con filas virtuales (solo se dibujan las visibles).
// Toda la lógica de datos vive en Python; aquí se dibuja y se llama al puente.
const RH = 22, BUF = 25;                       // alto de fila y filas extra arriba y abajo
const H = { estado: null, sel: { r: 0, c: 0 }, foc: { r: 0, c: 0 }, editor: null, vis: null, malas: [], nf: 0, nc: 0, rango: [0, 0], arrastre: false, marcadas: [] };
const esc = t => String(t).replace(/[&<>"]/g, m => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[m]));
const filaDe = r => (r < 0 ? -1 : H.vis ? (H.vis[r] ?? null) : r);          // fila de datos de una fila mostrada
const mostradaDe = f => (f < 0 ? -1 : H.vis ? H.vis.indexOf(f) : f);
const hojaEl = () => $("#hoja");

function pintarHoja(estado) {
  H.estado = estado;
  H.vis = estado.visibles;
  H.nc = estado.vista_columnas;
  H.nf = H.vis ? H.vis.length : estado.vista_filas;
  H.malas = estado.columnas.map(c => new Set(c.invalida));
  const cols = estado.columnas, tieneRol = cols.some(c => c.rol);
  let h = '<table><thead><tr class="num"><th class="fila esquina" data-accion="todo" title="Seleccionar todo"></th>';
  for (let j = 0; j < H.nc; j++) h += `<th class="enc" data-c="${j}" title="Clic: seleccionar la columna">${cols[j] ? cols[j].etiqueta : "C" + (j + 1)}</th>`;
  h += '</tr><tr class="nom"><th class="fila"></th>';
  for (let j = 0; j < H.nc; j++) h += `<th class="nombre" data-r="-1" data-f="-1" data-c="${j}">${esc(cols[j] ? cols[j].nombre : "")}</th>`;
  if (tieneRol) {
    h += '</tr><tr class="rol"><th class="fila"></th>';
    for (let j = 0; j < H.nc; j++) h += `<th title="${esc(cols[j] ? cols[j].desc || "" : "")}">${esc(cols[j] && cols[j].rol ? cols[j].rol : "")}</th>`;
  }
  h += '</tr></thead><tbody id="hoja-cuerpo"></tbody></table>';
  $("#hoja-tabla").innerHTML = h;
  H.rango = [-1, -1];
  acotar(); dibujarFilas(true); pintarSeleccion(false);
  $("#info-filtro").textContent = estado.filtro && estado.filtro.length ? `Filtro activo: ${H.nf} de ${estado.filas} filas` : "";
  $("#info-filtro").hidden = !(estado.filtro && estado.filtro.length);
}

function acotar() {
  const lim = (p, n) => ({ r: Math.max(-1, Math.min(H.nf - 1, p.r)), c: Math.max(0, Math.min(H.nc - 1, p.c)) });
  H.sel = lim(H.sel); H.foc = lim(H.foc);
}

function dibujarFilas(forzar = false) {
  const cuerpo = $("#hoja-cuerpo"); if (!cuerpo) return;
  const m = hojaEl(), cab = $("#hoja-tabla thead").offsetHeight || 70;
  const a = Math.max(0, Math.floor((m.scrollTop - cab) / RH) - BUF), b = Math.min(H.nf, Math.ceil((m.scrollTop + m.clientHeight - cab) / RH) + BUF);
  if (!forzar && a >= H.rango[0] && b <= H.rango[1]) return;
  const ini = Math.max(0, a - BUF), fin = Math.min(H.nf, b + BUF);
  H.rango = [ini, fin];
  const cols = H.estado.columnas; let h = `<tr class="relleno" style="height:${ini * RH}px"><td colspan="${H.nc + 1}"></td></tr>`;
  for (let r = ini; r < fin; r++) {
    const f = filaDe(r);
    h += `<tr><th class="fila" data-r="${r}" data-f="${f}">${f + 1}</th>`;
    for (let j = 0; j < H.nc; j++) {
      const c = cols[j], t = c && f < H.estado.filas ? c.texto[f] : "";
      const mal = c && H.malas[j].has(f), cls = [c && c.tipo && c.tipo !== "num" ? "t" : "", mal ? "mal" : ""].join(" ").trim();
      h += `<td data-r="${r}" data-f="${f}" data-c="${j}"${cls ? ` class="${cls}"` : ""}${mal ? ' title="No corresponde al tipo de la columna; no entra en los cálculos"' : ""}>${esc(t)}</td>`;
    }
    h += "</tr>";
  }
  h += `<tr class="relleno" style="height:${Math.max(0, H.nf - fin) * RH}px"><td colspan="${H.nc + 1}"></td></tr>`;
  cuerpo.innerHTML = h; pintarSeleccion(false);
}

const celdaEl = (r, c) => $(`#hoja-tabla [data-r="${r}"][data-c="${c}"]`);
const rect = () => ({ r0: Math.min(H.sel.r, H.foc.r), r1: Math.max(H.sel.r, H.foc.r), c0: Math.min(H.sel.c, H.foc.c), c1: Math.max(H.sel.c, H.foc.c) });

function pintarSeleccion(desplazar = true) {
  H.marcadas.forEach(x => x.classList.remove("sel", "rango", "rango-borde")); H.marcadas = [];
  const q = rect(), uno = q.r0 === q.r1 && q.c0 === q.c1;
  for (let r = Math.max(q.r0, H.rango[0]); r <= Math.min(q.r1, H.rango[1] - 1); r++) {
    for (let c = q.c0; c <= q.c1; c++) {
      const e = celdaEl(r, c); if (!e) continue;
      if (!uno) e.classList.add("rango");
      if (r === H.sel.r && c === H.sel.c) e.classList.add("sel");
      H.marcadas.push(e);
    }
  }
  if (q.r0 < 0 && uno) { const e = celdaEl(-1, q.c0); if (e) { e.classList.add("sel"); H.marcadas.push(e); } }
  document.querySelectorAll("#hoja-tabla .enc.activo, #hoja-tabla th.fila.activo").forEach(x => x.classList.remove("activo"));
  for (let c = q.c0; c <= q.c1; c++) { const e = $(`#hoja-tabla .enc[data-c="${c}"]`); if (e) e.classList.add("activo"); }
  if (desplazar) asegurarVisible(H.foc.r, H.foc.c);
  $("#celda-activa").textContent = (H.sel.r < 0 ? `C${H.sel.c + 1}, nombre` : `C${H.sel.c + 1}, fila ${filaDe(H.sel.r) + 1}`) +
    (uno ? "" : ` · ${q.r1 - q.r0 + 1} × ${q.c1 - q.c0 + 1}`);
  estadoRango();
}

function asegurarVisible(r, c) {
  const m = hojaEl(), cab = $("#hoja-tabla thead").offsetHeight || 70;
  if (r >= 0) {
    const y = r * RH;
    if (y < m.scrollTop) m.scrollTop = y; else if (y + RH + cab > m.scrollTop + m.clientHeight) m.scrollTop = y + RH + cab - m.clientHeight;
    dibujarFilas();
  }
  const e = celdaEl(r, c); if (e) { const rc = e.getBoundingClientRect(), rm = m.getBoundingClientRect();
    if (rc.left < rm.left + 40) m.scrollLeft -= rm.left + 40 - rc.left; else if (rc.right > rm.right) m.scrollLeft += rc.right - rm.right + 4; }
}

// Suma, promedio y cuenta de la selección (como la barra de estado de una hoja de cálculo)
function estadoRango() {
  const q = rect(); if (q.r0 === q.r1 && q.c0 === q.c1) { $("#estado-rango").textContent = ""; return; }
  let n = 0, s = 0, mn = Infinity, mx = -Infinity, cuenta = 0;
  for (let c = q.c0; c <= q.c1; c++) {
    const col = H.estado.columnas[c]; if (!col) continue;
    for (let r = Math.max(q.r0, 0); r <= q.r1; r++) {
      const f = filaDe(r); if (f === null || f < 0) continue; const t = col.texto[f]; if (t === "" || t === undefined) continue;
      cuenta++; if (col.tipo === "num" && !H.malas[c].has(f)) { const x = parseFloat(String(t).replace(/,/g, "")); if (!isNaN(x)) { n++; s += x; mn = Math.min(mn, x); mx = Math.max(mx, x); } }
    }
  }
  const f4 = x => Number.isInteger(x) ? x.toLocaleString("es-MX") : (+x.toPrecision(7)).toLocaleString("es-MX", { maximumFractionDigits: 6 });
  $("#estado-rango").textContent = n ? `Cuenta ${cuenta} · Suma ${f4(s)} · Promedio ${f4(s / n)} · Mín ${f4(mn)} · Máx ${f4(mx)}` : `Cuenta ${cuenta}`;
}

function seleccionar(r, c, extender = false) {
  H.foc = { r, c }; if (!extender) H.sel = { r, c }; acotar(); pintarSeleccion();
}
function mover(dr, dc, extender = false) { const p = extender ? H.foc : H.sel; seleccionar(p.r + dr, p.c + dc, extender); }

function ultimaFila() { let u = -1; (H.estado.columnas).forEach(c => { for (let i = c.texto.length - 1; i > u; i--) if (c.texto[i] !== "") { u = i; break; } }); return u; }
function saltar(dr, dc, extender) {                    // Ctrl + flecha: hasta el borde del bloque de datos
  const p = extender ? H.foc : H.sel, lleno = (r, c) => { const f = filaDe(r), col = H.estado.columnas[c]; return f >= 0 && col && (col.texto[f] || "") !== ""; };
  let r = p.r, c = p.c; const sigue = () => { const r2 = r + dr, c2 = c + dc; return r2 >= 0 && r2 < H.nf && c2 >= 0 && c2 < H.nc; };
  if (!sigue()) return seleccionar(r, c, extender);
  const parte = lleno(r, c) && lleno(r + dr, c + dc);
  r += dr; c += dc;
  if (parte) { while (sigue() && lleno(r + dr, c + dc)) { r += dr; c += dc; } }
  else { while (sigue() && !lleno(r, c)) { r += dr; c += dc; } }
  seleccionar(r, c, extender);
}

async function aplicar(respPromesa) {
  const r = await respPromesa;
  if (r.sesion) registrarSesion(r.sesion);
  if (r.hoja) pintarHoja(r.hoja);
  else if (r.delta) aplicarDelta(r.delta);
  if (r.archivo) pintarArchivo(r.archivo);
  return r;
}
function aplicarDelta(d) {                              // cambio de una sola celda: no se vuelve a pedir la hoja completa
  const col = H.estado.columnas[d.c]; col.texto[d.f] = d.texto;
  if (d.valida) H.malas[d.c].delete(d.f); else H.malas[d.c].add(d.f);
  col.invalida = [...H.malas[d.c]];
  const r = mostradaDe(d.f), e = celdaEl(r, d.c);
  if (e) { e.textContent = d.texto; e.classList.toggle("mal", !d.valida); if (!d.valida) e.title = "No corresponde al tipo de la columna; no entra en los cálculos"; else e.removeAttribute("title"); }
  estadoRango();
}

// ---------- edición ----------
function abrirEditor(textoInicial, modo) {
  asegurarVisible(H.sel.r, H.sel.c); const td = celdaEl(H.sel.r, H.sel.c); if (!td) return;
  const marco = hojaEl(), rc = td.getBoundingClientRect(), rm = marco.getBoundingClientRect();
  const inp = el("input", { class: "editor", spellcheck: "false" });
  inp.value = textoInicial ?? td.textContent;
  Object.assign(inp.style, { left: rc.left - rm.left + marco.scrollLeft + "px", top: rc.top - rm.top + marco.scrollTop + "px",
    width: Math.max(rc.width, 90) + "px", height: rc.height + "px", textAlign: td.classList.contains("t") || H.sel.r < 0 ? "left" : "right" });
  marco.append(inp); inp.focus(); if (textoInicial === null) inp.select();
  H.editor = { inp, modo };
  inp.addEventListener("keydown", async ev => {
    const k = ev.key, mov = { Enter: [ev.shiftKey ? -1 : 1, 0], Tab: [0, ev.shiftKey ? -1 : 1] };
    if (modo === "entrar") Object.assign(mov, { ArrowDown: [1, 0], ArrowUp: [-1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] });
    if (k === "Escape") { ev.preventDefault(); cerrarEditor(); hojaEl().focus(); }
    else if (mov[k]) { ev.preventDefault(); await confirmarEditor(); mover(...mov[k]); }
  });
  inp.addEventListener("blur", () => { if (H.editor && H.editor.inp === inp) confirmarEditor(); });
}
function cerrarEditor() { if (H.editor) { const i = H.editor.inp; H.editor = null; i.remove(); } }
async function confirmarEditor() {
  if (!H.editor) return;
  const valor = H.editor.inp.value, f = filaDe(H.sel.r), c = H.sel.c;
  cerrarEditor(); hojaEl().focus();
  if (f === null) return;
  await aplicar(f < 0 ? api().renombrar(c, valor) : api().editar(f, c, valor));
}

// ---------- portapapeles y rangos ----------
function filasDelRango(q) { const out = []; for (let r = Math.max(q.r0, 0); r <= q.r1; r++) { const f = filaDe(r); if (f !== null && f >= 0) out.push(f); } return out; }
function textoDelRango() {
  const q = rect(), fil = []; const col = c => H.estado.columnas[c];
  if (q.r0 < 0) fil.push(Array.from({ length: q.c1 - q.c0 + 1 }, (_, k) => (col(q.c0 + k) || {}).nombre || "").join("\t"));
  for (const f of filasDelRango(q)) fil.push(Array.from({ length: q.c1 - q.c0 + 1 }, (_, k) => { const c = col(q.c0 + k); return c && f < H.estado.filas ? c.texto[f] : ""; }).join("\t"));
  return fil.join("\n");
}
const hayFiltro = () => !!H.vis;
function avisoFiltro(que) { registrarSesion({ hora: hora(), texto: `${que} no está disponible con un filtro activo: quita el filtro en Datos > Quitar filtro.`, tipo: "aviso" }); }
const hora = () => new Date().toTimeString().slice(0, 8);

async function borrarSeleccion() {
  const q = rect(), fil = hayFiltro() ? filasDelRango(q) : null;
  const f0 = q.r0 < 0 ? -1 : filaDe(q.r0), f1 = Math.max(...(filasDelRango(q).length ? filasDelRango(q) : [0]), 0);
  await aplicar(api().borrar_rango(f0, q.c0, q.r1 < 0 ? -1 : f1, q.c1, fil));
}
async function pegarTexto(texto) {
  if (!texto) return;
  const q = rect(), f = filaDe(q.r0); if (f === null) return;
  const unico = !/[\t\n]/.test(texto.replace(/\n$/, ""));
  if (unico && (q.r1 > q.r0 || q.c1 > q.c0) && q.r0 >= 0) { await aplicar(api().llenar_con(f, q.c0, filaDe(q.r1) ?? f, q.c1, texto.trim(), hayFiltro() ? filasDelRango(q) : null)); return; }
  await aplicar(api().pegar(f, q.c0, texto));
}
async function copiarSeleccion(cortar = false) {
  const t = textoDelRango();
  try { await navigator.clipboard.writeText(t); } catch (e) { const a = el("textarea", { style: "position:fixed;opacity:0" }); a.value = t; document.body.append(a); a.select(); document.execCommand("copy"); a.remove(); }
  H.copiado = t;
  if (cortar) await borrarSeleccion();
  hojaEl().focus();
}
async function pegarDelPortapapeles() {
  let t = ""; try { t = await navigator.clipboard.readText(); } catch (e) { t = H.copiado || ""; }
  await pegarTexto(t);
}
async function rellenar(dir) {
  if (hayFiltro()) return avisoFiltro("Rellenar");
  const q = rect(), f0 = filaDe(q.r0), f1 = filaDe(q.r1);
  if (f0 < 0) return;
  await aplicar(api().rellenar(f0, q.c0, f1, q.c1, dir));
}
async function seleccionarTodo() {
  const u = Math.max(ultimaFila(), 0), nc = Math.max(H.estado.columnas.length, 1);
  const ya = H.sel.r === 0 && H.sel.c === 0 && H.foc.r === Math.min(u, H.nf - 1) && H.foc.c === nc - 1;
  H.sel = { r: 0, c: 0 }; H.foc = ya ? { r: H.nf - 1, c: H.nc - 1 } : { r: Math.min(u, H.nf - 1), c: nc - 1 }; pintarSeleccion(false);
}
async function insertarEnSeleccion() {
  if (hayFiltro()) return avisoFiltro("Insertar");
  const q = rect(), todoCol = q.r0 <= 0 && q.r1 >= Math.max(ultimaFila(), 0) && H.sel.r !== H.foc.r;
  if (todoCol) await aplicar(api().insertar_columna(q.c0)); else await aplicar(api().insertar_filas(Math.max(filaDe(q.r0), 0), q.r1 - Math.max(q.r0, 0) + 1));
}
async function eliminarEnSeleccion() {
  if (hayFiltro()) return avisoFiltro("Eliminar");
  const q = rect(), todoCol = q.r0 <= 0 && q.r1 >= Math.max(ultimaFila(), 0) && H.sel.r !== H.foc.r;
  if (todoCol) await aplicar(api().eliminar_columnas(q.c0, q.c1)); else await aplicar(api().eliminar_filas(Math.max(filaDe(q.r0), 0), filaDe(q.r1) ?? 0));
}
async function ordenarColumna(desc) { await aplicar(api().ejecutar_modulo("ORDENAR", { col: H.sel.c, orden: desc ? "desc" : "asc" })); }

// ---------- filtro ----------
async function dialogoFiltro() {
  const info = await api().info_filtro(); if (!info.cols.length) return;
  const cuerpo = el("div", { class: "formulario filtro" });
  const fila = (f = {}) => {
    const col = el("select", {}, info.cols.map(c => el("option", { value: c.j, selected: c.j === f.col }, `C${c.j + 1} ${c.nombre}`)));
    const op = el("select", {}, info.ops.map(([k, t]) => el("option", { value: k, selected: k === f.op }, t)));
    const val = el("input", { value: f.valor || "", placeholder: "valor", autocomplete: "off" });
    const quitar = el("button", { class: "quitar", title: "Quitar condición", onclick: () => d.remove() }, "×");
    const d = el("div", { class: "cond", "data-cond": "1" }, col, op, val, quitar); return d;
  };
  (info.filtro.length ? info.filtro : [{ col: Math.max(H.sel.c, 0) < H.estado.columnas.length ? Math.max(H.sel.c, 0) : info.cols[0].j, op: "=" }]).forEach(f => cuerpo.append(fila(f)));
  const mas = el("button", { class: "boton chico", onclick: () => cuerpo.insertBefore(fila(), mas) }, "Agregar condición");
  cuerpo.append(mas, el("p", { class: "vacio" }, "Las condiciones se combinan con «y». Las filas que no cumplen se ocultan y no entran a los análisis; no se borran."));
  const error = el("p", { class: "error-dialogo", role: "alert" }); cuerpo.append(error);
  dialogo("Filtrar filas", cuerpo, async () => {
    const conds = [...cuerpo.querySelectorAll("[data-cond]")].map(d => { const [c, o, v] = d.querySelectorAll("select, input"); return { col: +c.value, op: o.value, valor: v.value }; });
    const r = await aplicar(api().filtrar(conds));
    if (r.error) { error.textContent = r.sesion[0].texto.replace(/^Filtro no aplicado: /, ""); return false; }
  }, "Aplicar");
}
async function filtrarPorValor() {
  const f = filaDe(H.sel.r); if (f === null || f < 0) return; const t = H.estado.columnas[H.sel.c].texto[f];
  await aplicar(api().filtrar([{ col: H.sel.c, op: t === "" ? "vacio" : "=", valor: t }]));
}

// ---------- menú contextual ----------
function menuContextual(x, y) {
  document.querySelectorAll(".contextual").forEach(m => m.remove());
  const q = rect(), t = (txt, fn, atajo = "", off = false) => el("button", { disabled: off, onclick: () => { cerrar(); fn(); } }, el("span", {}, txt), el("kbd", {}, atajo));
  const cerrar = () => { m.remove(); document.removeEventListener("mousedown", fuera, true); };
  const fuera = ev => { if (!m.contains(ev.target)) cerrar(); };
  const m = el("div", { class: "contextual", role: "menu" },
    t("Cortar", () => copiarSeleccion(true), "Ctrl+X"), t("Copiar", () => copiarSeleccion(false), "Ctrl+C"), t("Pegar", pegarDelPortapapeles, "Ctrl+V"),
    t("Borrar contenido", borrarSeleccion, "Supr"), el("hr"),
    t("Rellenar hacia abajo", () => rellenar("abajo"), "Ctrl+D", q.r1 <= q.r0), t("Rellenar hacia la derecha", () => rellenar("derecha"), "Ctrl+R", q.c1 <= q.c0), el("hr"),
    t("Insertar filas o columna", insertarEnSeleccion, "Ctrl+Mayús++"), t("Eliminar filas o columnas", eliminarEnSeleccion, "Ctrl+-"), el("hr"),
    t("Ordenar de menor a mayor (A a Z)", () => ordenarColumna(false)), t("Ordenar de mayor a menor (Z a A)", () => ordenarColumna(true)),
    t("Filtrar por el valor de esta celda", filtrarPorValor), t("Filtrar…", dialogoFiltro, "Ctrl+Mayús+L"), el("hr"),
    t("Tipo de columna…", dialogoTipo), t("Buscar y reemplazar…", () => abrirModulo("REEMPLAZAR"), "Ctrl+F"));
  document.body.append(m);
  m.style.left = Math.min(x, innerWidth - m.offsetWidth - 6) + "px"; m.style.top = Math.min(y, innerHeight - m.offsetHeight - 6) + "px";
  setTimeout(() => document.addEventListener("mousedown", fuera, true));
}

// ---------- eventos ----------
function prepararHoja() {
  const hoja = hojaEl();
  hoja.append(el("div", { id: "hoja-tabla" }));
  let raf = 0; hoja.addEventListener("scroll", () => { if (!raf) raf = requestAnimationFrame(() => { raf = 0; dibujarFilas(); }); });
  const celdaDe = ev => ev.target.closest("td[data-r], th[data-r]");
  hoja.addEventListener("mousedown", ev => {
    if (ev.button === 2 && celdaDe(ev)) { const q = rect(), td = celdaDe(ev); const r = +td.dataset.r, c = +td.dataset.c;
      if (!(r >= q.r0 && r <= q.r1 && c >= q.c0 && c <= q.c1)) seleccionar(r, c); return; }
    if (ev.button !== 0) return;
    if (H.editor) confirmarEditor();
    const esq = ev.target.closest(".esquina"); if (esq) { seleccionarTodo(); hoja.focus(); return; }
    const enc = ev.target.closest(".enc");
    if (enc) { const c = +enc.dataset.c, u = Math.max(Math.min(ultimaFila(), H.nf - 1), 0);
      if (ev.shiftKey) { H.foc = { r: u, c }; } else { H.sel = { r: 0, c }; H.foc = { r: u, c }; } pintarSeleccion(false); hoja.focus(); ev.preventDefault(); return; }
    const fh = ev.target.closest("th.fila[data-r]");
    if (fh) { const r = +fh.dataset.r; H.sel = ev.shiftKey ? H.sel : { r, c: 0 }; H.foc = { r, c: Math.max(H.estado.columnas.length, 1) - 1 }; pintarSeleccion(false); hoja.focus(); ev.preventDefault(); return; }
    const td = celdaDe(ev); if (!td) return;
    seleccionar(+td.dataset.r, +td.dataset.c, ev.shiftKey); H.arrastre = true; hoja.focus();
  });
  hoja.addEventListener("mousemove", ev => {
    if (!H.arrastre) return;
    if (!(ev.buttons & 1)) { H.arrastre = false; return; }
    const td = document.elementFromPoint(ev.clientX, ev.clientY); const c = td && td.closest("td[data-r]");
    if (c && (+c.dataset.r !== H.foc.r || +c.dataset.c !== H.foc.c)) { H.foc = { r: +c.dataset.r, c: +c.dataset.c }; pintarSeleccion(false); }
  });
  document.addEventListener("mouseup", () => { H.arrastre = false; });
  hoja.addEventListener("dblclick", ev => { if (celdaDe(ev) && !ev.target.closest(".enc")) abrirEditor(null, "editar"); });
  hoja.addEventListener("contextmenu", ev => { ev.preventDefault(); if (celdaDe(ev) || ev.target.closest(".enc")) menuContextual(ev.clientX, ev.clientY); });
  hoja.addEventListener("keydown", async ev => {
    if (H.editor || ev.target !== hoja) return;
    const k = ev.key, ctrl = ev.ctrlKey || ev.metaKey, may = ev.shiftKey;
    const flecha = { ArrowDown: [1, 0], ArrowUp: [-1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] }[k];
    if (ctrl && flecha) { ev.preventDefault(); return saltar(...flecha, may); }
    if (flecha) { ev.preventDefault(); return mover(...flecha, may); }
    if (ctrl) {
      const l = k.toLowerCase();
      if (l === "a") { ev.preventDefault(); return seleccionarTodo(); }
      if (l === "c") { ev.preventDefault(); return copiarSeleccion(false); }
      if (l === "x") { ev.preventDefault(); return copiarSeleccion(true); }
      if (l === "d") { ev.preventDefault(); return rellenar("abajo"); }
      if (l === "r") { ev.preventDefault(); return rellenar("derecha"); }
      if (l === "f" || l === "h") { ev.preventDefault(); return abrirModulo("REEMPLAZAR"); }
      if (l === "l" && may) { ev.preventDefault(); return dialogoFiltro(); }
      if (k === "Home") { ev.preventDefault(); return seleccionar(0, 0, may); }
      if (k === "End") { ev.preventDefault(); return seleccionar(Math.max(Math.min(ultimaFila(), H.nf - 1), 0), Math.max(H.estado.columnas.length - 1, 0), may); }
      if (k === "-" || k === "_") { ev.preventDefault(); return eliminarEnSeleccion(); }
      if (k === "+" || k === "=") { ev.preventDefault(); return insertarEnSeleccion(); }
      return;                                                        // Ctrl+V lo atiende el evento paste; Ctrl+Z, S, B... el controlador global
    }
    if (k === "Enter") { ev.preventDefault(); const q = rect(); const mr = q.r1 > q.r0 || q.c1 > q.c0;
      if (mr) { let r = H.sel.r + (may ? -1 : 1), c = H.sel.c; if (r > q.r1) { r = q.r0; c++; } if (r < q.r0) { r = q.r1; c--; } if (c > q.c1) c = q.c0; if (c < q.c0) c = q.c1; H.sel = { r, c }; pintarSeleccion(); }
      else mover(may ? -1 : 1, 0); }
    else if (k === "Tab") { ev.preventDefault(); mover(0, may ? -1 : 1); }
    else if (k === "Home") { ev.preventDefault(); seleccionar(H.sel.r, 0, may); }
    else if (k === "End") { ev.preventDefault(); seleccionar(H.sel.r, Math.max(H.estado.columnas.length - 1, 0), may); }
    else if (k === "PageDown" || k === "PageUp") { ev.preventDefault(); const n = Math.floor(hoja.clientHeight / RH) - 2; mover(k === "PageDown" ? n : -n, 0, may); }
    else if (k === "Escape") { H.foc = { ...H.sel }; pintarSeleccion(false); }
    else if (k === "F2") { ev.preventDefault(); abrirEditor(null, "editar"); }
    else if (k === "Delete" || k === "Backspace") { ev.preventDefault(); await borrarSeleccion(); }
    else if (k.length === 1 && !ctrl && !ev.altKey) { ev.preventDefault(); abrirEditor(k, "entrar"); }
  });
  hoja.addEventListener("paste", async ev => { if (H.editor) return; ev.preventDefault(); await pegarTexto(ev.clipboardData.getData("text/plain")); });
  hoja.addEventListener("copy", ev => { if (H.editor) return; ev.preventDefault(); ev.clipboardData.setData("text/plain", textoDelRango()); });
  hoja.addEventListener("cut", async ev => { if (H.editor) return; ev.preventDefault(); ev.clipboardData.setData("text/plain", textoDelRango()); await borrarSeleccion(); });
  new ResizeObserver(() => dibujarFilas(true)).observe(hoja);
}

function dialogoTipo() {
  const c = Math.max(0, H.sel.c), actual = (H.estado.columnas[c] || {}).tipo || "num";
  const opciones = [["num", "Numérico"], ["texto", "Texto"], ["fecha", "Fecha (DD/MM/AAAA)"]];
  const cuerpo = el("div", { class: "opciones" }, el("p", {}, `Columna C${c + 1}`),
    opciones.map(([v, t]) => el("label", {}, el("input", { type: "radio", name: "tipo", value: v, checked: v === actual }), " " + t)));
  dialogo("Tipo de columna", cuerpo, () => aplicar(api().cambiar_tipo(c, cuerpo.querySelector("input:checked").value)));
}
