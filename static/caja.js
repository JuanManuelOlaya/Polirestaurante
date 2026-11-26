// Vista previa del cambio y del saldo. El servidor vuelve a validar todo.
(() => {
  const form = document.querySelector('#cobro');
  const total = Number(form.dataset.total);
  const pesos = (n) => '$ ' + n.toLocaleString('es-CO');
  const numero = (v) => Number(String(v).replace(/[$.\s]/g, ''));
  function actualizar() {
    const dividido = form.dividido.checked;
    document.querySelector('#simple').hidden = dividido;
    document.querySelector('#varios').hidden = !dividido;
    const metodo = form.querySelector('[name=metodo]:checked').value;
    const valor = form.valor;
    valor.readOnly = metodo !== 'EFECTIVO';
    if (valor.readOnly) valor.value = total;
    document.querySelector('#fallido').hidden = !dividido && metodo === 'EFECTIVO';
    let texto, listo;
    if (dividido) {
      const suma = [...form.querySelectorAll('.parte')].reduce((s, c) => s + (numero(c.value) || 0), 0);
      listo = suma >= total;
      texto = listo ? `Saldo pendiente $ 0 · Cambio ${pesos(suma - total)}` : `Saldo pendiente ${pesos(total - suma)}`;
    } else {
      const n = numero(valor.value);
      listo = Number.isFinite(n) && n >= total;
      texto = listo ? `Cambio a entregar: ${pesos(n - total)}` : `Faltan ${pesos(total - (n > 0 ? n : 0))}`;
    }
    document.querySelector('#resumen').textContent = texto;
    // En pago dividido el botón solo se habilita cuando la suma cubre el total (CU-05)
    document.querySelector('#confirmar-pago').disabled = dividido && !listo;
  }
  form.addEventListener('input', actualizar);
  form.addEventListener('change', (e) => {
    if (e.target.name === 'metodo' && e.target.value === 'EFECTIVO') form.valor.value = '';
    actualizar();
  });
  actualizar();
})();
