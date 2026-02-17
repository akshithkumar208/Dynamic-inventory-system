import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

df = pd.read_csv("data/sales_big.csv")

forecast_list = []

for (store, product), grp in df.groupby(["store", "product_id"]):
    ts = grp.groupby("date")["units_sold"].sum()
    try:
        model = ARIMA(ts, order=(1,1,1))
        result = model.fit()
        forecast = int(result.forecast(7).sum())
    except:
        forecast = int(ts.mean() * 7)

    forecast_list.append([store, product, forecast])

forecast_df = pd.DataFrame(
    forecast_list,
    columns=["store", "product_id", "weekly_demand"]
)

forecast_df.to_csv("data/forecast.csv", index=False)
print("FORECAST GENERATED")
