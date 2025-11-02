from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import json
import pandas as pd
import os

# --- Initialize Flask and enable CORS ---
app = Flask(__name__, static_folder="build", static_url_path="")
CORS(app, resources={r"/*": {"origins": "*"}})


# --- File locations ---
DATA_FILE = "ny_scratch_data.json"
HISTORY_FILE = "ny_scratch_history.json"

# --- Helper functions ---
def load_data():
    """Load the most recent dataset"""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE) as f:
        return json.load(f)

def load_history():
    """Load historical snapshots"""
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE) as f:
        return json.load(f)

# --- API routes ---

@app.route("/api/recommendation")
def recommendation():
    """Return the single best game by smart scoring"""
    data = load_data()
    if not data:
        return jsonify({"error": "No data available"}), 404

    df = pd.DataFrame(data)

    # Safe normalization (avoids divide-by-zero)
    def safe_normalize(series):
        if series.max() == series.min():
            return pd.Series([0.0] * len(series))
        return (series - series.min()) / (series.max() - series.min())

    df["value_norm"] = safe_normalize(df["expected_value"])
    df["prize_norm"] = safe_normalize(df["remaining_prizes"])
    df["grand_norm"] = safe_normalize(df["grand_prizes_remaining"])

    df["smart_score"] = (
        0.5 * df["value_norm"] +
        0.3 * df["prize_norm"] +
        0.2 * df["grand_norm"]
    )

    best = df.sort_values("smart_score", ascending=False).head(1).iloc[0].to_dict()
    return jsonify(best)


@app.route("/api/best_any")
def best_any():
    """Top 10 games by remaining prizes"""
    data = load_data()
    if not data:
        return jsonify({"error": "No data available"}), 404
    df = pd.DataFrame(data)
    best = df.sort_values(by="remaining_prizes", ascending=False).head(10)
    return jsonify(best.to_dict(orient="records"))


@app.route("/api/best_grand")
def best_grand():
    """Top 10 games with highest grand prizes remaining"""
    data = load_data()
    if not data:
        return jsonify({"error": "No data available"}), 404
    df = pd.DataFrame(data)
    best = df.sort_values(by="grand_prizes_remaining", ascending=False).head(10)
    return jsonify(best.to_dict(orient="records"))


@app.route("/api/history")
def history():
    """Return historical data snapshots"""
    hist = load_history()
    return jsonify(hist)


@app.route("/api/movers")
def movers():
    """Show which games improved or declined since last scrape"""
    history = load_history()
    if len(history) < 2:
        return jsonify({"error": "Not enough data yet"}), 400

    latest = pd.DataFrame(history[-1]["data"])
    prev = pd.DataFrame(history[-2]["data"])

    merged = pd.merge(
        latest[["name", "expected_value"]],
        prev[["name", "expected_value"]],
        on="name",
        suffixes=("_now", "_prev"),
    )

    merged["change"] = merged["expected_value_now"] - merged["expected_value_prev"]
    gainers = merged.sort_values("change", ascending=False).head(5).to_dict(orient="records")
    losers = merged.sort_values("change", ascending=True).head(5).to_dict(orient="records")

    return jsonify({"gainers": gainers, "losers": losers})


# --- Serve React frontend ---
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    if path != "" and os.path.exists(f"build/{path}"):
        return send_from_directory("build", path)
    else:
        return send_from_directory("build", "index.html")


# --- Start Flask app ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting Flask server on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
