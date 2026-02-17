import pandas as pd

df = pd.read_csv("data/gap_analysis.csv")

excess = df[df["gap"] > 30]
shortage = df[df["gap"] < -20]

transfers = []

for _, s in shortage.iterrows():
    for _, e in excess.iterrows():
        if s["product_id"] == e["product_id"] and s["store"] != e["store"]:
            qty = min(abs(s["gap"]), e["gap"])
            if qty > 0:
                transfers.append([
                    e["store"], s["store"], s["product_id"], qty
                ])
                excess.loc[e.name, "gap"] -= qty
                break

transfer_df = pd.DataFrame(
    transfers,
    columns=["from_store", "to_store", "product_id", "quantity"]
)

transfer_df.to_csv("data/transfer_plan.csv", index=False)
print("TRANSFER PLAN READY")
