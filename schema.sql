-- Crear base de datos si no existe (opcional, el usuario puede importarlo en su base de datos existente)
CREATE DATABASE IF NOT EXISTS invitaciones_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE invitaciones_db;

-- Tabla de Usuarios (Administradores y Super Admins)
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    rol VARCHAR(50) NOT NULL DEFAULT 'ADMIN_ORGANIZADOR', -- 'SUPER_ADMIN' o 'ADMIN_ORGANIZADOR'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Tabla de Invitaciones (Estructura principal del evento)
CREATE TABLE IF NOT EXISTS invitaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    tipo_evento VARCHAR(50) NOT NULL, -- 'Boda', 'Quinceañero', 'Cumpleaños', 'Bautizo', 'Otro'
    plantilla VARCHAR(50) NOT NULL DEFAULT 'elegance-gold', -- 'elegance-gold', 'royal-luxury', 'terracota-premium', 'floral-garden', 'minimal-white'
    musica_url VARCHAR(300) NULL,
    video_url VARCHAR(300) NULL,
    fecha_evento DATETIME NOT NULL,
    lugar_nombre VARCHAR(200) NULL,
    lugar_direccion VARCHAR(300) NULL,
    lugar_gmaps_url TEXT NULL,
    historia TEXT NULL,
    codigo_vestimenta VARCHAR(100) NULL,
    codigo_vestimenta_detalles TEXT NULL,
    regalos_banco VARCHAR(150) NULL,
    regalos_cuenta VARCHAR(100) NULL,
    regalos_nequi VARCHAR(50) NULL,
    regalos_daviplata VARCHAR(50) NULL,
    regalos_lista_url TEXT NULL,
    mensaje_final TEXT NULL,
    whatsapp_confirmacion VARCHAR(50) NULL, -- Celular organizador
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Tabla de Cronograma del Evento
CREATE TABLE IF NOT EXISTS cronograma_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invitacion_id INT NOT NULL,
    hora VARCHAR(50) NOT NULL,
    titulo VARCHAR(100) NOT NULL,
    descripcion VARCHAR(255) NULL,
    icono VARCHAR(50) NULL, -- 'clock', 'church', 'glass', 'utensils', 'music', 'camera'
    orden INT DEFAULT 0,
    FOREIGN KEY (invitacion_id) REFERENCES invitaciones(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Tabla de Invitados (Personalización, UUID de acceso y QR)
CREATE TABLE IF NOT EXISTS invitados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invitacion_id INT NOT NULL,
    uuid VARCHAR(36) UNIQUE NOT NULL, -- Token UUID v4 único
    nombre VARCHAR(200) NOT NULL,
    correo VARCHAR(150) NULL,
    telefono VARCHAR(50) NULL,
    cupos_asignados INT DEFAULT 1,
    cupos_confirmados INT DEFAULT 0,
    mesa VARCHAR(50) DEFAULT 'Por asignar',
    mensaje_bienvenida TEXT NULL,
    qr_path VARCHAR(255) NULL, -- Ruta a la imagen del QR
    estado_rsvp VARCHAR(20) DEFAULT 'Pendiente', -- 'Pendiente', 'Confirmado', 'Rechazado'
    mensaje_rsvp TEXT NULL,
    fecha_rsvp DATETIME NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (invitacion_id) REFERENCES invitaciones(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Tabla de Galería de Fotos
CREATE TABLE IF NOT EXISTS galeria_fotos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invitacion_id INT NOT NULL,
    foto_url VARCHAR(300) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (invitacion_id) REFERENCES invitaciones(id) ON DELETE CASCADE
) ENGINE=InnoDB;
