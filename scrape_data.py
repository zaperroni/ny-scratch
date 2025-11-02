import requests
import pandas as pd
import json
import datetime
import os

DATA_URL = "https://data.ny.gov/resource/nzqa-7unk.json"

def fetch_dataset():
    """Download official NY Lottery scratch-off dataset."""
    print("🔄 Fetching dataset from New York Open Data…")
    r = requests.get(DATA_URL)
    r.raise_for_status()
    data = r.json()
    print(f"✅ Retrieved {len(data)} rows from dataset.")
    return pd.DataFrame(data)

def clean_and_compute(df):
    """Convert and compute realistic expected value metrics."""
    print("📊 Raw data columns:", df.columns.tolist())
    print("First few rows:\n", df.head(3))

    # Remove $ and commas before numeric conversion
    if "prize_amount" in df.columns:
        df["prize_amount"] = (
            df["prize_amount"]
            .astype(str)
            .str.replace(r"[^0-9.]", "", regex=True)
        )

    # Convert numeric fields safely
    for col in ["game_number", "prize_amount", "paid", "unpaid", "total"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Rename columns for consistency
    df.rename(columns={
        "game_name": "name",
        "game_number": "number",
        "unpaid": "remaining_prizes",
        "total": "total_prizes"
    }, inplace=True)

    # Remove zero rows
    df = df[(df["prize_amount"] > 0) & (df["total_prizes"] > 0)]

    # Group by game name
    summary = (
        df.groupby("name")
          .agg({
              "remaining_prizes": "sum",
              "total_prizes": "sum",
              "prize_amount": "max"
          })
          .reset_index()
    )

    # Calculate ratios and expected values
    summary["remaining_ratio"] = (
        summary["remaining_prizes"] / summary["total_prizes"]
    ).fillna(0)

    # Compute expected values
    summary["expected_value"] = (
        summary["prize_amount"] * summary["remaining_ratio"] * 0.1
    ).round(2)

    summary["value_score"] = (
        summary["expected_value"] / summary["expected_value"].max()
    ).fillna(0)

    # Estimate grand prizes (max remaining per game)
    summary["grand_prizes_remaining"] = (
        df.groupby("name")["remaining_prizes"].max().values
    )

    print("🔍 Sample cleaned data:")
    print(summary.head(10))
    print("Summary shape:", summary.shape)

    return summary.sort_values(by="expected_value", ascending=False)

def scrape_all():
    df = fetch_dataset()
    result_df = clean_and_compute(df)

    # Save the cleaned dataset
    result_df.to_json("ny_scratch_data.json", orient="records", indent=2)

    # Append to historical log
    timestamp = datetime.datetime.now().isoformat(timespec="seconds")
    history_path = "ny_scratch_history.json"
    history = []

    if os.path.exists(history_path):
        with open(history_path, "r") as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                pass

    history.append({
        "timestamp": timestamp,
        "data": result_df.to_dict(orient="records")
    })

    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)

    print("✅ Saved ny_scratch_data.json and ny_scratch_history.json")

if __name__ == "__main__":
    scrape_all()
