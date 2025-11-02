import React, { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [bestAny, setBestAny] = useState([]);
  const [bestGrand, setBestGrand] = useState([]);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const API_BASE = "https://ny-scratch-backend.onrender.com/api";

  useEffect(() => {
    async function fetchData() {
      try {
        const [anyRes, grandRes, histRes] = await Promise.all([
          fetch(`${API_BASE}/best_any`),
          fetch(`${API_BASE}/best_grand`),
          fetch(`${API_BASE}/history`)
        ]);

        if (!anyRes.ok || !grandRes.ok || !histRes.ok)
          throw new Error("Backend request failed");

        const [anyData, grandData, historyData] = await Promise.all([
          anyRes.json(),
          grandRes.json(),
          histRes.json()
        ]);

        setBestAny(anyData);
        setBestGrand(grandData);

        if (historyData.length > 0) {
          const latest = historyData[historyData.length - 1].timestamp;
          setLastUpdated(new Date(latest));
        }
      } catch (err) {
        console.error("Error fetching data:", err);
        setError("Unable to load data. Please try again later.");
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading)
    return (
      <div className="App">
        <div className="loading">Loading scratch-off data…</div>
      </div>
    );

  if (error)
    return (
      <div className="App">
        <div className="error">⚠️ {error}</div>
      </div>
    );

  return (
    <div className="App">
      <header className="header">
        <h1>🎯 NY Scratch-Off Analyzer</h1>
        <p className="subtitle">Live insights from NY Lottery data</p>
        {lastUpdated && (
          <p className="updated">
            ⏱️ Updated: {lastUpdated.toLocaleDateString()}{" "}
            {lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </p>
        )}
      </header>

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

      <footer className="footer">
        Data auto-updates daily from NY Lottery Open Data • Built by Zappico Analytics 🧠
      </footer>
    </div>
  );
}

export default App;
