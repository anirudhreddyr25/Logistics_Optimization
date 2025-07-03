import pandas as pd
import os
import googlemaps
from haversine import haversine
from pulp import LpProblem, LpVariable, LpMinimize, lpSum, LpBinary, LpStatus
from dotenv import load_dotenv
from preprocessing import preprocess_all

# Load environment variables for the API key
load_dotenv()

def find_potential_routes(warehouses, stores, gmaps_client, top_n=5):
    """
    For each store, finds the top N nearest warehouses by straight-line distance,
    then gets actual driving distance for those candidates from Google Maps API.
    """
    print("Finding potential routes using Google Maps API...")
    potential_routes = []
    
    for _, store in stores.iterrows():
        store_coords = (store['lat'], store['lon'])
        
        # Step 1: Calculate cheap haversine distance to all warehouses
        warehouses['distance'] = warehouses.apply(
            lambda wh: haversine((wh['lat'], wh['lon']), store_coords),
            axis=1
        )
        
        # Step 2: Filter to the top N nearest candidates
        nearest_warehouses = warehouses.nsmallest(top_n, 'distance')
        
        # Step 3: Call Google Maps API only for these candidates
        for _, warehouse in nearest_warehouses.iterrows():
            origin = (warehouse['lat'], warehouse['lon'])
            destination = store_coords
            
            try:
                directions_result = gmaps_client.directions(origin, destination, mode="driving")
                if directions_result:
                    leg = directions_result[0]['legs'][0]
                    distance_km = round(leg['distance']['value'] / 1000, 2)
                    
                    # Create realistic metrics based on real distance
                    fuel_cost = round(distance_km * 0.7 + 25, 2) # Example cost function
                    delay_prob = round(min(0.5, distance_km / 20000 + 0.01), 3) # Example delay function
                    
                    potential_routes.append({
                        'warehouse_id': warehouse['warehouse_id'],
                        'store_id': store['store_id'],
                        'distance_km': distance_km,
                        'fuel_cost_usd': fuel_cost,
                        'delay_probability': delay_prob
                    })
                    print(f"  -> Route found from {warehouse['location']} to {store['location']}: {distance_km} km")
                else:
                    print(f"  -- No driving route from {warehouse['location']} to {store['location']}. Skipping.")
            except Exception as e:
                print(f"  !! API Error for route {warehouse['location']} to {store['location']}: {e}")

    return pd.DataFrame(potential_routes)

def optimize_assignments():
    """
    Dynamically calculates potential routes and then finds the optimal assignment of orders.
    """
    API_KEY = os.getenv("Maps_API_KEY")
    if not API_KEY:
        raise ValueError("Google Maps API key not found in .env file.")
    gmaps = googlemaps.Client(key=API_KEY)

    warehouses, stores, _, orders = preprocess_all()
    if orders.empty or stores.empty or warehouses.empty:
        return pd.DataFrame()

    # This is the new dynamic step, replacing the read from routes.csv
    routes = find_potential_routes(warehouses, stores, gmaps)

    if routes.empty:
        print("No valid routes found after API calls.")
        return pd.DataFrame()

    # The rest of the optimization logic remains the same, but uses the dynamically generated routes
    prob = LpProblem("Logistics_Optimization", LpMinimize)
    possible_routes = pd.merge(orders[['order_id', 'store_id']], routes, on='store_id')
    
    costs = {
        (row.order_id, row.warehouse_id): (row.fuel_cost_usd * 0.5 + row.delay_probability * 100 * 0.3 + row.distance_km * 0.2)
        for _, row in possible_routes.iterrows()
    }
    
    possible_assignments = list(costs.keys())
    x = LpVariable.dicts("x", possible_assignments, 0, 1, LpBinary)
    prob += lpSum([costs[i] * x[i] for i in possible_assignments]), "Total_Weighted_Cost"

    for order_id in orders['order_id']:
        prob += lpSum([x[(o_id, w_id)] for (o_id, w_id) in possible_assignments if o_id == order_id]) == 1, f"Assign_Order_{order_id}"

    prob.solve()

    if prob.status != LpStatus['Optimal']:
        return pd.DataFrame()

    chosen_assignments = [(o_id, w_id) for (o_id, w_id), var in x.items() if var.varValue == 1]
    assignments_df = pd.DataFrame(chosen_assignments, columns=['order_id', 'warehouse_id'])
    final_assignments = pd.merge(assignments_df, possible_routes, on=['order_id', 'warehouse_id'])
    output_columns = ['order_id', 'store_id', 'warehouse_id', 'distance_km', 'fuel_cost_usd', 'delay_probability']
    return final_assignments[output_columns].drop_duplicates()