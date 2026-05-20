# main.py — Simple Inventory Tracking System
# CCC 151 Final Project | Python + Flet + MySQL
# ──────────────────────────────────────────────
# HOW TO RUN:
#   1. pip install flet mysql-connector-python
#   2. Run db_setup.sql in MySQL Workbench first
#   3. Edit DB_HOST / DB_USER / DB_PASS below
#   4. python main.py
# ──────────────────────────────────────────────

import flet as ft
import mysql.connector

# ═══════════════════════════════════════
#  DATABASE CONFIG  ← edit these
# ═══════════════════════════════════════
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = ""          # your MySQL password
DB_NAME = "inventory_db"

# ═══════════════════════════════════════
#  DB HELPERS
# ═══════════════════════════════════════
def get_conn():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME
    )

def run(sql, params=(), fetch=False):
    c = get_conn()
    cur = c.cursor(dictionary=True)
    cur.execute(sql, params)
    result = cur.fetchall() if fetch else None
    c.commit()
    c.close()
    return result or []

def get_products(search=""):
    if search:
        kw = f"%{search}%"
        return run("""
            SELECT p.product_id, p.product_name, c.category_name,
                   s.supplier_name, p.quantity, p.price
            FROM   products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            LEFT JOIN suppliers  s ON p.supplier_id  = s.supplier_id
            WHERE  p.product_name LIKE %s OR c.category_name LIKE %s
            ORDER BY p.product_name
        """, (kw, kw), fetch=True)
    return run("""
        SELECT p.product_id, p.product_name, c.category_name,
               s.supplier_name, p.quantity, p.price
        FROM   products p
        LEFT JOIN categories c ON p.category_id = c.category_id
        LEFT JOIN suppliers  s ON p.supplier_id  = s.supplier_id
        ORDER BY p.product_name
    """, fetch=True)

def get_categories():  return run("SELECT * FROM categories ORDER BY category_name", fetch=True)
def get_suppliers():   return run("SELECT * FROM suppliers  ORDER BY supplier_name",  fetch=True)
def get_transactions():
    return run("""
        SELECT t.transaction_id, p.product_name, t.type,
               t.quantity, t.transaction_date
        FROM   transactions t
        JOIN   products p ON t.product_id = p.product_id
        ORDER  BY t.transaction_date DESC LIMIT 100
    """, fetch=True)

def add_product(name, cat_id, sup_id, qty, price):
    run("INSERT INTO products (product_name,category_id,supplier_id,quantity,price) VALUES (%s,%s,%s,%s,%s)",
        (name, cat_id, sup_id, qty, price))

def update_product(pid, name, cat_id, sup_id, qty, price):
    run("UPDATE products SET product_name=%s,category_id=%s,supplier_id=%s,quantity=%s,price=%s WHERE product_id=%s",
        (name, cat_id, sup_id, qty, price, pid))

def delete_product(pid):
    run("DELETE FROM products WHERE product_id=%s", (pid,))

def log_transaction(pid, tx_type, qty):
    run("INSERT INTO transactions (product_id,type,quantity) VALUES (%s,%s,%s)", (pid, tx_type, qty))
    delta = qty if tx_type == "IN" else -qty
    run("UPDATE products SET quantity = quantity + %s WHERE product_id=%s", (delta, pid))

def add_category(name):   run("INSERT IGNORE INTO categories (category_name) VALUES (%s)", (name,))
def add_supplier(name, contact): run("INSERT INTO suppliers (supplier_name,contact) VALUES (%s,%s)", (name, contact))

# ═══════════════════════════════════════
#  COLORS
# ═══════════════════════════════════════
NAVY   = "#1B3A6B"
BLUE   = "#2E86AB"
GREEN  = "#27AE60"
RED    = "#E74C3C"
AMBER  = "#F39C12"
BG     = "#F5F7FA"
WHITE  = "#FFFFFF"
GRAY   = "#6B7280"

