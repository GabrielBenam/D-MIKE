// D-MIKE v0.25 · gráficas interactivas (estilo híbrido de Excel): paleta general en Ver, opciones rápidas sobre la gráfica,
// pestaña «Gráfico» para editar propiedades y botón «Escala original». Prioridad alta. La imagen fija se conserva para reportes.
const GPAL = {"Relieve D-MIKE":["#2b2620","#6b2d0c","#9a3e0e","#dd5813","#f08a4b","#fbe8dd"],"Durazno sobre carbón":["#1c1916","#9a3e0e","#f6c9a8"],"Viridis":["#440154","#3b528b","#21918c","#5ec962","#fde725"],"Cividis":["#00224e","#35456c","#666970","#948e77","#c8b866","#fee838"],"Plasma":["#0d0887","#7e03a8","#cc4778","#f89540","#f0f921"],"Magma":["#000004","#51127c","#b73779","#fc8961","#fcfdbf"],"Clásico (azul a rojo)":["#000083","#0066ff","#00ffff","#ffff00","#ff3300","#800000"],"Divergente":["#2166ac","#67a9cf","#f7f7f7","#ef8a62","#b2182b"],"Azules":["#08306b","#2171b5","#6baed6","#c6dbef"],"Grises para imprimir":["#111111","#525252","#969696","#d9d9d9"]};
const GR = { estilos: {}, vivas: {}, paleta: null };
const gEscala = p => GPAL[p].map((c, i, a) => [i / (a.length - 1), c]);
function gTono(p, t) { const a = GPAL[p], x = Math.max(0, Math.min(1, t)) * (a.length - 1), i = Math.min(Math.floor(x), a.length - 2), f = x - i, h = c => [1, 3, 5].map(k => parseInt(c.substr(k, 2), 16)); const A = h(a[i]), B = h(a[i + 1]); return `rgb(${A.map((v, k) => Math.round(v + (B[k] - v) * f)).join(",")})`; }
const gcss = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim() || "#2b2620";
const gLay = (o = {}) => Object.assign({ paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)", margin: { l: 52, r: 18, t: 34, b: 46 }, font: { family: "Montserrat, Segoe UI, sans-serif", size: 11, color: gcss("--tinta") }, showlegend: false,
  xaxis: { gridcolor: gcss("--linea"), zerolinecolor: gcss("--linea") }, yaxis: { gridcolor: gcss("--linea"), zerolinecolor: gcss("--linea") } }, o);
