-- Run this file first in MySQL Workbench
-- CCC 151 Final Project - Inventory Tracking System

CREATE DATABASE IF NOT EXISTS inventory_db;
USE inventory_db;

CREATE TABLE IF NOT EXISTS categories (
    category_id   INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id   INT AUTO_INCREMENT PRIMARY KEY,
    supplier_name VARCHAR(150) NOT NULL,
    contact       VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS products (
    product_id   INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(150) NOT NULL,
    category_id  INT,
    supplier_id  INT,
    quantity     INT DEFAULT 0,
    price        DECIMAL(10,2) DEFAULT 0.00,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)  ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id   INT AUTO_INCREMENT PRIMARY KEY,
    product_id       INT NOT NULL,
    type             ENUM('IN','OUT') NOT NULL,
    quantity         INT NOT NULL,
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

-- Sample data
INSERT IGNORE INTO categories (category_name) VALUES ('Electronics'),('Food'),('Office Supplies'),('Clothing');
INSERT IGNORE INTO suppliers  (supplier_name, contact) VALUES ('TechWorld','09171234567'),('FoodHub','09281234567'),('OfficeMax','09391234567');
INSERT IGNORE INTO products   (product_name, category_id, supplier_id, quantity, price) VALUES
    ('Laptop',        1, 1, 10, 35000),
    ('Ballpen (box)', 3, 3, 50,   120),
    ('Rice (50kg)',   2, 2, 30,  2500);
