import React, { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [games, setGames] = useState([]);
  const [best, setBest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // ✅ Use your live backend
  const API_BASE = "https://ny-scratch-backend.onrender.com/api";

  useEffect(() => {
    async function fetchData() {
      try {
        const [gamesRes, bestRes] = await Promise.all([
          fetch(`${API_BASE}/best_any`),
          fetch(`${API_BASE}/recommendation`)
        ]);

        if (!gamesRes.ok || !bestRes.ok) {
          throw new Error("Backend request failed");
        }

        const gamesData = await gamesRes.json();
        const bestData = await bestRes.json();

        setGames(gamesData);
        setBest(bestData);
      } catch (err) {
        console.error("Error fetching data:", err);
        setError("Unable to load data. Please try again later.");
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) {
    return <div className="App"><h2>Loading scratch-off data…</h2></div>;
  }

  if (error) {
    return <div className="App"><h2>⚠️ {error}</h2></div>;
  }

  return (
    <div className="App">
      <h1>🎯 NY Scratch-Off Analyzer</h1>

      {best && (
        <div className="card">
          <h2>Best Ticket to Play</h2>
          <p><strong>{best.name}</strong></p>
          <p>Expected Value: ${best.expected_value?.toFixed(2)}</p>
          <p>Remaining Prizes: {best.remaining_prizes}</p>
          <p>Grand Prizes Remaining: {best.grand_prizes_remaining}</p>
        </div>
      )}

      <h2>All Games</h2>
      <table>
        <thead>
          <tr>
            <th>Game</th>
            <th>Prize Amount</th>
            <th>Remaining</th>
            <th>Total</th>
            <th>Expected Value</th>
          </tr>
        </thead>
        <tbody>
          {games.map((g, i) => (
            <tr key={i}>
              <td>{g.name}</td>
              <td>${Number(g.prize_amount).toLocaleString()}</td>
              <td>{g.remaining_prizes}</td>
              <td>{g.total_prizes}</td>
              <td>${Number(g.expected_value).toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;
