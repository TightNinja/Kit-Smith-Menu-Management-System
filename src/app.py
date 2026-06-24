import pandas as pd
import os

def load_and_analyze_inventory():
    file_path = "data/mock_vendor_prices.xlsx"
    
    if not os.path.exists(file_path):
        print(f"❌ Error: Could not find the inventory file at {file_path}")
        return

    df = pd.read_excel(file_path)
    
    print("\n" + "="*65)
    print("      KIT-SMITH MENU ENGINEERING SYSTEM - COST & YIELD ANALYSIS      ")
    print("="*65)
    
    for index, row in df.iterrows():
        try:
            # Parse split matrices like '12/1 QT' or '4/5 LB'
            # Extracts the numeric portions and multiplies them for true case volume
            raw_pack = row['Pack_Size'].split()[0] # Get '12/1' or '4/5'
            
            if '/' in raw_pack:
                case_count, unit_size = raw_pack.split('/')
                total_units = float(case_count) * float(unit_size)
            else:
                total_units = float(raw_pack)
                
        except (ValueError, IndexError):
            total_units = 1.0 # Safe fallback

        # Dynamic unit cost calculations based on actual volume
        raw_cost_per_unit = row['Case_Price'] / total_units
        usable_cost_per_unit = raw_cost_per_unit / row['Yield_Factor']
        
        print(f"🔹 Item: {row['Description'][:30]:<30}")
        print(f"   Vendor: {row['Vendor']:<15} | Category: {row['Category']}")
        print(f"   Pack Volume:   {total_units:.1f} Total {row['Unit_of_Measure']}(s) per Case")
        print(f"   Raw Cost/Unit: ${raw_cost_per_unit:.2f} / {row['Unit_of_Measure']}")
        print(f"   Yield Factor:  {row['Yield_Factor'] * 100:.0f}% Usable Product")
        print(f"   🔴 TRUE USABLE COST: ${usable_cost_per_unit:.2f} / {row['Unit_of_Measure']}")
        print("-" * 65)

if __name__ == "__main__":
    load_and_analyze_inventory()
