# main.py – Inventory Tracking System
# CCC 151 Final Project  |  Python + Flet + MySQL
# ─────────────────────────────────────────────────────────────

import flet as ft
from flet import (
    Page, View, AppBar, NavigationRail, NavigationRailDestination,
    Text, Icon, icons, colors, ElevatedButton, TextButton,
    TextField, Dropdown, dropdown, DataTable, DataColumn, DataRow, DataCell,
    Column, Row, Container, Card, Divider, AlertDialog,
    MainAxisAlignment, CrossAxisAlignment, ScrollMode,
    SnackBar, IconButton, FilledButton, OutlinedButton,
    padding, border_radius, border, FontWeight, TextThemeStyle,
    ThemeMode, Theme, ColorScheme,
)
import db

# ═══════════════════════════════════════════════════════════════
#  COLOUR TOKENS
# ═══════════════════════════════════════════════════════════════
PRIMARY        = "#1E3A5F"   # deep navy
SECONDARY      = "#2E86AB"   # teal-blue
ACCENT         = "#F0A500"   # amber
DANGER         = "#E63946"   # red
SUCCESS        = "#2DC653"   # green
BG             = "#F4F6FB"   # light grey bg
SURFACE        = "#FFFFFF"
TEXT_DARK      = "#1A1A2E"
TEXT_MUTED     = "#6B7280"
NAV_BG         = "#1E3A5F"
NAV_SELECTED   = "#2E86AB"


# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════

def stat_card(title: str, value: str, icon_name: str, color: str):
    return Card(
        elevation=3,
        surface_tint_color=color,
        content=Container(
            padding=padding.all(20),
            width=200,
            content=Column(
                spacing=8,
                controls=[
                    Icon(icon_name, color=color, size=32),
                    Text(value, size=28, weight=FontWeight.BOLD, color=TEXT_DARK),
                    Text(title,  size=13, color=TEXT_MUTED),
                ],
            ),
        ),
    )


def section_title(text: str):
    return Text(text, size=20, weight=FontWeight.BOLD, color=PRIMARY)


def snack(page: Page, msg: str, error=False):
    page.snack_bar = SnackBar(
        content=Text(msg, color=colors.WHITE),
        bgcolor=DANGER if error else SUCCESS,
        duration=2500,
    )
    page.snack_bar.open = True
    page.update()


def confirm_dialog(page: Page, message: str, on_confirm):
    dlg = AlertDialog(
        modal=True,
        title=Text("Confirm Action", weight=FontWeight.BOLD),
        content=Text(message),
        actions=[
            TextButton("Cancel",  on_click=lambda e: close_dlg(page, dlg)),
            FilledButton(
                "Confirm",
                style=ft.ButtonStyle(bgcolor=DANGER),
                on_click=lambda e: [close_dlg(page, dlg), on_confirm()],
            ),
        ],
    )
    page.dialog = dlg
    dlg.open = True
    page.update()


def close_dlg(page: Page, dlg: AlertDialog):
    dlg.open = False
    page.update()


# ═══════════════════════════════════════════════════════════════
#  PAGE BUILDERS
# ═══════════════════════════════════════════════════════════════

# ───────────────────────────────────────────
#  DASHBOARD
# ───────────────────────────────────────────

