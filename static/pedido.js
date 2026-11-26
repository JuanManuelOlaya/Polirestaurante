// CU-02: el borrador se conserva en el dispositivo hasta que el servidor confirme el envío.
const LLAVE = 'borrador-pedido-' + ID_MESERO;
const vacio = () => ({ tipo_servicio: null, id_mesa: '', nombre_cliente: '', nota_general: '', items: [], clave_envio: nuevaClave() });
function nuevaClave() { return Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 12); }
const pesos = (n) => '$ ' + n.toLocaleString('es-CO');
let borrador = vacio(), productos = [], mesas = [], enviando = false;
try { borrador = JSON.parse(localStorage.getItem(LLAVE)) || borrador; } catch (e) {}

const pedida = new URLSearchParams(location.search).get('mesa');
if (pedida) { borrador.tipo_servicio = 'SALON'; borrador.id_mesa = pedida; }

function guardar() { try { localStorage.setItem(LLAVE, JSON.stringify(borrador)); } catch (e) {} }

function el(etiqueta, props = {}, ...hijos) {
  const n = Object.assign(document.createElement(etiqueta), props);
  n.append(...hijos);
  return n;
}

function mensaje(texto, tipo = 'error', boton) {
  const caja = el('div', { className: 'aviso ' + tipo, textContent: texto + ' ' });
  if (boton) caja.append(el('button', { type: 'button', className: 'mini', textContent: boton[0], onclick: boton[1] }));
  $('#mensaje').replaceChildren(caja);
  $('#mensaje').scrollIntoView({ block: 'nearest' });
}

