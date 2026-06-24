import pandas as pd
import os

def calculate_recipe_cost(recipe_name, ingredients_list, target_food_cost_pct=0.30):
    """
    Calculates total plate cost and engineering price recommendations.
    target_food_cost_pct: e.g., 0.30 for a 30% target food cost.
    """
    inventory_path = "data/mock_vendor_prices.xlsx"
    if not os.path.exists(inventory_path):
        print("❌ Inventory database not found.")
        return

    df = pd.read_excel(inventory_path)
    total_recipe_cost = 0.0
    
    print("\n" + "="*55)
    print(f" RECIPE CARD: {recipe_name.upper()}")
    print("="*55)
    print(f"{'Ingredient':<30} | {'Qty':<6} | {'Cost':<7}")
    print("-" * 55)

    for item_id, qty in ingredients_list:
        matched_row = df[df['Item_ID'] == item_id]
        if not matched_row.empty:
            row = matched_row.iloc[0]
            
            raw_pack = row['Pack_Size'].split()[0]
            if '/' in raw_pack:
                case_count, unit_size = raw_pack.split('/')
                total_units = float(case_count) * float(unit_size)
            else:
                total_units = float(raw_pack)
                
            true_unit_cost = (row['Case_Price'] / total_units) / row['Yield_Factor']
            item_cost = true_unit_cost * qty
            total_recipe_cost += item_cost
            
            print(f"🔹 {row['Description'][:28]:<28} | {qty:<6} | ${item_cost:.2f}")

    # Financial Menu Engineering Calculations
    suggested_retail = total_recipe_cost / target_food_cost_pct
    gross_profit_margin = suggested_retail - total_recipe_cost

    print("-" * 55)
    print(f"💵 TOTAL PLATE PRODUCTION COST:            ${total_recipe_cost:.2f}")
    print(f"🎯 TARGET FOOD COST PERCENTAGE:           {target_food_cost_pct * 100:.0f}%")
    print(f"🚀 SUGGESTED MENU RETAIL PRICE:           ${suggested_retail:.2f}")
    print(f"📈 PROJECTED GROSS PROFIT PER PLATE:       ${gross_profit_margin:.2f}")
    print("="*55)

if __name__ == "__main__":
    salmon_plate = [
        ('INV-003', 0.5),   # 0.5 LB Salmon Fillet
        ('INV-004', 0.75),  # 0.75 LB Yukon Gold Potatoes
        ('INV-007', 0.12),  # 0.12 LB Unsalted Butter
        ('INV-008', 0.05)   # 0.05 GAL Olive Oil
    ]
    # Evaluate salmon plate targeting a strict 28% food cost threshold
    calculate_recipe_cost("Pan Seared Salmon Plate", salmon_plate, target_food_cost_pct=0.28)
