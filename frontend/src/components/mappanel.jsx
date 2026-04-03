// src/components/MapPanel.jsx
import { useState, useEffect } from "react";

const API = "http://localhost:8000/api";

export default function MapPanel({ tick }) {
  const [html, setHtml]   = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/map`)
      .then((r) => r.text())
      .then((h) => { setHtml(h); setLoading(false); })
      .catch(() => setLoading(false));
  }, [tick]);

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Live Congestion Map</span>
        <span className="panel-badge">FOLIUM · 5s REFRESH</span>
      </div>
      <div className="map-panel">
        {loading ? (
          <div className="map-loading">
            <div className="map-spinner" />
            <span>Waiting for map data…</span>
          </div>
        ) : (
          <iframe
            srcDoc={html}
            title="Live Traffic Map"
            sandbox="allow-scripts allow-same-origin"
          />
        )}
      </div>
    </div>
  );
}