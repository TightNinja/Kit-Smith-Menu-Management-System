import os
import sqlite3
from flask import Blueprint, render_template, request, redirect, flash, abort
from . import item_maintenance as im

items_bp = Blueprint('items', __name__, url_prefix='/items')


def _db():
    conn = im.connect()
    im.init_item_tables(conn)
    return conn


def _back(item_id):
    return redirect(f'/items/{item_id}')


def _guard(item_id, fn, *args):
    """Run an item-maintenance action, flashing validation / constraint errors."""
    conn = _db()
    try:
        fn(conn, *args)
    except (ValueError, KeyError, sqlite3.IntegrityError) as exc:
        conn.rollback()
        flash(str(exc))
    finally:
        conn.close()
    return _back(item_id)


@items_bp.route('/')
def list_items():
    conn = _db()
    items = conn.execute("SELECT * FROM inventory ORDER BY Item_ID").fetchall()
    nodes = conn.execute("SELECT * FROM item_hierarchy ORDER BY level, name").fetchall()
    conn.close()
    return render_template('items.html', items=items, nodes=nodes, detail=None)


@items_bp.route('/<string:item_id>')
def detail(item_id):
    conn = _db()
    d = im.item_detail(conn, item_id)
    nodes = conn.execute("SELECT * FROM item_hierarchy ORDER BY level, name").fetchall()
    conn.close()
    if d is None:
        abort(404)
    return render_template('items.html', items=None, nodes=nodes, detail=d)


@items_bp.route('/save', methods=['POST'])
def save():
    f = request.form
    item_id = f['item_id'].strip()
    try:
        conn = _db()
        im.save_item(conn, item_id, f['description'], f['category'], f['vendor'], f['pack_size'],
                     float(f['case_price']), f['uom'], float(f['yield_factor']))
        conn.close()
    except ValueError as exc:
        flash(str(exc))
    return _back(item_id)


@items_bp.route('/<string:item_id>/delete', methods=['POST'])
def delete(item_id):
    conn = _db()
    try:
        im.delete_item(conn, item_id)
    except ValueError as exc:
        flash(str(exc))
        return _back(item_id)
    finally:
        conn.close()
    return redirect('/items/')


@items_bp.route('/<string:item_id>/upc', methods=['POST'])
def upc(item_id):
    return _guard(item_id, im.add_upc, item_id, request.form['upc'], 'primary' in request.form)


@items_bp.route('/<string:item_id>/plu', methods=['POST'])
def plu(item_id):
    return _guard(item_id, im.add_plu, item_id, request.form['plu'], 'organic' in request.form)


@items_bp.route('/<string:item_id>/xref', methods=['POST'])
def xref(item_id):
    return _guard(item_id, im.add_vendor_xref, item_id, request.form['vendor'],
                  request.form['vendor_item_code'], 'preferred' in request.form)


@items_bp.route('/<string:item_id>/pack', methods=['POST'])
def pack(item_id):
    try:
        units = float(request.form['units_per_pack'])
    except ValueError:
        flash("Units per pack must be a number")
        return _back(item_id)
    return _guard(item_id, im.add_pack_size, item_id, request.form['pack_size'], units)


@items_bp.route('/<string:item_id>/uom', methods=['POST'])
def uom(item_id):
    try:
        conv = float(request.form['conversion'])
    except ValueError:
        flash("Conversion must be a number")
        return _back(item_id)
    return _guard(item_id, im.add_uom, item_id, request.form['uom'], conv)


@items_bp.route('/<string:item_id>/price', methods=['POST'])
def price(item_id):
    try:
        p = float(request.form['sell_price'])
    except ValueError:
        flash("Price must be a number")
        return _back(item_id)
    return _guard(item_id, im.set_price, item_id, p, request.form['effective_date'])


@items_bp.route('/<string:item_id>/classify', methods=['POST'])
def classify(item_id):
    return _guard(item_id, im.classify_item, item_id, int(request.form['node_id']))


@items_bp.route('/<string:item_id>/remove/<string:kind>/<string:key>', methods=['POST'])
def remove(item_id, kind, key):
    if kind not in im._CHILD_TABLES:
        abort(404)
    return _guard(item_id, im.remove_child, kind, key)


@items_bp.route('/hierarchy', methods=['POST'])
def hierarchy():
    f = request.form
    parent = int(f['parent_id']) if f.get('parent_id') else None
    conn = _db()
    try:
        im.add_hierarchy_node(conn, f['name'], f['level'], parent)
    except (ValueError, KeyError, sqlite3.IntegrityError) as exc:
        flash(str(exc))
    finally:
        conn.close()
    return redirect('/items/')
