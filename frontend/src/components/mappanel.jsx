import { useState, useEffect, useRef } from "react";

const API = "/api";

const PLACEHOLDER = `
<html>
<head><style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #0A0F1E;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    height: 100vh;
    font-family: "Courier New", monospace;
    color: #334155;
    gap: 14px;
  }
  .pulse-ring {
    width: 52px; height: 52px;
    border: 2px solid #1E3A5F;
    border-top-color: #38BDF8;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .msg { font-size: 13px; color: #475569; letter-spacing: 1px; }
  .sub { font-size: 11px; color: #1E3A5F; letter-spacing: 0.5px; }
</style></head>
<body>
  <div class="pulse-ring"></div>
  <div class="msg">⬡ AWAITING MAP DATA</div>
  <div class="sub">Kafka stream initialising…</div>
</body>
</html>`;

export default function MapPanel({ tick }) {
  const [html, setHtml]         = useState(PLACEHOLDER);
  const [hasRealMap, setHasRealMap] = useState(false);
  const intervalRef             = useRef(null);

  const fetchMap = async () => {
    try {
      const r = await fetch(`${API}/map`);
      if (!r.ok) return;
      const text = await r.text();
      // The backend returns a waiting-message HTML when live_map.html doesn't exist yet
      const isReal = text.includes("folium") || text.includes("leaflet");
      if (isReal) {
        setHtml(text);
        setHasRealMap(true);
      }
    } catch (_) {}
  };

  useEffect(() => {
    // Fetch immediately on mount — no waiting for first tick
    fetchMap();
  }, []);

  // While no real map: poll every 2s; once we have it: poll every 5s (driven by tick)
  useEffect(() => {
    if (hasRealMap) {
      // Handed off to tick-based refresh below; clear fast poller
      if (intervalRef.current) clearInterval(intervalRef.current);
      return;
    }
    if (intervalRef.current) clearInterval(intervalRef.current);
    intervalRef.current = setInterval(fetchMap, 2000);
    return () => clearInterval(intervalRef.current);
  }, [hasRealMap]);

  // Normal 5s refresh once map is live (driven by parent tick)
  useEffect(() => {
    if (hasRealMap) fetchMap();
  }, [tick]);

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Live Congestion Map</span>
        <span className="panel-badge">
          {hasRealMap ? "FOLIUM · 5s REFRESH" : "WAITING FOR STREAM…"}
        </span>
      </div>
      <div className="map-panel">
        <iframe
          srcDoc={html}
          title="Live Traffic Map"
          sandbox="allow-scripts allow-same-origin"
          style={{ width: "100%", height: "100%", border: "none", borderRadius: "8px" }}
        />
      </div>
    </div>
  );
}