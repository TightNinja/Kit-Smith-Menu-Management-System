"""Item Maintenance (requirements 1-13).

`inventory` remains the enterprise item master (single source of truth for item
attributes). Satellite tables hold multi-valued / historical data. They are keyed
by Item_ID without hard FKs because sync_data.py rebuilds `inventory`.
"""
import sqlite3
from datetime import date

DB_PATH = "data/menu_system.db"

SCHEMA = [
    '''CREATE TABLE IF NOT EXISTS item_hierarchy (
        node_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        level TEXT NOT NULL CHECK (level IN ('department','category','subcategory')),
        parent_id INTEGER REFERENCES item_hierarchy (node_id),
        UNIQUE (name, level, parent_id))''',
    '''CREATE TABLE IF NOT EXISTS item_classification (
        item_id TEXT PRIMARY KEY,
        node_id INTEGER REFERENCES item_hierarchy (node_id))''',
    '''CREATE TABLE IF NOT EXISTS item_upcs (
        upc TEXT PRIMARY KEY,
        item_id TEXT NOT NULL,
        is_primary INTEGER DEFAULT 0)''',
    '''CREATE TABLE IF NOT EXISTS item_plu (
        plu TEXT PRIMARY KEY,
        item_id TEXT NOT NULL,
        is_organic INTEGER DEFAULT 0)''',
    '''CREATE TABLE IF NOT EXISTS item_vendor_xref (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id TEXT NOT NULL,
        vendor TEXT NOT NULL,
        vendor_item_code TEXT NOT NULL,
        is_preferred INTEGER DEFAULT 0,
        UNIQUE (vendor, vendor_item_code))''',
    '''CREATE TABLE IF NOT EXISTS item_pack_sizes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id TEXT NOT NULL,
        pack_size TEXT NOT NULL,
        units_per_pack REAL NOT NULL DEFAULT 1,
        UNIQUE (item_id, pack_size))''',
    '''CREATE TABLE IF NOT EXISTS item_uoms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id TEXT NOT NULL,
        uom TEXT NOT NULL,
        conversion_to_base REAL NOT NULL DEFAULT 1,
        UNIQUE (item_id, uom))''',
    '''CREATE TABLE IF NOT EXISTS item_prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id TEXT NOT NULL,
        sell_price REAL NOT NULL,
        effective_date TEXT NOT NULL,
        UNIQUE (item_id, effective_date))''',
    '''CREATE TABLE IF NOT EXISTS item_cost_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id TEXT NOT NULL,
        case_price REAL NOT NULL,
        effective_date TEXT NOT NULL,
        changed_at TEXT DEFAULT CURRENT_TIMESTAMP)''',
]


def connect(db_path=None):
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_item_tables(conn):
    for ddl in SCHEMA:
        conn.execute(ddl)
    conn.commit()


def _valid_date(value):
    return date.fromisoformat(value).isoformat()


# ---- Item master create / update / delete (req 1, 2, 12) ----
def save_item(conn, item_id, description, category, vendor, pack_size,
              case_price, uom, yield_factor):
    """Insert or update an item; logs cost history when the case price changes."""
    old = conn.execute("SELECT Case_Price FROM inventory WHERE Item_ID = ?", (item_id,)).fetchone()
    conn.execute('''INSERT INTO inventory (Item_ID, Description, Category, Vendor, Pack_Size,
                    Case_Price, Unit_of_Measure, Yield_Factor) VALUES (?,?,?,?,?,?,?,?)
                    ON CONFLICT(Item_ID) DO UPDATE SET Description=excluded.Description,
                    Category=excluded.Category, Vendor=excluded.Vendor, Pack_Size=excluded.Pack_Size,
                    Case_Price=excluded.Case_Price, Unit_of_Measure=excluded.Unit_of_Measure,
                    Yield_Factor=excluded.Yield_Factor''',
                 (item_id, description, category, vendor, pack_size, case_price, uom, yield_factor))
    if old is None or old["Case_Price"] != case_price:
        conn.execute("INSERT INTO item_cost_history (item_id, case_price, effective_date) VALUES (?,?,?)",
                     (item_id, case_price, date.today().isoformat()))
    conn.commit()


