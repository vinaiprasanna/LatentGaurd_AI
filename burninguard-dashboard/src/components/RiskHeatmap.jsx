import { useState } from "react";

const checkpoints = ["0h", "24h", "48h", "72h", "96h", "120h", "144h", "168h"];

const components = [
  {
    dutId: "DUT-0001",
    scores: [0.12, 0.18, 0.24, 0.31, 0.42, 0.55, 0.68, 0.82],
  },
  {
    dutId: "DUT-0002",
    scores: [0.08, 0.16, 0.22, 0.38, 0.51, 0.72, 0.86, 0.93],
  },
  {
    dutId: "DUT-0003",
    scores: [0.10, 0.14, 0.19, 0.27, 0.33, 0.41, 0.48, 0.52],
  },
  {
    dutId: "DUT-0004",
    scores: [0.18, 0.23, 0.32, 0.44, 0.58, 0.64, 0.71, 0.78],
  },
  {
    dutId: "DUT-0005",
    scores: [0.06, 0.12, 0.18, 0.25, 0.31, 0.36, 0.43, 0.49],
  },
  {
    dutId: "DUT-0006",
    scores: [0.21, 0.29, 0.36, 0.48, 0.61, 0.74, 0.81, 0.91],
  },
  {
    dutId: "DUT-0007",
    scores: [0.09, 0.17, 0.28, 0.35, 0.45, 0.51, 0.63, 0.69],
  },
  {
    dutId: "DUT-0008",
    scores: [0.13, 0.20, 0.26, 0.34, 0.47, 0.59, 0.73, 0.88],
  },
  {
    dutId: "DUT-0009",
    scores: [0.05, 0.11, 0.15, 0.21, 0.29, 0.37, 0.44, 0.50],
  },
  {
    dutId: "DUT-0010",
    scores: [0.17, 0.25, 0.39, 0.52, 0.67, 0.79, 0.88, 0.96],
  },
  {
    dutId: "DUT-0011",
    scores: [0.11, 0.19, 0.27, 0.33, 0.41, 0.53, 0.62, 0.76],
  },
  {
    dutId: "DUT-0012",
    scores: [0.07, 0.13, 0.21, 0.29, 0.35, 0.48, 0.57, 0.66],
  },
];

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

function RiskHeatmap() {
  const [hoveredCell, setHoveredCell] = useState(null);
const [tooltipPosition, setTooltipPosition] = useState({
  x: 0,
  y: 0,
});

  return (
    <div className="heatmap-container">
      <div className="heatmap-scroll">
        <div className="heatmap-grid">
          <div className="heatmap-corner">
            DUT ID
          </div>

          {checkpoints.map((checkpoint) => (
            <div className="heatmap-header" key={checkpoint}>
              {checkpoint}
            </div>
          ))}

          {components.map((component) => (
            <div className="heatmap-row" key={component.dutId}>
              <div className="dut-label">
                {component.dutId}
              </div>

              {component.scores.map((score, index) => {
                const cellId = `${component.dutId}-${checkpoints[index]}`;

                return (
                  <div
                    key={cellId}
                    className="heatmap-cell"
                    style={{
  background: `linear-gradient(
    135deg,
    ${getRiskColor(score)}55,
    ${getRiskColor(score)}22
  )`,
  border: `1px solid ${getRiskColor(score)}66`,
  boxShadow: `
    inset 0 1px 0 rgba(255, 255, 255, 0.30),
    inset 0 -10px 18px rgba(0, 0, 0, 0.12),
    0 0 14px ${getRiskColor(score)}35
  `,
}}
                    onMouseEnter={(event) => {
  setHoveredCell({
    dutId: component.dutId,
    checkpoint: checkpoints[index],
    score,
    risk: getRiskLevel(score),
  });

  const container = event.currentTarget.closest(".heatmap-container");
  const rect = container.getBoundingClientRect();

  setTooltipPosition({
    x: event.clientX - rect.left + 14,
    y: event.clientY - rect.top + 14,
  });
}}

onMouseMove={(event) => {
  const container = event.currentTarget.closest(".heatmap-container");
  const rect = container.getBoundingClientRect();

  setTooltipPosition({
    x: event.clientX - rect.left + 14,
    y: event.clientY - rect.top + 14,
  });
}}
                    onMouseLeave={() => setHoveredCell(null)}
                  >
                    {score.toFixed(2)}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      {hoveredCell && (
        <div
  className="heatmap-tooltip"
  style={{
    left: `${tooltipPosition.x}px`,
    top: `${tooltipPosition.y}px`,
  }}
>
          <strong>{hoveredCell.dutId}</strong>

          <span>
            Checkpoint: {hoveredCell.checkpoint}
          </span>

          <span>
            Risk Score: {hoveredCell.score.toFixed(2)}
          </span>

          <span>
            Risk Level: {hoveredCell.risk}
          </span>
        </div>
      )}

      <div className="heatmap-legend">
        <span>
          <i style={{ background: "#22c55e" }}></i>
          Low
        </span>

        <span>
          <i style={{ background: "#eab308" }}></i>
          Medium
        </span>

        <span>
          <i style={{ background: "#f97316" }}></i>
          High
        </span>

        <span>
          <i style={{ background: "#ef4444" }}></i>
          Critical
        </span>
      </div>
    </div>
  );
}

export default RiskHeatmap;