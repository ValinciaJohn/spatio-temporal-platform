// src/components/ClusterTable.jsx
function RegimeBadge({ regime }) {
  const r = regime || "unknown";
  return <span className={`regime-badge regime-${r}`}>{r}</span>;
}

export default function ClusterTable({ summary }) {
  if (!summary || summary.length === 0) {
    return (
      <div className="panel">
        <div className="panel-header">
          <span className="panel-title">Cluster Intelligence</span>
          <span className="panel-badge">ST-DBSCAN</span>
        </div>
        <div className="no-data">No clusters detected yet</div>
      </div>
    );
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Cluster Intelligence</span>
        <span className="panel-badge">{summary.length} CLUSTERS</span>
      </div>
      <div className="cluster-table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>SIZE</th>
              <th>REGIME</th>
              <th>HOTSPOT</th>
              <th>NEXT REGIME</th>
              <th>AVG SPD</th>
              <th>LAT</th>
              <th>LON</th>
            </tr>
          </thead>
          <tbody>
            {summary.map((c) => (
              <tr key={c.cluster_id}>
                <td className="mono-val">{c.cluster_id}</td>
                <td className="mono-val">{c.size}</td>
                <td><RegimeBadge regime={c.regime} /></td>
                <td>
                  {c.is_hotspot
                    ? <span className="hotspot-yes">● YES</span>
                    : <span className="hotspot-no">● NO</span>}
                </td>
                <td><RegimeBadge regime={c.predicted || c.regime} /></td>
                <td className="mono-val">{(c.avg_speed ?? 0).toFixed(1)}</td>
                <td className="mono-val">{(c.centroid_lat ?? 0).toFixed(4)}</td>
                <td className="mono-val">{(c.centroid_lon ?? 0).toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}