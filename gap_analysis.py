import pandas as pd

inventory = pd.read_csv("data/inventory.csv")
forecast = pd.read_csv("data/forecast.csv")

df = inventory.merge(forecast, on=["store", "product_id"])
df["gap"] = df["units_in_stock"] - df["weekly_demand"]

df.to_csv("data/gap_analysis.csv", index=False)
print("GAP ANALYSIS DONE")
