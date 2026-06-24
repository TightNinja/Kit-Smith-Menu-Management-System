import sqlite3
import pandas as pd
import os

def sync_all_data():
    db_path = "data/menu_system.db"
    excel_path = "data/mock_vendor_prices.xlsx"
    
    if not os.path.exists(excel_path):
        print("❌ Error: Missing your vendor Excel spreadsheet.")
        return

    # 1. Read Excel data via Pandas
    df = pd.read_excel(excel_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 2. Re-create an inventory reference table directly inside SQLite
    cursor.execute("DROP TABLE IF EXISTS inventory")
    cursor.execute('''
        CREATE TABLE inventory (
            Item_ID TEXT PRIMARY KEY,
            Description TEXT,
            Category TEXT,
            Vendor TEXT,
            Pack_Size TEXT,
            Case_Price REAL,
            Unit_of_Measure TEXT,
            Yield_Factor REAL
        )
    ''')
    
    # 3. Stream data frames into SQLite
    for _, row in df.iterrows():
        cursor.execute('''
            INSERT INTO inventory VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (row['Item_ID'], row['Description'], row['Category'], row['Vendor'], 
              row['Pack_Size'], row['Case_Price'], row['Unit_of_Measure'], row['Yield_Factor']))
        
    # 4. Insert or ignore the Salmon recipe row
    cursor.execute("INSERT OR IGNORE INTO recipes (recipe_name, target_cost_pct) VALUES ('Pan Seared Salmon Plate', 0.28)")
    
    # Fetch the recipe ID to associate relational ingredients
    cursor.execute("SELECT recipe_id FROM recipes WHERE recipe_name = 'Pan Seared Salmon Plate'")
    recipe_id = cursor.fetchone()[0]
    
    # Clear previous mock lists to prevent stack duplicates
    cursor.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", (recipe_id,))
    
    # 5. Insert ingredients directly linked to our schema
    salmon_ingredients = [
        (recipe_id, 'INV-003', 0.5),   # 0.5 LB Salmon Fillet
        (recipe_id, 'INV-004', 0.75),  # 0.75 LB Yukon Gold Potatoes
        (recipe_id, 'INV-007', 0.12),  # 0.12 LB Unsalted Butter
        (recipe_id, 'INV-008', 0.05)   # 0.05 GAL Olive Oil
    ]
    cursor.executemany("INSERT INTO recipe_ingredients (recipe_id, item_id, quantity) VALUES (?, ?, ?)", salmon_ingredients)
    
    conn.commit()
    conn.close()
    print("📊 Data migration successful! All inventory records and ingredients migrated to SQL database storage.")

if __name__ == "__main__":
    sync_all_data()
