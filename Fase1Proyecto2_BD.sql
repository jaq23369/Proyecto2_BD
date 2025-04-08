
-- Tabla de Eventos
CREATE TABLE eventos (
    id_evento SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    fecha TIMESTAMP NOT NULL
);

-- Tabla de Usuarios
CREATE TABLE usuarios (
    id_usuario SERIAL PRIMARY KEY,
    nombre_usuario VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE
);

-- Tabla de Asientos
CREATE TABLE asientos (
    id_asiento SERIAL PRIMARY KEY,
    id_evento INT NOT NULL,
    numero_asiento INT NOT NULL,
    estado VARCHAR(20) DEFAULT 'disponible' NOT NULL,
    FOREIGN KEY (id_evento) REFERENCES eventos(id_evento) ON DELETE CASCADE,
    CONSTRAINT unique_asiento_evento UNIQUE (id_evento, numero_asiento),
    CONSTRAINT check_estado CHECK (estado IN ('disponible', 'reservado'))
);

-- Tabla de Reservas
CREATE TABLE reservas (
    id_reserva SERIAL PRIMARY KEY,
    id_evento INT NOT NULL,
    id_asiento INT NOT NULL,
    id_usuario INT NOT NULL,
    fecha_reserva TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (id_evento) REFERENCES eventos(id_evento) ON DELETE CASCADE,
    FOREIGN KEY (id_asiento) REFERENCES asientos(id_asiento) ON DELETE CASCADE,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    CONSTRAINT unique_asiento_reservado UNIQUE (id_asiento)
);

-- Índices para mejorar rendimiento en consultas frecuentes
CREATE INDEX idx_asientos_evento ON asientos(id_evento);
CREATE INDEX idx_reservas_evento ON reservas(id_evento);
CREATE INDEX idx_reservas_usuario ON reservas(id_usuario);