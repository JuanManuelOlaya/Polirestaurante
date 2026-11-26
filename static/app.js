// Cliente web liviano: polling cada 2 s (ADR-005), avisos y control de conexión.
const CSRF = document.querySelector('meta[name=csrf]').content;
const $ = (s) => document.querySelector(s);
let version = null, ultimoAviso = null, refrescado = Date.now();

function conexion(hay) { $('#conexion').hidden = hay; }

function mostrarAviso(texto) {
  const d = document.createElement('div');
  d.className = 'aviso alerta';
  d.textContent = '🔔 ' + texto;
  $('#avisos').prepend(d);
  setTimeout(() => d.remove(), 8000);
}

async function refrescar() {
  const vivo = $('#vivo');
  if (!vivo) return;
  const r = await fetch(location.href, { cache: 'no-store' });
  if (!r.ok) throw new Error();
  const nuevo = new DOMParser().parseFromString(await r.text(), 'text/html').querySelector('#vivo');
  if (!nuevo) { location.reload(); return; }
  vivo.innerHTML = nuevo.innerHTML;
  if ($('#activos') && nuevo.dataset.activos) $('#activos').textContent = `🔥 ${nuevo.dataset.activos} Activos`;
  refrescado = Date.now();
  filtrarOrdenes();
}

async function consultar() {
  try {
    const q = ultimoAviso === null ? '' : '?desde=' + ultimoAviso;
    const r = await fetch('/api/cambios' + q, { cache: 'no-store' });
    if (r.status === 401) { location.href = '/login'; return; }
    if (!r.ok) throw new Error();
    const d = await r.json();
    ultimoAviso = d.ultimo;
    d.avisos.forEach(mostrarAviso);
    // También se refresca cada 30 s para actualizar los "hace X min"
    if ((version !== null && d.version !== version) || Date.now() - refrescado > 30000) {
      await refrescar();
      document.dispatchEvent(new Event('datos-cambiaron'));
    }
    version = d.version;
    conexion(true);
  } catch (e) { conexion(false); }
  setTimeout(consultar, 2000);
}
if (document.body.dataset.sesion) consultar();

// Antes de enviar un formulario se verifica el servidor; si falla, nada cambia.
let pendiente = null;
document.addEventListener('submit', async (ev) => {
  const form = ev.target;
  if (form.method !== 'post' || form.dataset.verificado) return;
  ev.preventDefault();
  const boton = ev.submitter;
  try {
    const r = await fetch('/api/ping', { cache: 'no-store', signal: AbortSignal.timeout(4000) });
    if (!r.ok) throw new Error();
    form.dataset.verificado = '1';
    form.requestSubmit(boton);
  } catch (e) { pendiente = [form, boton]; conexion(false); }
});
$('#reintentar').addEventListener('click', () => {
  conexion(true);
  if (pendiente && pendiente[0].isConnected) pendiente[0].requestSubmit(pendiente[1]);
  else if (pendiente || !document.querySelector('#enviar')) location.reload();
  else document.dispatchEvent(new Event('datos-cambiaron'));
});

document.addEventListener('click', (ev) => {
  const abrir = ev.target.closest('[data-abrir]');
  if (abrir) document.getElementById(abrir.dataset.abrir).showModal();
  if (ev.target.closest('[data-cerrar]')) ev.target.closest('dialog').close();
  const filtro = ev.target.closest('[data-filtro]');
  if (filtro) {
    document.querySelectorAll('[data-filtro]').forEach((b) => b.classList.toggle('activo', b === filtro));
    filtrarOrdenes();
  }
  if (ev.target.id === 'imprimir') window.print();
});

function filtrarOrdenes() {
  const estado = document.querySelector('[data-filtro].activo')?.dataset.filtro || '';
  const texto = ($('#filtrar')?.value || '').toLowerCase();
  document.querySelectorAll('.orden').forEach((o) => {
    o.hidden = (estado && o.dataset.estado !== estado) || !o.dataset.texto.includes(texto);
  });
}
$('#filtrar')?.addEventListener('input', filtrarOrdenes);
