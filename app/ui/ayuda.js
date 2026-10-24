// Ayuda de D-MIKE (F1): navegador a la izquierda y contenido a la derecha. Funciona dentro del programa (datos del puente)
// y fuera de él (la guía publicada carga los mismos datos en window.AYUDA_DATOS).
const AYUDA_TEXTOS = {
  inicio: ["Primeros pasos", `
    <p>D-MIKE administra proyectos de mejora por fases DMAIC: <b>Definir, Medir, Analizar, Mejorar y Controlar</b>. Reúne una hoja de datos, análisis estadísticos tipo Minitab y formatos Lean y de gestión en un solo archivo <code>.dmike</code>.</p>
    <ol><li>Abre un proyecto o empieza uno nuevo desde la pantalla de inicio.</li>
    <li>Si tienes el perfil del diagnóstico, cárgalo (Proyecto › Abrir perfil del diagnóstico): activa los módulos que tu caso necesita en cada fase.</li>
    <li>Captura o pega tus datos en la hoja (Ctrl+V desde Excel) o impórtalos (Archivo › Importar).</li>
    <li>Abre cada módulo desde el riel DMAIC, la cinta o la paleta de comandos (Ctrl+K).</li>
    <li>Guarda con Ctrl+S. Todo queda en un solo archivo: datos, resultados, formatos y avance.</li></ol>`],
  interfaz: ["La interfaz", `
    <p><b>Cinta.</b> Las pestañas de arriba (Archivo, Datos, Estadística, Calidad, Lean, Gestión…) muestran sus comandos como botones agrupados. El botón «Cinta» (o Ctrl+F1) la fija o la contrae: contraída libera ese espacio para la hoja y los resultados, y cada pestaña abre sus comandos como menú desplegable. Lo que elijas se recuerda al volver a abrir el programa.</p>
    <p><b>Riel DMAIC.</b> La columna angosta de la izquierda tiene una letra por fase. Un clic en la letra despliega sus módulos activos y, debajo, el grupo «Inactivos» cerrado. Desde ahí se abren los módulos, se activan (botón +) y se marca su avance (botón ⋯ o clic derecho). Los botones «Tablero de módulos» y «Ruta DMAIC» abren la vista completa de todas las fases.</p>
    <p><b>Pestañas.</b> Cada módulo abierto es una pestaña, como en un navegador. Clic derecho en una pestaña: cerrar, cerrar las demás, reabrir la última cerrada, abrir a la derecha (vista dividida), repetir, modificar o exportar.</p>
    <p><b>Vista dividida.</b> Un resultado se puede abrir a la derecha mientras trabajas con la hoja o con otro módulo. Los formatos con gráficas (como el QFD) tienen su propio botón para ver las gráficas a la derecha mientras capturas.</p>
    <p><b>Barra contextual.</b> Junto a los botones generales aparecen los del módulo abierto: Modificar, Repetir, Exportar, Verificar en Excel y el siguiente paso sugerido.</p>
    <p><b>Varios proyectos.</b> Cada proyecto abierto es una pestaña arriba de la hoja, como los dibujos en AutoCAD. La pestaña «Inicio» (o el botón de carpeta arriba del riel) gestiona los abiertos y los recientes; la «×» cierra un proyecto y pregunta si tiene cambios.</p>
    <p><b>Botones del riel.</b> Arriba de las letras: ocultar el riel (la hoja ocupa todo el ancho; para volver, el botón de la izquierda de las pestañas o Ctrl+B), gestionar proyectos y mostrar la sesión.</p>
    <p><b>Módulos del proyecto.</b> Una sola ventana con la ruta DMAIC arriba y los módulos de cada fase abajo; un clic en una fase muestra solo la suya.</p>
    <p><b>Ayuda rápida.</b> Al pasar el cursor por un botón de la cinta aparece una tarjeta con lo que hace; F1 en ese momento abre su página de ayuda. Al final de cada módulo, un párrafo explica para qué sirve y enlaza a su ayuda; las fuentes quedan en «Fuentes y criterios».</p>
    <p><b>Sesión.</b> El registro de lo que haces queda abajo en una sola línea; un clic en «Sesión» lo despliega.</p>
    <p><b>Tema.</b> El interruptor de la esquina superior derecha cambia entre claro y oscuro. Con la cinta fija, la barra de íconos chicos se oculta y el grupo «Módulo abierto» queda en la cinta.</p>
    <p><b>Recetas.</b> Una plantilla de Excel generada por el Diagnóstico en línea se abre con Archivo › Abrir proyecto: D-MIKE pregunta si se ejecuta la receta y arma el proyecto.</p>`],
  paleta: ["Paleta de comandos", `
    <p>Ctrl+K abre un buscador de todos los comandos. Escribe parte del nombre y presiona Enter. Prefijos: <code>@</code> solo módulos, <code>&gt;</code> solo comandos, <code>?</code> busca en esta ayuda.</p>`],
  contextual: ["Clic derecho", `
    <p>Casi todo tiene menú de clic derecho: celdas y encabezados de la hoja, pestañas, letras y módulos del riel, gráficas de resultados, proyectos recientes y tarjetas del tablero. Cada menú muestra solo lo que aplica a ese elemento.</p>`],
  fases: ["Fases y avance", `
    <p>Cada módulo activo tiene un avance: pendiente, en curso o hecho. El avance alimenta la pantalla de inicio, el tablero y la ruta DMAIC. «Pasar a inactivos» no borra nada: las capturas y resultados se conservan.</p>`],
};

