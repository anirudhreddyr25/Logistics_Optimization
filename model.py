from preprocessing import preprocess_all

def get_optimized_route(source_warehouse_id, destination_store_id):
    """
    Finds the best available route between a specific warehouse and store.
    """
    try:
        _, _, routes, _ = preprocess_all()
        if routes.empty:
            return "Error: Routes data has not been loaded. Please check the /data directory."

        match = routes[(routes['warehouse_id'] == source_warehouse_id) & (routes['store_id'] == destination_store_id)]
        
        if not match.empty:
            row = match.iloc[0]
            # Return a formatted string for display
            return (f"Optimal Route Found:\n"
                    f"---------------------\n"
                    f"From: {source_warehouse_id}\n"
                    f"To: {destination_store_id}\n"
                    f"Distance: {row['distance_km']:.1f} km\n"
                    f"Est. Fuel Cost: ${row['fuel_cost_usd']:.2f}\n"
                    f"Delay Probability: {100 * row['delay_probability']:.1f}%")
        return "No direct route found for the given source and destination."
    except Exception as e:
        return f"An error occurred: {e}"