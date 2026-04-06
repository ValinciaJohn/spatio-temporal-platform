export default function DriftPanel({ drift }) {
  const d     = drift || {};
  const label = d.label || "STABLE";
  const score = (d.stability ?? 1.0).toFixed(3);
  const count = d.drift_count ?? 0;
  const events = (d.drift_events || []).slice(-8).reverse();

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Drift Detection</span>
        <span className="panel-badge">JACCARD STABILITY</span>
      </div>
      <div className="drift-wrap">
        <div className="drift-score-row">
          <div className={`drift-score-big ${label}`}>{score}</div>
          <div className="drift-label-block">
            <span className={`drift-state-badge ${label}`}>{label}</span>
            <span className="drift-count">{count} drift event{count !== 1 ? "s" : ""} total</span>
          </div>
        </div>
        {events.length > 0 && (
          <div className="drift-events-list">
            {events.map((ts, i) => (
              <div key={i} className="drift-event-item">
                🔵 Drift at {new Date(ts * 1000).toLocaleTimeString()}
              </div>
            ))}
          </div>
        )}
        {events.length === 0 && (
          <div className="no-data" style={{ padding: "8px 0" }}>
            No drift events detected
          </div>
        )}
      </div>
    </div>
  );
}