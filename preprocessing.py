# preprocessing.py
import pandas as pd

def load_data():
    """Loads all data from the /data directory."""
    try:
        warehouses = pd.read_csv("data/warehouses.csv")
        stores = pd.read_csv("data/stores.csv")
        orders = pd.read_csv("data/orders.csv")
        # We no longer load routes.csv here
        return warehouses, stores, orders
    except FileNotFoundError as e:
        print(f"Data loading error: {e}. Make sure warehouses, stores, and orders CSV files are in the 'data' directory.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def preprocess_all():
    """Loads and preprocesses all data files."""
    # Note: routes is no longer returned from this function
    warehouses, stores, orders = load_data()
    return warehouses, stores, orders