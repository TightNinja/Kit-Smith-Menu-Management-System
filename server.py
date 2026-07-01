from flask import Flask, render_template, request, redirect
import sqlite3
import os

app = Flask(__name__, template_folder='templates')
DB_PATH = "data/menu_system.db"

@app.route('/')
def home():
    if not os.path.exists(DB_PATH):
        return "❌ Relational database file missing. Please run sync_data.py first."

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Fetch Salmon Plate metadata
    cursor.execute("SELECT recipe_id, target_cost_pct FROM recipes WHERE recipe_name = 'Pan Seared Salmon Plate'")
    recipe_meta = cursor.fetchone()
    if not recipe_meta:
        return "❌ Recipe 'Pan Seared Salmon Plate' not found in database. Run sync_data.py."
    recipe_id, target_cost_pct = recipe_meta
    
    # 2. Extract mapped ingredients including Item_ID using a SQL JOIN
    query = """
        SELECT i.Item_ID, i.Description, ri.quantity, i.Pack_Size, i.Case_Price, i.Yield_Factor
        FROM recipe_ingredients ri
        JOIN inventory i ON ri.item_id = i.Item_ID
        WHERE ri.recipe_id = ?
    """
    cursor.execute(query, (recipe_id,))
    rows = cursor.fetchall()
    
    ingredients_list = []
    total_cost = 0.0
    
    # 3. Apply the yield string volume logic matrices
    for row in rows:
        item_id, description, qty, pack_size, case_price, yield_factor = row
        try:
            pack_str = str(pack_size).strip()
            
            if '/' in pack_str:
                case_count, unit_size = pack_str.split('/')
                # Fix: Add [0] to grab the first word string out of the split list
                unit_size_clean = unit_size.split()[0]
                total_units = float(case_count) * float(unit_size_clean)
            else:
                total_units = float(pack_str.split()[0])
        except (ValueError, IndexError):
            total_units = 1.0

        item_cost = ((case_price / total_units) / yield_factor) * qty
        total_cost += item_cost
        ingredients_list.append({'id': item_id, 'description': description, 'qty': qty, 'cost': item_cost})
        
    conn.close()
    
    # 4. Compile layout dictionary analytics
    metrics = {
        'total_cost': total_cost,
        'target_pct': target_cost_pct,
        'retail_price': total_cost / target_cost_pct if target_cost_pct else total_cost,
        'profit': ((total_cost / target_cost_pct) - total_cost) if target_cost_pct else 0.0
    }
    
    return render_template('index.html', recipe_name="Pan Seared Salmon Plate", ingredients=ingredients_list, metrics=metrics)

@app.route('/add-ingredient', methods=['POST'])
def add_ingredient():
    item_id = request.form['item_id']
    description = request.form['description']
    category = request.form['category']
    vendor = request.form['vendor']
    pack_size = request.form['pack_size']
    case_price = float(request.form['case_price'])
    uom = request.form['uom']
    yield_factor = float(request.form['yield_factor'])

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO inventory (Item_ID, Description, Category, Vendor, Pack_Size, Case_Price, Unit_of_Measure, Yield_Factor)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (item_id, description, category, vendor, pack_size, case_price, uom, yield_factor))
    
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/delete-ingredient/<string:item_id>', methods=['POST'])
def delete_ingredient(item_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Clean relational mapping hooks out of link tables first, then remove inventory entry rows
    cursor.execute("DELETE FROM recipe_ingredients WHERE item_id = ?", (item_id,))
    cursor.execute("DELETE FROM inventory WHERE Item_ID = ?", (item_id,))
    
    conn.commit()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
