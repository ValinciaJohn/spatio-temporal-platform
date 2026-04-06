export default function StatsBar({ stats, summary }) {
  const s = stats || {};

  const sil = s.silhouette ?? 0;
  const silColor = sil > 0.3 ? "green" : sil > 0 ? "yellow" : "red";
  const stab = s.stability_now ?? s.stability ?? 1;
  const stabColor = stab > 0.7 ? "green" : stab > 0.4 ? "yellow" : "red";

  const lastUpd = s.last_updated
    ? new Date(s.last_updated * 1000).toLocaleTimeString()
    : "—";

  // Derive counts directly from summary array 
  const clusterCount = Array.isArray(summary) ? summary.length : (s.clusters ?? 0);
  const hotspotCount = Array.isArray(summary)
    ? summary.filter(c => c.is_hotspot).length
    : (s.hotspots ?? 0);

  const cards = [
    { label: "CLUSTERS",     value: clusterCount,                        color: "cyan" },
    { label: "HOTSPOTS",     value: hotspotCount,                        color: hotspotCount > 0 ? "red" : "" },
    { label: "ANOMALIES",    value: s.anomalies    ?? 0,                 color: (s.anomalies ?? 0) > 0 ? "yellow" : "" },
    { label: "BATCHES",      value: s.batches      ?? 0,                 color: "" },
    { label: "DRIFT EVENTS", value: s.drift_events ?? 0,                 color: (s.drift_events ?? 0) > 0 ? "orange" : "" },
    { label: "SILHOUETTE",   value: sil.toFixed(3),                      color: silColor },
    { label: "STABILITY",    value: stab.toFixed(3),                     color: stabColor },
    { label: "NOISE %",      value: `${(s.noise_pct ?? 0).toFixed(1)}%`, color: "" },
    { label: "UPDATED",      value: lastUpd,                             color: "", small: true },
  ];

  return (
    <div className="stats-bar">
      {cards.map((c) => (
        <div key={c.label} className={`stat-card ${c.color}`}>
          <div className="stat-label">{c.label}</div>
          <div className={`stat-value ${c.color} ${c.small ? "small-val" : ""}`}>
            {c.value}
          </div>
        </div>
      ))}
    </div>
  );
}