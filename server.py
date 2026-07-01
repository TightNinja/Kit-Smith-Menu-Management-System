from flask import Flask, render_template, request, redirect
import sqlite3
import os

app = Flask(__name__, template_folder='templates')
DB_PATH = "data/menu_system.db"

# Global fallback string block to preserve view memory
ACTIVE_RECIPE = ["Pan Seared Salmon Plate"]

@app.route('/')
def home():
    if not os.path.exists(DB_PATH):
        return "❌ Relational database file missing. Please run sync_data.py first."

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # A. Fixed: Maps r[0] to id and r[1] to name strings
    cursor.execute("SELECT recipe_id, recipe_name FROM recipes")
    all_rec_rows = cursor.fetchall()
    all_recipes = [{'id': r[0], 'name': r[1]} for r in all_rec_rows]

    # B. Fixed: Maps i[0] to id and i[1] to desc strings
    cursor.execute("SELECT Item_ID, Description FROM inventory")
    all_inv_rows = cursor.fetchall()
    all_inventory = [{'id': i[0], 'desc': i[1]} for i in all_inv_rows]


    # C. Track targeted viewing state layout properties
    target_name = ACTIVE_RECIPE[0]
    cursor.execute("SELECT recipe_id, target_cost_pct FROM recipes WHERE recipe_name = ?", (target_name,))
    recipe_meta = cursor.fetchone()
    
    if not recipe_meta:
        target_name = all_recipes[0]['name'] if all_recipes else "Pan Seared Salmon Plate"
        ACTIVE_RECIPE[0] = target_name
        cursor.execute("SELECT recipe_id, target_cost_pct FROM recipes WHERE recipe_name = ?", (target_name,))
        recipe_meta = cursor.fetchone()
        
    recipe_id, target_cost_pct = recipe_meta
    
    # D. Extract mapped ingredients using a SQL JOIN
    query = """
        SELECT i.Item_ID, i.Description, ri.quantity, i.Pack_Size, i.Case_Price, i.Yield_Factor, i.Unit_of_Measure
        FROM recipe_ingredients ri
        JOIN inventory i ON ri.item_id = i.Item_ID
        WHERE ri.recipe_id = ?
    """
    cursor.execute(query, (recipe_id,))
    rows = cursor.fetchall()
    
    ingredients_list = []
    total_cost = 0.0
    
    for row in rows:
        item_id, description, qty, pack_size, case_price, yield_factor, uom = row
        try:
            pack_str = str(pack_size).strip()
            if '/' in pack_str:
                case_count, unit_size = pack_str.split('/')
                unit_size_clean = unit_size.split()[0]
                total_units = float(case_count) * float(unit_size_clean)
            else:
                total_units = float(pack_str.split()[0])
        except (ValueError, IndexError):
            total_units = 1.0

        item_cost = ((case_price / total_units) / yield_factor) * qty
        total_cost += item_cost
        ingredients_list.append({'id': item_id, 'description': description, 'qty': qty, 'cost': item_cost, 'uom': uom})
        
    conn.close()
    
    metrics = {
        'total_cost': total_cost,
        'target_pct': target_cost_pct,
        'retail_price': total_cost / target_cost_pct if target_cost_pct else total_cost,
        'profit': ((total_cost / target_cost_pct) - total_cost) if target_cost_pct else 0.0
    }
    
    return render_template('index.html', recipe_name=target_name, ingredients=ingredients_list, 
                           metrics=metrics, all_recipes=all_recipes, all_inventory=all_inventory)

@app.route('/select-recipe', methods=['POST'])
def select_recipe():
    recipe_id = request.form['selected_recipe_id']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT recipe_name FROM recipes WHERE recipe_id = ?", (recipe_id,))
    res = cursor.fetchone()
    if res:
        ACTIVE_RECIPE[0] = res[0]
    conn.close()
    return redirect('/')

@app.route('/create-blank-recipe', methods=['POST'])
def create_blank_recipe():
    new_name = request.form['new_recipe_name'].strip()
    if new_name:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO recipes (recipe_name, target_cost_pct) VALUES (?, 0.30)", (new_name,))
        conn.commit()
        conn.close()
        ACTIVE_RECIPE[0] = new_name
    return redirect('/')

@app.route('/add-recipe-ingredient', methods=['POST'])
def add_recipe_ingredient():
    recipe_id = int(request.form['recipe_id'])
    item_id = request.form['item_id']
    quantity = float(request.form['quantity'])

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO recipe_ingredients (recipe_id, item_id, quantity) VALUES (?, ?, ?)', (recipe_id, item_id, quantity))
    conn.commit()
    
    cursor.execute("SELECT recipe_name FROM recipes WHERE recipe_id = ?", (recipe_id,))
    res = cursor.fetchone()
    if res:
        ACTIVE_RECIPE[0] = res[0]
    conn.close()
    return redirect('/')

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
    cursor.execute("SELECT recipe_id FROM recipes WHERE recipe_name = ?", (ACTIVE_RECIPE[0],))
    recipe_id = cursor.fetchone()[0]
    cursor.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ? AND item_id = ?", (recipe_id, item_id))
    conn.commit()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
