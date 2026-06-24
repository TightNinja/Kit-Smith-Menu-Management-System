import sqlite3
import os

def init_database():
    db_path = "data/menu_system.db"
    # Ensure the data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Establish local relational database link
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Create Recipes Master Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_name TEXT NOT NULL UNIQUE,
            target_cost_pct REAL DEFAULT 0.30
        )
    ''')
    
    # 2. Create Recipe Ingredients Relational Link Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipe_ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            item_id TEXT,
            quantity REAL,
            FOREIGN KEY (recipe_id) REFERENCES recipes (recipe_id),
            FOREIGN KEY (item_id) REFERENCES inventory (Item_ID)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"🎉 Success! Local SQLite database initialized at '{db_path}' with schema structures.")

if __name__ == "__main__":
    init_database()