const gH = (y, c, d = "dash") => ({ type: "line", xref: "paper", x0: 0, x1: 1, y0: y, y1: y, line: { color: c, dash: d, width: 1.5 } });
const gV = (x, c, d = "solid") => ({ type: "line", yref: "paper", y0: 0, y1: 1, x0: x, x1: x, line: { color: c, dash: d, width: 2 } });
const pdf = (v, m, s) => Math.exp(-(((v - m) / s) ** 2) / 2) / (s * Math.sqrt(2 * Math.PI));
// ---------- catálogo: estilos (propuestas), elementos encendibles y dibujo a partir de la especificación del módulo ----------
// probabilidad normal (la usan probnormal y residuos 4 en 1)
function gPN(s, o, p) {
  const col = s.x.map((_, i) => s.marcar && s.marcar[i] ? gcss("--acento") : gTono(p, .5)), d = [{ type: "scatter", x: s.x, y: s.q, mode: o.e.eti && s.marcar ? "markers+text" : "markers",
    marker: { size: 7, color: col }, text: s.x.map((_, i) => (o.e.eti && s.marcar && s.marcar[i]) ? s.etiq[i] : ""), textposition: "top left", textfont: { size: 9 }, name: "Datos" }], sh = [];
  if (o.e.lin && s.linea) d.push({ type: "scatter", x: s.linea.x, y: s.linea.q, mode: "lines", line: { color: gcss("--tinta"), width: 1 }, name: "Normal" });
  return { d, l: gLay({ showlegend: false, xaxis: { title: s.xl || "", gridcolor: gcss("--linea") }, yaxis: { title: "Porcentaje", tickvals: s.tq, ticktext: s.tl, gridcolor: gcss("--linea") }, shapes: sh }) };
}
const GCAT = {
  pareto: { est: ["Barras con acumulado", "Barras horizontales"], el: { acum: ["Línea acumulada", 1], c80: ["Corte en 80 %", 1], eti: ["Valores", 0] },
    f: (s, o, p) => { const col = s.conteo.map((_, i) => gTono(p, .85 - i * .6 / Math.max(1, s.conteo.length - 1)));
      if (o.s === 1) return { d: [{ type: "bar", orientation: "h", y: s.cat.slice().reverse(), x: s.conteo.slice().reverse(), marker: { color: col.slice().reverse() }, text: o.e.eti ? s.conteo.slice().reverse() : null, textposition: "outside" }], l: gLay({ margin: { l: 150, r: 20, t: 34, b: 40 } }) };
      const d = [{ type: "bar", x: s.cat, y: s.conteo, marker: { color: col }, text: o.e.eti ? s.conteo : null, textposition: "outside", name: s.yl }];
      if (o.e.acum) d.push({ type: "scatter", x: s.cat, y: s.acum, yaxis: "y2", mode: "lines+markers", line: { color: gcss("--tinta") }, name: "% acumulado" });
      return { d, l: gLay({ yaxis: { title: s.yl, gridcolor: gcss("--linea") }, yaxis2: { overlaying: "y", side: "right", range: [0, 105], ticksuffix: "%", showgrid: false, title: "% acumulado del total" },
        shapes: o.e.c80 && o.e.acum ? [{ type: "line", xref: "paper", yref: "y2", x0: 0, x1: 1, y0: 80, y1: 80, line: { color: "#b3261e", dash: "dash" } }] : [] }) }; } },
  histograma: { est: ["Barras con curva", "Densidad suavizada", "Barras con contorno"], el: { curva: ["Curva normal", 1], media: ["Media", 1], lim: ["Límites de especificación", 1] },
    f: (s, o, p) => { const x = s.x.filter(v => v !== null), b = s.bordes, w = b[1] - b[0], xs = [...Array(121)].map((_, i) => b[0] + (b[b.length - 1] - b[0]) * i / 120), d = [];
      if (o.s !== 1) d.push({ type: "histogram", x, xbins: { start: b[0], end: b[b.length - 1], size: w }, marker: { color: o.s === 2 ? "rgba(0,0,0,0)" : gTono(p, .7), line: { color: gTono(p, .35), width: o.s === 2 ? 2 : 1 } }, name: "Frecuencia" });
      if (o.e.curva || o.s === 1) d.push({ type: "scatter", x: xs, y: xs.map(v => x.length * w * pdf(v, s.media, s.desv)), mode: "lines", fill: o.s === 1 ? "tozeroy" : null, line: { color: o.s === 1 ? gTono(p, .5) : gcss("--tinta"), width: 2 }, name: "Normal" });
      const sh = []; if (o.e.media) sh.push(gV(s.media, gcss("--tinta"), "dot")); if (o.e.lim) [s.lie, s.lse].forEach(v => v !== null && v !== undefined && sh.push(gV(v, "#b3261e")));
      return { d, l: gLay({ shapes: sh, bargap: .03, yaxis: { title: "Frecuencia", gridcolor: gcss("--linea") } }) }; } },
  caja: { est: ["Cajas", "Cajas con puntos", "Violín"], el: { media: ["Media", 1], atip: ["Atípicos", 1] },
    f: (s, o, p) => { const ks = Object.keys(s.grupos); return { d: ks.map((k, i) => ({ type: o.s === 2 ? "violin" : "box", name: k, y: s.grupos[k], boxmean: o.e.media, box: { visible: true }, meanline: { visible: o.e.media },
      boxpoints: o.s === 1 ? "all" : (o.e.atip ? "outliers" : false), jitter: .4, marker: { color: gTono(p, .25 + .5 * i / Math.max(1, ks.length - 1)), size: 4 }, line: { color: gTono(p, .2 + .45 * i / Math.max(1, ks.length - 1)) } })), l: gLay({ yaxis: { title: s.yl, gridcolor: gcss("--linea") } }) }; } },
  corrida: { est: ["Línea con puntos", "Solo puntos", "Área"], el: { med: ["Mediana", 1] },
    f: (s, o, p) => ({ d: [{ type: "scatter", x: s.etiq, y: s.y, mode: o.s === 1 ? "markers" : "lines+markers", fill: o.s === 2 ? "tozeroy" : null, line: { color: gTono(p, .55) }, marker: { color: gTono(p, .4), size: 5 } }],
      l: gLay({ shapes: o.e.med ? [gH(s.mediana, gcss("--tinta"))] : [], yaxis: { title: s.yl, gridcolor: gcss("--linea") }, xaxis: { type: "category", gridcolor: gcss("--linea") } }) }) },
  carta: { est: ["Clásica", "Zonas A-B-C sombreadas", "Minimalista"], el: { lim: ["Límites de control", 1], sen: ["Señales en rojo", 1], zon: ["Líneas de zona", 0] },
    f: (s, o, p) => { const n = s.cartas.length, d = [], sh = [], lay = gLay({ grid: { rows: n, columns: 1, pattern: "independent" }, margin: { l: 56, r: 18, t: 34, b: 40 } });
      s.cartas.forEach((c, q) => { const ax = q ? String(q + 1) : "", xs = c.puntos.map((_, i) => s.etiq[i] || String(i + 1));
        d.push({ type: "scatter", x: xs, y: c.puntos, xaxis: "x" + ax, yaxis: "y" + ax, mode: o.s === 2 ? "lines" : "lines+markers", line: { color: gTono(p, .5), width: o.s === 2 ? 1.5 : 1 }, marker: { size: 6, color: c.puntos.map((_, i) => o.e.sen && c.senales.includes(i) ? "#b3261e" : gTono(p, .35)) }, name: c.nombre });
        const st = (a, col, dash) => d.push({ type: "scatter", x: xs, y: a, xaxis: "x" + ax, yaxis: "y" + ax, mode: "lines", line: { color: col, dash, width: 1.4, shape: "hv" }, hoverinfo: "skip" });
        st(c.cl, gcss("--tinta"), "solid"); if (o.e.lim) { st(c.ucl, "#b3261e", "dash"); st(c.lcl, "#b3261e", "dash"); }
        const m = c.cl[0], sg = (c.ucl[0] - m) / 3;
        if (o.e.zon) [1, 2, -1, -2].forEach(k => sh.push({ type: "line", xref: "x" + ax + " domain", yref: "y" + ax, x0: 0, x1: 1, y0: m + k * sg, y1: m + k * sg, line: { color: gcss("--linea"), dash: "dot" } }));
        if (o.s === 1) [[2, 3, .22], [1, 2, .12], [-2, -3, .22], [-1, -2, .12]].forEach(([a, b, q2]) => sh.push({ type: "rect", xref: "x" + ax + " domain", yref: "y" + ax, x0: 0, x1: 1, y0: m + a * sg, y1: m + b * sg, fillcolor: gTono(p, .6), opacity: q2, line: { width: 0 } }));
        lay["yaxis" + ax] = { title: c.nombre, gridcolor: gcss("--linea") }; lay["xaxis" + ax] = { type: "category", gridcolor: gcss("--linea"), showticklabels: q === n - 1 }; });
      lay.shapes = sh; return { d, l: lay }; } },
  capacidad: { est: ["Histograma con curvas", "Curvas con área fuera de especificación"], el: { lim: ["LIE y LSE", 1], obj: ["Objetivo", 1], ind: ["Cuadro de índices", 1], glob: ["Curva global", 1] },
    f: (s, o, p) => { const x = s.x.filter(v => v !== null), b = s.bordes, w = b[1] - b[0], lo = Math.min(b[0], s.lie ?? b[0]), hi = Math.max(b[b.length - 1], s.lse ?? b[b.length - 1]), xs = [...Array(161)].map((_, i) => lo + (hi - lo) * i / 160), d = [];
      if (o.s === 0) d.push({ type: "histogram", x, xbins: { start: b[0], end: b[b.length - 1], size: w }, marker: { color: gTono(p, .72) }, name: "Datos" });
      const yd = xs.map(v => x.length * w * pdf(v, s.media, s.s_dentro));
      d.push({ type: "scatter", x: xs, y: yd, mode: "lines", line: { color: gTono(p, .4), width: 2 }, name: "Dentro de subgrupos" });
      if (o.e.glob) d.push({ type: "scatter", x: xs, y: xs.map(v => x.length * w * pdf(v, s.media, s.s_global)), mode: "lines", line: { color: gcss("--tinta"), width: 1.4, dash: "dash" }, name: "Global" });
      if (o.s === 1) [[v => s.lie !== null && v < s.lie], [v => s.lse !== null && v > s.lse]].forEach(([f]) => { const xx = xs.filter(f); if (xx.length) d.push({ type: "scatter", x: xx, y: xx.map(v => x.length * w * pdf(v, s.media, s.s_dentro)), fill: "tozeroy", mode: "none", fillcolor: "rgba(179,38,30,.35)", name: "Fuera" }); });
      const sh = []; if (o.e.lim) [s.lie, s.lse].forEach(v => v !== null && sh.push(gV(v, "#b3261e"))); if (o.e.obj && s.obj !== null) sh.push(gV(s.obj, "#2e7d32", "dash"));
      const I = s.indices || {}, txt = ["cp", "cpk", "pp", "ppk"].filter(k => I[k] !== undefined && I[k] !== null).map(k => `${k.toUpperCase().replace("K", "k").replace("PP", "Pp").replace("CP", "Cp")} ${(+I[k]).toFixed(2)}`).join("<br>");
      return { d, l: gLay({ shapes: sh, bargap: .03, showlegend: true, legend: { orientation: "h", y: -0.18 }, annotations: o.e.ind && txt ? [{ xref: "paper", yref: "paper", x: .99, y: .98, xanchor: "right", showarrow: false, align: "left", bgcolor: gcss("--superficie"), bordercolor: gcss("--linea"), text: txt }] : [] }) }; } },
  regresion: { est: ["Puntos con recta", "Puntos coloreados por residual"], el: { rec: ["Recta ajustada", 1], ic: ["IC 95 % de la media", 1], ip: ["Intervalo de predicción", 0], ec: ["R² y S", 1] },
    f: (s, o, p) => { const res = s.x.map((xv, i) => { let k = 0; while (k < s.grid.length - 1 && s.grid[k] < xv) k++; return s.y[i] - s.pred[k]; });
      const d = [{ type: "scatter", x: s.x, y: s.y, mode: "markers", marker: { size: 7, color: o.s === 1 ? res : gTono(p, .45), colorscale: gEscala(p), opacity: .85 }, name: "Datos" }];
      if (o.e.ic) d.push({ type: "scatter", x: s.grid.concat(s.grid.slice().reverse()), y: s.ic_hi.concat(s.ic_lo.slice().reverse()), fill: "toself", fillcolor: "rgba(221,88,19,.14)", line: { width: 0 }, mode: "lines", name: "IC 95 %" });
      if (o.e.ip) d.push({ type: "scatter", x: s.grid, y: s.ip_hi, mode: "lines", line: { dash: "dot", color: gTono(p, .5) }, name: "IP" }, { type: "scatter", x: s.grid, y: s.ip_lo, mode: "lines", line: { dash: "dot", color: gTono(p, .5) }, showlegend: false });
      if (o.e.rec) d.push({ type: "scatter", x: s.grid, y: s.pred, mode: "lines", line: { color: gcss("--tinta"), width: 2 }, name: "Ajuste" });
      return { d, l: gLay({ xaxis: { title: s.xl, gridcolor: gcss("--linea") }, yaxis: { title: s.yl, gridcolor: gcss("--linea") }, annotations: o.e.ec ? [{ xref: "paper", yref: "paper", x: .01, y: .99, xanchor: "left", showarrow: false, text: `R² = ${(100 * s.r2).toFixed(1)} % · S = ${(+s.s).toFixed(3)}` }] : [] }) }; } },
  contorno: { est: ["Relleno", "Solo líneas", "Mapa de calor"], el: { eti: ["Etiquetas de nivel", 1], pts: ["Corridas del diseño", 1] },
    f: (s, o, p) => { const d = [{ type: o.s === 2 ? "heatmap" : "contour", x: s.x, y: s.y, z: s.z, colorscale: gEscala(p), contours: { coloring: o.s === 1 ? "lines" : "fill", showlabels: o.e.eti }, line: { width: o.s === 1 ? 2 : .5 }, colorbar: { title: s.zl, thickness: 12 } }];
      if (o.e.pts) d.push({ type: "scatter", x: s.px, y: s.py, mode: "markers", marker: { color: gcss("--tinta"), size: 6, line: { color: "#fff", width: 1 } }, name: "Corridas" });
      return { d, l: gLay({ xaxis: { title: s.xl, gridcolor: gcss("--linea") }, yaxis: { title: s.yl, gridcolor: gcss("--linea") } }) }; } },
  superficie: { est: ["Sólida con contorno en el piso", "Malla translúcida", "Curvas sobre la superficie", "Corridas y residuales"], el: { piso: ["Contorno en el piso", 1], pts: ["Corridas del diseño", 0], plano: ["Plano de especificación", 0] }, tresd: true,
    f: (s, o, p) => { const op = o.s === 1 ? .55 : o.s === 3 ? .85 : 1, sp = { type: "surface", x: s.x, y: s.y, z: s.z, colorscale: gEscala(p), opacity: op, colorbar: { title: s.zl, thickness: 12, len: .6 },
        contours: { z: { show: o.e.piso || o.s === 2, usecolormap: o.s !== 2, color: "#fff", width: 2, project: { z: o.e.piso && o.s !== 2 } }, x: { show: o.s === 1, color: gcss("--tinta") }, y: { show: o.s === 1, color: gcss("--tinta") } } }, d = [sp];
      if (o.e.pts || o.s === 3) d.push({ type: "scatter3d", mode: "markers", x: s.px, y: s.py, z: s.pz, marker: { size: 4, color: gcss("--acento"), line: { color: "#fff", width: 1 } }, name: "Corridas" });
      if (o.e.plano && o.plano !== undefined && o.plano !== "") d.push({ type: "surface", x: s.x, y: s.y, z: s.z.map(r => r.map(() => +o.plano)), showscale: false, opacity: .35, colorscale: [[0, "#2b6f8f"], [1, "#2b6f8f"]] });
      const ej = t => ({ title: { text: t }, gridcolor: gcss("--linea"), showbackground: false });
      return { d, l: gLay({ margin: { l: 0, r: 0, t: 30, b: 0 }, scene: { xaxis: ej(s.xl), yaxis: ej(s.yl), zaxis: ej(s.zl), camera: { eye: { x: 1.55, y: -1.55, z: .95 } }, aspectmode: "manual", aspectratio: { x: 1, y: 1, z: .7 } } }) }; } },
  pefectos: { est: ["Barras", "Piruleta"], el: { lin: ["Línea de significancia", 1], eti: ["Valores", 0] },
    f: (s, o, p) => { const col = s.terminos.map(t => s.sig.includes(t) ? gTono(p, .6) : gTono(p, .88)), d = [];
      if (o.s === 1) { d.push({ type: "scatter", y: s.terminos, x: s.valores, mode: "markers", marker: { size: 12, color: col } }); s.terminos.forEach((t, i) => d.push({ type: "scatter", y: [t, t], x: [0, s.valores[i]], mode: "lines", line: { color: gcss("--linea") }, hoverinfo: "skip" })); }
      else d.push({ type: "bar", orientation: "h", y: s.terminos, x: s.valores, marker: { color: col, line: { color: gTono(p, .5), width: 1 } }, text: o.e.eti ? s.valores.map(v => v.toFixed(2)) : null, textposition: "outside" });
      return { d, l: gLay({ margin: { l: 110, r: 20, t: 34, b: 40 }, xaxis: { title: "Efecto estandarizado (valor absoluto)", gridcolor: gcss("--linea") }, shapes: o.e.lin ? [gV(s.crit, "#b3261e", "dash")] : [] }) }; } },
  efectos: { est: ["Paneles por factor"], el: { med: ["Media general", 1], pts: ["Marcadores", 1] },
    f: (s, o, p) => { const n = s.efectos.length, lay = gLay({ grid: { rows: 1, columns: n, pattern: "independent" } }), d = [];
      s.efectos.forEach((e, q) => { const ax = q ? String(q + 1) : ""; d.push({ type: "scatter", x: e.niveles, y: e.medias, xaxis: "x" + ax, yaxis: "y" + ax, mode: o.e.pts ? "lines+markers" : "lines", line: { color: gTono(p, .3 + .5 * q / Math.max(1, n - 1)), width: 3 }, name: e.factor });
        lay["xaxis" + ax] = { title: { text: e.factor, font: { size: 10 } }, type: "category" }; lay["yaxis" + ax] = { matches: q ? "y" : undefined, gridcolor: gcss("--linea") };
        if (o.e.med) (lay.shapes = lay.shapes || []).push({ type: "line", xref: "x" + ax + " domain", yref: "y" + ax, x0: 0, x1: 1, y0: s.media, y1: s.media, line: { color: gcss("--linea"), dash: "dot" } }); });
      return { d, l: lay }; } },
  interaccion: { est: ["Paneles por par"], el: { pts: ["Marcadores", 1] },
    f: (s, o, p) => { const n = s.pares.length, lay = gLay({ grid: { rows: 1, columns: n, pattern: "independent" }, showlegend: false }), d = [];
      s.pares.forEach((pr, q) => { const ax = q ? String(q + 1) : ""; pr.series.forEach((se, k) => d.push({ type: "scatter", x: pr.niveles, y: se.medias, xaxis: "x" + ax, yaxis: "y" + ax, mode: o.e.pts ? "lines+markers" : "lines", line: { color: gTono(p, k ? .75 : .3), width: 3, dash: k ? "dash" : "solid" }, name: se.nombre }));
        lay["xaxis" + ax] = { title: { text: pr.par, font: { size: 10 } }, type: "category" }; lay["yaxis" + ax] = { gridcolor: gcss("--linea") }; });
      return { d, l: lay }; } },
  probnormal: { est: ["Puntos con recta"], el: { lin: ["Recta de referencia", 1], eti: ["Etiquetas de los puntos marcados", 1] },
    f: (s, o, p) => gPN(s, o, p, "", "") },
  residuos: { est: ["4 en 1"], el: { lin: ["Recta de referencia", 1], cero: ["Línea en cero", 1] },
    f: (s, o, p) => { const pn = gPN(s.pn, o, p, "", ""), n = s.res.length, d = [], lay = gLay({ grid: { rows: 2, columns: 2, pattern: "independent" }, showlegend: false, margin: { l: 56, r: 18, t: 44, b: 44 } });
      pn.d.forEach(t => d.push(Object.assign({}, t, { xaxis: "x", yaxis: "y" })));
      d.push({ type: "scatter", x: s.aj, y: s.res, mode: "markers", xaxis: "x2", yaxis: "y2", marker: { color: gTono(p, .45), size: 6 } });
      d.push({ type: "histogram", x: s.res, xaxis: "x3", yaxis: "y3", marker: { color: gTono(p, .75), line: { color: gTono(p, .35), width: 1 } } });
      d.push({ type: "scatter", x: s.res.map((_, i) => i + 1), y: s.res, mode: "lines+markers", xaxis: "x4", yaxis: "y4", line: { color: gTono(p, .5), width: 1 }, marker: { size: 4, color: gTono(p, .4) } });
      Object.assign(lay, { xaxis: { title: "Residuo", gridcolor: gcss("--linea") }, yaxis: pn.l.yaxis, xaxis2: { title: "Ajustado", gridcolor: gcss("--linea") }, yaxis2: { title: "Residuo", gridcolor: gcss("--linea") },
        xaxis3: { title: "Residuo", gridcolor: gcss("--linea") }, yaxis3: { title: "Frecuencia", gridcolor: gcss("--linea") }, xaxis4: { title: "Orden de observación", gridcolor: gcss("--linea") }, yaxis4: { title: "Residuo", gridcolor: gcss("--linea") } });
      lay.shapes = (o.e.lin ? (pn.l.shapes || []).map(sh => Object.assign({}, sh, { xref: "x", yref: "y" })) : []);
      if (o.e.cero) [["x2", "y2"], ["x4", "y4"]].forEach(([xa, ya]) => lay.shapes.push({ type: "line", xref: xa + " domain", yref: ya, x0: 0, x1: 1, y0: 0, y1: 0, line: { color: gcss("--tinta"), width: 1 } }));
      return { d, l: lay }; } },
  ascenso: { est: ["Respuesta y factores por paso"], el: { lim: ["Límites seguros", 1] },
    f: (s, o, p) => { const n = s.factores.length + 1, d = [], lay = gLay({ grid: { rows: 1, columns: n, pattern: "independent" }, showlegend: false, margin: { l: 52, r: 18, t: 44, b: 44 } }), sh = [];
      d.push({ type: "scatter", x: s.pasos, y: s.y, mode: "lines+markers", line: { color: gTono(p, .5) }, marker: { size: 6, color: gTono(p, .4) }, name: s.yl });
      lay.xaxis = { title: "Paso", dtick: 1, gridcolor: gcss("--linea") }; lay.yaxis = { title: s.yl + " del modelo", gridcolor: gcss("--linea") };
      s.factores.forEach((f, q) => { const ax = String(q + 2);
        d.push({ type: "scatter", x: s.pasos, y: f.valores, xaxis: "x" + ax, yaxis: "y" + ax, mode: "lines+markers", line: { color: gTono(p, .3 + .5 * q / Math.max(1, n - 2)) }, marker: { size: 6 }, name: f.nombre });
        lay["xaxis" + ax] = { title: "Paso", dtick: 1, gridcolor: gcss("--linea") }; lay["yaxis" + ax] = { title: f.nombre, gridcolor: gcss("--linea") };
        if (o.e.lim && f.limite) f.limite.forEach(v => sh.push({ type: "line", xref: "x" + ax + " domain", yref: "y" + ax, x0: 0, x1: 1, y0: v, y1: v, line: { color: "#b3261e", dash: "dash" } })); });
      lay.shapes = sh; if (s.detenida) lay.annotations = [{ xref: "paper", yref: "paper", x: .5, y: -.28, showarrow: false, text: "La ruta se detiene antes del primer paso que cruzaría los límites seguros", font: { size: 10 } }];
      return { d, l: lay }; } },
  optimizacion: { est: ["Respuestas contra factores"], el: { opt: ["Óptimo", 1], obj: ["Objetivo", 1], reg: ["Región de búsqueda", 1] },
    f: (s, o, p) => { const R = s.resps.length, C = s.factores.length, d = [], sh = [], lay = gLay({ grid: { rows: R, columns: C, pattern: "independent" }, showlegend: false, margin: { l: 56, r: 18, t: 44, b: 44 } });
      s.resps.forEach((r, a) => s.factores.forEach((fn, i) => { const k = a * C + i + 1, ax = k > 1 ? String(k) : "", cv = r.curvas[i];
        d.push({ type: "scatter", x: cv.x, y: cv.y, mode: "lines", xaxis: "x" + ax, yaxis: "y" + ax, line: { color: gTono(p, .5), width: 2 } });
        lay["xaxis" + ax] = { title: a === R - 1 ? fn : "", gridcolor: gcss("--linea") }; lay["yaxis" + ax] = { title: i === 0 ? r.nombre : "", gridcolor: gcss("--linea") };
        if (o.e.opt) sh.push({ type: "line", xref: "x" + ax, yref: "y" + ax + " domain", x0: s.optimo[i], x1: s.optimo[i], y0: 0, y1: 1, line: { color: "#b3261e", width: 1.4 } });
        if (o.e.obj && r.objetivo !== null) sh.push({ type: "line", xref: "x" + ax + " domain", yref: "y" + ax, x0: 0, x1: 1, y0: r.objetivo, y1: r.objetivo, line: { color: gTono(p, .3), dash: "dash" } });
        if (o.e.reg) { const [lo, hi] = s.busqueda[i]; [lo, hi].forEach(v => sh.push({ type: "line", xref: "x" + ax, yref: "y" + ax + " domain", x0: v, x1: v, y0: 0, y1: 1, line: { color: gcss("--linea"), dash: "dot" } })); } }));
      lay.shapes = sh; lay.annotations = [{ xref: "paper", yref: "paper", x: 0, y: 1.1, xanchor: "left", showarrow: false, font: { size: 10 }, text: "Línea roja: óptimo · punteado: región de búsqueda" + (s.autorizada ? " (limitada por los límites seguros)" : "") }];
      return { d, l: lay }; } },
  tukey: { est: ["Intervalos por par"], el: { cero: ["Línea en cero", 1], sig: ["Resaltar los que difieren", 1] },
    f: (s, o, p) => { const d = [], n = s.pares.length;
      s.pares.forEach((q, i) => { const c = o.e.sig && q.sig ? gTono(p, .55) : gTono(p, .88);
        d.push({ type: "scatter", x: [q.lo, q.hi], y: [q.par, q.par], mode: "lines", line: { color: c, width: 4 }, showlegend: false, hoverinfo: "x" });
        d.push({ type: "scatter", x: [q.dif], y: [q.par], mode: "markers", marker: { size: 9, color: c }, showlegend: false, hovertemplate: "%{y}: %{x:.4g}<extra></extra>" }); });
      return { d, l: gLay({ margin: { l: 110, r: 20, t: 34, b: 44 }, showlegend: false, xaxis: { title: s.xl, gridcolor: gcss("--linea") }, yaxis: { autorange: "reversed", gridcolor: gcss("--linea") },
        shapes: o.e.cero ? [gV(0, "#b3261e", "dash")] : [] }) }; } },
  rendimiento: { est: ["Barras por paso"], el: { eti: ["Valores", 1] },
    f: (s, o, p) => ({ d: [{ type: "bar", x: s.etiq, y: s.vals, marker: { color: s.vals.map((_, i) => s.rty && i === s.vals.length - 1 ? gcss("--tinta") : (s.ok[i] ? gTono(p, .55) : "#cfc8bb")) },
      text: o.e.eti ? s.vals.map(v => v ? v.toFixed(1) + " %" : "") : null, textposition: "outside", customdata: s.n, hovertemplate: "%{x}: %{y:.1f} %<br>Unidades: %{customdata}<extra></extra>" }],
      l: gLay({ yaxis: { title: "% aprobado a la primera", range: [0, 108], gridcolor: gcss("--linea") }, xaxis: { type: "category" } }) }) },
  gage: { est: ["6 paneles"], el: { lim: ["Límites de control", 1] },
    f: (s, o, p) => { const d = [], sh = [], lay = gLay({ grid: { rows: 2, columns: 3, pattern: "independent" }, margin: { l: 48, r: 14, t: 52, b: 40 }, showlegend: true, legend: { orientation: "h", y: -0.12 } }), tit = [];
      const ax = k => k > 1 ? String(k) : "", pie = (k, t) => { tit.push({ text: t, xref: "x" + ax(k) + " domain", yref: "y" + ax(k) + " domain", x: .5, y: 1.12, showarrow: false, font: { size: 11 } }); };
      s.componentes.series.forEach((se, i) => d.push({ type: "bar", x: s.componentes.nombres, y: se.vals, name: se.et, xaxis: "x", yaxis: "y", marker: { color: gTono(p, .3 + .25 * i) } })); pie(1, "Componentes de variación");
      s.cartaR.ops.forEach((q, i) => d.push({ type: "scatter", x: q.rg.map((_, j) => j + 1), y: q.rg, mode: "lines+markers", name: q.nombre, xaxis: "x2", yaxis: "y2", line: { color: gTono(p, .25 + .5 * i / Math.max(1, s.cartaR.ops.length - 1)), width: 1 }, marker: { size: 5 } })); pie(2, "Carta R por evaluador");
      sh.push({ type: "line", xref: "x2 domain", yref: "y2", x0: 0, x1: 1, y0: s.cartaR.rb, y1: s.cartaR.rb, line: { color: gcss("--tinta") } }); if (o.e.lim) sh.push({ type: "line", xref: "x2 domain", yref: "y2", x0: 0, x1: 1, y0: s.cartaR.lsc, y1: s.cartaR.lsc, line: { color: "#b3261e", dash: "dash" } });
      s.cartaX.ops.forEach((q, i) => d.push({ type: "scatter", x: q.m.map((_, j) => j + 1), y: q.m, mode: "lines+markers", name: q.nombre, showlegend: false, xaxis: "x3", yaxis: "y3", line: { color: gTono(p, .25 + .5 * i / Math.max(1, s.cartaX.ops.length - 1)), width: 1 }, marker: { size: 5 } })); pie(3, "Carta X̄ por evaluador");
      sh.push({ type: "line", xref: "x3 domain", yref: "y3", x0: 0, x1: 1, y0: s.cartaX.mg, y1: s.cartaX.mg, line: { color: gcss("--tinta") } }); if (o.e.lim) [s.cartaX.lsc, s.cartaX.lic].forEach(v => sh.push({ type: "line", xref: "x3 domain", yref: "y3", x0: 0, x1: 1, y0: v, y1: v, line: { color: "#b3261e", dash: "dash" } }));
      d.push({ type: "scatter", x: s.piezas.x, y: s.piezas.y, mode: "markers", showlegend: false, xaxis: "x4", yaxis: "y4", marker: { size: 5, color: gTono(p, .5), opacity: .6 } });
      d.push({ type: "scatter", x: s.piezas.medias.map((_, j) => j + 1), y: s.piezas.medias, mode: "lines", showlegend: false, xaxis: "x4", yaxis: "y4", line: { color: gcss("--tinta"), width: 1 } }); pie(4, "Mediciones por pieza");
      s.evaluadores.nombres.forEach((nm, i) => d.push({ type: "box", y: s.evaluadores.grupos[i], name: nm, showlegend: false, xaxis: "x5", yaxis: "y5", marker: { color: gTono(p, .4) } })); pie(5, "Mediciones por evaluador");
      s.cartaX.ops.forEach((q, i) => d.push({ type: "scatter", x: q.m.map((_, j) => j + 1), y: q.m, mode: "lines+markers", name: q.nombre, showlegend: false, xaxis: "x6", yaxis: "y6", line: { color: gTono(p, .25 + .5 * i / Math.max(1, s.cartaX.ops.length - 1)), width: 1 }, marker: { size: 5 } })); pie(6, "Interacción pieza * evaluador");
      for (let k = 1; k <= 6; k++) { lay["xaxis" + ax(k)] = { gridcolor: gcss("--linea"), type: k === 1 || k === 5 ? "category" : "linear" }; lay["yaxis" + ax(k)] = { gridcolor: gcss("--linea") }; }
      lay.shapes = sh; lay.annotations = tit; return { d, l: lay }; } },
};
// ---------- estado por gráfica (se guarda con el proyecto) ----------
function gEstado(clave, spec) {
  const def = GCAT[spec.g]; if (!GR.estilos[clave]) GR.estilos[clave] = {};
  const e = GR.estilos[clave]; if (e.s === undefined) e.s = 0; e.e = Object.assign(Object.fromEntries(Object.entries(def.el).map(([k, v]) => [k, !!v[1]])), e.e || {});
  return e;
}
const gPaleta = e => e.p || GR.paleta || "Relieve D-MIKE";
function gDibujar(div, spec, e) { const def = GCAT[spec.g]; if (!def || !window.Plotly) return; const r = def.f(spec, e, gPaleta(e)); r.l.title = { text: e.titulo || spec.titulo, font: { size: 13 } };
  Plotly.react(div, r.d, r.l, { displaylogo: false, responsive: true, modeBarButtonsToRemove: ["toImage", "resetScale2d", "autoScale2d", "resetCameraDefault3d", "resetCameraLastSave3d"] }); }
