import requests
import pandas as pd
import json
import datetime
import os

# Official New York State Open Data source
DATA_URL = "https://data.ny.gov/resource/nzqa-7unk.json"

def fetch_dataset():
    """Download the official NY Lottery scratch-off dataset."""
    print("🔄 Fetching dataset from New York Open Data…")
    r = requests.get(DATA_URL)
    r.raise_for_status()
    data = r.json()
    print(f"✅ Retrieved {len(data)} rows from dataset.")
    return pd.DataFrame(data)

def clean_and_compute(df):
    """Convert fields and compute simple metrics."""
    # Convert numeric fields safely
    numeric_fields = ["game_number", "prize_amount", "paid", "unpaid", "total"]
    for col in numeric_fields:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Rename columns to consistent names used later
    df.rename(columns={
        "game_name": "name",
        "game_number": "number",
        "prize_amount": "prize_amount",
        "unpaid": "remaining_prizes",
        "total": "total_prizes"
    }, inplace=True)

    # Group by game name to summarize prizes
    summary = (
        df.groupby("name")
          .agg({
              "remaining_prizes": "sum",
              "total_prizes": "sum",
              "prize_amount": "mean"
          })
          .reset_index()
    )

    # Calculate ratios and expected values
    summary["remaining_ratio"] = (
        summary["remaining_prizes"] / summary["total_prizes"]
    ).fillna(0)

    summary["expected_value"] = (
        summary["prize_amount"] * summary["remaining_ratio"]
    )

    summary["value_score"] = (
        summary["expected_value"] / summary["prize_amount"]
    ).fillna(0)

    # Grand prize = max remaining for each game
    summary["grand_prizes_remaining"] = (
        df.groupby("name")["remaining_prizes"].max().values
    )

    return summary.sort_values(by="expected_value", ascending=False)

def scrape_all():
    """Main entry point — fetch, compute, and save JSON files."""
    df = fetch_dataset()
    result_df = clean_and_compute(df)

    # Save latest snapshot
    result_df.to_json("ny_scratch_data.json", orient="records", indent=2)

    # Append to history log
    timestamp = datetime.datetime.now().isoformat(timespec="seconds")
    history_path = "ny_scratch_history.json"
    if os.path.exists(history_path):
        with open(history_path, "r") as f:
            history = json.load(f)
    else:
        history = []

    history.append({
        "timestamp": timestamp,
        "data": result_df.to_dict(orient="records")
    })

    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)

    print("✅ Saved ny_scratch_data.json and ny_scratch_history.json")

if __name__ == "__main__":
    scrape_all()