async function api(url, cuerpo) {
  const r = await fetch(url, cuerpo ? { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRF': CSRF }, body: JSON.stringify(cuerpo) } : { cache: 'no-store' });
  const d = await r.json();
  if (r.status === 401) location.href = '/login';
  if (!r.ok) throw Object.assign(new Error(d.error), { datos: d });
  return d;
}

async function cargar() {
  try {
    [productos, mesas] = await Promise.all([api('/api/productos'), api('/api/mesas')]);
    pintar();
    if (!productos.length) mensaje('No hay productos activos.', 'alerta', ['Reintentar', cargar]);
  } catch (e) { mensaje('No se pudo cargar el menú.', 'error', ['Reintentar', cargar]); }
}

function pintarServicio() {
  document.querySelectorAll('[data-tipo]').forEach((b) => b.classList.toggle('activo', b.dataset.tipo === borrador.tipo_servicio));
  $('#bloque-mesa').hidden = borrador.tipo_servicio !== 'SALON';
  $('#bloque-cliente').hidden = borrador.tipo_servicio !== 'LLEVAR';
  $('#mesa').replaceChildren(el('option', { value: '', textContent: 'Seleccione una mesa' }),
    ...mesas.map((m) => el('option', { value: m.id, textContent: `Mesa ${String(m.numero).padStart(2, '0')} · ${m.estado === 'OCUPADA' ? 'Ocupada' : 'Disponible'}` })));
  $('#mesa').value = borrador.id_mesa;
  const m = mesas.find((x) => String(x.id) === String(borrador.id_mesa));
  $('#titulo').textContent = 'Nuevo Pedido' + (borrador.tipo_servicio === 'SALON' && m ? ' - Mesa ' + String(m.numero).padStart(2, '0') : '');
}

function pintarResultados() {
  const q = $('#buscar').value.trim().toLowerCase();
  $('#resultados').replaceChildren(...productos.filter((p) => !q || p.nombre.toLowerCase().includes(q)).map((p) =>
    el('div', { className: 'tarjeta fila' + (p.agotado ? ' apagado' : '') },
      el('span', {}, el('small', { textContent: p.categoria }), el('b', { textContent: p.nombre }), el('span', { className: 'precio', textContent: pesos(p.precio) })),
      el('button', { type: 'button', className: 'mini', disabled: p.agotado, textContent: p.agotado ? 'Agotado' : '+ Agregar', onclick: () => agregar(p.id) }))));
}

function agregar(id) {
  const i = borrador.items.find((x) => x.id_producto === id);
  if (i) i.cantidad = (parseInt(i.cantidad, 10) || 0) + 1;
  else borrador.items.push({ id_producto: id, cantidad: 1, nota: '' });
  guardar(); pintarCarrito();
}

function calcularTotal() {
  const total = borrador.items.reduce((s, i) => {
    const p = productos.find((x) => x.id === i.id_producto);
    return s + (p ? p.precio * Math.max(0, Number(i.cantidad) || 0) : 0);
  }, 0);
  $('#total').textContent = pesos(total);
}

async function guardarNota(item, campo) {
  try {
    const d = await api('/api/notas/validar', { nota: campo.value });
    item.nota = item.guardada = campo.value = d.nota; guardar(); mensaje(d.mensaje, 'ok');
  } catch (e) {
    if (!e.datos) { mensaje('No se pudo guardar la nota'); return; }
    item.nota = campo.value = item.guardada || ''; guardar(); mensaje(e.message);
  }
}

function pintarCarrito(marcados = []) {
  const filas = borrador.items.map((i, n) => {
    const p = productos.find((x) => x.id === i.id_producto);
    const agotado = !p || p.agotado || marcados.includes(i.id_producto);
    const cambiar = (delta) => { i.cantidad = Math.max(1, (parseInt(i.cantidad, 10) || 0) + delta); guardar(); pintarCarrito(); };
    const cantidad = el('input', { value: i.cantidad, inputMode: 'numeric', ariaLabel: 'Cantidad', oninput: (e) => { i.cantidad = e.target.value; guardar(); calcularTotal(); } });
    const nota = el('input', { value: i.nota, placeholder: 'Nota del platillo (ej. Sin cebolla)', ariaLabel: 'Nota del platillo', oninput: (e) => { i.nota = e.target.value; guardar(); } });
    return el('div', { className: 'tarjeta item' + (agotado ? ' agotado' : '') },
      el('div', { className: 'fila' },
        el('span', {}, el('b', { textContent: (p ? p.nombre : 'Producto no disponible') + (agotado ? ' (agotado)' : '') }), el('span', { className: 'precio', textContent: p ? pesos(p.precio) : '' })),
        el('button', { type: 'button', className: 'borrar', textContent: '🗑', ariaLabel: 'Quitar', onclick: () => { borrador.items.splice(n, 1); guardar(); pintarCarrito(); } })),
      el('div', { className: 'en-fila cantidad' },
        el('button', { type: 'button', textContent: '−', onclick: () => cambiar(-1) }), cantidad,
        el('button', { type: 'button', textContent: '+', onclick: () => cambiar(1) })),
      el('div', { className: 'en-fila' }, nota, el('button', { type: 'button', className: 'mini', textContent: 'Guardar nota', onclick: () => guardarNota(i, nota) })));
  });
  $('#carrito').replaceChildren(...(filas.length ? filas : [el('p', { className: 'suave', textContent: 'Aún no hay productos en el pedido.' })]));
  calcularTotal();
}

function pintar() {
  pintarServicio(); pintarResultados();
  if (!$('#carrito').contains(document.activeElement)) pintarCarrito();
  $('#general').value = borrador.nota_general;
}

async function enviar(confirmarOcupada = false) {
  if (enviando) return;
  enviando = true; $('#enviar').disabled = true;
  try {
    const d = await api('/api/pedidos', { ...borrador, confirmar_ocupada: confirmarOcupada });
    borrador = vacio(); guardar();
    history.replaceState(null, '', location.pathname);
    await cargar(); pintarCarrito();
    mensaje(`${d.mensaje} · Pedido #${d.id} (llegada ${d.numero_llegada})`, 'ok');
  } catch (e) {
    if (!e.datos) mensaje('No se pudo enviar. El pedido se conserva en este dispositivo.', 'error', ['Reintentar', () => enviar(confirmarOcupada)]);
    else if (e.datos.codigo === 'MESA_OCUPADA') mensaje(e.message, 'alerta', ['Confirmar y enviar', () => enviar(true)]);
    else {
      mensaje(e.message);
      if (e.datos.codigo === 'AGOTADO') { await cargarSinMensaje(); pintarCarrito(e.datos.productos); }
    }
  } finally { enviando = false; $('#enviar').disabled = false; }
}

async function cargarSinMensaje() {
  try { [productos, mesas] = await Promise.all([api('/api/productos'), api('/api/mesas')]); pintar(); } catch (e) {}
}

document.querySelectorAll('[data-tipo]').forEach((b) => b.addEventListener('click', () => {
  borrador.tipo_servicio = b.dataset.tipo; guardar(); pintarServicio();
}));
$('#mesa').addEventListener('change', (e) => { borrador.id_mesa = e.target.value; guardar(); pintarServicio(); });
$('#cliente').value = borrador.nombre_cliente;
$('#cliente').addEventListener('input', (e) => { borrador.nombre_cliente = e.target.value; guardar(); });
$('#general').addEventListener('input', (e) => { borrador.nota_general = e.target.value; guardar(); });
$('#buscar').addEventListener('input', pintarResultados);
$('#enviar').addEventListener('click', () => enviar());
$('#descartar').addEventListener('click', () => {
  if (!confirm('¿Desea descartar el pedido?')) return;
  borrador = vacio(); guardar(); $('#cliente').value = ''; $('#mensaje').replaceChildren(); pintar(); pintarCarrito();
});
document.addEventListener('datos-cambiaron', cargarSinMensaje);
cargar();
