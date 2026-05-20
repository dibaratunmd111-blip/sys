-- ============================================================
--  Inventory Tracking System - Database Setup
--  CCC 151 Final Project
-- ============================================================

CREATE DATABASE IF NOT EXISTS inventory_db;
USE inventory_db;

-- ─────────────────────────────────────────────
-- TABLE 1: categories
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS categories (
    category_id   INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description   TEXT,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
-- TABLE 2: suppliers
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id   INT AUTO_INCREMENT PRIMARY KEY,
    supplier_name VARCHAR(150) NOT NULL,
    contact_name  VARCHAR(100),
    phone         VARCHAR(20),
    email         VARCHAR(100),
    address       TEXT,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
-- TABLE 3: products  (core inventory table)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    product_id    INT AUTO_INCREMENT PRIMARY KEY,
    product_name  VARCHAR(150) NOT NULL,
    sku           VARCHAR(50) UNIQUE,
    category_id   INT,
    supplier_id   INT,
    quantity      INT NOT NULL DEFAULT 0,
    unit_price    DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    reorder_level INT DEFAULT 10,
    description   TEXT,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE SET NULL
);

-- ─────────────────────────────────────────────
-- TABLE 4: stock_transactions  (audit log)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS stock_transactions (
    transaction_id   INT AUTO_INCREMENT PRIMARY KEY,
    product_id       INT NOT NULL,
    transaction_type ENUM('IN', 'OUT', 'ADJUSTMENT') NOT NULL,
    quantity_change  INT NOT NULL,
    notes            TEXT,
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- SAMPLE DATA
-- ─────────────────────────────────────────────
INSERT IGNORE INTO categories (category_name, description) VALUES
    ('Electronics',   'Electronic devices and components'),
    ('Office Supplies','Stationery and office materials'),
    ('Furniture',     'Office and home furniture'),
    ('Clothing',      'Apparel and accessories'),
    ('Food & Beverage','Consumable food items');

INSERT IGNORE INTO suppliers (supplier_name, contact_name, phone, email, address) VALUES
    ('TechWorld Inc.',    'Juan dela Cruz',  '09171234567', 'juan@techworld.ph',    'Makati City, Metro Manila'),
    ('OfficeHub PH',      'Maria Santos',    '09281234567', 'maria@officehub.ph',   'Quezon City, Metro Manila'),
    ('FurniCo Trading',   'Pedro Reyes',     '09391234567', 'pedro@furnico.ph',     'Pasig City, Metro Manila');

INSERT IGNORE INTO products (product_name, sku, category_id, supplier_id, quantity, unit_price, reorder_level, description) VALUES
    ('Laptop ASUS VivoBook',  'SKU-001', 1, 1, 15, 35000.00, 5,  '15.6-inch, Core i5, 8GB RAM'),
    ('Wireless Mouse',        'SKU-002', 1, 1, 50, 850.00,   10, 'USB wireless mouse'),
    ('Ballpen Box (50pcs)',   'SKU-003', 2, 2, 30, 120.00,   15, 'Black ballpen set'),
    ('A4 Bond Paper (ream)',  'SKU-004', 2, 2, 25, 280.00,   20, '80gsm white bond paper'),
    ('Office Chair',          'SKU-005', 3, 3, 8,  4500.00,  3,  'Ergonomic mesh back chair'),
    ('Filing Cabinet',        'SKU-006', 3, 3, 5,  6800.00,  2,  '4-drawer steel filing cabinet'),
    ('USB-C Hub 7-in-1',      'SKU-007', 1, 1, 40, 1200.00,  8,  '7-port USB-C hub');
