import React, { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [bestAny, setBestAny] = useState([]);
  const [bestGrand, setBestGrand] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const API_BASE = "https://ny-scratch-backend.onrender.com/api";

  useEffect(() => {
    async function fetchData() {
      try {
        const [anyRes, grandRes] = await Promise.all([
          fetch(`${API_BASE}/best_any`),
          fetch(`${API_BASE}/best_grand`)
        ]);

        if (!anyRes.ok || !grandRes.ok)
          throw new Error("Backend request failed");

        const anyData = await anyRes.json();
        const grandData = await grandRes.json();

        setBestAny(anyData);
        setBestGrand(grandData);
      } catch (err) {
        console.error("Error fetching data:", err);
        setError("Unable to load data. Please try again later.");
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) return <div className="App"><h2>Loading scratch-off data…</h2></div>;
  if (error) return <div className="App"><h2>⚠️ {error}</h2></div>;

  return (
    <div className="App">
      <h1>🎯 NY Scratch-Off Analyzer</h1>

      <div className="grid">
        <div className="card">
          <h2>💰 Top 10 Tickets — Best Chance for Any Prize</h2>
          <table>
            <thead>
              <tr>
                <th>Game</th>
                <th>Remaining</th>
                <th>Total</th>
                <th>Remaining %</th>
              </tr>
            </thead>
            <tbody>
              {bestAny.map((g, i) => (
                <tr key={i}>
                  <td>{g.name}</td>
                  <td>{g.remaining_prizes.toLocaleString()}</td>
                  <td>{g.total_prizes.toLocaleString()}</td>
                  <td>{(g.remaining_ratio * 100).toFixed(2)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card">
          <h2>🏆 Top 10 Tickets — Best Chance for a Grand Prize</h2>
          <table>
            <thead>
              <tr>
                <th>Game</th>
                <th>Grand Prizes Remaining</th>
              </tr>
            </thead>
            <tbody>
              {bestGrand.map((g, i) => (
                <tr key={i}>
                  <td>{g.name}</td>
                  <td>{g.grand_prizes_remaining.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default App;
