# app.py
from flask import Flask, request, jsonify, render_template, abort
import pandas as pd
import os
from werkzeug.utils import secure_filename
from optimization import optimize_assignments
from model import get_optimized_route
from preprocessing import preprocess_all

app = Flask(__name__, template_folder='templates', static_folder='static')

UPLOAD_FOLDER = './data'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
        warehouses_df, stores_df, orders_df = preprocess_all()
        log_df = pd.read_csv('scheduler_log.csv') if os.path.exists('scheduler_log.csv') else pd.DataFrame()
        
        latest_routes = log_df.tail(5).to_dict(orient='records') if not log_df.empty else []
        last_run = pd.to_datetime(log_df['run_timestamp']).max().strftime('%Y-%m-%d %I:%M %p') if not log_df.empty else "Not run yet"

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
    data = request.get_json()
    result = get_optimized_route(data.get('source'), data.get('destination'))
    return jsonify({'route_details': result})

@app.route('/api/run_scheduler', methods=['POST'])
def run_scheduler_api():
    try:
        results = optimize_assignments()
        if results.empty:
            return jsonify({'message': 'Optimization run skipped, data might be missing or no routes found.'}), 400
        
        timestamp = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        results['run_timestamp'] = timestamp
        header = not os.path.exists('scheduler_log.csv')
        results.to_csv('scheduler_log.csv', mode='a', index=False, header=header)
        return jsonify({'message': 'Scheduler run completed successfully!', 'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %I:%M %p')})
    except Exception as e:
        return jsonify({'error': f'Failed to run scheduler: {e}'}), 500

@app.route('/api/model_insights_data', methods=['GET'])
def get_model_insights_data():
    """Provides aggregated data for charts from the optimization log."""
    if not os.path.exists('scheduler_log.csv'):
        return jsonify({"error": "scheduler_log.csv not found. Run the optimizer first."}), 400
    
    try:
        log_df = pd.read_csv('scheduler_log.csv')
        # Delay vs. Distance Chart Data
        delay_chart = log_df.sort_values('distance_km').head(15)
        # Warehouse Fuel Cost Chart Data
        fuel_chart = log_df.groupby('warehouse_id')['fuel_cost_usd'].mean().sort_values().reset_index()

        return jsonify({
            "delay_chart": {"labels": delay_chart['distance_km'].tolist(), "data": (delay_chart['delay_probability'] * 100).tolist()},
            "fuel_chart": {"labels": fuel_chart['warehouse_id'].tolist(), "data": fuel_chart['fuel_cost_usd'].tolist()}
        })
    except Exception as e:
        return jsonify({"error": f"Could not generate model insights: {e}"}), 500

# --- ADD THIS MISSING ROUTE ---
@app.route('/api/upload_data', methods=['POST'])
def upload_data_api():
    """API endpoint to handle CSV file uploads."""
    if 'files' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    files = request.files.getlist('files')
    for file in files:
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
    return jsonify({'message': 'Files uploaded successfully! The new data will be used on the next optimization run.'})
# -----------------------------

if __name__ == '__main__':
    app.run(debug=True, port=5001)