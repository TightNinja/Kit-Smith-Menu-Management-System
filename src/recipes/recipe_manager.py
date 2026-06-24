import pandas as pd
import os

def calculate_recipe_cost(recipe_name, ingredients_list):
    """
    ingredients_list looks like: [('INV-001', 0.5), ('INV-005', 0.25)] -> (Item_ID, Amount_Needed_In_UOM)
    """
    inventory_path = "data/mock_vendor_prices.xlsx"
    if not os.path.exists(inventory_path):
        print("❌ Inventory database not found.")
        return

    # Ingest baseline cost arrays
    df = pd.read_excel(inventory_path)
    
    total_recipe_cost = 0.0
    print("\n" + "="*55)
    print(f" RECIPE CARD: {recipe_name.upper()}")
    print("="*55)
    print(f"{'Ingredient':<30} | {'Qty':<6} | {'Cost':<7}")
    print("-" * 55)

    for item_id, qty in ingredients_list:
        # Match item ID to extract pricing rows
        matched_row = df[df['Item_ID'] == item_id]
        
        if not matched_row.empty:
            row = matched_row.iloc[0]
            
            # Recalculate true unit yield rate dynamically
            raw_pack = row['Pack_Size'].split()
            if '/' in raw_pack[0]:
                case_count, unit_size = raw_pack[0].split('/')
                total_units = float(case_count) * float(unit_size)
            else:
                total_units = float(raw_pack[0])
                
            true_unit_cost = (row['Case_Price'] / total_units) / row['Yield_Factor']
            item_cost = true_unit_cost * qty
            total_recipe_cost += item_cost
            
            print(f"🔹 {row['Description'][:28]:<28} | {qty:<6} | ${item_cost:.2f}")
        else:
            print(f"⚠️ Warning: Item ID {item_id} missing from vendor registry.")

    print("-" * 55)
    print(f"🔴 TOTAL PLATE PRODUCTION COST:            ${total_recipe_cost:.2f}")
    print("="*55)

if __name__ == "__main__":
    # Test Scenario: Seared Salmon Plate with Garlic Mashed Potatoes
    # Format: (Item_ID, quantity_needed_in_ounces_or_lbs)
    salmon_plate = [
        ('INV-003', 0.5),   # 0.5 LB Salmon Fillet
        ('INV-004', 0.75),  # 0.75 LB Yukon Gold Potatoes
        ('INV-007', 0.12),  # 0.12 LB Unsalted Butter
        ('INV-008', 0.05)   # 0.05 GAL Olive Oil
    ]
    calculate_recipe_cost("Pan Seared Salmon Plate", salmon_plate)
