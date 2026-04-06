function getAlertClass(alert) {
  const a = (alert || "").toLowerCase();
  if (a.includes("hotspot"))   return "hotspot";
  if (a.includes("congestion") || a.includes("gridlock") || a.includes("alert")) return "congestion";
  if (a.includes("anomaly"))   return "anomaly";
  if (a.includes("drift"))     return "drift";
  return "anomaly";
}

function getIcon(alert) {
  const a = (alert || "").toLowerCase();
  if (a.includes("hotspot"))   return "🔴";
  if (a.includes("congestion") || a.includes("gridlock")) return "⚠️";
  if (a.includes("anomaly"))   return "🟡";
  if (a.includes("drift"))     return "🔵";
  return "🟡";
}

export default function AlertFeed({ alerts }) {
  const items = (alerts || []).slice(-15).reverse();

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Anomaly & Alert Feed</span>
        <span className="panel-badge">{items.length} ALERTS</span>
      </div>
      {items.length === 0 ? (
        <div className="no-data">No alerts generated yet</div>
      ) : (
        <div className="alert-list">
          {items.map((alert, i) => (
            <div key={i} className={`alert-item ${getAlertClass(alert)}`}>
              <span className="alert-icon">{getIcon(alert)}</span>
              <span className="alert-text">{alert}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}