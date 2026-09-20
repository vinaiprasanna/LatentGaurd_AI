import { useState } from "react";

function getRiskLevel(score) {
  if (score >= 0.85) return "CRITICAL";
  if (score >= 0.65) return "HIGH";
  if (score >= 0.4) return "MEDIUM";
  return "LOW";
}

function getRiskColor(score) {
  if (score >= 0.85) return "#ef4444";
  if (score >= 0.65) return "#f97316";
  if (score >= 0.4) return "#eab308";
  return "#22c55e";
}

function RiskHeatmap({ anomalyData: propData, onSelect }) {
  const [hoveredCell, setHoveredCell] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  const data = propData || [];
  const observedCheckpoints = [...new Set(data.map((component) => Number(component.checkpoint_h)).filter(Number.isFinite))].sort((a, b) => a - b);
  const currentCheckpoint = observedCheckpoints.length ? `${observedCheckpoints.at(-1)}h` : "Current";
  const anomalyCount = data.filter((component) => component.anomaly_decision === "ANOMALY").length;
  const highestRisk = data.reduce((highest, component) => {
    const score = getRiskScore(component);
    return score > highest.score ? { id: component.dut_id || component.dutId, score } : highest;
  }, { id: '--', score: 0 });

  function getRiskScore(component) {
    const rawScore = Number(component.risk_score);
    if (Number.isFinite(rawScore)) return rawScore;
    if (component.risk_band) {
      const riskScores = { LOW: 20, MEDIUM: 50, HIGH: 75, CRITICAL: 92 };
      return riskScores[component.risk_band] || 0;
    }
    return 0;
  }

  const getComponentScore = (component) => {
    return getRiskScore(component);
  };

  if (!data.length) {
    return (
      <div className="heatmap-container">
        <p>No risk heatmap data is available for the current upload.</p>
      </div>
    );
  }

  return (
    <div className="heatmap-container">
      <div className="heatmap-scroll">
        <div className="chamber-tray">
          <div className="chamber-rail chamber-rail-top"><span>CHAMBER RAIL A</span><strong>{currentCheckpoint} LIVE</strong></div>
          <div className="tray-summary">
            <div><span>OCCUPIED</span><strong>{data.length}</strong></div>
            <div><span>ANOMALIES</span><strong className={anomalyCount ? 'summary-alert' : ''}>{anomalyCount}</strong></div>
            <div><span>PEAK RISK</span><strong className={highestRisk.score >= 60 ? 'summary-alert' : ''}>{highestRisk.id} · {highestRisk.score.toFixed(1)}</strong></div>
          </div>
          <div className="tray-grid">
            {data.map((component, index) => {
              const riskScore = getComponentScore(component);
              const score = Math.min(Math.max(riskScore / 100, 0), 1);
              const dutId = component.dut_id || component.dutId;
              const cellId = `${dutId}-${currentCheckpoint}`;
              return (
                  <div key={cellId} className="tray-slot"
                    style={{
                      '--slot-color': getRiskColor(score),
                      '--slot-fill': `linear-gradient(145deg, ${getRiskColor(score)}cc, ${getRiskColor(score)}44)`,
}}
                    onMouseEnter={(event) => {
                      setHoveredCell({ dutId, checkpoint: currentCheckpoint, score: riskScore, risk: getRiskLevel(riskScore / 100) });
                      const container = event.currentTarget.closest(".heatmap-container");
                      const rect = container.getBoundingClientRect();
                      setTooltipPosition({ x: event.clientX - rect.left + 14, y: event.clientY - rect.top + 14 });
                    }}
                    onMouseMove={(event) => {
                      const container = event.currentTarget.closest(".heatmap-container");
                      const rect = container.getBoundingClientRect();
                      setTooltipPosition({ x: event.clientX - rect.left + 14, y: event.clientY - rect.top + 14 });
                    }}
                    onMouseLeave={() => setHoveredCell(null)}
                    onClick={() => onSelect?.(component)}
                  >
                    <span className="tray-slot-number">{String(index + 1).padStart(2, '0')}</span>
                    <strong>{dutId}</strong>
                    <span className="tray-slot-score">{riskScore.toFixed(1)}</span>
                  </div>
              );
            })}
          </div>
          <div className="chamber-rail chamber-rail-bottom"><span>CHAMBER RAIL B</span><span>THERMAL TELEMETRY ACTIVE</span></div>
        </div>
      </div>
      {hoveredCell && (
        <div className="heatmap-tooltip" style={{ left: `${tooltipPosition.x}px`, top: `${tooltipPosition.y}px` }}>
          <strong>{hoveredCell.dutId}</strong>
          <span>Checkpoint: {hoveredCell.checkpoint}</span>
          <span>Risk Score: {hoveredCell.score?.toFixed(1)}</span>
          <span>Risk Level: {hoveredCell.risk}</span>
        </div>
      )}
      <div className="heatmap-legend">
        <span><i style={{ background: "#22c55e" }}></i>Low</span>
        <span><i style={{ background: "#eab308" }}></i>Medium</span>
        <span><i style={{ background: "#f97316" }}></i>High</span>
        <span><i style={{ background: "#ef4444" }}></i>Critical</span>
      </div>
    </div>
  );
}

export default RiskHeatmap;