function ayudaNorm(s) { return (s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, ""); }

function pintarAyuda(cont, datos, inicial) {
  const CTX = { G: "Global", H: "Hoja", F: "Formatos", R: "Resultados", T: "Tablero", P: "Riel DMAIC" };
  const cats = [...new Set(datos.comandos.map(c => c.cat))];
  const mods = [];
  for (const m of datos.menus) for (const o of m.opciones) if (o.accion && o.accion.startsWith("mod:")) mods.push({ id: o.accion.slice(4), texto: o.texto, menu: m.titulo });
  const arbol = [["Guía", Object.keys(AYUDA_TEXTOS).map(k => ["txt:" + k, AYUDA_TEXTOS[k][0]])],
    ["Módulos por menú", datos.menus.filter(m => m.opciones.some(o => o.accion && o.accion.startsWith("mod:"))).map(m => ["menu:" + m.titulo, m.titulo])],
    ["Fases DMAIC", datos.fases.map(f => ["fase:" + f.id, `${f.id} · ${f.nombre}`])],
    ["Comandos", [["cmd:*", `Todos (${datos.comandos.length})`]].concat(cats.map(c => ["cmd:" + c, c]))],
    ["Atajos", [["atajos", "Atajos de teclado"]]]];
  cont.innerHTML = "";
  const nav = document.createElement("nav"); nav.className = "ay-nav"; nav.setAttribute("aria-label", "Contenido de la ayuda");
  const buscar = document.createElement("input"); buscar.className = "ay-buscar"; buscar.placeholder = "Buscar en la ayuda"; buscar.setAttribute("aria-label", "Buscar en la ayuda");
  nav.append(buscar);
  const cuerpo = document.createElement("article"); cuerpo.className = "ay-cuerpo";
  for (const [grupo, items] of arbol) {
    const det = document.createElement("details"); det.open = true;
    det.innerHTML = `<summary>${grupo}</summary>`;
    for (const [id, t] of items) {
      const b = document.createElement("button"); b.className = "ay-item"; b.dataset.id = id; b.textContent = t;
      b.addEventListener("click", () => mostrar(id)); det.append(b);
    }
    nav.append(det);
  }
  cont.append(nav, cuerpo);
  const filaCmd = c => `<tr><td>${c.n}</td><td class="ay-atajo">${c.a === "—" ? "" : c.a}</td><td>${c.c.map(x => CTX[x] || x).join(", ")}</td><td><span class="ay-estado ${c.e === "D" ? "d" : "p"}">${c.e === "D" ? "Disponible" : "Propuesto"}</span></td><td>${c.d}</td></tr>`;
  const tablaCmd = lista => `<div class="ay-tabla"><table><thead><tr><th>Comando</th><th>Atajo</th><th>Funciona en</th><th>Estado</th><th>Qué hace</th></tr></thead><tbody>${lista.map(filaCmd).join("")}</tbody></table></div>`;
  function mostrar(id, q) {
    nav.querySelectorAll(".ay-item").forEach(b => b.classList.toggle("activo", b.dataset.id === id));
    let h = "";
    if (q) {
      const n = ayudaNorm(q), cm = datos.comandos.filter(c => ayudaNorm(c.n + " " + c.d + " " + c.cat).includes(n)), md = mods.filter(m => ayudaNorm(m.texto).includes(n));
      const tx = Object.entries(AYUDA_TEXTOS).filter(([, v]) => ayudaNorm(v[1]).includes(n));
      h = `<h1>Resultados para «${q}»</h1>` + (tx.length ? `<h2>En la guía</h2><ul>${tx.map(([k, v]) => `<li><button class="ay-link" data-ir="txt:${k}">${v[0]}</button></li>`).join("")}</ul>` : "") +
        (md.length ? `<h2>Módulos</h2><ul>${md.map(m => `<li>${m.texto} <span class="ay-ruta">(${m.menu})</span>${window.abrirModulo ? ` <button class="ay-link" data-abrir="${m.id}">abrir</button>` : ""}</li>`).join("")}</ul>` : "") +
        (cm.length ? `<h2>Comandos (${cm.length})</h2>` + tablaCmd(cm) : "") || `<p>No hay resultados.</p>`;
    } else if (id.startsWith("txt:")) { const [t, x] = AYUDA_TEXTOS[id.slice(4)]; h = `<h1>${t}</h1>${x}`; }
    else if (id.startsWith("menu:")) {
      const m = datos.menus.find(x => x.titulo === id.slice(5));
      h = `<h1>${m.titulo}</h1><p>Módulos y comandos de este menú. ${window.abrirModulo ? "Usa «abrir» para ir directo." : ""}</p><ul class="ay-mods">` + m.opciones.filter(o => o.texto !== "-" && !o.texto.startsWith("§")).map(o => {
        const c = datos.comandos.find(x => ayudaNorm(x.n) === ayudaNorm(o.texto.replace(/…$/, "")));
        return `<li><b>${o.accion && o.accion.startsWith("mod:") ? `<button class="ay-link" data-ir="mod:${o.accion.slice(4)}">${o.texto}</button>` : o.texto}</b>${c ? ` — ${c.d}` : ""}${o.accion && o.accion.startsWith("mod:") && window.abrirModulo ? ` <button class="ay-link" data-abrir="${o.accion.slice(4)}">abrir</button>` : ""}</li>`;
      }).join("") + "</ul>";
    } else if (id.startsWith("mod:")) {
      const mid = id.slice(4), m = (datos.modulos || {})[mid] || { titulo: mid };
      h = `<h1>${m.titulo}</h1>${m.desc ? `<p class="ay-lead">${m.desc}.</p>` : ""}
        <p><b>Dónde está:</b> <span class="ay-ruta">${m.ruta || "panel DMAIC"}</span>${m.fases && m.fases.length ? ` · <b>Fases:</b> ${m.fases.join(", ")}` : ""}</p>
        ${window.abrirModulo ? `<p><button class="ay-link" data-abrir="${mid}">Abrir el módulo</button></p>` : ""}
        ${m.nota ? `<h2>Criterios y fuentes</h2><p>${m.nota}</p>` : `<h2>Criterios y fuentes</h2><p>Cada resultado de este análisis trae al final sus fórmulas, supuestos y la sección del material del curso de donde salen, en «Fuentes y criterios».</p>`}`;
    } else if (id.startsWith("fase:")) {
      const f = datos.fases.find(x => x.id === id.slice(5)), lista = datos.catalogo[f.id] || [];
      h = `<h1>${f.id} · ${f.nombre}</h1><p>${lista.length} módulos disponibles en esta fase. Los marcados «complementario» son herramientas de D-MIKE fuera del árbol del diagnóstico.</p><ul class="ay-mods">` +
        lista.map(m => `<li><b>${m.nombre}</b>${m.construido ? "" : " <span class='ay-ruta'>(en construcción)</span>"}${m.complementario ? " <span class='ay-ruta'>complementario</span>" : ""}${m.construido && window.abrirModulo ? ` <button class="ay-link" data-abrir="${m.id}">abrir</button>` : ""}</li>`).join("") + "</ul>";
    } else if (id.startsWith("cmd:")) {
      const c = id.slice(4), lista = c === "*" ? datos.comandos : datos.comandos.filter(x => x.cat === c);
      h = `<h1>${c === "*" ? "Todos los comandos" : c}</h1><p>${lista.length} comandos · ${lista.filter(x => x.e === "D").length} disponibles hoy; los «propuestos» se agregan en las siguientes versiones.</p>` + tablaCmd(lista);
    } else if (id === "atajos") {
      const con = datos.comandos.filter(c => c.a && c.a !== "—" && /Ctrl|Alt|Mayús|F\d/.test(c.a));
      h = `<h1>Atajos de teclado</h1><p>${con.length} atajos. Inspirados en Office y Minitab para que un mismo atajo funcione en la hoja y en los formatos.</p>` + tablaCmd(con);
    }
    cuerpo.innerHTML = h; cuerpo.scrollTop = 0;
    cuerpo.querySelectorAll("[data-ir]").forEach(b => b.addEventListener("click", () => mostrar(b.dataset.ir)));
    cuerpo.querySelectorAll("[data-abrir]").forEach(b => b.addEventListener("click", () => window.abrirModulo(b.dataset.abrir)));
  }
  let t0; buscar.addEventListener("input", () => { clearTimeout(t0); t0 = setTimeout(() => buscar.value.trim() ? mostrar("", buscar.value.trim()) : mostrar("txt:inicio"), 150); });
  mostrar(inicial || "txt:inicio");
  return { mostrar, buscar: q => { buscar.value = q; mostrar("", q); } };
}