function gEscalaOriginal(div, spec) { if (GCAT[spec.g] && GCAT[spec.g].tresd) Plotly.relayout(div, { "scene.camera": { eye: { x: 1.55, y: -1.55, z: .95 } } }); else { const u = {}; Object.keys(div.layout || {}).filter(k => /^[xy]axis\d*$/.test(k)).forEach(k => u[k + ".autorange"] = true); Plotly.relayout(div, u); } }
function gGuardar(clave) { try { api().guardar_estilo_grafica(clave, GR.estilos[clave]); } catch (e) { } }
// ---------- opciones rápidas (clic sobre la gráfica) ----------
function gMenuRapido(ev, clave, spec, div, uid, k) {
  ev.preventDefault(); ev.stopPropagation(); document.querySelectorAll(".g-pop").forEach(x => x.remove());
  const def = GCAT[spec.g], e = gEstado(clave, spec), pop = el("div", { class: "g-pop", role: "menu" });
  const re = () => { gDibujar(div, spec, e); gGuardar(clave); };
  pop.append(el("div", { class: "g-tit" }, "Estilo"), el("div", { class: "g-fila" }, ...def.est.map((t, i) => el("button", { class: "boton chico" + (e.s === i ? " on" : ""), onclick: () => { e.s = i; re(); pop.querySelectorAll(".g-fila:first-of-type .boton").forEach((b, j) => b.classList.toggle("on", j === i)); } }, t))));
  const sel = el("select", { onchange: () => { e.p = sel.value || null; re(); } }, el("option", { value: "" }, "(paleta de Ver)"), ...Object.keys(GPAL).map(n => el("option", { value: n, selected: e.p === n }, n)));
  pop.append(el("div", { class: "g-tit" }, "Color"), sel, el("div", { class: "g-tit" }, "Elementos"),
    ...Object.entries(def.el).map(([kk, v]) => { const c = el("input", { type: "checkbox", checked: e.e[kk], onchange: () => { e.e[kk] = c.checked; re(); } }); return el("label", { class: "g-ck" }, c, " " + v[0]); }),
    el("div", { class: "g-fila", style: "margin-top:8px" }, el("button", { class: "boton chico", onclick: () => gEscalaOriginal(div, spec) }, "Escala original"),
      el("button", { class: "boton chico primario", onclick: () => { pop.remove(); gEditar(uid, k); } }, "Editar propiedades del gráfico…")));
  document.body.append(pop); const r = pop.getBoundingClientRect();
  pop.style.left = Math.min(ev.clientX, innerWidth - r.width - 8) + "px"; pop.style.top = Math.min(ev.clientY, innerHeight - r.height - 8) + "px";
}
document.addEventListener("mousedown", ev => { if (!ev.target.closest(".g-pop")) document.querySelectorAll(".g-pop").forEach(x => x.remove()); });
// ---------- gráfica dentro de un resultado ----------
window.graficaInteractiva = function (res, k, b) {
  const clave = `${res.uid}:${k}`, cont = el("div", { class: "grafica g-int" }), div = el("div", { class: "g-plot" + (GCAT[b.inter.g] && GCAT[b.inter.g].tresd ? " g-3d" : "") });
  const barra = el("div", { class: "g-barra" },
    el("button", { class: "boton chico", title: "Estilo, color y elementos (también con clic derecho)", onclick: ev => gMenuRapido(ev, clave, b.inter, div, res.uid, k) }, "Estilo y color"),
    el("button", { class: "boton chico", title: "Vuelve la escala y la vista a como estaban al abrir la gráfica", onclick: () => gEscalaOriginal(div, b.inter) }, "Escala original"),
    el("button", { class: "boton chico", title: "Abre la gráfica en su propia pestaña con la pestaña «Gráfico» en la cinta", onclick: () => gEditar(res.uid, k) }, "Editar propiedades…"));
  cont.append(barra, div); div.addEventListener("contextmenu", ev => gMenuRapido(ev, clave, b.inter, div, res.uid, k));
  GR.vivas[clave] = { div, spec: b.inter };
  requestAnimationFrame(() => gDibujar(div, b.inter, gEstado(clave, b.inter)));
  return cont;
};
// ---------- pestaña de edición y pestaña «Gráfico» en la cinta ----------
function gEditar(uid, k) { const a = P.abiertas.find(x => x.id === `res:${uid}`); const res = a ? a.res : null; if (!res) return;
  abrirPestana(`graf:${uid}:${k}`, { uid, k, res }, "Gráfico · " + (res.bloques.filter(b => b.tipo === "grafica")[k]?.inter?.titulo || res.titulo).slice(0, 34)); }
