# 📦 Inventory Tracking System
### CCC 151 Final Project | Python + Flet + MySQL

---

## 📁 Project Structure

```
inventory_system/
├── main.py              ← Main Flet application (UI + logic)
├── db.py                ← MySQL database helper functions
├── database_setup.sql   ← Run this first to create the database
├── requirements.txt     ← Python dependencies
└── README.md            ← This file
```

---

## ⚙️ Setup Instructions

### Step 1 – Install Python packages
Open a terminal in VS Code and run:
```bash
pip install flet mysql-connector-python
```
> Or: `pip install -r requirements.txt`

---

### Step 2 – Set up MySQL Database

1. Open **MySQL Workbench** or any MySQL client.
2. Run the file `database_setup.sql` — it will:
   - Create the `inventory_db` database
   - Create 4 tables: `categories`, `suppliers`, `products`, `stock_transactions`
   - Insert sample data so the app is ready to use immediately

---

### Step 3 – Configure DB credentials in `db.py`

Open `db.py` and edit the top section:
```python
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",       # ← your MySQL username
    "password": "",           # ← your MySQL password
    "database": "inventory_db",
}
```

---

### Step 4 – Run the App
```bash
python main.py
```

A desktop window will open automatically.

---

## 🗂️ Database ERD (Entity Relationship Diagram)

```
categories          suppliers
│  category_id PK   │  supplier_id PK
│  category_name     │  supplier_name
│  description        │  contact_name
│  created_at         │  phone / email / address
│                     │  created_at
└──────────┐ ┌───────┘
           ↓ ↓
         products
         │  product_id PK
         │  product_name
         │  sku (UNIQUE)
         │  category_id  FK → categories
         │  supplier_id  FK → suppliers
         │  quantity
         │  unit_price
         │  reorder_level
         │  description
         │  created_at / updated_at
         │
         ↓ (1 product → many transactions)
    stock_transactions
         │  transaction_id PK
         │  product_id  FK → products
         │  transaction_type  (IN / OUT / ADJUSTMENT)
         │  quantity_change
         │  notes
         │  transaction_date
```

**Relationships:**
- `products.category_id` → `categories.category_id` (Many-to-One)
- `products.supplier_id` → `suppliers.supplier_id` (Many-to-One)
- `stock_transactions.product_id` → `products.product_id` (Many-to-One)

---

## 🖥️ System Features

| Feature | Description |
|---|---|
| **Dashboard** | Overview stats: total products, low-stock alerts, inventory value, today's transactions |
| **Products** | Full CRUD — Add, View/Search, Edit, Delete products |
| **Stock Management** | Record Stock IN / Stock OUT / Adjustments with full audit log |
| **Categories** | Add and delete product categories |
| **Suppliers** | Add and delete supplier records |
| **Low-Stock Alerts** | Automatic highlighting when quantity ≤ reorder level |
| **Search** | Real-time product search by name, SKU, or category |

---

## 🎓 Grading Checklist

| Criterion | How it's met |
|---|---|
| ✅ Functionality (30%) | Select, Add, Edit, Delete all working for Products; Stock IN/OUT/Adjust |
| ✅ GUI Design (15%) | Professional Flet desktop UI with navigation rail, cards, color-coded alerts |
| ✅ Programming Standards (15%) | Separated `db.py` (data layer) and `main.py` (UI layer), clean functions |
| ✅ Database ERD (20%) | 4 related tables with proper PKs, FKs, data types |
| ✅ Presentation (20%) | Clear screens per module, intuitive navigation |
