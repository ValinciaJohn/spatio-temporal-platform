// src/components/RegimeChart.jsx
const REGIME_ORDER = ["gridlock", "congested", "slow", "free_flow", "unknown"];

export default function RegimeChart({ summary }) {
  if (!summary || summary.length === 0) {
    return (
      <div className="panel">
        <div className="panel-header">
          <span className="panel-title">Predicted Next Regime</span>
          <span className="panel-badge">MARKOV CHAIN</span>
        </div>
        <div className="no-data">No predictions yet</div>
      </div>
    );
  }

  // Count predicted regimes
  const counts = { gridlock: 0, congested: 0, slow: 0, free_flow: 0, unknown: 0 };
  summary.forEach((c) => {
    const r = c.predicted_next || "unknown";
    if (counts[r] !== undefined) counts[r]++;
    else counts.unknown++;
  });

  const total = summary.length || 1;

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Predicted Next Regime</span>
        <span className="panel-badge">MARKOV CHAIN</span>
      </div>
      <div className="regime-chart-wrap">
        {REGIME_ORDER.filter(r => counts[r] > 0).map((regime) => {
          const pct = Math.round((counts[regime] / total) * 100);
          return (
            <div key={regime} className="bar-row">
              <span className="bar-label">{regime.replace("_", " ")}</span>
              <div className="bar-track">
                <div
                  className={`bar-fill ${regime}`}
                  style={{ width: `${Math.max(pct, 4)}%` }}
                >
                  {pct >= 10 ? `${counts[regime]} clusters` : ""}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}