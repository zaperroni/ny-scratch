from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import json
import pandas as pd
import os

app = Flask(__name__, static_folder="build", static_url_path="")
CORS(app)

DATA_FILE = "ny_scratch_data.json"
HISTORY_FILE = "ny_scratch_history.json"


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


@app.route("/api/recommendations")
def recommendations():
    """Return all scratch-off games with calculated metrics"""
    data = load_data()
    return jsonify(data)


@app.route("/api/best_any")
def best_any():
    """Return top 10 games by best odds (any prize)"""
    data = load_data()
    if not data:
        return jsonify({"error": "No data available"}), 404
    df = pd.DataFrame(data)
    best = df.sort_values(by="remaining_prizes", ascending=False).head(10)
    return jsonify(best.to_dict(orient="records"))


@app.route("/api/best_grand")
def best_grand():
    """Return top 10 games with highest remaining grand prizes"""
    data = load_data()
    if not data:
        return jsonify({"error": "No data available"}), 404
    df = pd.DataFrame(data)
    best = df.sort_values(by="grand_prizes_remaining", ascending=False).head(10)
    return jsonify(best.to_dict(orient="records"))


@app.route("/api/history")
def history():
    """Return historical data"""
    hist = load_history()
    return jsonify(hist)


@app.route("/api/movers")
def movers():
    """Show which games improved or declined since last run"""
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


@app.route("/api/recommendation")
def recommendation():
    """Return the single best game by smart scoring"""
    data = load_data()
    if not data:
        return jsonify({"error": "No data available"}), 404

    df = pd.DataFrame(data)
    df["value_norm"] = (df["expected_value"] - df["expected_value"].min()) / (
        df["expected_value"].max() - df["expected_value"].min()
    )
    df["prize_norm"] = (df["remaining_prizes"] - df["remaining_prizes"].min()) / (
        df["remaining_prizes"].max() - df["remaining_prizes"].min()
    )
    df["grand_norm"] = (df["grand_prizes_remaining"] - df["grand_prizes_remaining"].min()) / (
        df["grand_prizes_remaining"].max() - df["grand_prizes_remaining"].min()
    )
    df["smart_score"] = 0.5 * df["value_norm"] + 0.3 * df["prize_norm"] + 0.2 * df["grand_norm"]

    best = df.sort_values("smart_score", ascending=False).head(1).iloc[0].to_dict()
    return jsonify(best)


# ✅ Serve React frontend (after build)
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    """Serve the React frontend build."""
    if path != "" and os.path.exists(f"build/{path}"):
        return send_from_directory("build", path)
    else:
        return send_from_directory("build", "index.html")


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting Flask server on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
