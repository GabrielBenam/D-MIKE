// Tablero de indicadores dentro del programa (diseño aprobado en el prototipo). Datos: formato «Tablero semanal» y catálogo de 109 KPI.
const TB = { nivel: "Ejecutivo", per: 0, area: "Todas", cat: "Todas", busca: "", d: null };
const tbFmt = (k, v) => v == null ? "—" : (k.unidad === "sigma" ? v.toFixed(2) : Math.abs(v) >= 100 ? v.toFixed(0) : (+v.toFixed(2)).toString()) + (k.unidad === "%" ? "%" : k.unidad ? " " + k.unidad : "");
const COL_E = { ok: "var(--tb-verde)", advertencia: "var(--tb-amar)", no: "var(--tb-rojo)" };
function tbSpark(k, w = 170, h = 34) {
  const v = k.vals.slice(-TB.per), pts = v.map((x, i) => [i, x]).filter(p => p[1] != null); if (!pts.length) return '<div class="tb-sin">sin datos</div>';
  const ys = pts.map(p => p[1]).concat(k.meta != null ? [k.meta] : []), mn = Math.min(...ys), mx = Math.max(...ys), sx = i => 2 + i * (w - 4) / Math.max(v.length - 1, 1), sy = y => h - 3 - (y - mn) / ((mx - mn) || 1) * (h - 6);
  const col = COL_E[k.estado] || "var(--tinta-suave)";
  return `<svg viewBox="0 0 ${w} ${h}" width="100%" height="${h}">${k.meta != null ? `<line x1="0" x2="${w}" y1="${sy(k.meta)}" y2="${sy(k.meta)}" style="stroke:var(--tinta-tenue)" stroke-dasharray="3 3"/>` : ""}
    <polyline fill="none" style="stroke:${col}" stroke-width="1.8" points="${pts.map(p => sx(p[0]) + "," + sy(p[1])).join(" ")}"/><circle cx="${sx(pts[pts.length - 1][0])}" cy="${sy(pts[pts.length - 1][1])}" r="2.8" style="fill:${col}"/></svg>`;
}
function tbTarjeta(k) {
  const bien = k.delta == null ? null : (k.sentido === ">=" ? k.delta >= 0 : k.delta <= 0);
  return `<div class="tb-kpi ${k.estado || ""}" data-i="${k.i}" tabindex="0"><div class="tb-n">${esc(k.nombre)}${k.tipo ? `<span class="tb-tipo" title="Indicador ${k.tipo.toLowerCase()} (PMBOK 7, 2.7.1.1)">${k.tipo === "Adelantado" ? "adelantado" : "atrasado"}</span>` : ""}</div><div class="tb-v">${tbFmt(k, k.ultimo)}</div>${tbSpark(k)}
    <div class="tb-m"><span>${k.meta != null ? `Meta ${k.sentido === ">=" ? "≥" : "≤"} ${tbFmt(k, k.meta)}` : "Sin meta"}</span><span class="tb-d ${bien == null ? "" : bien ? "bien" : "mal"}">${k.delta == null ? "" : (k.delta >= 0 ? "▲ " : "▼ ") + Math.abs(+k.delta.toFixed(2))}</span></div></div>`;
}
async function pintarTableroVista(recargar = true) {
  if (recargar || !TB.d) TB.d = await api().datos_tablero();
  const d = TB.d, v = $("#vista"); if (!TB.per) TB.per = Math.min(d.semanas, 12);
  const niveles = ["Ejecutivo", "Por área", "Exploración"];
  const cab = el("div", { class: "vista-barra tb-barra" }, el("h2", { class: "vista-titulo" }, "Tablero de indicadores"),
    el("div", { class: "tb-seg" }, niveles.map(n => el("button", { class: n === TB.nivel ? "on" : "", onclick: () => { TB.nivel = n; pintarTableroVista(false); } }, n))),
    el("span", { style: "flex:1" }),
    el("select", { class: "tb-sel", "aria-label": "Periodo", onchange: e => { TB.per = +e.target.value; pintarTableroVista(false); } },
      [4, 6, 8, 12].filter(n => n <= d.semanas).concat(d.semanas).filter((x, i, a) => a.indexOf(x) === i).map(n => el("option", { value: n, selected: n === TB.per }, `Últimas ${n} semanas`))),
    el("button", { class: "boton chico", onclick: () => { TB.nivel = "Exploración"; pintarTableroVista(false); } }, "Agregar indicadores"),
    el("button", { class: "boton chico", onclick: () => abrirModulo("TABLERO") }, "Capturar datos…"),
    el("button", { class: "boton chico", title: "Libro de Excel con los indicadores y sus semanas", onclick: () => aplicarProyecto(api().exportar_formato("TABLERO")) }, "Exportar…"));
  const cuerpo = el("div", { class: "tb-cuerpo" });
  v.innerHTML = ""; v.append(cab);
  if (d.avisos && d.avisos.length) v.append(el("div", { class: "tb-avisos" }, d.avisos.map(a => el("p", { class: "aviso-res" }, a))));
  v.append(cuerpo);
  if (TB.nivel === "Exploración") cuerpo.innerHTML = tbExplora(d);
  else if (!d.indicadores.length) cuerpo.innerHTML = `<div class="tb-vacio"><h3>El tablero está vacío</h3><p>Agrega indicadores del catálogo de 109 o captúralos en el formato «Tablero semanal». Los valores semanales pueden venir de la hoja de datos.</p></div>`;
  else cuerpo.innerHTML = TB.nivel === "Ejecutivo" ? tbEjecutivo(d) : tbArea(d);
  cuerpo.querySelectorAll(".tb-kpi[data-i], .tb-alerta[data-i]").forEach(e => { e.onclick = () => tbDetalle(+e.dataset.i); e.onkeydown = ev => { if (ev.key === "Enter") tbDetalle(+e.dataset.i); }; });
  cuerpo.querySelectorAll("[data-area]").forEach(b => b.onclick = () => { TB.area = b.dataset.area; pintarTableroVista(false); });
  cuerpo.querySelectorAll("[data-cat]").forEach(b => b.onclick = () => { TB.cat = b.dataset.cat; pintarTableroVista(false); });
  cuerpo.querySelectorAll("[data-agregar]").forEach(b => b.onclick = async ev => { ev.stopPropagation(); const r = await api().tablero_kpi("agregar", { kpi_id: b.dataset.agregar }); registrarSesion(r.sesion); TB.d = r.tablero || TB.d; pintarTableroVista(false); });
  cuerpo.querySelectorAll("[data-quitar]").forEach(b => b.onclick = async ev => { ev.stopPropagation(); const r = await api().tablero_kpi("quitar", { i: +b.dataset.quitar }); registrarSesion(r.sesion); TB.d = r.tablero || TB.d; pintarTableroVista(false); });
  const b = cuerpo.querySelector("#tb-busca"); if (b) b.oninput = () => { TB.busca = b.value; const p = b.selectionStart; pintarTableroVista(false); const n = $("#tb-busca"); n.focus(); n.setSelectionRange(p, p); };
}
function tbEjecutivo(d) {
  const L = d.indicadores.filter(k => k.resumen).length ? d.indicadores.filter(k => k.resumen) : d.indicadores, c = { ok: 0, advertencia: 0, no: 0 };
  L.forEach(k => { if (c[k.estado] != null) c[k.estado]++; });
  const rojos = d.indicadores.filter(k => k.estado === "no");
  return `<div class="tb-resumen"><div class="tb-res"><b>${L.length}</b><span>indicadores en el resumen</span></div><div class="tb-res ok"><b>${c.ok}</b><span>en meta</span></div>
    <div class="tb-res advertencia"><b>${c.advertencia}</b><span>en advertencia</span></div><div class="tb-res no"><b>${c.no}</b><span>fuera de meta</span></div></div>
    <div class="tb-dos"><div><h3 class="tb-h">Indicadores clave</h3><div class="tb-rejilla">${L.map(tbTarjeta).join("")}</div></div>
    <div><h3 class="tb-h">Requiere atención</h3><div class="tb-panel">${rojos.map(k => `<div class="tb-alerta" data-i="${k.i}"><div><span>${esc(k.nombre)}</span>${k.explicacion ? `<small class="tb-expl">${esc(k.explicacion)}</small>` : '<small class="tb-falta">Falta la explicación (PMBOK 7, 2.7.3.1)</small>'}</div><span class="tb-chip no">${tbFmt(k, k.ultimo)}</span></div>`).join("") || '<p class="tb-ok">Todo en meta o advertencia.</p>'}</div>
    ${d.fases && d.fases.length ? `<h3 class="tb-h">Avance del proyecto por fase</h3><div class="tb-panel">${d.fases.map(f => `<div class="tb-fase"><b class="${f.fase === d.fase_actual ? "actual" : ""}">${f.fase}</b><div class="tb-barra-f"><i style="width:${f.total ? 100 * f.hechos / f.total : 0}%"></i><i class="curso" style="width:${f.total ? 100 * f.en_curso / f.total : 0}%"></i></div><small>${f.hechos} de ${f.total}</small></div>`).join("")}<p class="tb-nota" style="margin:6px 0 0">Módulos del perfil hechos (verde) y en curso (naranja). Fase actual en naranja.</p></div>` : ""}
    <h3 class="tb-h">Trabajos en proceso</h3><div class="tb-panel">${d.wip.map(w => `<div class="tb-wip"><b>${esc(w.unidad || "")}</b><small>${esc(w.estado || "")}${w.responsable ? " · " + esc(w.responsable) : ""}</small></div>`).join("") || '<p class="tb-ok">Sin trabajos registrados en el formato.</p>'}</div></div></div>
    <p class="tb-nota">Verde cumple la meta, amarillo está entre la meta y el límite de advertencia y rojo no cumple. Las tarjetas son los indicadores marcados «En resumen».</p>`;
}
function tbArea(d) {
  const cats = ["Todas", ...new Set(d.indicadores.map(k => k.categoria))]; if (!cats.includes(TB.area)) TB.area = "Todas";
  const por = {}; d.indicadores.filter(k => TB.area === "Todas" || k.categoria === TB.area).forEach(k => (por[k.categoria] = por[k.categoria] || []).push(k));
  return `<div class="tb-chips">${cats.map(c => `<button class="${c === TB.area ? "on" : ""}" data-area="${esc(c)}">${esc(c)}</button>`).join("")}</div>` +
    Object.entries(por).map(([c, l]) => `<h3 class="tb-h">${esc(c)} · ${l.length}</h3><div class="tb-rejilla chica">${l.map(tbTarjeta).join("")}</div>`).join("");
}
function tbExplora(d) {
  const cats = ["Todas", ...new Set(d.catalogo.map(k => k.categoria))], q = TB.busca.toLowerCase(), ya = new Map(d.indicadores.filter(k => k.kpi_id).map(k => [k.kpi_id, k.i]));
  const L = d.catalogo.filter(k => (TB.cat === "Todas" || k.categoria === TB.cat) && (k.nombre + " " + k.formula).toLowerCase().includes(q));
  return `<div class="tb-chips"><input type="search" id="tb-busca" placeholder="Buscar en los ${d.catalogo.length} indicadores…" value="${esc(TB.busca)}">${cats.map(c => `<button class="${c === TB.cat ? "on" : ""}" data-cat="${esc(c)}">${esc(c)}</button>`).join("")}</div>
    <p class="tb-nota">${L.length} indicadores. «Agregar» lo suma al tablero; luego define su meta y captura sus semanas en el formato o tómalas de la hoja.</p>
    <div class="tb-cat">${L.map(k => `<div class="tb-item"><div><b>${esc(k.nombre)}</b><small>${esc(k.categoria)} · ${esc(k.unidad)} · mejor si ${k.sentido === ">=" ? "mayor" : "menor"}</small><p>${esc(k.formula)}</p></div>
      ${ya.has(k.id) ? `<button class="boton chico" data-quitar="${ya.get(k.id)}">Quitar</button>` : `<button class="boton chico primario" data-agregar="${k.id}">Agregar</button>`}</div>`).join("")}</div>`;
}
function tbDetalle(i) {
  const k = TB.d.indicadores.find(x => x.i === i); if (!k) return;
  const W = 640, H = 210, v = k.vals, num_ = v.filter(x => x != null).concat(k.meta != null ? [k.meta] : []);
  let svg = '<p class="tb-sin">Sin valores capturados.</p>';
  if (v.some(x => x != null)) {
    const mn = Math.min(...num_), mx = Math.max(...num_), pad = (mx - mn) * .1 || 1, sx = j => 40 + j * (W - 54) / Math.max(v.length - 1, 1), sy = y => H - 24 - (y - mn + pad) / (mx - mn + 2 * pad) * (H - 36);
    const x0 = sx(Math.max(0, v.length - TB.per));
    svg = `<svg viewBox="0 0 ${W} ${H}" width="100%"><rect x="${x0}" y="6" width="${W - 10 - x0}" height="${H - 30}" style="fill:var(--acento-suave)" opacity=".5"/>
      ${k.meta != null ? `<line x1="40" x2="${W - 10}" y1="${sy(k.meta)}" y2="${sy(k.meta)}" style="stroke:var(--acento)" stroke-dasharray="4 4"/><text x="44" y="${sy(k.meta) - 4}" font-size="10" style="fill:var(--acento)">meta ${tbFmt(k, k.meta)}</text>` : ""}
      ${k.adv != null ? `<line x1="40" x2="${W - 10}" y1="${sy(k.adv)}" y2="${sy(k.adv)}" style="stroke:var(--tb-amar)" stroke-dasharray="2 4"/>` : ""}
      <polyline fill="none" style="stroke:var(--tinta)" stroke-width="1.6" points="${v.map((y, j) => y == null ? null : sx(j) + "," + sy(y)).filter(Boolean).join(" ")}"/>
      ${v.map((y, j) => y == null ? "" : `<circle cx="${sx(j)}" cy="${sy(y)}" r="3" style="fill:${COL_E[k.estados[j]] || "var(--tinta-suave)"}"/>`).join("")}
      ${v.map((_, j) => `<text x="${sx(j)}" y="${H - 8}" font-size="10" text-anchor="middle" style="fill:var(--tinta-suave)">S${j + 1}</text>`).join("")}
      ${[mn - pad, (mn + mx) / 2, mx + pad].map(t => `<text x="36" y="${sy(t) + 3}" font-size="9" text-anchor="end" style="fill:var(--tinta-suave)">${tbFmt({ unidad: "" }, t)}</text>`).join("")}</svg>`;
  }
  const cat = TB.d.catalogo.find(x => x.id === k.kpi_id);
  const per = k.vals.slice(-TB.per).filter(x => x != null), est = k.estados.slice(-TB.per).filter(x => x);
  const stats = per.length ? `<p class="tb-sub">Últimas ${TB.per} semanas: promedio ${tbFmt(k, per.reduce((a, b) => a + b, 0) / per.length)} · último ${tbFmt(k, k.ultimo)} · mínimo ${tbFmt(k, Math.min(...per))} · máximo ${tbFmt(k, Math.max(...per))}${k.meta != null ? ` · en meta ${est.filter(x => x === "ok").length} de ${est.length} semanas` : ""}</p>` : "";
  const meta = el("input", { type: "number", step: "any", value: k.meta ?? "", style: "width:110px" }), adv = el("input", { type: "number", step: "any", value: k.adv ?? "", style: "width:110px" });
  const tipo = el("select", {}, [["", "(sin definir)"], ["Adelantado", "Adelantado (anticipa)"], ["Atrasado", "Atrasado (resultado)"]].map(([v, t]) => el("option", { value: v, selected: v === k.tipo }, t)));
  const expl = el("textarea", { rows: 2, placeholder: "Por qué no cumple y qué se hará (obligatorio si está en rojo)", style: "width:100%" }); expl.value = k.explicacion || "";
  const res = el("input", { type: "checkbox", checked: k.resumen });
  const cuerpo = el("div", { class: "tb-detalle" }); cuerpo.innerHTML = `<p class="tb-sub">${esc(k.categoria)}${cat ? " · " + esc(cat.formula) : ""}</p>${svg}${stats}`;
  cuerpo.append(el("div", { class: "tb-campos" }, el("label", {}, "Meta ", meta, ` ${k.unidad} (${k.sentido === ">=" ? "mayor o igual" : "menor o igual"} es mejor)`),
    el("label", {}, "Límite de advertencia ", adv), el("label", {}, "Tipo ", tipo), el("label", { class: "casilla" }, res, " Mostrar en el resumen ejecutivo"),
    el("label", { class: "tb-expl-campo" }, "Explicación si no cumple la meta (PMBOK 7, 2.7.3.1)", expl),
    el("button", { class: "boton chico", onclick: async () => { document.querySelector(".velo")?.remove(); const r = await api().tablero_kpi("quitar", { i }); registrarSesion(r.sesion); TB.d = r.tablero; pintarTableroVista(false); } }, "Quitar del tablero")));
  dialogo(k.nombre, cuerpo, async () => {
    let r = await api().tablero_kpi("meta", { i, meta: meta.value, adv: adv.value, tipo: tipo.value, explicacion: expl.value }); if (res.checked !== k.resumen) r = await api().tablero_kpi("resumen", { i, valor: res.checked });
    registrarSesion(r.sesion); TB.d = r.tablero; pintarTableroVista(false);
  }, "Guardar");
  document.querySelector(".dialogo").classList.add("ancho");
}
