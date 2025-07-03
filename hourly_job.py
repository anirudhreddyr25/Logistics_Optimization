import requests
import time
import os

# For Docker, the web service is at 'http://web:5001'
# For local testing, it's at 'http://localhost:5001'
# We use an environment variable to switch between them.
WEB_APP_URL = os.environ.get("SCHEDULER_TARGET_URL", "http://localhost:5001/api/run_scheduler")

print(f"Scheduler job started. Target URL: {WEB_APP_URL}")

while True:
    try:
        print("Triggering the hourly optimization run...")
        response = requests.post(WEB_APP_URL)
        
        if response.status_code == 200:
            print(f"Successfully triggered scheduler: {response.json().get('message')}")
        else:
            print(f"Error triggering scheduler. Status: {response.status_code}, Response: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Could not connect to the web application: {e}")

    # Wait for one hour (3600 seconds) before the next run
    print("Next run in 1 hour.")
    time.sleep(3600)