def build_dashboard(page: Page):
    stats = db.get_dashboard_stats()
    low   = db.get_low_stock_products()

    low_rows = [
        DataRow(cells=[
            DataCell(Text(r["product_name"])),
            DataCell(Text(r["sku"] or "")),
            DataCell(Text(r["category_name"] or "")),
            DataCell(Text(str(r["quantity"]), color=DANGER, weight=FontWeight.BOLD)),
            DataCell(Text(str(r["reorder_level"]))),
        ])
        for r in low
    ]

    return Column(
        scroll=ScrollMode.AUTO,
        spacing=24,
        controls=[
            section_title("📊  Dashboard"),
            Divider(height=1, color="#E5E7EB"),
            Row(
                wrap=True,
                spacing=16,
                controls=[
                    stat_card("Total Products",   str(stats["total_products"]),  icons.INVENTORY_2,      SECONDARY),
                    stat_card("Low Stock Items",  str(stats["low_stock"]),       icons.WARNING_ROUNDED,  DANGER),
                    stat_card("Inventory Value",  f"₱{stats['inventory_value']:,.2f}", icons.MONETIZATION_ON, SUCCESS),
                    stat_card("Today's Transactions", str(stats["today_tx"]),   icons.SWAP_HORIZ,       ACCENT),
                ],
            ),
            section_title("⚠️  Low Stock Alerts"),
            Card(
                elevation=2,
                content=Container(
                    padding=padding.all(16),
                    content=DataTable(
                        columns=[
                            DataColumn(Text("Product",      weight=FontWeight.BOLD)),
                            DataColumn(Text("SKU",          weight=FontWeight.BOLD)),
                            DataColumn(Text("Category",     weight=FontWeight.BOLD)),
                            DataColumn(Text("Qty",          weight=FontWeight.BOLD)),
                            DataColumn(Text("Reorder Lvl",  weight=FontWeight.BOLD)),
                        ],
                        rows=low_rows if low_rows else [
                            DataRow(cells=[
                                DataCell(Text("✅ No low-stock items!", color=SUCCESS)),
                                DataCell(Text("")), DataCell(Text("")),
                                DataCell(Text("")), DataCell(Text("")),
                            ])
                        ],
                        border=ft.border.all(1, "#E5E7EB"),
                        border_radius=border_radius.all(8),
                        horizontal_lines=ft.border.BorderSide(1, "#F3F4F6"),
                    ),
                ),
            ),
        ],
    )


# ───────────────────────────────────────────
#  PRODUCTS  (full CRUD)
# ───────────────────────────────────────────

