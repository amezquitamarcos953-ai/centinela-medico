CREATE TABLE IF NOT EXISTS medicos(id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, especialidad TEXT, correo TEXT UNIQUE, password_hash TEXT, instance_id TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS pacientes(id INTEGER PRIMARY KEY AUTOINCREMENT, medico_id INTEGER, nombre TEXT, edad INTEGER, sexo TEXT, ciudad TEXT, telefono TEXT, alergias TEXT, medicamentos TEXT, antecedentes TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS chequeos(id INTEGER PRIMARY KEY AUTOINCREMENT, paciente_id INTEGER, sintomas TEXT, temperatura REAL, spo2 REAL, urgencia TEXT, probabilidades TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS recetas(id INTEGER PRIMARY KEY AUTOINCREMENT, paciente_id INTEGER, medicamento TEXT, dosis TEXT, frecuencia TEXT, duracion TEXT, cantidad TEXT, indicaciones TEXT, notas TEXT, entregada INTEGER DEFAULT 0, created_at TEXT);
CREATE TABLE IF NOT EXISTS citas(id INTEGER PRIMARY KEY AUTOINCREMENT, paciente_id INTEGER, fecha TEXT, hora TEXT, motivo TEXT, tipo TEXT, notas TEXT, atendida INTEGER DEFAULT 0, created_at TEXT);
CREATE TABLE IF NOT EXISTS examenes(id INTEGER PRIMARY KEY AUTOINCREMENT, paciente_id INTEGER, nombre_archivo TEXT, tipo TEXT, fecha TEXT, notas TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS imagenes(id INTEGER PRIMARY KEY AUTOINCREMENT, paciente_id INTEGER, tipo TEXT, nombre_archivo TEXT, interpretacion TEXT, estado TEXT, created_at TEXT);