def get_recipe_links(conn, item_id):
    return conn.execute('''SELECT r.recipe_id, r.recipe_name, ri.quantity FROM recipe_ingredients ri
                           JOIN recipes r ON r.recipe_id = ri.recipe_id WHERE ri.item_id = ?''',
                        (item_id,)).fetchall()


def delete_item(conn, item_id):
    """Delete an item and its satellite data. Refuses if any recipe uses it."""
    links = get_recipe_links(conn, item_id)
    if links:
        raise ValueError("Item is used in recipe(s): " + ", ".join(l["recipe_name"] for l in links))
    for table in ("item_classification", "item_upcs", "item_plu", "item_vendor_xref",
                  "item_pack_sizes", "item_uoms", "item_prices", "item_cost_history"):
        conn.execute(f"DELETE FROM {table} WHERE item_id = ?", (item_id,))
    conn.execute("DELETE FROM inventory WHERE Item_ID = ?", (item_id,))
    conn.commit()


# ---- Multi-valued attributes (req 3, 4, 5, 7, 8) ----
def add_upc(conn, item_id, upc, is_primary=False):
    upc = upc.strip()
    if not upc.isdigit() or len(upc) not in (8, 12, 13, 14):
        raise ValueError("UPC must be 8, 12, 13 or 14 digits")
    if is_primary:
        conn.execute("UPDATE item_upcs SET is_primary = 0 WHERE item_id = ?", (item_id,))
    conn.execute("INSERT INTO item_upcs (upc, item_id, is_primary) VALUES (?,?,?)",
                 (upc, item_id, int(is_primary)))
    conn.commit()


def add_plu(conn, item_id, plu, is_organic=False):
    plu = plu.strip()
    if not plu.isdigit() or len(plu) not in (4, 5):
        raise ValueError("PLU must be 4 or 5 digits")
    conn.execute("INSERT INTO item_plu (plu, item_id, is_organic) VALUES (?,?,?)",
                 (plu, item_id, int(is_organic)))
    conn.commit()


def add_vendor_xref(conn, item_id, vendor, vendor_item_code, is_preferred=False):
    if is_preferred:
        conn.execute("UPDATE item_vendor_xref SET is_preferred = 0 WHERE item_id = ?", (item_id,))
    conn.execute("INSERT INTO item_vendor_xref (item_id, vendor, vendor_item_code, is_preferred) VALUES (?,?,?,?)",
                 (item_id, vendor.strip(), vendor_item_code.strip(), int(is_preferred)))
    conn.commit()


def add_pack_size(conn, item_id, pack_size, units_per_pack):
    if units_per_pack <= 0:
        raise ValueError("units_per_pack must be positive")
    conn.execute("INSERT INTO item_pack_sizes (item_id, pack_size, units_per_pack) VALUES (?,?,?)",
                 (item_id, pack_size.strip(), units_per_pack))
    conn.commit()


def add_uom(conn, item_id, uom, conversion_to_base):
    if conversion_to_base <= 0:
        raise ValueError("conversion_to_base must be positive")
    conn.execute("INSERT INTO item_uoms (item_id, uom, conversion_to_base) VALUES (?,?,?)",
                 (item_id, uom.strip(), conversion_to_base))
    conn.commit()


_CHILD_TABLES = {"upc": ("item_upcs", "upc"), "plu": ("item_plu", "plu"),
                 "xref": ("item_vendor_xref", "id"), "pack": ("item_pack_sizes", "id"),
                 "uom": ("item_uoms", "id"), "price": ("item_prices", "id")}


def remove_child(conn, kind, key):
    table, col = _CHILD_TABLES[kind]
    conn.execute(f"DELETE FROM {table} WHERE {col} = ?", (key,))
    conn.commit()


