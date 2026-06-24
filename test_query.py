import sqlite3
import pandas as pd

# Open connection to your local, secured database file tracking matrix
conn = sqlite3.connect("data/menu_system.db")

# Use Pandas to execute a direct query and print a beautiful terminal table grid
df = pd.read_sql_query("SELECT * FROM inventory", conn)

print("\n📊 LIVE DATABASE ROWS DETECTED INSIDE INVENTORY TABLE:")
print(df.to_string(index=False))

conn.close()
