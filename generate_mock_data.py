import pandas as pd
import os

# Create the data directory if it got skipped earlier
os.makedirs("data", exist_ok=True)

# Define high-volume procurement mock variables
mock_items = {
    "Item_ID": ["INV-001", "INV-002", "INV-003", "INV-004", "INV-005", "INV-006", "INV-007", "INV-008", "INV-009", "INV-010"],
    "Description": [
        "Beef Ribeye Lip-On Fresh", "Chicken Breast Boneless Skinless",
        "Atlantic Salmon Fillet Fresh", "Yukon Gold Potatoes #1",
        "Yellow Onions Medium", "Heavy Whipping Cream 36%",
        "Unsalted Butter Kosher", "Extra Virgin Olive Oil",
        "White Granulated Sugar", "All Purpose Flour Bleached"
    ],
    "Category": ["Proteins", "Proteins", "Proteins", "Produce", "Produce", "Dairy", "Dairy", "Grocery", "Grocery", "Grocery"],
    "Vendor": ["US Foods", "Sysco", "Sysco", "Local Produce Inc", "Local Produce Inc", "Dairy Gold", "Dairy Gold", "US Foods", "Sysco", "Sysco"],
    "Pack_Size": ["1/15 LB", "4/5 LB", "1/10 LB", "1/50 LB", "1/50 LB", "12/1 QT", "36/1 LB", "4/1 GAL", "1/50 LB", "1/50 LB"],
    "Case_Price": [185.50, 48.25, 92.00, 24.50, 18.00, 54.00, 112.50, 84.00, 32.50, 22.00],
    "Unit_of_Measure": ["LB", "LB", "LB", "LB", "LB", "QT", "LB", "GAL", "LB", "LB"],
    "Yield_Factor": [0.82, 0.98, 0.90, 0.85, 0.88, 1.00, 1.00, 1.00, 1.00, 1.00]
}

# Convert to a DataFrame
df = pd.DataFrame(mock_items)

# Calculate standard cost per procurement pack unit dynamically
df["Unit_Cost"] = round(df["Case_Price"] / 10, 2) 

# Save directly into your data folder
output_path = "data/mock_vendor_prices.xlsx"
df.to_excel(output_path, index=False)
print(f"🎉 Success! Your mock vendor data file has been created at '{output_path}'")
