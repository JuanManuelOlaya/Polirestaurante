# PoliRestaurante

Aplicativo web en Python (Flask) con base de datos SQLite.

## Cómo ejecutarlo (Python 3.10 o superior)

Abra una terminal dentro de la carpeta `PoliRestaurante`:

    python -m venv venv
    venv\Scripts\activate            (Windows)
    source venv/bin/activate         (Mac / Linux)
    pip install -r requirements.txt
    python app.py

Abra http://127.0.0.1:5000

Para usarlo desde celulares en el mismo WiFi: `python app.py --red` y entre a
http://IP-DEL-COMPUTADOR:5000. Use esta opción solo en una red de confianza y
cambie antes las contraseñas de demostración.

## Usuarios de demostración (contraseña: Poli2026*)

| Rol | Usuarios |
|---|---|
| Mesero | mesero1, mesero2, mesero4, mesero7 (mesero5 está desactivado) |
| Cocina | cocina1, cocina2 |
| Administrador | admin1, admi2 |

La clave para autorizar cancelaciones es la contraseña de un administrador activo.

Para probar los tres roles a la vez, use tres navegadores distintos o ventanas de
incógnito de navegadores diferentes: las pestañas de un mismo navegador comparten la sesión.

Para reiniciar los datos, detenga el programa y borre la carpeta `instance`.

## Estructura MVC (con capas Service y DAO, ADR-002)

    app.py             Arranque y ensamblado
    config.py          Parámetros
    modelos/           MODELO: entidades y patrones State, Strategy, Observer
    vistas/ static/    VISTA: plantillas HTML, CSS y JavaScript
    controladores/     CONTROLADOR: rutas web y API REST
    servicios/         Reglas de negocio
    dao/               Acceso a datos (SQL)
    database/          Esquema, conexión y datos iniciales
    tests/             Pruebas del mazo de pruebas
    respaldo.py        Copia de seguridad

Recorrido: Vista -> Controller -> Service -> DAO -> Base de datos.
Los controladores no llaman a los DAO.

## Patrones de diseño

| Patrón | Archivo | Uso |
|---|---|---|
| State | modelos/estados.py | Transiciones válidas del pedido |
| Strategy | modelos/pagos.py | Efectivo, Tarjeta y Nequi |
| Observer | modelos/observador.py, servicios/notificaciones.py | Avisos a mesero y cocina |

## Casos de uso

| Caso | Servicio |
|---|---|
| CU-01 Iniciar sesión | AuthService.autenticar |
| CU-02 Registrar pedido | PedidoService.crear_pedido |
| CU-03 Preparar pedido | iniciar_preparacion, marcar_listo, devolver_a_preparacion |
| CU-04 Entregar | PedidoService.entregar |
| CU-05 Cobrar | PagoService.procesar_pago |
| CU-06 Cancelar | PedidoService.cancelar |

Además: mesas, menú, notas, catálogo, disponibilidad, usuarios y reportes de ventas.

## Pruebas

    python -m unittest -v

## Decisiones y supuestos

- Estados según los casos de uso: Recibido, En preparación, Listo, Entregado, Pagado, Cancelado.
- Tras 3 intentos fallidos el bloqueo dura 5 minutos (config.py).
- Las unidades se descuentan al enviar el pedido y se devuelven si se cancela en Recibido.
- Las pantallas consultan cambios cada 2 segundos (ADR-005).
- SQLite como base de datos relacional (ADR-003).

## Alcance pendiente

- HTTPS (ADR-004): se ejecuta en HTTP. Para producción se necesita un certificado y un
  servidor de producción; el servidor incluido en Flask es para desarrollo.
- Recuperación de contraseña por correo (BPMN): el administrador la restablece.
- Flujo del cliente con su propio acceso (BPMN): no tiene caso de uso detallado.
- respaldo.py se debe programar en el sistema operativo.
- Al salir de "Nuevo pedido" el borrador se conserva; solo se pregunta al usar "Descartar pedido".
- El menú de cocina abre el detalle desde cada pedido, no como opción aparte.
- Los productos no tienen fotografías.
