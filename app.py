from flask import Flask, request, jsonify, render_template
import pandas as pd
import os
from optimization import optimize_assignments
from model import get_optimized_route
from preprocessing import preprocess_all

# Initialize Flask App
app = Flask(__name__, template_folder='templates', static_folder='static')

# --- Page Rendering Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/scheduler')
def scheduler():
    return render_template('scheduler.html')

@app.route('/model_insights')
def model_insights():
    return render_template('model_insights.html')

# --- API Endpoints ---
@app.route('/api/dashboard_data', methods=['GET'])
def get_dashboard_data():
    """Provides initial data for the dashboard page."""
    try:
        warehouses_df, stores_df, _, orders_df = preprocess_all()
        
        if os.path.exists('scheduler_log.csv'):
            log_df = pd.read_csv('scheduler_log.csv')
            latest_routes = log_df.tail(5).to_dict(orient='records')
            last_run = pd.to_datetime(log_df['run_timestamp']).max().strftime('%Y-%m-%d %I:%M %p') if not log_df.empty else "Not run yet"
        else:
            latest_routes = []
            last_run = "Not run yet"

        return jsonify({
            "stats": {
                "total_orders": len(orders_df),
                "total_warehouses": len(warehouses_df),
                "total_stores": len(stores_df),
                "last_run": last_run
            },
            "warehouses": warehouses_df.to_dict(orient='records'),
            "stores": stores_df.to_dict(orient='records'),
            "latest_routes": latest_routes
        })
    except Exception as e:
        return jsonify({"error": f"Could not load dashboard data: {e}"}), 500

@app.route('/api/get_route', methods=['POST'])
def find_route_api():
    """API endpoint to find a specific route."""
    data = request.get_json()
    source = data.get('source')
    destination = data.get('destination')
    result = get_optimized_route(source, destination)
    return jsonify({'route_details': result})

@app.route('/api/run_scheduler', methods=['POST'])
def run_scheduler_api():
    """API endpoint to trigger the main optimization process."""
    try:
        results = optimize_assignments()
        if results.empty:
            return jsonify({'message': 'Optimization run skipped, data might be missing.'}), 400
        
        timestamp = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        results['run_timestamp'] = timestamp
        header = not os.path.exists('scheduler_log.csv')
        results.to_csv('scheduler_log.csv', mode='a', index=False, header=header)
        return jsonify({'message': 'Scheduler run completed successfully!', 'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %I:%M %p')})
    except Exception as e:
        return jsonify({'error': f'Failed to run scheduler: {e}'}), 500

@app.route('/api/model_insights_data', methods=['GET'])
def get_model_insights_data():
    """Provides aggregated data for the charts page."""
    try:
        _, _, routes, _ = preprocess_all()
        if routes.empty:
            return jsonify({"error": "Routes data not found."}), 400

        # Delay vs. Distance Chart Data
        delay_chart = routes.sort_values('distance_km').head(15)
        
        # Warehouse Fuel Cost Chart Data
        fuel_chart = routes.groupby('warehouse_id')['fuel_cost_usd'].mean().sort_values().reset_index()

        return jsonify({
            "delay_chart": {
                "labels": delay_chart['distance_km'].tolist(),
                "data": (delay_chart['delay_probability'] * 100).tolist()
            },
            "fuel_chart": {
                "labels": fuel_chart['warehouse_id'].tolist(),
                "data": fuel_chart['fuel_cost_usd'].tolist()
            }
        })
    except Exception as e:
        return jsonify({"error": f"Could not generate model insights: {e}"}), 500

# This block allows you to run the app directly for local testing
if __name__ == '__main__':
    app.run(debug=True, port=5001)