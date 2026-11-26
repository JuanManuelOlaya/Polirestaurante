-- ADR-006: el rol se identifica por la tabla donde aparece el usuario
CREATE TABLE IF NOT EXISTS administrador (
  id INTEGER PRIMARY KEY, nombre TEXT NOT NULL, username TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL, activo INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS mesero (
  id INTEGER PRIMARY KEY, nombre TEXT NOT NULL, username TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL, activo INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS cocinero (
  id INTEGER PRIMARY KEY, nombre TEXT NOT NULL, username TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL, activo INTEGER NOT NULL DEFAULT 1);

CREATE TABLE IF NOT EXISTS cliente (
  id INTEGER PRIMARY KEY, nombre TEXT NOT NULL, telefono TEXT, email TEXT,
  fecha_registro TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS categoria (
  id INTEGER PRIMARY KEY, nombre TEXT NOT NULL UNIQUE, descripcion TEXT);
CREATE TABLE IF NOT EXISTS presentacion (
  id INTEGER PRIMARY KEY, nombre TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS producto (
  id INTEGER PRIMARY KEY, nombre TEXT NOT NULL, descripcion TEXT,
  id_categoria INTEGER NOT NULL REFERENCES categoria(id),
  id_presentacion INTEGER NOT NULL REFERENCES presentacion(id),
  unidades INTEGER NOT NULL CHECK (unidades >= 0),
  precio INTEGER NOT NULL CHECK (precio > 0),         -- pesos colombianos
  disponible INTEGER NOT NULL DEFAULT 1,
  activo INTEGER NOT NULL DEFAULT 1);                 -- ADR-007: no se borra
CREATE TABLE IF NOT EXISTS mesa (
  id INTEGER PRIMARY KEY, numero INTEGER NOT NULL UNIQUE,
  estado TEXT NOT NULL DEFAULT 'DISPONIBLE' CHECK (estado IN ('DISPONIBLE','OCUPADA')));

CREATE TABLE IF NOT EXISTS pedido (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  numero_llegada INTEGER NOT NULL UNIQUE,
  clave_envio TEXT UNIQUE,                            -- evita duplicados al reintentar
  tipo_servicio TEXT NOT NULL CHECK (tipo_servicio IN ('SALON','LLEVAR')),
  id_mesa INTEGER REFERENCES mesa(id),
  id_cliente INTEGER REFERENCES cliente(id),
  id_mesero INTEGER NOT NULL REFERENCES mesero(id),
  id_cocinero INTEGER REFERENCES cocinero(id),        -- bloquea el pedido (CU-03)
  estado TEXT NOT NULL CHECK (estado IN
    ('RECIBIDO','EN_PREPARACION','LISTO','ENTREGADO','PAGADO','CANCELADO')),
  nota_general TEXT NOT NULL DEFAULT '',
  total INTEGER NOT NULL,
  fecha_creacion TEXT NOT NULL,
  hora_inicio TEXT, hora_listo TEXT, hora_entrega TEXT,
  CHECK ((tipo_servicio='SALON' AND id_mesa IS NOT NULL) OR
         (tipo_servicio='LLEVAR' AND id_cliente IS NOT NULL)));
CREATE INDEX IF NOT EXISTS ix_pedido_estado ON pedido(estado);
CREATE INDEX IF NOT EXISTS ix_pedido_mesero ON pedido(id_mesero, estado);

CREATE TABLE IF NOT EXISTS detalle_pedido (
  id INTEGER PRIMARY KEY, id_pedido INTEGER NOT NULL REFERENCES pedido(id),
  id_producto INTEGER NOT NULL REFERENCES producto(id),
  nombre_producto TEXT NOT NULL, precio_unitario INTEGER NOT NULL,   -- ADR-007
  cantidad INTEGER NOT NULL CHECK (cantidad > 0),
  nota TEXT NOT NULL DEFAULT '' CHECK (length(nota) <= 150));

CREATE TABLE IF NOT EXISTS pago (
  id INTEGER PRIMARY KEY, id_pedido INTEGER NOT NULL REFERENCES pedido(id),
  metodo TEXT NOT NULL CHECK (metodo IN ('EFECTIVO','TARJETA','NEQUI')),
  monto INTEGER NOT NULL, valor_recibido INTEGER NOT NULL, cambio INTEGER NOT NULL,
  fecha_pago TEXT NOT NULL, id_administrador INTEGER NOT NULL REFERENCES administrador(id));

CREATE TABLE IF NOT EXISTS historial_estado (
  id INTEGER PRIMARY KEY, id_pedido INTEGER NOT NULL REFERENCES pedido(id),
  estado TEXT NOT NULL, usuario TEXT NOT NULL, fecha TEXT NOT NULL,
  motivo TEXT, autorizado_por TEXT);

CREATE TABLE IF NOT EXISTS notificacion (
  id INTEGER PRIMARY KEY, rol TEXT NOT NULL, id_usuario INTEGER,
  mensaje TEXT NOT NULL, fecha TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS intento (
  clave TEXT PRIMARY KEY, fallidos INTEGER NOT NULL, bloqueado_hasta TEXT);
CREATE TABLE IF NOT EXISTS registro_acceso (
  id INTEGER PRIMARY KEY, username TEXT NOT NULL, resultado TEXT NOT NULL, fecha TEXT NOT NULL);

-- ADR-005: contador de cambios para el polling
CREATE TABLE IF NOT EXISTS version (id INTEGER PRIMARY KEY CHECK (id=1), numero INTEGER NOT NULL);
INSERT OR IGNORE INTO version VALUES (1, 0);
