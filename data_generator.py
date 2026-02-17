import pandas as pd
import numpy as np

np.random.seed(42)

stores = ["Factory", "Shop_A", "Shop_B", "Shop_C", "Shop_D"]
products = [f"P{i}" for i in range(1, 51)]
dates = pd.date_range("2023-01-01", "2024-12-31")

rows = []

for date in dates:
    for store in stores:
        for product in products:
            rows.append([
                date,
                store,
                product,
                np.random.poisson(6),
                np.random.randint(50, 300)
            ])

df = pd.DataFrame(rows, columns=[
    "date", "store", "product_id", "units_sold", "units_in_stock"
])

df.to_csv("data/sales_big.csv", index=False)

inventory = df.groupby(["store", "product_id"])["units_in_stock"].mean().reset_index()
inventory.to_csv("data/inventory.csv", index=False)

print("BIG DATASET GENERATED")
