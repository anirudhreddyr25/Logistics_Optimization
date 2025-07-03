import pandas as pd

def load_data():
    """Loads all data from the /data directory."""
    try:
        warehouses = pd.read_csv("data/warehouses.csv")
        stores = pd.read_csv("data/stores.csv")
        routes = pd.read_csv("data/routes.csv")
        orders = pd.read_csv("data/orders.csv")
        return warehouses, stores, routes, orders
    except FileNotFoundError as e:
        print(f"Data loading error: {e}. Make sure all CSV files are in the 'data' directory.")
        # Return empty DataFrames to prevent crashes if files are missing
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def preprocess_all():
    """Loads and preprocesses all data files."""
    warehouses, stores, routes, orders = load_data()
    # In a real project, you might add more preprocessing steps here.
    return warehouses, stores, routes, orders