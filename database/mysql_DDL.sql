-- ============================================================
-- BASE DE DATOS: curso_python_db
-- ============================================================
-- Indica al servidor que este script está escrito en UTF-8. Sin esta
-- línea, algunos clientes (como el `mysql` de consola) envían el texto
-- como latin1 y los acentos se guardan dañados ("ElectrÃ³nica").
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE DATABASE IF NOT EXISTS curso_python_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE curso_python_db;

-- ------------------------------------------------------------
-- 1. TABLA: roles
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 2. TABLA: usuarios
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rol_id INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_usuarios_roles
        FOREIGN KEY (rol_id) REFERENCES roles(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 3. TABLA: categorias
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categorias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 4. TABLA: productos
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS productos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    categoria_id INT NOT NULL,
    sku VARCHAR(50) NOT NULL UNIQUE,
    nombre VARCHAR(150) NOT NULL,
    precio DECIMAL(10, 2) NOT NULL CHECK (precio >= 0),
    stock INT NOT NULL DEFAULT 0 CHECK (stock >= 0),
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_productos_categorias
        FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- DATOS SEMILLA (Seeders de prueba)
-- ------------------------------------------------------------
INSERT INTO roles (nombre, descripcion) VALUES
('Administrador', 'Acceso total al sistema'),
('Operador', 'Gestión de productos e inventario');

INSERT INTO categorias (nombre, descripcion) VALUES
('Electrónica', 'Dispositivos y accesorios electrónicos'),
('Oficina', 'Artículos y suministros de oficina');

-- Contraseña por defecto: Admin123
-- Hash generado con utils/security.py (bcrypt, costo 12).
-- Para generar otro:  python -m utils.security
INSERT INTO usuarios (rol_id, nombre, email, password_hash) VALUES
(1, 'Admin Sistema', 'admin@escuela.edu', '$2b$12$GbU6spXHM6SzD9RKidrIketco.0unEaobDVEobRxS8SzScb0.MVnS');

INSERT INTO productos (categoria_id, sku, nombre, precio, stock) VALUES
(1, 'PROD-001', 'Teclado Mecánico RGB', 85.50, 15),
(1, 'PROD-002', 'Monitor 24 Pulgadas FHD', 190.00, 8),
(2, 'PROD-003', 'Silla Ergonómica', 220.00, 5);

-- ------------------------------------------------------------
-- Si la base ya existía con el hash anterior (que no correspondía
-- a Admin123), basta con ejecutar solo esta sentencia:
-- ------------------------------------------------------------
-- UPDATE usuarios
-- SET password_hash = '$2b$12$GbU6spXHM6SzD9RKidrIketco.0unEaobDVEobRxS8SzScb0.MVnS'
-- WHERE email = 'admin@escuela.edu';
