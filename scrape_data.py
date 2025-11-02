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

def _clean_money_series(s):
    """Turn strings like '$10,000' into floats."""
    return (
        s.astype(str)
         .str.replace(r"[^0-9.]", "", regex=True)
         .replace({"": "0"})
         .astype(float)
    )

def estimate_ticket_price(top_prize):
    """
    Very simple, transparent heuristic for NY scratchers.
    You can refine these thresholds later with a price table per game.
    """
    if top_prize >= 20_000_000:  # some $50 games
        return 50
    if top_prize >= 10_000_000:
        return 30  # many $30 games carry $10M+ top prizes
    if top_prize >= 5_000_000:
        return 20
    if top_prize >= 2_000_000:
        return 10
    if top_prize >= 500_000:
        return 5
    if top_prize >= 20_000:
        return 2
    return 1

def clean_and_compute(df):
    """Compute tier-weighted EV, EV per dollar, and other useful fields."""
    # Parse/convert numerics safely
    if "prize_amount" in df.columns:
        df["prize_amount"] = _clean_money_series(df["prize_amount"])

    for col in ["game_number", "paid", "unpaid", "total"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Standardize column names we use downstream
    df = df.rename(
        columns={
            "game_name": "name",
            "game_number": "number",
            "unpaid": "unpaid",
            "total": "total",
        }
    )

    # Keep only rows with a real prize tier and prize counts
    df = df[(df["prize_amount"] > 0) & (df["total"] > 0)]

    # Build per-game metrics
    def summarize_game(g):
        # Top prize for the game
        top_prize = g["prize_amount"].max()

        # Tier-weighted EV of what's left (unitless dollars; proxy)
        # EV_raw = sum(prize_amount * (unpaid / total))
        ev_raw = float((g["prize_amount"] * (g["unpaid"] / g["total"])).sum())

        # Estimate ticket price and compute EV per $1 cost
        ticket_price = estimate_ticket_price(top_prize)
        ev_per_dollar = ev_raw / ticket_price if ticket_price > 0 else 0.0

        # Odds-style summaries
        remaining_prizes = int(g["unpaid"].sum())
        total_prizes = int(g["total"].sum())
        remaining_ratio = (remaining_prizes / total_prizes) if total_prizes else 0.0

        # “Grand” = count of unpaid at the top tier
        grand_unpaid = int(g.loc[g["prize_amount"] == top_prize, "unpaid"].sum())

        return pd.Series(
            {
                "name": g["name"].iloc[0],
                "top_prize": float(top_prize),
                "ticket_price_est": float(ticket_price),
                "ev_raw": round(ev_raw, 4),
                # Keep this for your frontend table — show EV per dollar
                "expected_value": round(ev_per_dollar, 2),
                "ev_per_dollar": round(ev_per_dollar, 4),
                "remaining_prizes": remaining_prizes,
                "total_prizes": total_prizes,
                "remaining_ratio": round(remaining_ratio, 6),
                "grand_prizes_remaining": grand_unpaid,
                # For compatibility with your current UI “Prize Amount” column:
                "prize_amount": float(top_prize),
            }
        )

    summary = df.groupby("name", as_index=False).apply(summarize_game)

    # Rank by EV per dollar by default
    summary = summary.sort_values("ev_per_dollar", ascending=False)

    # Normalized score useful for “top lists”
    max_evpd = summary["ev_per_dollar"].max() or 1.0
    summary["value_score"] = (summary["ev_per_dollar"] / max_evpd).round(6)

    return summary.reset_index(drop=True)

def scrape_all():
    df = fetch_dataset()
    result_df = clean_and_compute(df)

    # Save the cleaned dataset the frontend/Flask serve
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

    history.append(
        {
            "timestamp": timestamp,
            "data": result_df.to_dict(orient="records"),
        }
    )

    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)

    print("✅ Saved ny_scratch_data.json and ny_scratch_history.json")

if __name__ == "__main__":
    scrape_all()
