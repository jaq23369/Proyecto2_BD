-- Script de carga de datos (data.sql)

-- Insertar datos en la tabla eventos
INSERT INTO eventos (nombre, fecha) VALUES
  ('Concierto Rock Nacional', '2025-06-15 19:00:00'),
  ('Obra de Teatro "El Fantasma"', '2025-05-20 20:30:00'),
  ('Conferencia de Tecnología', '2025-07-10 09:00:00');

-- Insertar datos en la tabla usuarios
INSERT INTO usuarios (nombre_usuario, email) VALUES
  ('Carlos Rodríguez', 'carlos.rodriguez@email.com'),
  ('María López', 'maria.lopez@email.com'),
  ('Juan Pérez', 'juan.perez@email.com'),
  ('Ana García', 'ana.garcia@email.com'),
  ('Pedro Sánchez', 'pedro.sanchez@email.com'),
  ('Laura Martínez', 'laura.martinez@email.com'),
  ('Roberto Fernández', 'roberto.fernandez@email.com'),
  ('Sofía Torres', 'sofia.torres@email.com'),
  ('Diego Ramírez', 'diego.ramirez@email.com'),
  ('Elena Castro', 'elena.castro@email.com');

-- Insertar asientos para el primer evento (Concierto Rock Nacional)
-- Se crean 50 asientos para este evento
DO $$
DECLARE
  i INT;
BEGIN
  FOR i IN 1..50 LOOP
    INSERT INTO asientos (id_evento, numero_asiento, estado) 
    VALUES (1, i, 'disponible');
  END LOOP;
END $$;

-- Insertar asientos para el segundo evento (Obra de Teatro)
-- Se crean 30 asientos para este evento
DO $$
DECLARE
  i INT;
BEGIN
  FOR i IN 1..30 LOOP
    INSERT INTO asientos (id_evento, numero_asiento, estado) 
    VALUES (2, i, 'disponible');
  END LOOP;
END $$;

-- Insertar asientos para el tercer evento (Conferencia)
-- Se crean 40 asientos para este evento
DO $$
DECLARE
  i INT;
BEGIN
  FOR i IN 1..40 LOOP
    INSERT INTO asientos (id_evento, numero_asiento, estado) 
    VALUES (3, i, 'disponible');
  END LOOP;
END $$;

-- Crear algunas reservas iniciales para el primer evento
-- Primero actualizamos el estado de los asientos que serán reservados
UPDATE asientos SET estado = 'reservado' WHERE id_evento = 1 AND numero_asiento IN (1, 2, 5, 10, 15);

-- Luego insertamos las reservas correspondientes
INSERT INTO reservas (id_evento, id_asiento, id_usuario, fecha_reserva) VALUES
  (1, (SELECT id_asiento FROM asientos WHERE id_evento = 1 AND numero_asiento = 1), 1, '2025-04-01 10:15:00'),
  (1, (SELECT id_asiento FROM asientos WHERE id_evento = 1 AND numero_asiento = 2), 2, '2025-04-02 14:30:00'),
  (1, (SELECT id_asiento FROM asientos WHERE id_evento = 1 AND numero_asiento = 5), 3, '2025-04-03 09:45:00'),
  (1, (SELECT id_asiento FROM asientos WHERE id_evento = 1 AND numero_asiento = 10), 4, '2025-04-04 16:20:00'),
  (1, (SELECT id_asiento FROM asientos WHERE id_evento = 1 AND numero_asiento = 15), 5, '2025-04-05 11:10:00');

-- Crear algunas reservas iniciales para el segundo evento
UPDATE asientos SET estado = 'reservado' WHERE id_evento = 2 AND numero_asiento IN (3, 7, 12);

INSERT INTO reservas (id_evento, id_asiento, id_usuario, fecha_reserva) VALUES
  (2, (SELECT id_asiento FROM asientos WHERE id_evento = 2 AND numero_asiento = 3), 6, '2025-04-06 13:25:00'),
  (2, (SELECT id_asiento FROM asientos WHERE id_evento = 2 AND numero_asiento = 7), 7, '2025-04-07 15:40:00'),
  (2, (SELECT id_asiento FROM asientos WHERE id_evento = 2 AND numero_asiento = 12), 8, '2025-04-08 17:55:00');

-- Crear algunas reservas iniciales para el tercer evento
UPDATE asientos SET estado = 'reservado' WHERE id_evento = 3 AND numero_asiento IN (4, 8);

INSERT INTO reservas (id_evento, id_asiento, id_usuario, fecha_reserva) VALUES
  (3, (SELECT id_asiento FROM asientos WHERE id_evento = 3 AND numero_asiento = 4), 9, '2025-04-09 08:30:00'),
  (3, (SELECT id_asiento FROM asientos WHERE id_evento = 3 AND numero_asiento = 8), 10, '2025-04-10 12:15:00');