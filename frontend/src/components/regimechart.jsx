// src/components/RegimeChart.jsx

const REGIME_COLORS = {
  free_flow: { bg: "#071A13", text: "#6EE7B7", border: "#00C896" },
  slow:      { bg: "#1C1A06", text: "#FDE68A", border: "#F59E0B" },
  congested: { bg: "#1F1208", text: "#FDBA74", border: "#F97316" },
  gridlock:  { bg: "#2D0A0A", text: "#FCA5A5", border: "#EF4444" },
  unknown:   { bg: "#111827", text: "#9CA3AF", border: "#374151" },
};

function RegimePill({ regime }) {
  const r = regime || "unknown";
  const c = REGIME_COLORS[r] || REGIME_COLORS.unknown;
  return (
    <span style={{
      background:    c.bg,
      color:         c.text,
      border:        `1px solid ${c.border}`,
      borderRadius:  "5px",
      padding:       "2px 8px",
      fontSize:      "10px",
      fontWeight:    700,
      letterSpacing: "0.5px",
      fontFamily:    "monospace",
      textTransform: "uppercase",
      whiteSpace:    "nowrap",
    }}>
      {r.replace("_", " ")}
    </span>
  );
}

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

  // Match dashboard.py: show up to 12 clusters
  const items = summary.slice(0, 12);

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Predicted Next Regime</span>
        <span className="panel-badge">MARKOV CHAIN</span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "6px", padding: "4px 0" }}>
        {items.map((c) => {
          // API field is 'predicted', fall back to 'regime' — matches dashboard.py logic
          const predicted = c.predicted || c.regime || "unknown";
          const current   = c.regime    || "unknown";

          return (
            <div key={c.cluster_id} style={{
              display:      "flex",
              alignItems:   "center",
              gap:          "10px",
              padding:      "5px 8px",
              background:   "#0A1520",
              borderRadius: "6px",
              border:       "1px solid #1E2D40",
            }}>
              {/* Cluster ID */}
              <span style={{
                fontFamily: "monospace", fontSize: "11px",
                color: "#64748B", minWidth: "22px", textAlign: "right",
              }}>
                {c.cluster_id}
              </span>

              {/* Current regime */}
              <RegimePill regime={current} />

              {/* Arrow */}
              <span style={{ color: "#334155", fontSize: "13px" }}>→</span>

              {/* Predicted next regime */}
              <RegimePill regime={predicted} />

              {/* Location name (added by updated api.py /summary) */}
              {c.location_name && (
                <span style={{
                  marginLeft:   "auto",
                  fontSize:     "10px",
                  color:        "#475569",
                  fontFamily:   "monospace",
                  overflow:     "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace:   "nowrap",
                  maxWidth:     "120px",
                }}>
                  {c.location_name}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}