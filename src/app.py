import pandas as pd
import os

def load_and_analyze_inventory():
    file_path = "data/mock_vendor_prices.xlsx"
    
    # Check if data file exists
    if not os.path.exists(file_path):
        print(f"❌ Error: Could not find the inventory file at {file_path}")
        return

    # Ingest data using Pandas
    df = pd.read_excel(file_path)
    
    print("\n" + "="*65)
    print("      KIT-SMITH MENU ENGINEERING SYSTEM - COST & YIELD ANALYSIS      ")
    print("="*65)
    
    # Process and calculate actual usable inventory unit metrics
    # True Cost per LB = (Case Price / Total Pack Weight) / Yield Factor
    for index, row in df.iterrows():
        # Clean up pack size parsing (e.g., "1/15 LB" -> 15)
        try:
            pack_weight = float(row['Pack_Size'].split('/')[-1].split()[0])
        except (ValueError, IndexError):
            pack_weight = 10.0 # Fallback default
            
        raw_cost_per_lb = row['Case_Price'] / pack_weight
        usable_cost_per_lb = raw_cost_per_lb / row['Yield_Factor']
        
        print(f"🔹 Item: {row['Description'][:30]:<30}")
        print(f"   Vendor: {row['Vendor']:<15} | Category: {row['Category']}")
        print(f"   Raw Cost/Unit: ${raw_cost_per_lb:.2f} / {row['Unit_of_Measure']}")
        print(f"   Yield Factor:  {row['Yield_Factor'] * 100:.0f}% Usable Product")
        print(f"   🔴 TRUE USABLE COST: ${usable_cost_per_lb:.2f} / {row['Unit_of_Measure']}")
        print("-" * 65)

if __name__ == "__main__":
    load_and_analyze_inventory()