# ═══════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════
def main(page: ft.Page):
    page.title         = "Inventory Tracking System"
    page.window_width  = 1000
    page.window_height = 680
    page.bgcolor       = BG
    page.padding       = 0
    page.theme_mode    = ft.ThemeMode.LIGHT

    body = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)

    # ── snackbar helper ──────────────────────────
    def toast(msg, ok=True):
        page.snack_bar = ft.SnackBar(
            ft.Text(msg, color=WHITE),
            bgcolor=GREEN if ok else RED, duration=2000
        )
        page.snack_bar.open = True
        page.update()

    # ═══════════════════════════════════════
    #  TAB 1 – PRODUCTS (main CRUD)
    # ═══════════════════════════════════════
    def products_tab():
        search_tf = ft.TextField(hint_text="Search product or category…",
                                 prefix_icon=ft.icons.SEARCH, expand=True,
                                 border_color=BLUE, border_radius=8)
        rows_col  = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=0)

        # ── form ────────────────────────────────
        edit_id   = {"v": None}
        name_tf   = ft.TextField(label="Product Name *", expand=True, border_color=BLUE)
        qty_tf    = ft.TextField(label="Qty *", width=100, border_color=BLUE,
                                 keyboard_type=ft.KeyboardType.NUMBER)
        price_tf  = ft.TextField(label="Price ₱ *", width=130, border_color=BLUE,
                                 keyboard_type=ft.KeyboardType.NUMBER)
        cat_dd    = ft.Dropdown(label="Category", width=180, border_color=BLUE)
        sup_dd    = ft.Dropdown(label="Supplier",  width=180, border_color=BLUE)
        form_title = ft.Text("Add Product", size=16, weight=ft.FontWeight.BOLD, color=NAVY)
        save_btn   = ft.ElevatedButton("Save", icon=ft.icons.SAVE,
                                        bgcolor=NAVY, color=WHITE)
        clear_btn  = ft.TextButton("Clear")

        def load_dropdowns():
            cat_dd.options = [ft.dropdown.Option(str(c["category_id"]), c["category_name"])
                              for c in get_categories()]
            sup_dd.options = [ft.dropdown.Option(str(s["supplier_id"]), s["supplier_name"])
                              for s in get_suppliers()]

        def load_table(search=""):
            rows_col.controls.clear()
            products = get_products(search)
            if not products:
                rows_col.controls.append(ft.Text("No products found.", color=GRAY, italic=True))
                page.update(); return

            # header
            rows_col.controls.append(
                ft.Container(
                    bgcolor=NAVY, border_radius=ft.border_radius.only(top_left=8, top_right=8),
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    content=ft.Row([
                        ft.Text("Product Name", color=WHITE, weight=ft.FontWeight.BOLD, expand=3),
                        ft.Text("Category",     color=WHITE, weight=ft.FontWeight.BOLD, expand=2),
                        ft.Text("Supplier",     color=WHITE, weight=ft.FontWeight.BOLD, expand=2),
                        ft.Text("Qty",          color=WHITE, weight=ft.FontWeight.BOLD, width=60),
                        ft.Text("Price",        color=WHITE, weight=ft.FontWeight.BOLD, width=100),
                        ft.Text("Actions",      color=WHITE, weight=ft.FontWeight.BOLD, width=90),
                    ])
                )
            )

            for i, p in enumerate(products):
                low = p["quantity"] <= 5
                qty_color = RED if low else ft.colors.BLACK
                bg = WHITE if i % 2 == 0 else "#F0F4FF"

                def make_edit(prod):
                    def do_edit(e):
                        edit_id["v"]  = prod["product_id"]
                        name_tf.value = prod["product_name"]
                        qty_tf.value  = str(prod["quantity"])
                        price_tf.value= str(prod["price"])
                        form_title.value = "✏️  Edit Product"
                        # match dropdowns
                        for c in get_categories():
                            if c["category_name"] == prod["category_name"]:
                                cat_dd.value = str(c["category_id"])
                        for s in get_suppliers():
                            if s["supplier_name"] == prod["supplier_name"]:
                                sup_dd.value = str(s["supplier_id"])
                        page.update()
                    return do_edit

                def make_delete(prod):
                    def do_delete(e):
                        dlg = ft.AlertDialog(
                            modal=True,
                            title=ft.Text("Delete Product?"),
                            content=ft.Text(f"Delete '{prod['product_name']}'? This cannot be undone."),
                            actions=[
                                ft.TextButton("Cancel", on_click=lambda e: setattr(dlg, 'open', False) or page.update()),
                                ft.FilledButton("Delete",
                                    style=ft.ButtonStyle(bgcolor=RED),
                                    on_click=lambda e: [
                                        setattr(dlg, 'open', False),
                                        delete_product(prod["product_id"]),
                                        toast("Product deleted."),
                                        load_table(search_tf.value),
                                    ]),
                            ]
                        )
                        page.dialog = dlg; dlg.open = True; page.update()
                    return do_delete

                rows_col.controls.append(
                    ft.Container(
                        bgcolor=bg,
                        padding=ft.padding.symmetric(horizontal=12, vertical=6),
                        border=ft.border.only(bottom=ft.border.BorderSide(1, "#E5E7EB")),
                        content=ft.Row([
                            ft.Text(p["product_name"], expand=3),
                            ft.Text(p["category_name"] or "—", expand=2, color=GRAY),
                            ft.Text(p["supplier_name"] or "—", expand=2, color=GRAY),
                            ft.Text(str(p["quantity"]), width=60, color=qty_color,
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(f"₱{p['price']:,.2f}", width=100),
                            ft.Row(width=90, spacing=0, controls=[
                                ft.IconButton(ft.icons.EDIT,   icon_color=BLUE, tooltip="Edit",
                                              on_click=make_edit(p)),
                                ft.IconButton(ft.icons.DELETE, icon_color=RED,  tooltip="Delete",
                                              on_click=make_delete(p)),
                            ]),
                        ])
                    )
                )
            page.update()

        def do_save(e):
            if not name_tf.value.strip():
                toast("Product name is required.", ok=False); return
            try:
                qty   = int(qty_tf.value or 0)
                price = float(price_tf.value or 0)
            except ValueError:
                toast("Qty and Price must be numbers.", ok=False); return

            cat = int(cat_dd.value) if cat_dd.value else None
            sup = int(sup_dd.value) if sup_dd.value else None

            if edit_id["v"]:
                update_product(edit_id["v"], name_tf.value.strip(), cat, sup, qty, price)
                toast("Product updated!")
            else:
                add_product(name_tf.value.strip(), cat, sup, qty, price)
                toast("Product added!")

            do_clear(None)
            load_table()

        def do_clear(e):
            edit_id["v"] = None
            name_tf.value = qty_tf.value = price_tf.value = ""
            cat_dd.value  = sup_dd.value = None
            form_title.value = "Add Product"
            page.update()

        save_btn.on_click  = do_save
        clear_btn.on_click = do_clear
        search_tf.on_submit = lambda e: load_table(search_tf.value.strip())
        ft.ElevatedButton  # just to avoid lint issue

        load_dropdowns()
        load_table()

        return ft.Column(spacing=16, controls=[
            # ── form card ────────────────────────
            ft.Card(elevation=2, content=ft.Container(
                padding=20, bgcolor=WHITE, border_radius=10,
                content=ft.Column(spacing=10, controls=[
                    form_title,
                    ft.Row([name_tf, qty_tf, price_tf], spacing=8),
                    ft.Row([cat_dd, sup_dd, save_btn, clear_btn], spacing=8),
                ])
            )),
            # ── search + table ───────────────────
            ft.Row([
                search_tf,
                ft.ElevatedButton("Search", bgcolor=BLUE, color=WHITE,
                                  on_click=lambda e: load_table(search_tf.value.strip())),
                ft.ElevatedButton("Show All", bgcolor=GRAY, color=WHITE,
                                  on_click=lambda e: [setattr(search_tf, 'value', ''), load_table(), page.update()]),
            ], spacing=8),
            ft.Card(elevation=2, content=ft.Container(
                padding=12, bgcolor=WHITE, border_radius=10,
                content=rows_col,
            )),
        ])

    # ═══════════════════════════════════════
    #  TAB 2 – STOCK IN / OUT
    # ═══════════════════════════════════════
    def stock_tab():
        prod_dd  = ft.Dropdown(label="Select Product *", expand=True, border_color=BLUE)
        type_dd  = ft.Dropdown(label="Type *", width=160, border_color=BLUE, options=[
            ft.dropdown.Option("IN",  "Stock IN"),
            ft.dropdown.Option("OUT", "Stock OUT"),
        ])
        qty_tf   = ft.TextField(label="Quantity *", width=120, border_color=BLUE,
                                keyboard_type=ft.KeyboardType.NUMBER)
        log_col  = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=0)

        def load():
            products = get_products()
            prod_dd.options = [
                ft.dropdown.Option(str(p["product_id"]),
                                   f"{p['product_name']}  (stock: {p['quantity']})")
                for p in products
            ]
            log_col.controls.clear()
            txs = get_transactions()
            if not txs:
                log_col.controls.append(ft.Text("No transactions yet.", color=GRAY, italic=True))
                page.update(); return

            log_col.controls.append(
                ft.Container(
                    bgcolor=NAVY, border_radius=ft.border_radius.only(top_left=8, top_right=8),
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    content=ft.Row([
                        ft.Text("#",       color=WHITE, weight=ft.FontWeight.BOLD, width=50),
                        ft.Text("Product", color=WHITE, weight=ft.FontWeight.BOLD, expand=3),
                        ft.Text("Type",    color=WHITE, weight=ft.FontWeight.BOLD, width=80),
                        ft.Text("Qty",     color=WHITE, weight=ft.FontWeight.BOLD, width=60),
                        ft.Text("Date",    color=WHITE, weight=ft.FontWeight.BOLD, expand=2),
                    ])
                )
            )
            for i, t in enumerate(txs):
                color = GREEN if t["type"] == "IN" else RED
                bg    = WHITE if i % 2 == 0 else "#F0F4FF"
                log_col.controls.append(
                    ft.Container(
                        bgcolor=bg,
                        padding=ft.padding.symmetric(horizontal=12, vertical=6),
                        border=ft.border.only(bottom=ft.border.BorderSide(1, "#E5E7EB")),
                        content=ft.Row([
                            ft.Text(str(t["transaction_id"]), width=50, color=GRAY),
                            ft.Text(t["product_name"], expand=3),
                            ft.Text(t["type"], width=80, color=color, weight=ft.FontWeight.BOLD),
                            ft.Text(str(t["quantity"]), width=60),
                            ft.Text(str(t["transaction_date"])[:16], expand=2, color=GRAY),
                        ])
                    )
                )
            page.update()

        def do_submit(e):
            if not prod_dd.value or not type_dd.value:
                toast("Select a product and type.", ok=False); return
            try:
                qty = int(qty_tf.value or 0)
                if qty <= 0: raise ValueError
            except ValueError:
                toast("Enter a valid quantity.", ok=False); return

            if type_dd.value == "OUT":
                prods = get_products()
                cur_qty = next((p["quantity"] for p in prods
                                if str(p["product_id"]) == prod_dd.value), 0)
                if qty > cur_qty:
                    toast(f"Not enough stock! Only {cur_qty} available.", ok=False); return

            log_transaction(int(prod_dd.value), type_dd.value, qty)
            toast(f"Stock {type_dd.value} recorded!")
            qty_tf.value = ""
            load()

        load()

        return ft.Column(spacing=16, controls=[
            ft.Card(elevation=2, content=ft.Container(
                padding=20, bgcolor=WHITE, border_radius=10,
                content=ft.Column(spacing=10, controls=[
                    ft.Text("Record Stock Movement", size=16,
                            weight=ft.FontWeight.BOLD, color=NAVY),
                    ft.Row([prod_dd, type_dd, qty_tf], spacing=8),
                    ft.ElevatedButton("Submit", icon=ft.icons.CHECK_CIRCLE,
                                      bgcolor=GREEN, color=WHITE, on_click=do_submit),
                ])
            )),
            ft.Text("Transaction History", size=16, weight=ft.FontWeight.BOLD, color=NAVY),
            ft.Card(elevation=2, content=ft.Container(
                padding=12, bgcolor=WHITE, border_radius=10,
                content=log_col,
            )),
        ])

    # ═══════════════════════════════════════
    #  TAB 3 – CATEGORIES & SUPPLIERS
    # ═══════════════════════════════════════
    def manage_tab():
        cat_tf   = ft.TextField(label="Category Name", expand=True, border_color=BLUE)
        sup_tf   = ft.TextField(label="Supplier Name", expand=True, border_color=BLUE)
        cont_tf  = ft.TextField(label="Contact",       width=180,   border_color=BLUE)
        cat_col  = ft.Column(spacing=4)
        sup_col  = ft.Column(spacing=4)

        def load():
            cat_col.controls.clear()
            for c in get_categories():
                cat_col.controls.append(ft.Container(
                    bgcolor="#F0F4FF", border_radius=6,
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    content=ft.Row([
                        ft.Icon(ft.icons.LABEL, color=BLUE, size=16),
                        ft.Text(c["category_name"], expand=True),
                    ])
                ))

            sup_col.controls.clear()
            for s in get_suppliers():
                sup_col.controls.append(ft.Container(
                    bgcolor="#F0F4FF", border_radius=6,
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    content=ft.Row([
                        ft.Icon(ft.icons.LOCAL_SHIPPING, color=BLUE, size=16),
                        ft.Text(s["supplier_name"], expand=True),
                        ft.Text(s["contact"] or "", color=GRAY),
                    ])
                ))
            page.update()

        def add_cat(e):
            if not cat_tf.value.strip():
                toast("Enter a category name.", ok=False); return
            add_category(cat_tf.value.strip())
            cat_tf.value = ""
            toast("Category added!")
            load()

        def add_sup(e):
            if not sup_tf.value.strip():
                toast("Enter a supplier name.", ok=False); return
            add_supplier(sup_tf.value.strip(), cont_tf.value.strip())
            sup_tf.value = cont_tf.value = ""
            toast("Supplier added!")
            load()

        load()

        return ft.Row(spacing=16, vertical_alignment=ft.CrossAxisAlignment.START, controls=[
            # categories
            ft.Card(elevation=2, expand=True, content=ft.Container(
                padding=20, bgcolor=WHITE, border_radius=10,
                content=ft.Column(spacing=10, controls=[
                    ft.Text("Categories", size=16, weight=ft.FontWeight.BOLD, color=NAVY),
                    ft.Row([cat_tf,
                            ft.ElevatedButton("Add", bgcolor=NAVY, color=WHITE, on_click=add_cat)]),
                    ft.Divider(),
                    cat_col,
                ])
            )),
            # suppliers
            ft.Card(elevation=2, expand=True, content=ft.Container(
                padding=20, bgcolor=WHITE, border_radius=10,
                content=ft.Column(spacing=10, controls=[
                    ft.Text("Suppliers", size=16, weight=ft.FontWeight.BOLD, color=NAVY),
                    ft.Row([sup_tf, cont_tf,
                            ft.ElevatedButton("Add", bgcolor=NAVY, color=WHITE, on_click=add_sup)]),
                    ft.Divider(),
                    sup_col,
                ])
            )),
        ])

    # ═══════════════════════════════════════
    #  TABS WRAPPER
    # ═══════════════════════════════════════
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=200,
        tab_alignment=ft.TabAlignment.START,
        expand=True,
        tabs=[
            ft.Tab(text="📦  Products",           content=ft.Container(padding=16, content=products_tab())),
            ft.Tab(text="🔄  Stock IN / OUT",     content=ft.Container(padding=16, content=stock_tab())),
            ft.Tab(text="🏷️  Categories & Suppliers", content=ft.Container(padding=16, content=manage_tab())),
        ]
    )

    page.add(
        # header bar
        ft.Container(
            bgcolor=NAVY, padding=ft.padding.symmetric(horizontal=24, vertical=14),
            content=ft.Row([
                ft.Icon(ft.icons.INVENTORY_2, color=WHITE, size=28),
                ft.Text("Inventory Tracking System", color=WHITE, size=20,
                        weight=ft.FontWeight.BOLD),
                ft.Text("CCC 151 Final Project", color="#90A4AE", size=12,
                        expand=True, text_align=ft.TextAlign.RIGHT),
            ])
        ),
        tabs,
    )

ft.app(target=main)
