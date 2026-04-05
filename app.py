import json
import os
from flask import Flask, jsonify, render_template
from apscheduler.schedulers.background import BackgroundScheduler
from model import run_model

app = Flask(__name__)

def scheduled_update():
    print("Running scheduled model update...")
    try:
        run_model()
        print("Update complete.")
    except Exception as e:
        print(f"Scheduled update failed: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_update, "cron", hour=14, minute=0, timezone="UTC")
scheduler.start()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/predictions")
def predictions():
    path = "data/predictions.json"
    if not os.path.exists(path):
        try:
            run_model()
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    with open(path) as f:
        return jsonify(json.load(f))

@app.route("/api/refresh")
def refresh():
    try:
        run_model()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