# ---- Hierarchy (req 6) ----
def add_hierarchy_node(conn, name, level, parent_id=None):
    expected_parent = {"department": None, "category": "department", "subcategory": "category"}[level]
    if expected_parent:
        parent = conn.execute("SELECT level FROM item_hierarchy WHERE node_id = ?", (parent_id,)).fetchone()
        if not parent or parent["level"] != expected_parent:
            raise ValueError(f"A {level} must belong to a {expected_parent}")
    elif parent_id is not None:
        raise ValueError("A department cannot have a parent")
    conn.execute("INSERT INTO item_hierarchy (name, level, parent_id) VALUES (?,?,?)", (name.strip(), level, parent_id))
    conn.commit()


def classify_item(conn, item_id, node_id):
    conn.execute("INSERT INTO item_classification (item_id, node_id) VALUES (?,?) "
                 "ON CONFLICT(item_id) DO UPDATE SET node_id = excluded.node_id", (item_id, node_id))
    conn.commit()


# ---- Pricing, cost history, margin (req 9, 10, 11) ----
def set_price(conn, item_id, sell_price, effective_date):
    if sell_price < 0:
        raise ValueError("Price cannot be negative")
    conn.execute("INSERT INTO item_prices (item_id, sell_price, effective_date) VALUES (?,?,?) "
                 "ON CONFLICT(item_id, effective_date) DO UPDATE SET sell_price = excluded.sell_price",
                 (item_id, sell_price, _valid_date(effective_date)))
    conn.commit()


def current_price(conn, item_id, as_of=None):
    row = conn.execute("SELECT sell_price FROM item_prices WHERE item_id = ? AND effective_date <= ? "
                       "ORDER BY effective_date DESC LIMIT 1",
                       (item_id, as_of or date.today().isoformat())).fetchone()
    return row["sell_price"] if row else None


def unit_cost(conn, item_id):
    """Cost per base unit, adjusted for yield (same math as the recipe costing)."""
    row = conn.execute("SELECT Pack_Size, Case_Price, Yield_Factor FROM inventory WHERE Item_ID = ?",
                       (item_id,)).fetchone()
    if row is None:
        return None
    try:
        pack = str(row["Pack_Size"]).strip()
        if "/" in pack:
            count, size = pack.split("/")
            units = float(count) * float(size.split()[0])
        else:
            units = float(pack.split()[0])
    except (ValueError, IndexError):
        units = 1.0
    return (row["Case_Price"] / units) / (row["Yield_Factor"] or 1.0)


def margin(cost, price):
    """Return (margin_amount, margin_pct) or (None, None) when price is unavailable."""
    if cost is None or not price:
        return None, None
    return price - cost, (price - cost) / price


def cost_history(conn, item_id):
    return conn.execute("SELECT case_price, effective_date, changed_at FROM item_cost_history "
                        "WHERE item_id = ? ORDER BY id DESC", (item_id,)).fetchall()


# ---- Aggregate view ----
def item_detail(conn, item_id):
    item = conn.execute("SELECT * FROM inventory WHERE Item_ID = ?", (item_id,)).fetchone()
    if item is None:
        return None
    q = lambda sql: conn.execute(sql, (item_id,)).fetchall()
    cost, price = unit_cost(conn, item_id), current_price(conn, item_id)
    amt, pct = margin(cost, price)
    return {
        "item": dict(item),
        "upcs": q("SELECT * FROM item_upcs WHERE item_id = ?"),
        "plus": q("SELECT * FROM item_plu WHERE item_id = ?"),
        "xrefs": q("SELECT * FROM item_vendor_xref WHERE item_id = ?"),
        "packs": q("SELECT * FROM item_pack_sizes WHERE item_id = ?"),
        "uoms": q("SELECT * FROM item_uoms WHERE item_id = ?"),
        "prices": q("SELECT * FROM item_prices WHERE item_id = ? ORDER BY effective_date DESC"),
        "history": cost_history(conn, item_id),
        "recipes": get_recipe_links(conn, item_id),
        "classification": conn.execute(
            "SELECT h.node_id, h.name, h.level FROM item_classification c "
            "JOIN item_hierarchy h ON h.node_id = c.node_id WHERE c.item_id = ?", (item_id,)).fetchone(),
        "unit_cost": cost, "sell_price": price, "margin_amt": amt, "margin_pct": pct,
    }
