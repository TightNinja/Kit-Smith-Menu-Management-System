from flask import Flask, render_template
import sqlite3
import os

app = Flask(__name__, template_folder='src/templates')

@app.route('/')
def home():
    db_path = "data/menu_system.db"
    if not os.path.exists(db_path):
        return "❌ Relational database file missing. Please run sync_data.py first."

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Fetch Salmon Plate metadata
    cursor.execute("SELECT recipe_id, target_cost_pct FROM recipes WHERE recipe_name = 'Pan Seared Salmon Plate'")
    recipe_id, target_cost_pct = cursor.fetchone()
    
    # 2. Extract mapped ingredients using a SQL JOIN
    query = """
        SELECT i.Description, ri.quantity, i.Pack_Size, i.Case_Price, i.Yield_Factor
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
        description, qty, pack_size, case_price, yield_factor = row
        try:
            raw_pack = pack_size.split()
            if '/' in raw_pack:
                case_count, unit_size = raw_pack.split('/')
                total_units = float(case_count) * float(unit_size)
            else:
                total_units = float(raw_pack)
        except (ValueError, IndexError):
            total_units = 1.0

        item_cost = ((case_price / total_units) / yield_factor) * qty
        total_cost += item_cost
        ingredients_list.append({'description': description, 'qty': qty, 'cost': item_cost})
        
    conn.close()
    
    # 4. Compile layout dictionary analytics
    metrics = {
        'total_cost': total_cost,
        'target_pct': target_cost_pct,
        'retail_price': total_cost / target_cost_pct,
        'profit': (total_cost / target_cost_pct) - total_cost
    }
    
    return render_template('index.html', recipe_name="Pan Seared Salmon Plate", ingredients=ingredients_list, metrics=metrics)

if __name__ == '__main__':
    app.run(debug=True)
