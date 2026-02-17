from flask import Flask, render_template, request, redirect, session, flash
import pandas as pd
import os

# ======================
# APP SETUP
# ======================

app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

app.secret_key = "inventory_ai_secret"

# ======================
# PATH SETUP
# ======================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "inventory.csv")
HISTORY_FILE = os.path.join(BASE_DIR, "data", "transfer_history.csv")

LOW_STOCK = 50

# ======================
# UTILITY FUNCTIONS
# ======================

def load_data():
    return pd.read_csv(DATA_FILE)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def logged_in():
    return "user" in session

# ======================
# AI LOGIC
# ======================

def ai_recommend_transfers(df, low_threshold=50, move_qty=40):
    recommendations = []

    for product in df["product_name"].unique():
        product_df = df[df["product_name"] == product]

        low_stores = product_df[product_df["units_in_stock"] < low_threshold]
        high_stores = product_df[product_df["units_in_stock"] > low_threshold * 2]

        for _, low in low_stores.iterrows():
            for _, high in high_stores.iterrows():
                if low["store"] != high["store"]:
                    recommendations.append({
                        "product": product,
                        "from": high["store"],
                        "to": low["store"],
                        "qty": min(move_qty, int(high["units_in_stock"] / 4)),
                        "reason": f"Low stock at {low['store']} ({low['units_in_stock']})"
                    })
                    break
    return recommendations

# ======================
# ROUTES
# ======================

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    session.pop('_flashes', None)

    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin123":
            session["user"] = "admin"
            return redirect("/dashboard")
        flash("Invalid credentials", "danger")

    return render_template("login.html", title="Login")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ======================
# DASHBOARD (FIXED)
# ======================

@app.route("/dashboard")
def dashboard():
    if not logged_in():
        return redirect("/login")

    df = load_data()

    # ------------------
    # BASIC METRICS
    # ------------------
    total_products = df["product_name"].nunique()
    total_stock = int(df["units_in_stock"].sum())
    low_stock_count = int(len(df[df["units_in_stock"] < LOW_STOCK]))

    # ------------------
    # BUILD SHOP + PRODUCT DATA
    # ------------------
    shops = []

    for store in df["store"].unique():
        store_df = df[df["store"] == store]

        products = []
        for _, row in store_df.iterrows():
            products.append({
                "product": row["product_name"],
                "qty": int(row["units_in_stock"])
            })

        shops.append({
            "name": store,
            "products": products
        })

    # ------------------
    # CHART DATA
    # ------------------
    pie_labels = [shop["name"] for shop in shops]
    pie_values = [
        sum(p["qty"] for p in shop["products"])
        for shop in shops
    ]

    # ------------------
    # TRANSFERS TODAY
    # ------------------
    transfers_today = 0
    if os.path.exists(HISTORY_FILE):
        history = pd.read_csv(HISTORY_FILE)
        today = pd.Timestamp.now().strftime("%Y-%m-%d")
        transfers_today = int(
            history[history["date"].astype(str).str.contains(today)].shape[0]
        )

    return render_template(
        "dashboard.html",
        total_products=total_products,
        total_stock=total_stock,
        low_stock_count=low_stock_count,
        transfers_today=transfers_today,
        shops=shops,
        pie_labels=pie_labels,
        pie_values=pie_values
    )

# ======================
# INVENTORY
# ======================

@app.route("/inventory", methods=["GET", "POST"])
def inventory():
    if not logged_in():
        return redirect("/login")

    df = load_data()

    if request.method == "POST":
        store = request.form["store"]
        product = request.form["product"]
        qty = int(request.form["qty"])

        df.loc[
            (df["store"] == store) &
            (df["product_name"] == product),
            "units_in_stock"
        ] = qty

        save_data(df)
        flash("Stock updated successfully", "success")

    return render_template("inventory.html", inventory=df.to_dict("records"))

# ======================
# TRANSFER
# ======================

@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    if not logged_in():
        return redirect("/login")

    df = load_data()
    stores = sorted(df["store"].unique())
    products = sorted(df["product_name"].unique())
    selected_store = request.args.get("store", stores[0])

    if request.method == "POST":
        from_store = request.form["from_store"]
        to_store = request.form["to_store"]
        product = request.form["product"]
        qty = int(request.form["qty"])

        src = (df["store"] == from_store) & (df["product_name"] == product)
        dst = (df["store"] == to_store) & (df["product_name"] == product)

        if df.loc[src, "units_in_stock"].values[0] >= qty:
            df.loc[src, "units_in_stock"] -= qty
            df.loc[dst, "units_in_stock"] += qty
            save_data(df)

            if not os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, "w") as f:
                    f.write("date,product,quantity,from_store,to_store\n")

            history = pd.read_csv(HISTORY_FILE)
            history.loc[len(history)] = [
                pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                product,
                qty,
                from_store,
                to_store
            ]
            history.to_csv(HISTORY_FILE, index=False)

            flash("Transfer successful", "success")
        else:
            flash("Not enough stock", "danger")

        df = load_data()

    return render_template(
        "transfer.html",
        stores=stores,
        products=products,
        selected_store=selected_store,
        pie_labels=df[df["store"] == selected_store]["product_name"].tolist(),
        pie_values=list(map(int, df[df["store"] == selected_store]["units_in_stock"].tolist())),
        ai_suggestions=ai_recommend_transfers(df)
    )

# ======================
# HISTORY
# ======================

@app.route("/history")
def history():
    if not logged_in():
        return redirect("/login")

    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as f:
            f.write("date,product,quantity,from_store,to_store\n")

    df = pd.read_csv(HISTORY_FILE)
    return render_template("history.html", history=df.to_dict("records"))
@app.route("/update_stock", methods=["POST"])
def update_stock():
    if not logged_in():
        return redirect("/login")

    store = request.form["store"]
    qty = int(request.form["qty"])

    df = load_data()
    df.loc[df["store"] == store, "units_in_stock"] = qty
    save_data(df)

    flash("Stock updated successfully", "success")
    return redirect("/dashboard")


# ======================
# START SERVER
# ======================

if __name__ == "__main__":
    app.run(debug=True)