def build_products(page: Page):
    search_tf = TextField(
        hint_text="Search by name, SKU or category…",
        prefix_icon=icons.SEARCH,
        expand=True,
        border_color=SECONDARY,
        focused_border_color=PRIMARY,
        border_radius=8,
    )

    table_container = Column(scroll=ScrollMode.AUTO, expand=True)

    # ── helpers ────────────────────────────────
    def refresh(keyword=""):
        rows_data = db.search_products(keyword) if keyword else db.get_all_products()
        table_container.controls.clear()
        if not rows_data:
            table_container.controls.append(Text("No products found.", color=TEXT_MUTED))
            page.update()
            return

        dt_rows = []
        for r in rows_data:
            qty_color = DANGER if r["quantity"] <= r["reorder_level"] else TEXT_DARK
            dt_rows.append(DataRow(
                cells=[
                    DataCell(Text(r["product_name"])),
                    DataCell(Text(r["sku"] or "")),
                    DataCell(Text(r["category_name"] or "")),
                    DataCell(Text(r["supplier_name"] or "")),
                    DataCell(Text(str(r["quantity"]), color=qty_color, weight=FontWeight.BOLD)),
                    DataCell(Text(f"₱{r['unit_price']:,.2f}")),
                    DataCell(
                        Row(spacing=4, controls=[
                            IconButton(icons.EDIT,   tooltip="Edit",   icon_color=SECONDARY, on_click=lambda e, row=r: open_edit(row)),
                            IconButton(icons.DELETE, tooltip="Delete", icon_color=DANGER,    on_click=lambda e, row=r: ask_delete(row)),
                        ])
                    ),
                ]
            ))

        table_container.controls.append(
            DataTable(
                columns=[
                    DataColumn(Text("Product Name", weight=FontWeight.BOLD)),
                    DataColumn(Text("SKU",          weight=FontWeight.BOLD)),
                    DataColumn(Text("Category",     weight=FontWeight.BOLD)),
                    DataColumn(Text("Supplier",     weight=FontWeight.BOLD)),
                    DataColumn(Text("Qty",          weight=FontWeight.BOLD)),
                    DataColumn(Text("Unit Price",   weight=FontWeight.BOLD)),
                    DataColumn(Text("Actions",      weight=FontWeight.BOLD)),
                ],
                rows=dt_rows,
                border=ft.border.all(1, "#E5E7EB"),
                border_radius=border_radius.all(8),
                horizontal_lines=ft.border.BorderSide(1, "#F3F4F6"),
                column_spacing=20,
            )
        )
        page.update()

    def on_search(e):
        refresh(search_tf.value.strip())

    # ── ADD / EDIT dialog ──────────────────────
    def open_form(existing=None):
        cats = db.get_categories()
        sups = db.get_suppliers()

        name_tf  = TextField(label="Product Name *", value=existing["product_name"] if existing else "", border_color=SECONDARY)
        sku_tf   = TextField(label="SKU",            value=existing["sku"]          if existing else "", border_color=SECONDARY)
        qty_tf   = TextField(label="Quantity *",     value=str(existing["quantity"])if existing else "0", keyboard_type=ft.KeyboardType.NUMBER, border_color=SECONDARY)
        price_tf = TextField(label="Unit Price (₱)*",value=str(existing["unit_price"]) if existing else "0", keyboard_type=ft.KeyboardType.NUMBER, border_color=SECONDARY)
        reorder_tf = TextField(label="Reorder Level", value=str(existing["reorder_level"]) if existing else "10", keyboard_type=ft.KeyboardType.NUMBER, border_color=SECONDARY)
        desc_tf  = TextField(label="Description",    value=existing["description"]  if existing else "", multiline=True, min_lines=2, border_color=SECONDARY)

        cat_options = [dropdown.Option(str(c["category_id"]), c["category_name"]) for c in cats]
        sup_options = [dropdown.Option(str(s["supplier_id"]), s["supplier_name"]) for s in sups]

        cat_dd = Dropdown(label="Category", options=cat_options, border_color=SECONDARY)
        sup_dd = Dropdown(label="Supplier", options=sup_options, border_color=SECONDARY)

        # pre-select if editing
        if existing:
            for c in cats:
                if c["category_name"] == existing.get("category_name"):
                    cat_dd.value = str(c["category_id"])
            for s in sups:
                if s["supplier_name"] == existing.get("supplier_name"):
                    sup_dd.value = str(s["supplier_id"])

        def save(e):
            if not name_tf.value.strip():
                snack(page, "Product name is required.", error=True); return
            try:
                qty   = int(qty_tf.value or 0)
                price = float(price_tf.value or 0)
                reorder = int(reorder_tf.value or 10)
            except ValueError:
                snack(page, "Qty, Price and Reorder must be numbers.", error=True); return

            data = {
                "product_name":  name_tf.value.strip(),
                "sku":           sku_tf.value.strip(),
                "category_id":   int(cat_dd.value) if cat_dd.value else None,
                "supplier_id":   int(sup_dd.value) if sup_dd.value else None,
                "quantity":      qty,
                "unit_price":    price,
                "reorder_level": reorder,
                "description":   desc_tf.value.strip(),
            }
            try:
                if existing:
                    db.update_product(existing["product_id"], data)
                    snack(page, "Product updated successfully.")
                else:
                    db.insert_product(data)
                    snack(page, "Product added successfully.")
            except Exception as ex:
                snack(page, f"Error: {ex}", error=True); return

            close_dlg(page, dlg)
            refresh()

        dlg = AlertDialog(
            modal=True,
            title=Text("Edit Product" if existing else "Add New Product", weight=FontWeight.BOLD, color=PRIMARY),
            content=Container(
                width=480,
                content=Column(
                    scroll=ScrollMode.AUTO,
                    spacing=10,
                    controls=[name_tf, sku_tf, cat_dd, sup_dd, qty_tf, price_tf, reorder_tf, desc_tf],
                ),
            ),
            actions=[
                TextButton("Cancel", on_click=lambda e: close_dlg(page, dlg)),
                FilledButton("Save", on_click=save, style=ft.ButtonStyle(bgcolor=PRIMARY)),
            ],
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    def open_edit(row):   open_form(existing=row)

    def ask_delete(row):
        confirm_dialog(
            page,
            f"Delete '{row['product_name']}'? This cannot be undone.",
            lambda: do_delete(row["product_id"]),
        )

    def do_delete(pid):
        try:
            db.delete_product(pid)
            snack(page, "Product deleted.")
            refresh()
        except Exception as ex:
            snack(page, f"Error: {ex}", error=True)

    refresh()

    return Column(
        spacing=16,
        expand=True,
        controls=[
            section_title("📦  Products"),
            Divider(height=1, color="#E5E7EB"),
            Row(controls=[
                search_tf,
                ElevatedButton("Search",     on_click=on_search,        bgcolor=SECONDARY, color=colors.WHITE),
                ElevatedButton("+ Add Product", on_click=lambda e: open_form(), bgcolor=PRIMARY, color=colors.WHITE),
                ElevatedButton("Refresh",    on_click=lambda e: refresh(), bgcolor=ACCENT,   color=colors.WHITE),
            ], spacing=8),
            Card(
                elevation=2,
                content=Container(
                    padding=padding.all(16),
                    content=table_container,
                ),
            ),
        ],
    )


# ───────────────────────────────────────────
#  STOCK MANAGEMENT (IN / OUT / ADJUST)
# ───────────────────────────────────────────

def build_stock(page: Page):
    products  = db.get_all_products()
    prod_opts = [dropdown.Option(str(p["product_id"]), f"{p['product_name']} (Qty: {p['quantity']})") for p in products]

    prod_dd   = Dropdown(label="Select Product *", options=prod_opts, border_color=SECONDARY, expand=True)
    type_dd   = Dropdown(label="Transaction Type *", border_color=SECONDARY, width=200, options=[
        dropdown.Option("IN",         "Stock In  (Receiving)"),
        dropdown.Option("OUT",        "Stock Out (Issuing)"),
        dropdown.Option("ADJUSTMENT", "Manual Adjustment"),
    ])
    qty_tf    = TextField(label="Quantity *", keyboard_type=ft.KeyboardType.NUMBER, border_color=SECONDARY, width=150)
    notes_tf  = TextField(label="Notes / Remarks", multiline=True, min_lines=2, border_color=SECONDARY, expand=True)

    log_container = Column(scroll=ScrollMode.AUTO)

    def refresh_log(pid=None):
        log_container.controls.clear()
        txs = db.get_transactions(pid)
        if not txs:
            log_container.controls.append(Text("No transactions yet.", color=TEXT_MUTED))
            page.update()
            return
        rows = []
        for t in txs:
            color = SUCCESS if t["transaction_type"] == "IN" else (DANGER if t["transaction_type"] == "OUT" else ACCENT)
            rows.append(DataRow(cells=[
                DataCell(Text(str(t["transaction_id"]))),
                DataCell(Text(t["product_name"])),
                DataCell(Text(t["transaction_type"], color=color, weight=FontWeight.BOLD)),
                DataCell(Text(str(t["quantity_change"]))),
                DataCell(Text(t["notes"] or "")),
                DataCell(Text(str(t["transaction_date"])[:16])),
            ]))
        log_container.controls.append(
            DataTable(
                columns=[
                    DataColumn(Text("#",           weight=FontWeight.BOLD)),
                    DataColumn(Text("Product",     weight=FontWeight.BOLD)),
                    DataColumn(Text("Type",        weight=FontWeight.BOLD)),
                    DataColumn(Text("Qty Change",  weight=FontWeight.BOLD)),
                    DataColumn(Text("Notes",       weight=FontWeight.BOLD)),
                    DataColumn(Text("Date",        weight=FontWeight.BOLD)),
                ],
                rows=rows,
                border=ft.border.all(1, "#E5E7EB"),
                border_radius=border_radius.all(8),
                horizontal_lines=ft.border.BorderSide(1, "#F3F4F6"),
            )
        )
        page.update()

    def do_transaction(e):
        if not prod_dd.value:
            snack(page, "Please select a product.", error=True); return
        if not type_dd.value:
            snack(page, "Please select a transaction type.", error=True); return
        try:
            qty = int(qty_tf.value or 0)
            if qty <= 0:
                raise ValueError
        except ValueError:
            snack(page, "Enter a valid positive quantity.", error=True); return

        pid    = int(prod_dd.value)
        txtype = type_dd.value
        delta  = qty if txtype == "IN" else (-qty if txtype == "OUT" else qty)

        # guard against negative stock
        if txtype == "OUT":
            prods = db.get_all_products()
            current = next((p["quantity"] for p in prods if p["product_id"] == pid), 0)
            if qty > current:
                snack(page, f"Cannot remove {qty}. Only {current} in stock.", error=True); return

        try:
            db.adjust_stock(pid, delta, txtype, notes_tf.value.strip())
            snack(page, f"Transaction recorded! Stock {'increased' if delta > 0 else 'decreased'} by {abs(delta)}.")
        except Exception as ex:
            snack(page, f"Error: {ex}", error=True); return

        qty_tf.value   = ""
        notes_tf.value = ""
        # refresh dropdown labels
        updated = db.get_all_products()
        prod_dd.options = [
            dropdown.Option(str(p["product_id"]), f"{p['product_name']} (Qty: {p['quantity']})")
            for p in updated
        ]
        refresh_log()

    refresh_log()

    return Column(
        spacing=16,
        scroll=ScrollMode.AUTO,
        controls=[
            section_title("🔄  Stock Management"),
            Divider(height=1, color="#E5E7EB"),
            Card(
                elevation=2,
                content=Container(
                    padding=padding.all(20),
                    content=Column(spacing=12, controls=[
                        Text("Record a Stock Transaction", weight=FontWeight.BOLD, size=16, color=PRIMARY),
                        Row(controls=[prod_dd, type_dd, qty_tf], spacing=10, wrap=True),
                        notes_tf,
                        ElevatedButton("Submit Transaction", on_click=do_transaction,
                                       bgcolor=PRIMARY, color=colors.WHITE, icon=icons.SWAP_HORIZ),
                    ]),
                ),
            ),
            section_title("📋  Transaction History"),
            Card(
                elevation=2,
                content=Container(padding=padding.all(16), content=log_container),
            ),
        ],
    )


# ───────────────────────────────────────────
#  CATEGORIES
# ───────────────────────────────────────────

def build_categories(page: Page):
    name_tf = TextField(label="Category Name *", border_color=SECONDARY, expand=True)
    desc_tf = TextField(label="Description",     border_color=SECONDARY, expand=True)
    container = Column(scroll=ScrollMode.AUTO)

    def refresh():
        container.controls.clear()
        cats = db.get_categories()
        if not cats:
            container.controls.append(Text("No categories yet.", color=TEXT_MUTED))
            page.update(); return

        rows = []
        for c in cats:
            rows.append(DataRow(cells=[
                DataCell(Text(str(c["category_id"]))),
                DataCell(Text(c["category_name"])),
                DataCell(Text(c["description"] or "")),
                DataCell(IconButton(icons.DELETE, icon_color=DANGER, tooltip="Delete",
                                    on_click=lambda e, cid=c["category_id"]: ask_del(cid))),
            ]))
        container.controls.append(DataTable(
            columns=[
                DataColumn(Text("#",           weight=FontWeight.BOLD)),
                DataColumn(Text("Name",        weight=FontWeight.BOLD)),
                DataColumn(Text("Description", weight=FontWeight.BOLD)),
                DataColumn(Text("Action",      weight=FontWeight.BOLD)),
            ],
            rows=rows,
            border=ft.border.all(1, "#E5E7EB"),
            border_radius=border_radius.all(8),
            horizontal_lines=ft.border.BorderSide(1, "#F3F4F6"),
        ))
        page.update()

    def add(e):
        if not name_tf.value.strip():
            snack(page, "Category name required.", error=True); return
        try:
            db.insert_category(name_tf.value.strip(), desc_tf.value.strip())
            snack(page, "Category added.")
            name_tf.value = ""; desc_tf.value = ""
            refresh()
        except Exception as ex:
            snack(page, f"Error: {ex}", error=True)

    def ask_del(cid):
        confirm_dialog(page, "Delete this category?", lambda: do_del(cid))

    def do_del(cid):
        db.delete_category(cid); snack(page, "Deleted."); refresh()

    refresh()

    return Column(
        spacing=16,
        scroll=ScrollMode.AUTO,
        controls=[
            section_title("🏷️  Categories"),
            Divider(height=1, color="#E5E7EB"),
            Card(elevation=2, content=Container(padding=padding.all(20), content=Column(spacing=10, controls=[
                Text("Add Category", weight=FontWeight.BOLD, color=PRIMARY),
                Row(controls=[name_tf, desc_tf], spacing=10),
                ElevatedButton("+ Add", on_click=add, bgcolor=PRIMARY, color=colors.WHITE),
            ]))),
            section_title("All Categories"),
            Card(elevation=2, content=Container(padding=padding.all(16), content=container)),
        ],
    )


# ───────────────────────────────────────────
#  SUPPLIERS
# ───────────────────────────────────────────

def build_suppliers(page: Page):
    name_tf    = TextField(label="Supplier Name *",  border_color=SECONDARY, expand=True)
    contact_tf = TextField(label="Contact Person",   border_color=SECONDARY, expand=True)
    phone_tf   = TextField(label="Phone",            border_color=SECONDARY, width=180)
    email_tf   = TextField(label="Email",            border_color=SECONDARY, expand=True)
    address_tf = TextField(label="Address",          border_color=SECONDARY, expand=True)
    container  = Column(scroll=ScrollMode.AUTO)

    def refresh():
        container.controls.clear()
        sups = db.get_suppliers()
        if not sups:
            container.controls.append(Text("No suppliers yet.", color=TEXT_MUTED))
            page.update(); return

        rows = []
        for s in sups:
            rows.append(DataRow(cells=[
                DataCell(Text(str(s["supplier_id"]))),
                DataCell(Text(s["supplier_name"])),
                DataCell(Text(s["contact_name"] or "")),
                DataCell(Text(s["phone"] or "")),
                DataCell(Text(s["email"] or "")),
                DataCell(IconButton(icons.DELETE, icon_color=DANGER, tooltip="Delete",
                                    on_click=lambda e, sid=s["supplier_id"]: ask_del(sid))),
            ]))
        container.controls.append(DataTable(
            columns=[
                DataColumn(Text("#",       weight=FontWeight.BOLD)),
                DataColumn(Text("Name",    weight=FontWeight.BOLD)),
                DataColumn(Text("Contact", weight=FontWeight.BOLD)),
                DataColumn(Text("Phone",   weight=FontWeight.BOLD)),
                DataColumn(Text("Email",   weight=FontWeight.BOLD)),
                DataColumn(Text("Action",  weight=FontWeight.BOLD)),
            ],
            rows=rows,
            border=ft.border.all(1, "#E5E7EB"),
            border_radius=border_radius.all(8),
            horizontal_lines=ft.border.BorderSide(1, "#F3F4F6"),
        ))
        page.update()

    def add(e):
        if not name_tf.value.strip():
            snack(page, "Supplier name required.", error=True); return
        try:
            db.insert_supplier({
                "supplier_name": name_tf.value.strip(),
                "contact_name":  contact_tf.value.strip(),
                "phone":         phone_tf.value.strip(),
                "email":         email_tf.value.strip(),
                "address":       address_tf.value.strip(),
            })
            snack(page, "Supplier added.")
            for tf in [name_tf, contact_tf, phone_tf, email_tf, address_tf]:
                tf.value = ""
            refresh()
        except Exception as ex:
            snack(page, f"Error: {ex}", error=True)

    def ask_del(sid):
        confirm_dialog(page, "Delete this supplier?", lambda: do_del(sid))

    def do_del(sid):
        db.delete_supplier(sid); snack(page, "Deleted."); refresh()

    refresh()

    return Column(
        spacing=16,
        scroll=ScrollMode.AUTO,
        controls=[
            section_title("🚚  Suppliers"),
            Divider(height=1, color="#E5E7EB"),
            Card(elevation=2, content=Container(padding=padding.all(20), content=Column(spacing=10, controls=[
                Text("Add Supplier", weight=FontWeight.BOLD, color=PRIMARY),
                Row(controls=[name_tf, contact_tf], spacing=10),
                Row(controls=[phone_tf, email_tf, address_tf], spacing=10),
                ElevatedButton("+ Add", on_click=add, bgcolor=PRIMARY, color=colors.WHITE),
            ]))),
            section_title("All Suppliers"),
            Card(elevation=2, content=Container(padding=padding.all(16), content=container)),
        ],
    )


# ═══════════════════════════════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════════════════════════════

def main(page: Page):
    page.title           = "Inventory Tracking System"
    page.theme_mode      = ThemeMode.LIGHT
    page.bgcolor         = BG
    page.window_width    = 1200
    page.window_height   = 760
    page.window_min_width  = 900
    page.window_min_height = 600
    page.padding         = 0
    page.fonts           = {}

    # ── content area ──────────────────────────────
    content_area = Container(expand=True, padding=padding.all(24), bgcolor=BG)

    def load_page(index: int):
        builders = [
            build_dashboard,
            build_products,
            build_stock,
            build_categories,
            build_suppliers,
        ]
        content_area.content = builders[index](page)
        page.update()

    # ── nav rail ──────────────────────────────────
    nav = NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=90,
        bgcolor=NAV_BG,
        indicator_color=NAV_SELECTED,
        on_change=lambda e: load_page(e.control.selected_index),
        leading=Container(
            padding=padding.symmetric(vertical=16, horizontal=8),
            content=Column(
                horizontal_alignment=CrossAxisAlignment.CENTER,
                spacing=2,
                controls=[
                    Icon(icons.INVENTORY, color=colors.WHITE, size=32),
                    Text("InvTrack", color=colors.WHITE, size=11, weight=FontWeight.BOLD),
                ],
            ),
        ),
        destinations=[
            NavigationRailDestination(
                icon=icons.DASHBOARD_OUTLINED, selected_icon=icons.DASHBOARD,
                label_content=Text("Dashboard", color=colors.WHITE70, size=11),
            ),
            NavigationRailDestination(
                icon=icons.INVENTORY_2_OUTLINED, selected_icon=icons.INVENTORY_2,
                label_content=Text("Products", color=colors.WHITE70, size=11),
            ),
            NavigationRailDestination(
                icon=icons.SWAP_HORIZ_OUTLINED, selected_icon=icons.SWAP_HORIZ,
                label_content=Text("Stock", color=colors.WHITE70, size=11),
            ),
            NavigationRailDestination(
                icon=icons.LABEL_OUTLINED, selected_icon=icons.LABEL,
                label_content=Text("Categories", color=colors.WHITE70, size=11),
            ),
            NavigationRailDestination(
                icon=icons.LOCAL_SHIPPING_OUTLINED, selected_icon=icons.LOCAL_SHIPPING,
                label_content=Text("Suppliers", color=colors.WHITE70, size=11),
            ),
        ],
    )

    page.add(
        Row(
            expand=True,
            spacing=0,
            controls=[
                nav,
                ft.VerticalDivider(width=1, color="#E5E7EB"),
                content_area,
            ],
        )
    )

    load_page(0)


if __name__ == "__main__":
    ft.app(target=main)