window.pintarGraficaEdicion = function (info) {
  const v = $("#vista"); v.innerHTML = ""; const b = info.res.bloques.filter(x => x.tipo === "grafica")[info.k], spec = b.inter, clave = `${info.uid}:${info.k}`, e = gEstado(clave, spec);
  const div = el("div", { class: "g-plot g-grande" }); v.append(el("div", { class: "vista-barra" }, el("span", { class: "vista-titulo" }, "Propiedades del gráfico"), el("span", { class: "vista-fecha" }, info.res.titulo)), div);
  gDibujar(div, spec, e); gCinta(clave, spec, div);
};
function gCinta(clave, spec, div) {
  const def = GCAT[spec.g], e = gEstado(clave, spec), c = $("#cinta"); if (!c) return;
  document.body.classList.add("cinta-grafico"); c.hidden = false;
  document.querySelectorAll("#menus .menu > button").forEach(b => b.classList.remove("cinta-activa"));
  let tab = document.getElementById("tab-grafico"); if (!tab) { tab = el("button", { id: "tab-grafico", class: "cinta-activa tab-ctx", onclick: () => gCinta(clave, spec, div) }, "Gráfico"); document.querySelector("#menus").append(tab); }
  const re = () => { gDibujar(div, spec, e); gGuardar(clave); const viva = GR.vivas[clave]; if (viva && document.body.contains(viva.div)) gDibujar(viva.div, spec, e); gCinta(clave, spec, div); };
  const grupo = (t, ...hijos) => el("div", { class: "cinta-grupo" }, el("div", { class: "cinta-botones g-cb" }, ...hijos), el("div", { class: "cinta-et" }, t));
  const tit = el("input", { class: "g-in", placeholder: spec.titulo, value: e.titulo || "", onchange: () => { e.titulo = tit.value || null; re(); } });
  const sel = el("select", { class: "g-in", onchange: () => { e.p = sel.value || null; re(); } }, el("option", { value: "" }, "(paleta de Ver)"), ...Object.keys(GPAL).map(n => el("option", { value: n, selected: e.p === n }, n)));
  c.innerHTML = "";
  c.append(grupo("Estilos", ...def.est.map((t, i) => el("button", { class: "cinta-b g-est" + (e.s === i ? " on" : ""), onclick: () => { e.s = i; re(); } }, t))),
    grupo("Colores", sel, el("div", { class: "g-mues", style: `background:linear-gradient(90deg,${GPAL[gPaleta(e)].join(",")})` })),
    grupo("Elementos", ...Object.entries(def.el).map(([kk, v]) => { const ck = el("input", { type: "checkbox", checked: e.e[kk], onchange: () => { e.e[kk] = ck.checked; re(); } }); return el("label", { class: "g-ck" }, ck, " " + v[0]); }),
      ...(spec.g === "superficie" ? [el("label", { class: "g-ck" }, "Plano en ", (() => { const i = el("input", { class: "g-in g-num", type: "number", value: e.plano ?? "", onchange: () => { e.plano = i.value; re(); } }); return i; })())] : [])),
    grupo("Título", tit),
    grupo("Escala", el("button", { class: "cinta-b", onclick: () => gEscalaOriginal(div, spec) }, "Escala original")),
    grupo("Restablecer", el("button", { class: "cinta-b", onclick: () => { GR.estilos[clave] = {}; gGuardar(clave); const n = gEstado(clave, spec); Object.assign(e, n); re(); } }, "Estilo por defecto")));
}
function gSalirCinta() { document.body.classList.remove("cinta-grafico"); document.getElementById("tab-grafico")?.remove(); if (window.pintarCinta && document.body.classList.contains("cinta-fija")) pintarCinta(U2.cintaActiva || "Estadística"); else if (!document.body.classList.contains("cinta-fija")) $("#cinta").hidden = true; }
window.gSalirCinta = gSalirCinta;
// ---------- paleta general (Ver › Paleta de las gráficas) ----------
function gDialogoPaleta() {
  const lista = el("div", { class: "g-paletas" }, ...Object.keys(GPAL).map(n => el("button", { class: "g-pal" + (GR.paleta === n || (!GR.paleta && n === "Relieve D-MIKE") ? " on" : ""), onclick: () => {
    GR.paleta = n; guardarPref("paleta", n); document.querySelectorAll(".velo").forEach(v => v.remove()); Object.entries(GR.vivas).forEach(([k2, g]) => { if (document.body.contains(g.div)) gDibujar(g.div, g.spec, gEstado(k2, g.spec)); }); } },
    el("i", { style: `background:linear-gradient(90deg,${GPAL[n].join(",")})` }), n)));
  dialogo("Paleta de las gráficas", el("div", {}, el("p", { class: "vacio" }, "Se aplica a todas las gráficas; cada gráfica puede tener su propio color con «Estilo y color»."), lista), () => {}, "Cerrar");
}
window.gIniciar = async function () {
  GR.paleta = leerPref("paleta") || null;
  try { GR.estilos = (await api().estilos_graficas()) || {}; } catch (e) { GR.estilos = {}; }
  Object.assign(ACCIONES_UI, { paleta_graficas: gDialogoPaleta });
};
