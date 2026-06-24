import sqlite3
import os

def load_recipe_from_db(search_recipe_name):
    db_path = "data/menu_system.db"
    if not os.path.exists(db_path):
        print("❌ Error: Relational system database not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Fetch Master Recipe Core Details
    cursor.execute("SELECT recipe_id, target_cost_pct FROM recipes WHERE recipe_name = ?", (search_recipe_name,))
    recipe_meta = cursor.fetchone()
    
    if not recipe_meta:
        print(f"❌ Error: Recipe '{search_recipe_name}' not found in relational database.")
        conn.close()
        return
        
    recipe_id, target_food_cost_pct = recipe_meta

    # 2. Run a 3-Table SQL JOIN to map out the production cost variables automatically
    query = """
        SELECT i.Description, ri.quantity, i.Pack_Size, i.Case_Price, i.Unit_of_Measure, i.Yield_Factor, i.Vendor
        FROM recipe_ingredients ri
        JOIN inventory i ON ri.item_id = i.Item_ID
        WHERE ri.recipe_id = ?
    """
    cursor.execute(query, (recipe_id,))
    ingredients_rows = cursor.fetchall()
    
    total_recipe_cost = 0.0
    print("\n" + "="*58)
    print(f"  SQL Relational Engine Card: {search_recipe_name.upper()}")
    print("="*58)
    print(f"{'Ingredient':<30} | {'Qty':<6} | {'Cost':<7}")
    print("-" * 58)

    # 3. Dynamic Calculation Loop
    for row in ingredients_rows:
        description, qty, pack_size, case_price, uom, yield_factor, vendor = row
        
        try:
            raw_pack = pack_size.split()
            if '/' in raw_pack[0]:
                case_count, unit_size = raw_pack[0].split('/')
                total_units = float(case_count) * float(unit_size)
            else:
                total_units = float(raw_pack[0])
        except (ValueError, IndexError):
            total_units = 1.0

        true_unit_cost = (case_price / total_units) / yield_factor
        item_cost = true_unit_cost * qty
        total_recipe_cost += item_cost
        
        print(f"🔹 {description[:28]:<28} | {qty:<6} | ${item_cost:.2f}")

    # Financial Matrix Formulas
    suggested_retail = total_recipe_cost / target_food_cost_pct
    gross_profit_margin = suggested_retail - total_recipe_cost

    print("-" * 58)
    print(f"💵 TOTAL SQL PRODUCTION COST:              ${total_recipe_cost:.2f}")
    print(f"🎯 TARGET FOOD COST PERCENTAGE:           {target_food_cost_pct * 100:.0f}%")
    print(f"🚀 SUGGESTED MENU RETAIL PRICE:           ${suggested_retail:.2f}")
    print(f"📈 PROJECTED GROSS PROFIT PER PLATE:       ${gross_profit_margin:.2f}")
    print("="*58)

    conn.close()

if __name__ == "__main__":
    # Query your relational database by name string
    load_recipe_from_db("Pan Seared Salmon Plate")
