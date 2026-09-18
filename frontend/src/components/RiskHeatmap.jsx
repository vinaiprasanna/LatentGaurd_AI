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

function RiskHeatmap({ anomalyData: propData }) {
  const [hoveredCell, setHoveredCell] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  const checkpoints = ["0h", "24h", "96h", "168h"];

  const data = propData || [];

  const getComponentScore = (component, index) => {
    const rawScore = Number(component.risk_score);
    if (Number.isFinite(rawScore)) return rawScore;
    const riskScores = { LOW: 20, MEDIUM: 50, HIGH: 75, CRITICAL: 92 };
    return riskScores[component.risk_band] || 10 + index * 8;
  };

  return (
    <div className="heatmap-container">
      <div className="heatmap-scroll">
        <div className="heatmap-grid">
          <div className="heatmap-corner">DUT ID</div>
          {checkpoints.map((checkpoint) => (
            <div className="heatmap-header" key={checkpoint}>{checkpoint}</div>
          ))}
          {data.map((component) => (
            <div className="heatmap-row" key={component.dut_id || component.dutId}>
              <div className="dut-label">{component.dut_id || component.dutId}</div>
              {checkpoints.map((checkpoint, index) => {
                const riskScore = getComponentScore(component, index);
                const score = Math.min(Math.max(riskScore / 100, 0), 1);
                const cellId = `${component.dut_id || component.dutId}-${checkpoint}`;
                return (
                  <div key={cellId} className="heatmap-cell"
                    style={{
  background: `linear-gradient(
    135deg,
    ${getRiskColor(score)}aa,
    ${getRiskColor(score)}66
  )`,
  border: `1px solid ${getRiskColor(score)}dd`,
  boxShadow: `
    inset 0 1px 0 rgba(255, 255, 255, 0.28),
    inset 0 -10px 18px rgba(0, 0, 0, 0.16),
    0 0 12px ${getRiskColor(score)}45
  `,
}}
                    onMouseEnter={(event) => {
                      setHoveredCell({ dutId: component.dut_id || component.dutId, checkpoint, score: riskScore, risk: getRiskLevel(riskScore / 100) });
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
                  >
                    {riskScore.toFixed(1)}
                  </div>
                );
              })}
            </div>
          ))}
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
